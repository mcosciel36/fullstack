"""Utilities for creating a local Spark session."""

from pyspark.sql import SparkSession


def get_local_spark(app_name: str = "fullstack-local") -> SparkSession:
    """Create or reuse a local Spark session for development and tests."""
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )
