.PHONY: install test lint clean demo help

help:
	@echo "CVG Harness - Comandos disponíveis:"
	@echo "  make install    - Instalar em modo desenvolvimento"
	@echo "  make test       - Executar todos os testes"
	@echo "  make test-verbose - Executar testes com output completo"
	@echo "  make coverage   - Executar com coverage report"
	@echo "  make demo       - Executar demo completo"
	@echo "  make lint       - Verificar código (sem tool instalada)"
	@echo "  make clean      - Remover arquivos temporários"

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --tb=short

test-verbose:
	pytest tests/ -vv

coverage:
	pytest tests/ --cov=cvg_harness --cov-report=term-missing --cov-report=html

demo:
	python examples/demo_complete_flow.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ 2>/dev/null || true

example-classify:
	python examples/example_classification.py

example-enterprise:
	python examples/example_enterprise.py

example-lint:
	python examples/example_spec_lint.py

example-flow:
	python examples/example_flow.py
