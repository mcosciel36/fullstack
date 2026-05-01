package fullstack.jobs

import org.apache.spark.sql.{SaveMode, SparkSession}
import org.apache.spark.sql.functions.{col, concat_ws, element_at, split, trim}

/**
  * Reads customers Parquet (from Python `customers_job`), splits email into token columns,
  * and writes Parquet for downstream use.
  *
  * Tokenization: `@` separates local part and domain; each side splits on `.` into arrays
  * (e.g. `alice.person` → [alice, person], `example.com` → [example, com]).
  *
  * Required args:
  *   0 - input parquet directory URI (local path, `dbfs:`, UC volume URI, ...)
  *   1 - output parquet directory URI
  *
  * Shell `run-local.sh` fills default repo-relative paths when positional args omitted.
  */
object TokenizeEmailsJob {
  def main(args: Array[String]): Unit = {
    if (args.length < 2) {
      Console.err.println(
        "Usage: TokenizeEmailsJob <input_parquet_dir> <output_parquet_dir>"
      )
      sys.exit(1)
    }

    val inputPath = args(0)
    val outputPath = args(1)

    val spark = SparkSession
      .builder()
      .appName("tokenize-emails")
      .getOrCreate()

    try {
      val df = spark.read.parquet(inputPath)

      val emailCol = trim(col("email"))
      val atParts = split(emailCol, "@")
      val localPart = element_at(atParts, 1)
      val domainPart = element_at(atParts, 2)

      val tokenized =
        df
          .withColumn("email_local", localPart)
          .withColumn("email_domain", domainPart)
          .withColumn("email_local_tokens", split(localPart, "\\."))
          .withColumn("email_domain_tokens", split(domainPart, "\\."))
          .withColumn(
            "email_token_string",
            concat_ws(
              " @ ",
              concat_ws(".", col("email_local_tokens")),
              concat_ws(".", col("email_domain_tokens"))))

      tokenized.show(false)
      tokenized.printSchema()
      tokenized.write.mode(SaveMode.Overwrite).parquet(outputPath)
    } finally {
      spark.stop()
    }
  }
}
