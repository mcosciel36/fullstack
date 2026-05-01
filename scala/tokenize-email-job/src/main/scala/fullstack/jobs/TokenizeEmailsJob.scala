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
  * Optional args:
  *   0 - input parquet directory (default: repo jobs/output)
  *   1 - output parquet directory (default: repo jobs/output_tokenized)
  */
object TokenizeEmailsJob {
  def main(args: Array[String]): Unit = {
    val defaultIn =
      "/Users/markcosciello/git/fullstack/src/fullstack/jobs/output"
    val defaultOut =
      "/Users/markcosciello/git/fullstack/src/fullstack/jobs/output_tokenized"

    val inputPath = args.lift(0).getOrElse(defaultIn)
    val outputPath = args.lift(1).getOrElse(defaultOut)

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
