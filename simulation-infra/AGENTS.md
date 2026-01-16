# Repository Guidelines

## Project Structure & Module Organization
- core: `components/` — main services
  - `api/` (FastAPI + clients), `ui/` (frontend), `stepper/` (workflow engine), `shared_py/` (shared libs), `db/` (migrations), `deploy/` (server files)
- orchestration: `docker-compose.yml`, `potato.sh` (dev CLI)
- tooling: `tools/`, `.github/`, `terraform/`, `secrets/`, `data/`
- configs: `pyproject.toml`, `.pre-commit-config.yaml`, `.env.example`

## Build, Test, and Development Commands
- start env: `./potato.sh up` — boot all dev containers
- status/logs: `./potato.sh status` • `./potato.sh logs [service]`
- rebuild: `./potato.sh build container [service|all]`
- API clients: `./potato.sh build api [all|python|typescript]`
- enter container: `./potato.sh enter devtools`
- database: `./potato.sh db shell` • `./potato.sh db migrate`
- test backend: `components/<component>/run.sh` - this command uses pytest and you can pass in pytest arguments

## Coding Style & Naming Conventions
- Python: Black (line length 88), 4‑space indents, type hints enforced by mypy (see `pyproject.toml`); shared code lives in `components/shared_py`
- JS/TS: Prettier + ESLint (Standard w/ TypeScript), `components/ui/src/**`
- CSS/SCSS: stylelint
- YAML/JSON: formatted via yamlfmt/Prettier
- Run locally via pre‑commit: `pre-commit install && pre-commit run -a`

## Coding Design Conventions:
- JS/TS: For styles, use css files in `components/ui/src/css/`

## Testing Guidelines
- UI tests: `./potato.sh test ui` (runs in `devtools`)
- Python (stepper): `components/stepper/100_run_tests.sh` or
  `docker compose exec -e PYTHONPATH=./src stepper bash -c "python3 -m unittest discover -s src/test -p 'test_*.py'"`
- Naming: place unit tests under `src/test/` as `test_*.py` (Python) and standard `*.test.ts(x)` for UI

## Commit & Pull Request Guidelines
- Commits: concise, imperative subject; include context or scope when helpful
  - Example: `fix(stepper): handle rollup transition edge case`
- PRs: clear description, linked issues, reproduction/testing notes, screenshots for UI changes
- Keep diffs focused; update docs/examples when behavior changes

## Security & Configuration Tips
- Use `.env.example` as a template; never commit secrets. Place local secrets in `.env` or use `secrets/` during development
- Bootstrap keys/tokens if needed: `./000a-generate-keys.sh`, `./000b-generate-dev-tokens.sh`
- Prefer `./potato.sh` over raw docker commands to ensure consistent env
