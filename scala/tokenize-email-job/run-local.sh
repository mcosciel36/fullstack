#!/usr/bin/env bash
set -euo pipefail

# Repo root (fullstack/), containing pyproject.toml and Poetry .venv
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

JAR="${ROOT}/scala/tokenize-email-job/target/scala-2.12/fullstack-tokenize-email-job_2.12-0.1.0.jar"
SPARK_SUBMIT="${SPARK_SUBMIT:-$(cd "${ROOT}" && poetry run python -c "import os, pyspark; print(os.path.join(os.path.dirname(pyspark.__file__), 'bin', 'spark-submit'))")}"

if [[ ! -f "${JAR}" ]]; then
  echo "Jar not found: ${JAR}" >&2
  echo "Build it first: cd ${ROOT}/scala/tokenize-email-job && sbt package" >&2
  exit 1
fi

DEFAULT_IN="${ROOT}/src/fullstack/jobs/output"
DEFAULT_OUT="${ROOT}/src/fullstack/jobs/output_tokenized"
INPUT_PATH="${1:-${DEFAULT_IN}}"
OUTPUT_PATH="${2:-${DEFAULT_OUT}}"

exec "${SPARK_SUBMIT}" \
  --class fullstack.jobs.TokenizeEmailsJob \
  --master 'local[*]' \
  "${JAR}" \
  "${INPUT_PATH}" \
  "${OUTPUT_PATH}"
