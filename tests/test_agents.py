"""
Testes para Research Agent, PRD Agent e Spec Builder Agent.
"""

import pytest
import tempfile
from pathlib import Path

from cvg_harness.research.research_agent import (
    ResearchAgent, ResearchNote, SystemMap,
    save_research, save_system_map, load_research, load_system_map
)
from cvg_harness.prd.prd_agent import PRDAgent, PRD, save_prd, load_prd
from cvg_harness.spec_builder.spec_builder import SpecBuilderAgent, Spec, save_spec, load_spec


def test_research_agent_infer_modules_auth():
    """Research Agent infere módulo auth corretamente."""
    agent = ResearchAgent()
    modules = agent._infer_modules("adição de autenticação OAuth2", "ENTERPRISE")
    assert "auth" in modules


def test_research_agent_infer_modules_api():
    """Research Agent infere módulo API."""
    agent = ResearchAgent()
    modules = agent._infer_modules("novo endpoint REST", "FAST")
    assert "api" in modules


def test_research_agent_investigate():
    """Research Agent gera notas e mapa."""
    agent = ResearchAgent()
    classification = {"mode": "ENTERPRISE", "total_score": 15}
    research, system_map = agent.investigate("proj", "OAuth2 auth", classification)

    assert research.project == "proj"
    assert len(research.modulos_impactados) > 0
    assert len(research.fatos) > 0
    assert system_map.project == "proj"
    assert len(system_map.modulos) > 0


def test_research_agent_uses_workspace_evidence(tmp_path: Path):
    """Research Agent preenche módulos e arquivos de área com evidência local quando disponível."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "api").mkdir(parents=True)
    (tmp_path / "src" / "api" / "endpoints.py").write_text("def get_feature():\n    return 'flow'\n")
    (tmp_path / "src" / "core").mkdir(parents=True)
    (tmp_path / "src" / "core" / "engine.py").write_text("# placeholder\n")

    agent = ResearchAgent()
    classification = {"mode": "FAST", "total_score": 5}
    research, system_map = agent.investigate(
        str(tmp_path),
        "novo fluxo de endpoint REST no api",
        classification,
        workspace=tmp_path,
    )

    assert research.modulos_impactados
    assert any(m in research.modulos_impactados for m in {"api", "core"})
    assert any("src/api/" in item for item in system_map.arquivos_area)


def test_research_agent_fallback_when_no_workspace_evidence():
    """Sem raiz de projeto válida, mantém caminho heurístico + hipótese rastreável."""
    agent = ResearchAgent()
    classification = {"mode": "ENTERPRISE", "total_score": 15}
    research, system_map = agent.investigate(
        "projeto-inexistente-qualquer",
        "OAuth2 auth",
        classification,
        workspace=Path("projeto-inexistente-qualquer"),
    )

    assert research.modulos_impactados
    assert research.hipoteses
    assert system_map.modulos


def test_research_persistence():
    """Salva e carrega research notes."""
    research = ResearchNote(
        project="proj",
        feature="test",
        fatos=["fato 1"],
        hipoteses=["hipotese 1"],
        riscos=["risco 1"],
        modulos_impactados=["auth"],
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        path = Path(f.name)
    save_research(research, path)
    loaded = load_research(path)
    assert loaded.project == "proj"
    assert "fato 1" in loaded.fatos
    path.unlink()


def test_prd_agent_create_prd():
    """PRD Agent cria PRD corretamente."""
    agent = PRDAgent()
    research_notes = {"modulos_impactados": ["auth"], "riscos": ["regressão"]}
    classification = {"mode": "ENTERPRISE", "total_score": 15}

    prd = agent.create_prd("proj", "OAuth2 auth", research_notes, classification)

    assert prd.project == "proj"
    assert prd.feature == "OAuth2 auth"
    assert len(prd.objetivo) > 0
    assert len(prd.escopo) > 0
    assert len(prd.fora_de_escopo) > 0


def test_prd_agent_scope_enterprise():
    """PRD Agent adiciona mais itens ao escopo em ENTERPRISE."""
    agent = PRDAgent()
    research = {"modulos_impactados": ["auth"], "riscos": []}
    classification = {"mode": "ENTERPRISE", "total_score": 15}

    prd = agent.create_prd("proj", "test", research, classification)

    assert "Validação de contrato de API" in prd.escopo
    assert "Testes de regressão" in prd.escopo


def test_prd_agent_uses_research_modules_auth():
    """PRD ganha diferenciação real quando research aponta módulos/auth."""
    agent = PRDAgent()
    research = {
        "modulos_impactados": ["auth", "api", "metrics_agg"],
        "riscos": ["sessão de usuário pode quebrar login social"],
        "restricoes": ["não alterar fluxo de sessão existente"],
        "fatos": ["Feature analisada com evidência local em src/auth/"],
    }
    classification = {"mode": "ENTERPRISE", "total_score": 15}

    prd = agent.create_prd("proj", "melhorar fluxo OAuth2", research, classification)

    assert "src/auth/" in prd.problema
    assert "não alterar fluxo de sessão existente" in prd.objetivo
    assert "Validar autenticação, autorização e cenários de sessão crítica" in prd.escopo
    assert any("restrição operacional" in risco.lower() for risco in prd.riscos)
    assert any("autenticado" in story.lower() for story in prd.user_stories)
    assert any("Restrição preservada" in criterio for criterio in prd.criterios_aceite)


def test_prd_agent_releases_scope_fast():
    """PRD para fluxo de release contempla rastreabilidade canônica."""
    agent = PRDAgent()
    research = {
        "modulos_impactados": ["release", "gates"],
        "riscos": ["dependência de gateway externo de aprovação"],
    }
    classification = {"mode": "FAST", "total_score": 8}

    prd = agent.create_prd("proj", "release readiness gates", research, classification)

    assert "Regras de promoção e rastreio de readiness" in prd.escopo
    assert any("dependência" in r.lower() for r in prd.riscos)
    assert any("operador" in story.lower() for story in prd.user_stories)


def test_prd_agent_changes_materially_with_research_context():
    """PRDs distintos são gerados quando o research muda de auth para release."""
    agent = PRDAgent()
    auth_research = {
        "modulos_impactados": ["auth"],
        "riscos": ["regressão em autenticação"],
        "restricoes": ["preservar fluxo de sessão"],
        "fatos": ["Contexto observado: src/auth"],
    }
    release_research = {
        "modulos_impactados": ["release", "gates"],
        "riscos": ["gate obrigatório pode bloquear promoção"],
        "restricoes": ["manter trilha de aprovação"],
        "fatos": ["Contexto observado: src/cvg_harness/release"],
    }

    auth_prd = agent.create_prd("proj", "melhorar auth", auth_research, {"mode": "ENTERPRISE", "total_score": 15})
    release_prd = agent.create_prd("proj", "melhorar release", release_research, {"mode": "FAST", "total_score": 8})

    assert auth_prd.problema != release_prd.problema
    assert auth_prd.objetivo != release_prd.objetivo
    assert auth_prd.escopo != release_prd.escopo
    assert auth_prd.criterios_aceite != release_prd.criterios_aceite


def test_prd_persistence():
    """Salva e carrega PRD."""
    prd = PRD(
        project="proj",
        feature="test",
        problema="problema",
        objetivo="objetivo",
        kpis=["kpi 1"],
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        path = Path(f.name)
    save_prd(prd, path)
    loaded = load_prd(path)
    assert loaded.project == "proj"
    assert loaded.objetivo == "objetivo"
    path.unlink()


def test_spec_builder_build():
    """Spec Builder constrói SPEC correta."""
    builder = SpecBuilderAgent()
    prd = {
        "objetivo": "implementar auth",
        "escopo": ["implementar auth"],
        "criterios_aceite": ["auth funciona"],
    }
    research = {
        "modulos_impactados": ["auth"],
        "arquivos_area": ["src/auth/"],
        "zonas_criticas": ["src/auth"],
        "boundaries": ["src/legacy"],
    }
    classification = {"mode": "FAST", "total_score": 5}

    spec = builder.build(prd, research, classification)

    assert spec.meta == "implementar auth"
    assert "auth" in spec.modulos
    assert "src/auth/" in spec.areas_autorizadas
    assert spec.version == "v1"


def test_spec_builder_edge_cases():
    """Spec Builder sugere edge cases corretos."""
    builder = SpecBuilderAgent()
    spec = builder.build(
        {"objetivo": "test", "escopo": [], "criterios_aceite": []},
        {"modulos_impactados": ["auth", "api"], "arquivos_area": [], "zonas_criticas": [], "boundaries": []},
        {"mode": "FAST", "total_score": 5},
    )
    assert "token expirado" in spec.edge_cases
    assert "payload inválido" in spec.edge_cases


def test_spec_builder_contracts_and_criteria_gaps():
    """Spec Builder adiciona contratos e marca lacunas explícitas quando necessário."""
    builder = SpecBuilderAgent()
    spec = builder.build(
        {
            "objetivo": "adicionar endpoint de autenticação para usuários",
            "escopo": ["implementar auth endpoint"],
            "criterios_aceite": ["auth funciona", "Feature implementada e funcionando"],
        },
        {
            "modulos_impactados": ["auth", "api", "release", "gates"],
            "arquivos_area": ["src/auth/", "src/api/"],
            "zonas_criticas": ["src/auth", "src/api"],
            "boundaries": ["src/legacy"],
        },
        {"mode": "ENTERPRISE", "total_score": 15},
    )

    api_contracts = [c for c in spec.contratos if c.get("tipo") == "integracao"]
    assert api_contracts, "espera contrato de integração para módulo api"
    assert any("exemplo_payload" in contrato for contrato in api_contracts)
    assert any(c.get("criticidade") == "high" for c in spec.contratos)
    assert any(c.get("superficie") == "auth" for c in spec.contratos)
    assert any(c.get("evidencia_minima") for c in spec.contratos)
    assert any(c["testavel"] is False and c["definido_como_lacuna"] for c in spec.criterios), (
        "espera ao menos uma lacuna explícita em critérios"
    )
    assert any(c["tipo"] == "auth" for c in spec.contratos)
    assert any(c["tipo"] == "processo" for c in spec.contratos)


def test_spec_builder_contextual_observability_and_rollback():
    """Spec Builder deixa observabilidade e rollback específicos quando o contexto exige."""
    builder = SpecBuilderAgent()
    spec = builder.build(
        {
            "objetivo": "revisar readiness de release com database e auth",
            "escopo": ["release", "database"],
            "criterios_aceite": ["release coerente"],
        },
        {
            "modulos_impactados": ["auth", "release", "database"],
            "arquivos_area": ["src/auth/", "src/release/", "src/database/"],
            "zonas_criticas": ["src/auth", "src/release", "src/database"],
            "boundaries": ["src/legacy"],
        },
        {"mode": "ENTERPRISE", "total_score": 15},
    )

    assert "sessão" in spec.observabilidade.lower()
    assert "readiness" in spec.observabilidade.lower()
    assert "migração" in spec.rollback.lower() or "snapshot" in spec.rollback.lower()


def test_spec_persistence():
    """Salva e carrega SPEC."""
    spec = Spec(
        meta="test",
        modulos=["auth"],
        areas_autorizadas=["src/auth/"],
        areas_proibidas=["src/legacy/"],
    )
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        path = Path(f.name)
    save_spec(spec, path)
    loaded = load_spec(path)
    assert loaded.meta == "test"
    assert "auth" in loaded.modulos
    path.unlink()
