from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp

from src.spark_jobs.path_config import load_storage_path_config


def main() -> int:
    spark = SparkSession.builder.appName("WaymoRawToParquet").getOrCreate()
    path_config = load_storage_path_config()

    df = (
        spark.read.option("recursiveFileLookup", "true")
        .option("pathGlobFilter", "*.json")
        .option("multiLine", "true")
        .json(path_config.raw_input_path)
    )

    source_count = df.count()
    if source_count == 0:
        print("[SILVER] No input JSON files found. Failing transformation.")
        spark.stop()
        return 1

    df_clean = (
        df.withColumn("event_time", to_timestamp(col("timestamp_micros") / 1e6))
        .withColumn("quality_flag", col("has_lidar").cast("string"))
    )

    (
        df_clean.write.mode("overwrite")
        .partitionBy("date", "vehicle_id")
        .parquet(path_config.silver_output_path)
    )

    output_count = spark.read.parquet(path_config.silver_output_path).count()
    print(
        "[SILVER] Transformation complete "
        f"(input_rows={source_count}, output_rows={output_count}, output_path='{path_config.silver_output_path}', raw_input_path='{path_config.raw_input_path}')"
    )

    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
