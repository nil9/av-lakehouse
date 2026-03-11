import pytest


@pytest.fixture(scope="session")
def spark():
    pyspark_sql = pytest.importorskip(
        "pyspark.sql",
        reason="pyspark is required for Spark-based tests",
    )
    spark_session_cls = pyspark_sql.SparkSession
    session = (
        spark_session_cls.builder.master("local[2]")
        .appName("av-lakehouse-tests")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    yield session
    session.stop()
