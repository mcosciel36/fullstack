# Running fullstack on Databricks

This guide describes how to put **`notebooks/fullstack_databricks.ipynb`** into a Databricks workspace and execute the sample pipeline (customers → Parquet → email token columns → Parquet) using the cluster’s Spark session.

For local laptops (Poetry, Jupyter, `spark-submit`), see the main **[README.md](README.md)**.

## What you need

- A cluster whose **Databricks Runtime** includes **Spark 3.5.x** and **Python 3.10 or 3.11** (the package declares `requires-python = ">=3.10,<3.13"`).
- Permission to install libraries on that cluster **or** to run `%pip`-style installs from a notebook restart (Databricks may restart Python after installs).
- A destination for Parquet writes: **`dbfs:`** paths such as `/tmp/...`, or Unity Catalog **[Volumes](https://docs.databricks.com/en/volumes/index.html)** (recommended for production workloads).

The notebook demonstrates **PySpark and Scala in the same file**: Part 1 writes customers Parquet and tokenizes using **`src/fullstack/jobs/email_tokenization.py`**; Part 2 runs the same DataFrame logic in a **`%%scala`** cell (mirrors **`TokenizeEmailsJob.scala`** on the shared **`spark`**). It does **not** run `sbt` or shell `spark-submit` on the driver.

## 1. Bring the notebook into your workspace

**Option A — Upload**

1. In Databricks: **Workspace** → folder of your choice → **Import**.
2. Choose **File** and select **`notebooks/fullstack_databricks.ipynb`** from this repo, or import from your Git remote if the file is already there.

**Option B — Databricks Repos**

1. Add this repository as a **Repo** in Databricks.
2. Open **`notebooks/fullstack_databricks.ipynb`** from the repo checkout in the UI.

## 2. Install the `fullstack` Python package

The notebook imports **`fullstack.spark_session`** and **`fullstack.jobs.email_tokenization`**. The cluster must have that package available in one of these ways.

### Option A — Wheel + widget (fits the notebook as written)

On your machine, from the repo root:

```bash
poetry build -f wheel
```

Upload the generated wheel (under `dist/`, e.g. `fullstack-0.1.0-py3-none-any.whl`) to Databricks (e.g. **Workspace** or a **Volume**).

In the notebook:

1. Run the first code cell (creates widgets).
2. Set widget **`pip_wheel_uri`** to the workspace or volume path of the wheel (examples: `/Workspace/.../fullstack-0.1.0-py3-none-any.whl` or a `/Volumes/...` path your cluster can read).
3. Run the **optional install** cell once. After a successful install, you can clear **`pip_wheel_uri`** for later runs if the library persists on the cluster.

### Option B — Cluster library or environment

Attach the same wheel (or an equivalent artifact) as a **cluster library** or **compute environment** so **`import fullstack`** works without the widget. Then leave **`pip_wheel_uri`** empty and skip the install cell’s real work (it will only print that it assumes the package is present).

### Option C — Install from Git

If your organization allows it, a notebook cell can use:

```python
%pip install "git+https://github.com/<org>/<repo>.git@<branch>"
```

Adjust URL and branch; you may need credentials or a private index. After install, **restart Python** if Databricks prompts you to.

## 3. Configure widgets and run

After the first code cell runs on a Databricks cluster, these **widgets** exist:

| Widget | Purpose | Example default in notebook |
|--------|---------|-----------------------------|
| **`customers_parquet_uri`** | Sample customers Parquet (written in Part 1) | `dbfs:/tmp/fullstack/customers_parquet` |
| **`tokenized_parquet_uri`** | PySpark tokenized output (Part 1) | `dbfs:/tmp/fullstack/customers_tokenized` |
| **`tokenized_scala_parquet_uri`** | Scala tokenized output (Part 2) | `dbfs:/tmp/fullstack/customers_tokenized_scala` |
| **`pip_wheel_uri`** | Optional path/URI to the wheel for one-shot `pip install` | (empty after package is installed) |

Two tokenized URIs keep **PySpark** and **Scala** writes separate for side-by-side verification.

Use **directory-style** Parquet paths (Spark writes a folder).

Execute cells **top to bottom**. The notebook does **not** call **`spark.stop()`**, which avoids tearing down Spark on shared clusters.

### PySpark and Scala cells (`%%scala`)

- Part 2 is one code cell whose first line is **`%%scala`**; the rest is Scala calling the notebook-bound **`spark`**, **`dbutils.widgets`** (same URIs as Python), and **`SaveMode.Overwrite`**.
- **`%%scala`** is provided by **Databricks**, not plain Jupyter / ipykernel. On your laptop: run **through Part 1** for a smoke test, stop before the Scala cell (or rely on **`nbconvert --allow-errors`**). For an all-shell local Scala path, use **`notebooks/fullstack_local_spark.ipynb`** and **`run-local.sh`** instead.
- The final Python cell compares the two tokenized datasets (row counts / `subtract` asymmetry)—it only compares when **`DATABRICKS_RUNTIME_VERSION`** is set; locally it prints a skip message.

## 4. Using `customers_job` from other notebooks

If you call **`fullstack.jobs.customers_job.run()`** elsewhere on Databricks, you must supply a writable URI explicitly or via environment variable:

```python
import os

os.environ["FULLSTACK_CUSTOMERS_OUTPUT_DIR"] = "dbfs:/tmp/fullstack/customers_parquet"

from fullstack.jobs.customers_job import run

run()
```

Or pass **`run(output_path="dbfs:/tmp/fullstack/customers_parquet")`**. On Databricks the job does **not** default to a path next to the installed package.

## 5. (Optional) Scala JAR pipeline

Besides the **`%%scala`** cells in **`fullstack_databricks.ipynb`**, you can package **`fullstack.jobs.TokenizeEmailsJob`** and run it as a **Databricks Job** Spark JAR task with two URI arguments. That repeats the **same semantics** if you prefer batch jobs instead of notebooks.

---

## Troubleshooting

- **`UsageError: Cell magic %%scala not found`** (local Jupyter) — Expected outside Databricks; use only Part 1 locally or execute on Databricks.
- **`ImportError: fullstack`** — Install the wheel (widget + install cell), cluster library, or `%pip` from Git; ensure the notebook is attached to a cluster that picked up the install.
- **Permission denied on URI** — Use a **`dbfs:`** or Volume path your identity can write to; **`file:/`** on the driver is usually wrong for collaborative clusters.
- **Widget already exists** — Remove or rename widgets from the notebook’s **Run** menu / widget UI, or use a fresh notebook attachment so the defining cell runs in a clean session.
