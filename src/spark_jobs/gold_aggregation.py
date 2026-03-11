from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, count

from src.spark_jobs.path_config import load_storage_path_config


def main() -> int:
    spark = SparkSession.builder.appName("GoldAggregation").getOrCreate()
    path_config = load_storage_path_config()

    df = spark.read.parquet(path_config.silver_output_path)
    source_count = df.count()

    if source_count == 0:
        print("[GOLD] No Silver rows found. Failing aggregation.")
        spark.stop()
        return 1

    df_gold = df.groupBy("date", "vehicle_id").agg(
        count("*").alias("frame_count"),
        avg(col("has_lidar").cast("int")).alias("lidar_coverage_ratio"),
    )

    df_gold.write.mode("overwrite").parquet(path_config.gold_output_path)

    summary_count = spark.read.parquet(path_config.gold_output_path).count()
    print(
        "[GOLD] Aggregation complete "
        f"(input_rows={source_count}, summary_rows={summary_count}, output_path='{path_config.gold_output_path}', silver_input_path='{path_config.silver_output_path}')"
    )

    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
