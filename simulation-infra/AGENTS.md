# Repository Guidelines

## Overview
This is a Docker Compose monorepo for Potato AI (Python services + a React/TypeScript UI).

## Key Entry Points
- `./potato.sh`: dev CLI wrapper around `docker compose` (start/stop/logs/build/lint/format/test/db/vault)
- `docker-compose.yml`: local dev stack + service definitions
- `Dockerfile`: multi-stage builds (targets like `api_base`, `devtools_base`, `ui_build`, `web_proxy`, etc.)

## Project Structure
- `components/`: services and shared libs
  - `api/`: FastAPI backend, OpenAPI schemas/client generation, pytest tests (`components/api/tests`)
  - `ui/`: React/TypeScript UI + SCSS, webpack, Jest, Storybook
  - `copilot/`: Python service + pytest tests (`components/copilot/tests`)
  - `stepper/`: workflow engine (Python; unit tests in `components/stepper/src/test`)
  - `file_router/`: Python service
  - `catalog/`: Python service/docs
  - `shared_py/`: shared Python library used across services
  - `db/`: Flyway migrations + DB tooling
  - `deploy/`: production deploy scripts/files
  - `web_proxy/`: nginx configs (local reverse proxy)
  - `vault/`: Vault config
  - `license/`: license keys + validation code
  - `unsafe_python/`, `unsafe_jupyter/`: isolated execution environments
- `docker_compose_scripts/`: bootstrap scripts (API client generation, init DB, etc.)
- `data/`: local state + generated code
  - `data/generated/api_client/`: generated Python + TypeScript API clients
- `tools/`: utilities/data pipelines (type-checked by `tools/precommit/mypy.py`)
- `terraform/`, `service/`, `secrets/`: infra/ops

## Common Commands
- Start stack: `./potato.sh up` (or `./potato.sh up <service>`)
- Status: `./potato.sh status`
- Logs: `./potato.sh logs [service]` (add `--show-http-logs` to include HTTP access logs)
- Enter toolbox container: `./potato.sh enter devtools`
- Rebuild containers: `./potato.sh build container [service|all]`
- Storybook: `./potato.sh storybook` (served from `http://localhost:6006`)

## API Client Generation (OpenAPI)
- `./potato.sh build api [all|python|typescript]`
- Output locations:
  - Python: `data/generated/api_client/python/` (mounted into containers at `<component>/src/api_client`)
  - TypeScript: `data/generated/api_client/typescript/api_client.ts` (symlinked into UI at `components/ui/src/ts/api_client/`)
- Treat `data/generated/**` (and the UI symlink `components/ui/src/ts/api_client/`) as generated; don’t hand-edit.

## Linting & Formatting
- Preferred wrappers:
  - `./potato.sh format <python|ui|css|js|yaml|json>`
  - `./potato.sh lint <python|ui|css|js|ts|yaml|json>`
- Python:
  - Ruff formatting/linting (`ruff format`, `ruff check`) configured in `pyproject.toml` (line length 88, target py312)
  - Mypy via `python3 tools/precommit/mypy.py`
- UI:
  - Prettier config: `components/ui/.prettierrc.json` (tabWidth 4, single quotes)
  - ESLint flat config: `components/ui/eslint.config.mjs`
  - Stylelint config: `components/ui/.stylelintrc.json` (SCSS + BEM-ish selector rules)
- Shell: Follow the existing formatting in the file
- YAML: `yamlfmt` + `yamllint` (`.yamllint.yml`)
- JSON: Prettier check/write via `210-lint-json.sh`
- Pre-commit is configured: run `pre-commit run --all-files` after edits.

## Testing
- UI: `./potato.sh test ui` or `cd components/ui && npm run test`
- API (pytest in Docker): `components/api/run_tests.sh [pytest args...]` (set `RUN_INTEGRATION=1` to enable integration tests)
- Copilot (pytest in Docker): `components/copilot/run_tests.sh [pytest args...]` (set `RUN_INTEGRATION=1` to enable integration tests)
- Stepper (unittest in running container): `components/stepper/run_tests.sh` (set `RUN_INTEGRATION=1` to enable integration tests)

## Database
- Shell: `./potato.sh db shell` (uses `100-psql.sh`)
- Migrate: `./potato.sh db migrate` (Flyway; migrations live in `components/db/migrations/`)
- Load data: `./potato.sh db load <bioprotocol|chebi|interpro|mesh|ncit|protocolsio|wiley>`
- Reset local DB (destructive): `./potato.sh db refresh`

## Dependencies
- Python deps live in `components/<component>/requirements.txt` (container builds use `uv` in `Dockerfile`).
- Devtools-only Python deps live in `build/devtools_requirements.txt`.
- UI deps live in `components/ui/package.json` (use `npm`; `package-lock.json` is authoritative).

## UI Design Conventions
- Put styles in `components/ui/src/css/` (SCSS).
- Follow the selector naming rules enforced by `components/ui/.stylelintrc.json` (BEM-ish; utilities like `.x-foo` / `.u-foo` are allowed).

## Security & Safety
- Never commit secrets. Use `.env.example` as a template; keep local values in `.env` and/or `${HOME}/.potato/`.
- Bootstrap keys/tokens if needed: `./000a-generate-keys.sh`, `./000b-generate-dev-tokens.sh`.
- Destructive commands: `./potato.sh db refresh`, `./potato.sh vault reset` (wipes `data/vault/`).
