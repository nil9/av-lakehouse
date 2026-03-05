from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp

RAW_PATH = "data/raw/uploads"
OUT_PATH = "data/silver/lakehouse"


def main() -> int:
    spark = SparkSession.builder.appName("WaymoRawToParquet").getOrCreate()

    df = (
        spark.read.option("recursiveFileLookup", "true")
        .option("pathGlobFilter", "*.json")
        .option("multiLine", "true")
        .json(RAW_PATH)
    )

    source_count = df.count()
    if source_count == 0:
        print("[SILVER] No input JSON files found. Failing transformation.")
        spark.stop()
        return 1

    df_clean = (
        df.withColumn("event_time", to_timestamp(col("timestamp_micros") / 1e6))
        .withColumn("quality_flag", (col("has_lidar") == True).cast("string"))
    )

    (
        df_clean.write.mode("overwrite")
        .partitionBy("date", "vehicle_id")
        .parquet(OUT_PATH)
    )

    output_count = spark.read.parquet(OUT_PATH).count()
    print(
        "[SILVER] Transformation complete "
        f"(input_rows={source_count}, output_rows={output_count}, output_path='{OUT_PATH}')"
    )

    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
