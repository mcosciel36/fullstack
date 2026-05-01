"""Utilities for creating Spark sessions in local and Databricks runtimes."""

import os

from pyspark.sql import SparkSession


def get_local_spark(app_name: str = "fullstack-local") -> SparkSession:
    """Create or reuse a local Spark session for development and tests."""
    return (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


def is_databricks_runtime() -> bool:
    """Return True when executing inside a Databricks cluster runtime."""
    return bool(
        os.getenv("DATABRICKS_RUNTIME_VERSION")
        or os.getenv("DATABRICKS_CLUSTER_ID")
        or os.getenv("DB_IS_DRIVER")
    )


def get_spark(app_name: str = "fullstack") -> SparkSession:
    """Return active Databricks Spark session, otherwise create local Spark."""
    if is_databricks_runtime():
        active = SparkSession.getActiveSession()
        if active is not None:
            return active
        return SparkSession.builder.appName(app_name).getOrCreate()

    return get_local_spark(app_name=app_name)
