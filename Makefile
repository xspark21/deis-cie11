# Makefile — ICD-OMS
BOLD := \033[1m
RESET := \033[0m

.PHONY: help sync build clean

help:
	@printf "\n$(BOLD):: DEIS-CIE11$(RESET)\n\n"

	@printf "  sync     sincroniza dependencias\n"
	@printf "  build    ejecuta pipeline completo\n"
	@printf "  clean    elimina archivos procesados\n"
	@printf "\n"

sync:
	@printf "\n --> sincronizando entorno...\n"
	@uv sync --quiet

build:
	@printf ":: procesando tabla maestra ICD-11...\n"
	@uv run python src/ingestion/master.py

	@printf "\n :: construyendo resolvedor semántico...\n"
	@uv run python src/ingestion/resolver.py

	@printf "\n :: curando registros de urgencia...\n"
	@uv run python src/ingestion/curator.py

clean:
	@printf "\n --> eliminando archivos procesados...\n"
	@rm -rf data/processed/*