.PHONY: format test run admin
 
format:
	@echo "Limpando imports inúteis e variáveis órfãs..."
	uv run autoflake .

test:
	@echo "Rodando testes automatizados..."
	PYTHONPATH=. uv run pytest tests/ -v

run:
	@echo "Iniciando DriveMatchBot..."
	PYTHONPATH=. uv run python main.py

admin:
	@echo "Iniciando Painel Administrativo Web..."
	uv run uvicorn web.main:app --host 0.0.0.0 --port 8001 --reload
