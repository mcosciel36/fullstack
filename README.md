# fullstack

Getting started guide for new contributors.

## Prerequisites

- macOS/Linux shell (examples use `zsh`)
- `git`
- `asdf` version manager
- `poetry` (project uses Poetry 2.x)

## 1) Clone the repository

```bash
git clone <your-repo-url>
cd fullstack
```

## 2) Install and configure asdf

If you do not already have `asdf`, install it first (macOS Homebrew example):

```bash
brew install asdf
```

Then add it to your shell startup file (example for zsh):

```bash
echo -e "\n. $(brew --prefix asdf)/libexec/asdf.sh" >> ~/.zshrc
source ~/.zshrc
```

Verify:

```bash
asdf --version
```

## 3) Install tools from `.tool-versions`

Check what tools/versions the repo expects:

```bash
cat .tool-versions
```

For this repo, Python is pinned there (currently `3.10.13`).

Install required plugins (safe to run even if already added):

```bash
asdf plugin add python
```

Confirm plugin + current selections:

```bash
asdf plugin list
asdf current
```

Install tool versions declared in `.tool-versions`:

```bash
asdf install
```

Re-check:

```bash
asdf current
python --version
```

## 4) Install Poetry (if needed)

Verify first:

```bash
poetry --version
```

If not installed, install Poetry (official installer):

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Then ensure Poetry is on PATH (per Poetry installer output).

## 5) Create/use project virtualenv in-repo

This repo is configured to keep the virtual environment in `.venv`.

```bash
poetry config virtualenvs.in-project true --local
poetry install --extras dev
```

Use `--extras dev` for local development so test tooling (like `pytest`) is installed.

`poetry install --extras dev` installs dependencies and the local package (`fullstack`) from `src/fullstack`.

## 5a) Dependency install modes (local vs deploy)

Local development (recommended: include dev tools):

```bash
poetry install --extras dev
```

Runtime-only environment (exclude dev tools, e.g. deploy images):

```bash
poetry install
```

If you need to switch modes cleanly, recreate the environment:

```bash
poetry env remove --all
poetry install --extras dev   # local dev
# or
poetry install                # runtime-only
```

## 6) Activate the virtualenv

Poetry 2.x does not include `poetry shell` by default.

Get activation command:

```bash
poetry env activate
```

Then run the printed `source ...` command, or directly:

```bash
source .venv/bin/activate
```

Verify you are using the venv interpreter:

```bash
which python
python --version
```

Deactivate later with:

```bash
deactivate
```

## 7) Useful day-to-day commands

Run without activating shell:

```bash
poetry run python --version
poetry run pytest
```

Inspect installed package/dependencies:

```bash
poetry run pip list | grep -i fullstack
poetry run pip freeze | grep -i fullstack
```

## 8) macOS Java setup for PySpark

Spark 3.5 requires a local Java runtime (JDK 11+ recommended).

Since this repo already uses `asdf`, install Java 11 with `asdf`:

```bash
asdf plugin add java
asdf install java temurin-11.0.30+7
asdf set -u java temurin-11.0.30+7
```

Set Java in your shell (`~/.zshrc`) so Spark picks it up:

```bash
export JAVA_HOME="$HOME/.asdf/installs/java/temurin-11.0.30+7"
export PATH="$JAVA_HOME/bin:$PATH"
```

Reload your shell and verify:

```bash
source ~/.zshrc
which java
java -version
echo $JAVA_HOME
```

Validate local Spark with one command:

```bash
poetry run pytest -q
```

## 9) CI/CD note (dev deps vs runtime deps)

Local development should include dev dependencies:

```bash
poetry install --extras dev
```

This installs quality/test tools used in CI: `black`, `isort`, `flake8`, `mypy`, and `pytest`.

Deploy/runtime environments should exclude dev dependencies:

```bash
poetry install
```

Recommended pipeline pattern:

- CI: run `poetry install --extras dev` and execute lint/type/test checks.
- Dev/Prod runtime: run `poetry install` for a smaller runtime-only environment.

## 10) Local pre-push commands (match CI)

Run these locally before pushing to avoid CI surprises:

```bash
poetry install --extras dev
poetry run black --check src tests
poetry run isort --check-only src tests
poetry run flake8 src tests
poetry run mypy src
poetry run pytest -q
```

Optional one-liner:

```bash
poetry run black --check src tests && poetry run isort --check-only src tests && poetry run flake8 src tests && poetry run mypy src && poetry run pytest -q
```

## Troubleshooting

- If `poetry shell` fails: expected on Poetry 2.x; use `poetry env activate` or `source .venv/bin/activate`.
- If package is not visible in `pip list`: ensure you are in Poetry env (`poetry run ...` or activated `.venv`).
- If Spark fails with `JAVA_GATEWAY_EXITED`: Java is missing or not configured; ensure `JAVA_HOME` points to OpenJDK 11+.
- If `rg` is unavailable in your terminal, use `grep` instead.
