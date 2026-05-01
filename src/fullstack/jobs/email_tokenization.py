"""PySpark email token columns (matches Scala TokenizeEmailsJob)."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def with_email_token_columns(df: DataFrame) -> DataFrame:
    """Derive ``email`` local/domain parts, dot tokens, and a readable token string."""
    email_col = F.trim(F.col("email"))
    at_parts = F.split(email_col, "@")
    local_part = F.element_at(at_parts, 1)
    domain_part = F.element_at(at_parts, 2)
    local_tokens = F.split(local_part, r"\.")
    domain_tokens = F.split(domain_part, r"\.")
    token_string = F.concat_ws(
        " @ ",
        F.concat_ws(".", local_tokens),
        F.concat_ws(".", domain_tokens),
    )
    return (
        df.withColumn("email_local", local_part)
        .withColumn("email_domain", domain_part)
        .withColumn("email_local_tokens", local_tokens)
        .withColumn("email_domain_tokens", domain_tokens)
        .withColumn("email_token_string", token_string)
    )
