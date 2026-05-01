name := "fullstack-tokenize-email-job"
version := "0.1.0"
scalaVersion := "2.12.18"

// Match PySpark in pyproject.toml (Spark 3.5.x)
val sparkVersion = "3.5.4"

libraryDependencies ++= Seq(
  "org.apache.spark" %% "spark-sql" % sparkVersion % Provided
)

Compile / scalacOptions ++= Seq("-deprecation", "-feature", "-unchecked")
