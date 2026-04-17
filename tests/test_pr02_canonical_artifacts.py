"""
PR-02: Testes de artefatos canônicos e geração consistente
Valida que agentes geram .md legíveis e .json determinístico
com versões sincronizadas.
"""

import pytest
import tempfile
from pathlib import Path

from cvg_harness.research.research_agent import (
    ResearchAgent, ResearchNote, SystemMap,
    save_research_markdown, save_system_map_markdown,
    render_research_notes_markdown, render_system_map_markdown,
    save_research, save_system_map, load_research, load_system_map
)
from cvg_harness.prd.prd_agent import (
    PRDAgent, PRD,
    save_prd_markdown, render_prd_markdown,
    save_prd, load_prd
)
from cvg_harness.spec_builder.spec_builder import (
    SpecBuilderAgent, Spec,
    save_spec_markdown, render_spec_markdown,
    save_spec_pair, save_spec, load_spec
)
from cvg_harness.contracts.artifact_contracts import validate_artifact


class TestResearchAgentMarkdown:
    """Valida geração de research-notes.md e system-map.md."""

    def test_research_notes_markdown_generation(self):
        """Research notes pode ser gerado como markdown."""
        agent = ResearchAgent()
        research, _ = agent.investigate("proj", "OAuth2 authentication", {"mode": "ENTERPRISE", "total_score": 15})

        md = render_research_notes_markdown(research)
        assert "# Research Notes" in md
        assert "OAuth2 authentication" in md
        assert "## Facts" in md
        assert "## Riscos" in md
        assert "## Módulos Impactados" in md

    def test_system_map_markdown_generation(self):
        """System map pode ser gerado como markdown."""
        agent = ResearchAgent()
        _, system_map = agent.investigate("proj", "OAuth2 authentication", {"mode": "ENTERPRISE", "total_score": 15})

        md = render_system_map_markdown(system_map)
        assert "# System Map" in md
        assert "OAuth2 authentication" in md
        assert "## Módulos" in md
        assert "## Boundaries" in md

    def test_research_save_markdown_file(self):
        """Research Agent salva research-notes.md corretamente."""
        agent = ResearchAgent()
        research, _ = agent.investigate("proj", "feature", {"mode": "FAST", "total_score": 5})

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "research-notes.md"
            save_research_markdown(research, path)
            assert path.exists()
            content = path.read_text()
            assert "# Research Notes" in content

    def test_system_map_save_markdown_file(self):
        """Research Agent salva system-map.md corretamente."""
        agent = ResearchAgent()
        _, system_map = agent.investigate("proj", "feature", {"mode": "FAST", "total_score": 5})

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "system-map.md"
            save_system_map_markdown(system_map, path)
            assert path.exists()
            content = path.read_text()
            assert "# System Map" in content

    def test_research_investigate_with_workspace_evidence(self, tmp_path: Path):
        """Research Agent separa evidência observada quando workspace é informativo."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "metrics").mkdir(parents=True)
        (tmp_path / "src" / "metrics" / "collector.py").write_text("def collect():\n    return 0\n")

        agent = ResearchAgent()
        research, system_map = agent.investigate(
            str(tmp_path),
            "melhorar fluxo de métricas",
            {"mode": "FAST", "total_score": 5},
            workspace=tmp_path,
        )

        assert "src/metrics/" in system_map.arquivos_area
        assert any("metrics" in f for f in research.fatos)


class TestPRDAgentMarkdown:
    """Valida geração de prd.md."""

    def test_prd_markdown_generation(self):
        """PRD pode ser gerado como markdown."""
        agent = PRDAgent()
        prd = agent.create_prd("proj", "feature", {"modulos_impactados": ["auth"]}, {"mode": "FAST", "total_score": 5})

        md = render_prd_markdown(prd)
        assert "# PRD:" in md
        assert "feature" in md
        assert "## Problema" in md
        assert "## Objetivo" in md
        assert "## Escopo" in md
        assert "## KPIs" in md

    def test_prd_save_markdown_file(self):
        """PRD Agent salva prd.md corretamente."""
        agent = PRDAgent()
        prd = agent.create_prd("proj", "feature", {}, {"mode": "FAST", "total_score": 5})

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "prd.md"
            save_prd_markdown(prd, path)
            assert path.exists()
            content = path.read_text()
            assert "# PRD:" in content

    def test_prd_markdown_reflects_research_constraints(self):
        """PRD markdown expõe restrições e critérios derivados do research."""
        agent = PRDAgent()
        prd = agent.create_prd(
            "proj",
            "release readiness gates",
            {
                "modulos_impactados": ["release", "gates"],
                "riscos": ["gate inconsistente pode bloquear promoção"],
                "restricoes": ["manter trilha de aprovação"],
                "fatos": ["Contexto observado: src/cvg_harness/release"],
            },
            {"mode": "FAST", "total_score": 8},
        )

        md = render_prd_markdown(prd)
        assert "manter trilha de aprovação" in md
        assert "Gates e evidência de readiness permanecem coerentes" in md
        assert "src/cvg_harness/release" in md


class TestSpecBuilderMarkdownAndJson:
    """Valida que spec.md e spec.json são gerados juntos com versão sincronizada."""

    def test_spec_markdown_generation(self):
        """Spec pode ser gerado como markdown."""
        agent = SpecBuilderAgent()
        spec = agent.build(
            prd={"objetivo": "implementar auth", "escopo": ["auth"], "criterios_aceite": ["auth funciona"]},
            research_notes={"modulos_impactados": ["auth"], "arquivos_area": ["src/auth/"], "zonas_criticas": [], "boundaries": []},
            classification={"mode": "FAST", "total_score": 5}
        )

        md = render_spec_markdown(spec)
        assert "# SPEC:" in md
        assert "## Meta" in md
        assert "## Módulos Afetados" in md
        assert "## Áreas Autorizadas" in md
        assert "## Critérios de Aceite" in md

    def test_spec_save_markdown_file(self):
        """Spec Builder salva spec.md corretamente."""
        agent = SpecBuilderAgent()
        spec = agent.build(
            prd={"objetivo": "test", "escopo": [], "criterios_aceite": []},
            research_notes={"modulos_impactados": ["core"], "arquivos_area": [], "zonas_criticas": [], "boundaries": []},
            classification={"mode": "FAST", "total_score": 5}
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "spec.md"
            save_spec_markdown(spec, path)
            assert path.exists()
            content = path.read_text()
            assert "# SPEC:" in content

    def test_spec_pair_synchronized_version(self):
        """spec.json e spec.md compartilham a mesma versão."""
        agent = SpecBuilderAgent()
        spec = agent.build(
            prd={"objetivo": "implementar feature", "escopo": ["core"], "criterios_aceite": ["funcional"]},
            research_notes={"modulos_impactados": ["core"], "arquivos_area": ["src/core/"], "zonas_criticas": [], "boundaries": []},
            classification={"mode": "FAST", "total_score": 5}
        )
        spec.version = "v2"

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "spec.json"
            md_path = Path(tmpdir) / "spec.md"
            save_spec_pair(spec, json_path, md_path)

            # Verifica que versão no JSON é v2
            import json
            with open(json_path) as f:
                spec_json = json.load(f)
            assert spec_json["version"] == "v2"

            # Verifica que versão no MD é v2
            md_content = md_path.read_text()
            assert "**Versão:** v2" in md_content


    def test_spec_contracts_include_risk_metadata(self):
        """spec.json carrega criticidade, superfície e evidência mínima dos contratos."""
        agent = SpecBuilderAgent()
        spec = agent.build(
            prd={"objetivo": "endurecer release api auth", "escopo": ["auth", "release"], "criterios_aceite": ["Contrato de API validado em integração"]},
            research_notes={
                "modulos_impactados": ["auth", "api", "release", "gates"],
                "arquivos_area": ["src/auth/", "src/api/", "src/release/"],
                "zonas_criticas": ["src/auth", "src/api"],
                "boundaries": ["src/legacy"],
            },
            classification={"mode": "ENTERPRISE", "total_score": 15}
        )

        assert spec.contratos
        assert all("criticidade" in contrato for contrato in spec.contratos)
        assert all("superficie" in contrato for contrato in spec.contratos)
        assert all("evidencia_minima" in contrato for contrato in spec.contratos)
        assert any(contrato["criticidade"] == "high" for contrato in spec.contratos)


class TestChangeReasonSupport:
    """Valida que artefatos mutáveis suportam change_reason."""

    def test_prd_has_change_reason_field(self):
        """PRD tem campo change_reason."""
        prd = PRD(
            project="proj",
            feature="feature",
            problema="problema",
            objetivo="objetivo",
            version="v1",
            change_reason="escopo alterado após feedback"
        )
        assert prd.change_reason == "escopo alterado após feedback"
        data = prd.to_dict()
        assert data["change_reason"] == "escopo alterado após feedback"

    def test_research_has_change_reason_field(self):
        """ResearchNote tem campo change_reason."""
        research = ResearchNote(
            project="proj",
            feature="feature",
            version="v1",
            change_reason="módulos corrigidos"
        )
        assert research.change_reason == "módulos corrigidos"
        data = research.to_dict()
        assert data["change_reason"] == "módulos corrigidos"

    def test_spec_has_change_reason_field(self):
        """Spec tem campo change_reason."""
        spec = Spec(
            meta="test",
            modulos=["auth"],
            version="v1",
            change_reason="critérios ajustados"
        )
        assert spec.change_reason == "critérios ajustados"
        data = spec.to_dict()
        assert data["change_reason"] == "critérios ajustados"


class TestArtifactContractValidation:
    """Valida que artefatos gerados passam na validação contratual."""

    def test_research_notes_validates_against_contract(self):
        """research-notes.md gerado valida contra contrato."""
        agent = ResearchAgent()
        research, _ = agent.investigate("proj", "feature", {"mode": "FAST", "total_score": 5})
        data = research.to_dict()

        errors = validate_artifact("research-notes.md", data)
        assert errors == [], f"Contract validation failed: {errors}"

    def test_system_map_validates_against_contract(self):
        """system-map.md gerado valida contra contrato."""
        agent = ResearchAgent()
        _, system_map = agent.investigate("proj", "feature", {"mode": "FAST", "total_score": 5})
        data = system_map.to_dict()

        errors = validate_artifact("system-map.md", data)
        assert errors == [], f"Contract validation failed: {errors}"

    def test_prd_validates_against_contract(self):
        """prd.md gerado valida contra contrato."""
        agent = PRDAgent()
        prd = agent.create_prd("proj", "feature", {}, {"mode": "FAST", "total_score": 5})
        data = prd.to_dict()

        errors = validate_artifact("prd.md", data)
        assert errors == [], f"Contract validation failed: {errors}"

    def test_spec_json_validates_against_contract(self):
        """spec.json gerado valida contra contrato."""
        agent = SpecBuilderAgent()
        spec = agent.build(
            prd={"objetivo": "test", "escopo": [], "criterios_aceite": []},
            research_notes={"modulos_impactados": ["core"], "arquivos_area": [], "zonas_criticas": [], "boundaries": []},
            classification={"mode": "FAST", "total_score": 5}
        )
        data = spec.to_dict()

        errors = validate_artifact("spec.json", data)
        assert errors == [], f"Contract validation failed: {errors}"
