"""Small local Spark job that builds and transforms a customers DataFrame."""

import os
from pathlib import Path

from pyspark.sql import functions as F

from fullstack.spark_session import get_spark, is_databricks_runtime

CUSTOMERS_OUTPUT_ENV = "FULLSTACK_CUSTOMERS_OUTPUT_DIR"


def default_local_output_dir() -> Path:
    """Directory next to this module where local Parquet is written by default."""
    return Path(__file__).resolve().parent / "output"


def resolve_customers_output_path(output_path: str | Path | None = None) -> Path:
    """
    Resolve where to write customers Parquet.

    Order: explicit ``output_path``, then ``FULLSTACK_CUSTOMERS_OUTPUT_DIR``, then
    package-adjacent local ``output``. On Databricks pass a URI or set the env var
    (no writable path under installed site-packages).
    """
    if output_path is not None:
        return Path(output_path)
    env = os.environ.get(CUSTOMERS_OUTPUT_ENV)
    if env:
        return Path(env)
    if is_databricks_runtime():
        raise ValueError(
            f"On Databricks set {CUSTOMERS_OUTPUT_ENV} or pass output_path="
            '(e.g. "dbfs:/tmp/fullstack/customers_parquet").'
        )
    return default_local_output_dir()


def _mkdir_parquet_parent_if_filesystem(output_path: Path) -> None:
    s = str(output_path)
    if s.startswith(
        ("dbfs:", "s3a:", "s3:", "abfss:", "gs:", "wasbs:", "/dbfs/")
    ) or "://" in s:
        return
    output_path.mkdir(parents=True, exist_ok=True)


def run(output_path: str | Path | None = None) -> None:
    """Create a manual customers DataFrame and add a datetime column."""
    spark = get_spark(app_name="customers-job")
    out = resolve_customers_output_path(output_path)
    _mkdir_parquet_parent_if_filesystem(out)

    customers_df = spark.createDataFrame(
        [
            (1, "Alice", "alice@example.com"),
            (2, "Bob", "bob@example.com"),
            (3, "Carlos", "carlos@example.com"),
        ],
        ["customer_id", "name", "email"],
    )

    transformed_df = customers_df.withColumn(
        "ingested_at",
        F.to_timestamp(F.lit("2026-01-01 09:30:00")),
    ).repartition(2)

    transformed_df.show(truncate=False)
    transformed_df.printSchema()
    transformed_df.write.mode("overwrite").parquet(str(out))

    if not is_databricks_runtime():
        spark.stop()


if __name__ == "__main__":
    run()
