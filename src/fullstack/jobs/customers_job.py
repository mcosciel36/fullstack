"""Small local Spark job that builds and transforms a customers DataFrame."""

from pathlib import Path

from pyspark.sql import functions as F

from fullstack.spark_session import get_spark, is_databricks_runtime


def run() -> None:
    """Create a manual customers DataFrame and add a datetime column."""
    spark = get_spark(app_name="customers-job")
    output_path = Path("/Users/markcosciello/git/fullstack/src/fullstack/jobs/output")

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
    transformed_df.write.mode("overwrite").parquet(str(output_path))

    if not is_databricks_runtime():
        spark.stop()


if __name__ == "__main__":
    run()
