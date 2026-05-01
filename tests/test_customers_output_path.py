"""Tests for ``customers_job.resolve_customers_output_path`` (no JVM)."""

from pathlib import Path

import pytest

from fullstack.jobs.customers_job import (
    CUSTOMERS_OUTPUT_ENV,
    resolve_customers_output_path,
)


def test_explicit_path_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv(CUSTOMERS_OUTPUT_ENV, raising=False)
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
    monkeypatch.delenv("DATABRICKS_CLUSTER_ID", raising=False)
    monkeypatch.delenv("DB_IS_DRIVER", raising=False)
    p = tmp_path / "out"
    assert resolve_customers_output_path(p) == p


def test_env_var_used_when_set(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABRICKS_RUNTIME_VERSION", raising=False)
    monkeypatch.delenv("DATABRICKS_CLUSTER_ID", raising=False)
    monkeypatch.delenv("DB_IS_DRIVER", raising=False)
    monkeypatch.setenv(CUSTOMERS_OUTPUT_ENV, str(tmp_path / "from_env"))
    assert resolve_customers_output_path() == Path(tmp_path / "from_env")


def test_databricks_requires_path_or_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABRICKS_RUNTIME_VERSION", "14.x")
    monkeypatch.delenv(CUSTOMERS_OUTPUT_ENV, raising=False)
    with pytest.raises(ValueError, match="On Databricks"):
        resolve_customers_output_path()
