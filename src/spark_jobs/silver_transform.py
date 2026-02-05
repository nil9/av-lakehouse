from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, to_timestamp

RAW_PATH = "data/raw/uploads"
OUT_PATH = "data/processed/lakehouse"

spark = (
    SparkSession.builder
    .appName("WaymoRawToParquet")
    .getOrCreate()
)

# Read all JSON recursively

df = (
    spark.read
    .option("recursiveFileLookup", "true")
    .option("pathGlobFilter", "*.json")
    .option("multiLine", "true")
    .json(RAW_PATH)
)

df = df.cache()
df.printSchema()
df.show(5, truncate=False)


# Basic normalization
df_clean = (
    df
    .withColumn("event_time",
                to_timestamp(col("timestamp_micros") / 1e6))
    .withColumn("quality_flag",
                (col("has_lidar") == True).cast("string"))
)

# Write partitioned Parquet
(
    df_clean
    .write
    .mode("overwrite")
    .partitionBy("date", "vehicle_id")
    .parquet(OUT_PATH)
)

print("Parquet write complete")
