from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import (
    avg,
    col,
    concat_ws,
    count,
    current_timestamp,
    date_format,
    lit,
    lower,
    regexp_replace,
    sha2,
    to_json,
    struct,
)

from src.spark_jobs.path_config import load_storage_path_config


def build_ai_compatible_export(df: DataFrame, source_table_path: str) -> DataFrame:
    return (
        df.withColumn(
            "document_id",
            concat_ws("::", col("source_manufacturer"), col("vehicle_id"), col("date")),
        )
        .withColumn(
            "chunk_id",
            sha2(
                concat_ws("::", col("source_manufacturer"), col("vehicle_id"), col("frame_id")),
                256,
            ),
        )
        .withColumn("event_timestamp", date_format(col("event_time"), "yyyy-MM-dd'T'HH:mm:ss'Z'"))
        .withColumn("exported_at_utc", current_timestamp())
        .withColumn(
            "normalized_text",
            regexp_replace(
                lower(
                    concat_ws(
                        " ",
                        lit("vehicle"),
                        col("vehicle_id"),
                        lit("frame"),
                        col("frame_id"),
                        lit("camera"),
                        col("camera_name"),
                        lit("date"),
                        col("date"),
                        lit("lidar"),
                        col("has_lidar").cast("string"),
                        lit("source"),
                        col("source_manufacturer"),
                    )
                ),
                r"\s+",
                " ",
            ),
        )
        .withColumn(
            "metadata_json",
            to_json(
                struct(
                    col("vehicle_id"),
                    col("frame_id"),
                    col("camera_name"),
                    col("has_lidar"),
                    col("source_manufacturer"),
                    col("date"),
                )
            ),
        )
        .select(
            "chunk_id",
            "document_id",
            "normalized_text",
            "metadata_json",
            col("event_time").alias("event_time_utc"),
            "event_timestamp",
            "exported_at_utc",
            "date",
            "vehicle_id",
            "frame_id",
            "camera_name",
            "has_lidar",
            "source_manufacturer",
            col("image_path").alias("source_image_path"),
            lit(source_table_path).alias("source_table_path"),
        )
    )


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

    df_ai = build_ai_compatible_export(df, path_config.silver_output_path)
    df_ai.write.mode("overwrite").parquet(path_config.gold_ai_output_path)

    summary_count = spark.read.parquet(path_config.gold_output_path).count()
    ai_export_count = spark.read.parquet(path_config.gold_ai_output_path).count()
    print(
        "[GOLD] Aggregation complete "
        f"(input_rows={source_count}, summary_rows={summary_count}, ai_export_rows={ai_export_count}, output_path='{path_config.gold_output_path}', ai_output_path='{path_config.gold_ai_output_path}', silver_input_path='{path_config.silver_output_path}')"
    )

    spark.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
