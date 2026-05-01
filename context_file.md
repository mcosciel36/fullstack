# Conversation Context Summary

Use this file to resume work in a new chat thread.

## Repository state (as of last update)

- **`feature/databricks-notebook`** (branch): **`notebooks/fullstack_databricks.ipynb`** for import/running in Databricks (widgets + optional wheel `%pip`; PySpark tokenization matches Scala); **`customers_job`** / Scala entrypoint no longer hard-code a developer home path—see below.
- **`main`** baseline also has **`notebooks/fullstack_local_spark.ipynb`**, optional **`notebook`** Poetry extra (Jupyter), and **`.gitignore`** on job Parquet under `src/fullstack/jobs/output/` and `output_tokenized/`.
- End-to-end **local** verification: `sbt package` → `poetry run python -m fullstack.jobs.customers_job` → `./scala/tokenize-email-job/run-local.sh` → `poetry run pytest -q`; local browser notebook: `poetry install --extras notebook` → `poetry run jupyter notebook notebooks/fullstack_local_spark.ipynb`.

## What exists in the codebase

### Python package (`src/fullstack/`)

- **`spark_session.py`**
  - `get_local_spark()` — `local[*]`, `spark.sql.shuffle.partitions=4`.
  - `is_databricks_runtime()` — true when `DATABRICKS_RUNTIME_VERSION`, `DATABRICKS_CLUSTER_ID`, or `DB_IS_DRIVER` is set.
  - **`get_spark()`** — on Databricks returns `SparkSession.getActiveSession()` or `getOrCreate()` **without** forcing `local[*]`; locally uses `get_local_spark()`.
- **`jobs/customers_job.py`**
  - Builds a 3-row customers DataFrame, adds `ingested_at`, `repartition(2)`, writes Parquet with **overwrite**.
  - **`run(output_path=...)`** resolution: explicit arg → **`FULLSTACK_CUSTOMERS_OUTPUT_DIR`** → local default **`Path(__file__).parent/"output"`**. On **Databricks**, no default path: callers must pass a URI or set the env var (writable package paths under `site-packages` are wrong).
  - Calls `spark.stop()` only when **not** on Databricks (safe for attached cluster session).
- **`jobs/email_tokenization.py`** — **`with_email_token_columns`**: PySpark parity with Scala **`TokenizeEmailsJob`** for use in **`fullstack_databricks.ipynb`** without `spark-submit`.

### Scala (`scala/tokenize-email-job/`)

- **`TokenizeEmailsJob.scala`** — reads Parquet, tokenizes `email` (`email_local`, `email_domain`, token arrays, `email_token_string`), writes Parquet overwrite.
- **CLI:** **two positional args required** — input parquet directory URI, output parquet directory URI (e.g. `dbfs:/...`). **`run-local.sh`** supplies repo-relative defaults when args omitted.
- **`run-local.sh`** — `spark-submit` using PySpark’s `spark-submit` from Poetry `.venv`; **`--master local[*]`**; passes **`"${INPUT_PATH}" "${OUTPUT_PATH}"`** to the JVM main.
- **`sbt package`** produces `target/scala-2.12/fullstack-tokenize-email-job_2.12-0.1.0.jar` (ignored by git via `scala/**/target/`).

### Docs / tooling

- **`README.md`** — setup (asdf, Poetry, Java §8), debugging (§11), parallelism (§12), Scala job (§13), troubleshooting.
- **`.vscode/launch.json`** — module debug `fullstack.jobs.customers_job` from repo root with Poetry `.venv`.
- **`context_file.md`**, **`initial_request.txt`** — prior notes.
- **`notebooks/fullstack_databricks.ipynb`** — import/run on **Databricks**: widgets for customers + separate **PySpark** / **Scala** tokenized URIs, optional **`pip_wheel_uri`**; Part 1 PySpark (**`email_tokenization.py`**), Part 2 **`%%scala`** (same logic as **`TokenizeEmailsJob`** on shared **`spark`**), Python compare cell. **`%%scala`** is **not** plain Jupyter-on-mac; see **[README.databricks.md](README.databricks.md)**.
- **`notebooks/fullstack_local_spark.ipynb`** — **local-only** Poetry + Jupyter: PySpark + **`%%bash`** `sbt` / `run-local.sh`. Not for uploading to Databricks as-is.
- Parquet under **`output/`** and **`output_tokenized/`** is **ignored by git**; recreate with jobs or the notebook.

### Dependencies (unchanged broadly)

- `pyspark>=3.5,<4.0`, `delta-spark>=3.2,<4.0`; dev extras: `pytest`, `black`, `isort`, `flake8`, `mypy`; optional **`notebook`** extra: `jupyter`, `ipykernel` (local Jupyter only—not a Databricks requirement).
- Scala build: Spark **3.5.x**, Scala **2.12**, sbt from `project/build.properties`.

## Local commands (canonical)

From repo root, after `poetry install --extras dev` and Java (`JAVA_HOME`):

```bash
cd scala/tokenize-email-job && sbt package && cd ../..
poetry run python -m fullstack.jobs.customers_job
./scala/tokenize-email-job/run-local.sh
poetry run pytest -q
```

Optional: `./scala/tokenize-email-job/run-local.sh <input_parquet_dir> <output_parquet_dir>`.

## Gaps before “clone anywhere, README-only”

1. **Done on `feature/databricks-notebook`:** `customers_job` / Scala mains no longer bake in a developer home directory; **`fullstack_databricks.ipynb`** uses **DB widgets** / env for URIs. Remaining polish: README section for “upload notebook + wheel + widget defaults.”
2. **`TokenizeEmailsJob`** ends with **`spark.stop()`** in `finally`. For **shared Databricks clusters** or JAR-as-library patterns, conditional stop (or separate `run(spark)` without stop).
3. **`run-local.sh`** remains **local** `spark-submit`; Databricks Jobs use **JAR task + DBFS/Volume URIs** or **`fullstack_databricks.ipynb`** (PySpark parity, no JVM submit).

---

## **`fullstack_databricks.ipynb`** (primary Databricks artifact)

Upload **`notebooks/fullstack_databricks.ipynb`** or sync via **Repos**. Flow:

1. **Widgets** — **`customers_parquet_uri`**, **`tokenized_parquet_uri`** (`dbfs:` or Volume URIs); optional **`pip_wheel_uri`** then run the **`pip`** cell once.
2. **Imports** — `from fullstack.jobs.email_tokenization import with_email_token_columns` (requires wheel/library).
3. **No** JVM `spark-submit`; tokenization mirrors Scala in **`email_tokenization.py`**.

Operational notes:

- Omit **`spark.stop()`** at the bottom (notebook already does)—shared clusters rely on reuse.
- For **`customers_job.run()`** from notebooks: pass **`output_path=`** widget value or **`FULLSTACK_CUSTOMERS_OUTPUT_DIR`** on cluster env.

Legacy **`fullstack_local_spark.ipynb`** is still **local-only** (`%%bash` + `run-local.sh`).

### Older mapping (still valid when porting arbitrary local notebooks)

| Pattern | Local | Databricks (`fullstack_databricks.ipynb`) |
|--------|--------|-------------------------------------------|
| `get_spark()` | ✅ | ✅ |
| `sys.path` to `src/` | ⚠️ | Prefer wheel / cluster library |
| `%%bash` + `sbt` / `run-local.sh` | ✅ | ❌ use this notebook instead or a JAR Job |

---

## Goal for the next thread: run Python + Scala workflows in **Databricks notebooks**

### A) Python (`customers_job`) in a notebook

1. **Get the package on the cluster**
   - **Wheel:** build/install in CI or locally (`poetry build`), upload to DBFS/workspace, then in notebook:
     - `%pip install /Workspace/.../fullstack-0.1.0-py3-none-any.whl`
   - **Or** `pip install git+https://github.com/<org>/<repo>.git@main` if you publish/install from git.
   - **Or** Databricks Repos: add repo, `%pip install -e ./path/to/pkg` if layout supports editable install (`pyproject`/src layout may need tweaks).
2. **Use the attached cluster Spark**
   - `get_spark()` already avoids `local[*]` when Databricks env vars are present.
3. **Paths**
   - Change output to something like `dbfs:/tmp/fullstack/customers_output` or a **Volumes** path (`/Volumes/catalog/schema/volume/...`) before relying on README-only instructions.
4. **Invoke**
   - Thin notebook cell:
     - `from fullstack.jobs.customers_job import run`
     - `run()` *(after fixing paths inside `run()` or passing parameters — refactoring recommended)*.

### B) Scala tokenization in Databricks

**Option 1 — JAR Spark Job / `spark-submit` task (closest to repo today)**

- Build JAR (`sbt package`), upload JAR to DBFS/workspace.
- Databricks Job: **Spark JAR** task, main class `fullstack.jobs.TokenizeEmailsJob`, arguments: `dbfs:/.../customers_parquet/` `dbfs:/.../output_tokenized/`.
- **Refactor recommendation:** skip `spark.stop()` on Databricks (same env detection as Python, or separate `run(spark)` that doesn’t stop).

**Option 2 — Scala notebook**

- Create a **Scala** notebook attached to Spark cluster; `spark` is already bound.
- Port the transformation block from `TokenizeEmailsJob` (read Parquet → `withColumn` chain → write) inline, using **DBFS/Volume URIs**.
- Avoid `SparkSession.builder.getOrCreate()` + `spark.stop()` pattern; use the notebook’s **`spark`** session.

**Option 3 — Run JAR via `%sh`** (less common)

- Cluster with appropriate Spark; `spark-submit` with `--class fullstack.jobs.TokenizeEmailsJob` and paths; still better as a Job for production.

### C) Typical pipeline on Databricks

1. Notebook (Python) generates Parquet → `dbfs:/.../customers/`.
2. Either Scala notebook cell/job reads that path and writes `dbfs:/.../customers_tokenized/`, **or** JAR job with the two URI arguments.

---

## Design notes (still valid)

- Keep **thin notebooks**, reusable logic in **package modules** / shared libraries.
- **Wheel + CI artifact** promotion to dev/prod is cleaner than ad-hoc notebook copies long term.
- `dbutils.notebook.run` / `%run` for orchestration when splitting steps.

---

## Quick file index

| Area | Path |
|------|------|
| Spark session (local + DB-aware) | `src/fullstack/spark_session.py` |
| Python customers sample job | `src/fullstack/jobs/customers_job.py` |
| Scala tokenize job | `scala/tokenize-email-job/src/main/scala/fullstack/jobs/TokenizeEmailsJob.scala` |
| Local Scala runner | `scala/tokenize-email-job/run-local.sh` |
| Contributor guide | `README.md` |
| Smoke test | `tests/test_spark_smoke.py` |
| Local browser notebook | `notebooks/fullstack_local_spark.ipynb` |
| Databricks import notebook | `notebooks/fullstack_databricks.ipynb` |
| Email token helpers (PySpark) | `src/fullstack/jobs/email_tokenization.py` |
