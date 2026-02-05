from pyspark.sql import SparkSession
from pyspark.sql.functions import count, avg, col

spark = SparkSession.builder.appName("GoldAggregation").getOrCreate()

# Read Silver data
df = spark.read.parquet("data/silver/lakehouse")

# Example business KPIs (Bosch-friendly)
df_gold = (
    df.groupBy("date", "vehicle_id")
      .agg(
          count("*").alias("frame_count"),
          avg(col("has_lidar").cast("int")).alias("lidar_coverage_ratio")
      )
)

# Write Gold layer
df_gold.write.mode("overwrite").parquet("data/gold/vehicle_daily_summary")

print("Gold layer created: vehicle_daily_summary")

df_gold.createOrReplaceTempView("vw_vehicle_daily_summary")

spark.sql("""
SELECT
  date,
  vehicle_id,
  frame_count,
  lidar_coverage_ratio
FROM vw_vehicle_daily_summary
""").show()
