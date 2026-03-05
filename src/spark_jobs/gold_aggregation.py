from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, count

SILVER_PATH = "data/silver/lakehouse"
GOLD_PATH = "data/gold/vehicle_daily_summary"


def main() -> int:
    spark = SparkSession.builder.appName("GoldAggregation").getOrCreate()

    df = spark.read.parquet(SILVER_PATH)
    source_count = df.count()

    if source_count == 0:
        print("[GOLD] No Silver rows found. Failing aggregation.")
        spark.stop()
        return 1

    df_gold = df.groupBy("date", "vehicle_id").agg(
        count("*").alias("frame_count"),
        avg(col("has_lidar").cast("int")).alias("lidar_coverage_ratio"),
    )

    df_gold.write.mode("overwrite").parquet(GOLD_PATH)

    summary_count = spark.read.parquet(GOLD_PATH).count()
    print(
        "[GOLD] Aggregation complete "
        f"(input_rows={source_count}, summary_rows={summary_count}, output_path='{GOLD_PATH}')"
    )

    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
