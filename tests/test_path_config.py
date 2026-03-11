from src.spark_jobs.path_config import LOCAL_DEFAULTS, load_storage_path_config


def test_load_storage_path_config_defaults(monkeypatch) -> None:
    monkeypatch.delenv("RAW_INPUT_PATH", raising=False)
    monkeypatch.delenv("SILVER_OUTPUT_PATH", raising=False)
    monkeypatch.delenv("GOLD_OUTPUT_PATH", raising=False)

    config = load_storage_path_config()

    assert config == LOCAL_DEFAULTS


def test_load_storage_path_config_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("RAW_INPUT_PATH", "s3a://bucket/raw")
    monkeypatch.setenv("SILVER_OUTPUT_PATH", "s3a://bucket/silver")
    monkeypatch.setenv("GOLD_OUTPUT_PATH", "abfss://gold@account.dfs.core.windows.net/path")

    config = load_storage_path_config()

    assert config.raw_input_path == "s3a://bucket/raw"
    assert config.silver_output_path == "s3a://bucket/silver"
    assert (
        config.gold_output_path
        == "abfss://gold@account.dfs.core.windows.net/path"
    )
