"""Basic smoke test for local Spark startup."""

import shutil
import subprocess

import pytest

from fullstack.spark_session import get_local_spark


def test_local_spark_smoke() -> None:
    java_bin = shutil.which("java")
    if java_bin is None:
        pytest.skip("Java runtime not found. Install Java 11+ to run local Spark.")
    java_check = subprocess.run([java_bin, "-version"], capture_output=True)
    if java_check.returncode != 0:
        pytest.skip("Java is present but no usable runtime is configured.")

    spark = get_local_spark(app_name="fullstack-smoke-test")
    try:
        df = spark.createDataFrame([(1, "ok"), (2, "spark")], ["id", "label"])
        assert df.count() == 2
    finally:
        spark.stop()
