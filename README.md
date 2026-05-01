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

## 11) Debugging jobs in Cursor/VS Code (Poetry + module mode)

For predictable imports, prefer module-style debug runs (`python -m ...`) from repo root.

### Launch config

This repo includes a debug target in `.vscode/launch.json`:

```json
{
  "name": "Python: customers job (module, Poetry .venv)",
  "type": "debugpy",
  "request": "launch",
  "python": "${workspaceFolder}/.venv/bin/python",
  "module": "fullstack.jobs.customers_job",
  "cwd": "${workspaceFolder}",
  "console": "integratedTerminal",
  "justMyCode": true
}
```

### How to use it

1. Install deps into the in-repo virtualenv:

```bash
poetry install --extras dev
```

2. In Cursor/VS Code, select the interpreter:
   - `${workspaceFolder}/.venv/bin/python`
3. Open Run and Debug, choose:
   - `Python: customers job (module, Poetry .venv)`
4. Press F5.

### Why this setup is preferred

- `module` is equivalent to `python -m fullstack.jobs.customers_job`.
- `cwd` as `${workspaceFolder}` keeps package resolution stable.
- explicit `.venv` interpreter aligns debugger runtime with Poetry dependencies.

## 12) Controlling local Spark parallelism and output file count

Spark output file count is usually driven by partition count (often one file per partition).

### Check how many CPU cores your Mac has

```bash
# Physical cores
sysctl -n hw.physicalcpu

# Logical cores (used by local[*] in many cases)
sysctl -n hw.logicalcpu

# Hardware summary
system_profiler SPHardwareDataType
```

On the example development machine used for this repo:

- `hw.physicalcpu` = `4`
- `hw.logicalcpu` = `8`
- Processor: `Quad-Core Intel Core i7`

### Check Spark parallelism from this project

```bash
poetry run python -c "from fullstack.spark_session import get_spark, is_databricks_runtime; s=get_spark('parallelism-check'); print('is_databricks_runtime=', is_databricks_runtime()); print('spark_master=', s.sparkContext.master); print('default_parallelism=', s.sparkContext.defaultParallelism); print('shuffle_partitions=', s.conf.get('spark.sql.shuffle.partitions')); s.stop()"
```

Expected output with current local settings:

- `is_databricks_runtime=False`
- `spark_master=local[*]`
- `default_parallelism=8`
- `shuffle_partitions=4`

### Why 8 parquet part files can happen with 3 rows

`local[*]` uses all local logical cores, which is 8 on this machine. If the DataFrame has 8 partitions at write time, Spark will emit 8 `part-*.parquet` files even for tiny data volumes.

### What controls parallelism

- `master("local[*]")`: use all local logical cores.
- `master("local[N]")`: cap local execution to `N` cores.
- `spark.default.parallelism`: baseline partition/task parallelism for many operations.
- `spark.sql.shuffle.partitions`: partition count for shuffle stages (joins/groupBy/orderBy), not every write.

### How to control output file count

```python
# Reduce partitions without full shuffle (good for tiny local outputs)
df.coalesce(1).write.mode("overwrite").parquet(path)

# Set partition count explicitly (does a shuffle)
df.repartition(4).write.mode("overwrite").parquet(path)
```

## 13) Scala Spark job (tokenized emails from Parquet)

The Python [`customers_job`](src/fullstack/jobs/customers_job.py) writes customers Parquet to `src/fullstack/jobs/output`. A small Scala Spark job reads that dataset, tokenizes **email** (local part, domain, and `.`-split arrays), and overwrites **`src/fullstack/jobs/output_tokenized`**.

Code lives under [`scala/tokenize-email-job`](scala/tokenize-email-job).

### Prerequisites

- Same **Java** as PySpark (`JAVA_HOME`; see §8).
- **sbt** (for building the jar), e.g. `brew install sbt`.
- **`poetry run python`** on PATH from the repo root (the helper script locates Spark’s `spark-submit` from your Poetry PySpark install).

### Build

```bash
cd scala/tokenize-email-job
sbt package
```

This produces:

- `scala/tokenize-email-job/target/scala-2.12/fullstack-tokenize-email-job_2.12-0.1.0.jar`

### Produce input Parquet (Python job)

```bash
poetry run python -m fullstack.jobs.customers_job
```

### Run the Scala job locally

From repo root (uses PySpark’s `spark-submit`; optional args are input dir, output dir):

```bash
./scala/tokenize-email-job/run-local.sh
```

Or custom paths:

```bash
./scala/tokenize-email-job/run-local.sh /path/to/input_parquet_dir /path/to/output_parquet_dir
```

### What the job writes

Adds columns **`email_local`**, **`email_domain`**, **`email_local_tokens`**, **`email_domain_tokens`**, and **`email_token_string`** (rejoined form), preserves original columns (`customer_id`, `name`, `email`, etc.), writes Parquet with `Overwrite` at the configured output directory.

`sbt`/Scala build output goes under **`scala/*/target/`** and is ignored by git via `.gitignore`.

## Troubleshooting

- If `poetry shell` fails: expected on Poetry 2.x; use `poetry env activate` or `source .venv/bin/activate`.
- If package is not visible in `pip list`: ensure you are in Poetry env (`poetry run ...` or activated `.venv`).
- If Spark fails with `JAVA_GATEWAY_EXITED`: Java is missing or not configured; ensure `JAVA_HOME` points to OpenJDK 11+.
- If `rg` is unavailable in your terminal, use `grep` instead.
