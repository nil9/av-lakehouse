import os
from dataclasses import dataclass


@dataclass(frozen=True)
class StoragePathConfig:
    raw_input_path: str
    silver_output_path: str
    gold_output_path: str


LOCAL_DEFAULTS = StoragePathConfig(
    raw_input_path="data/raw/uploads",
    silver_output_path="data/silver/lakehouse",
    gold_output_path="data/gold/vehicle_daily_summary",
)


def load_storage_path_config() -> StoragePathConfig:
    return StoragePathConfig(
        raw_input_path=os.getenv("RAW_INPUT_PATH", LOCAL_DEFAULTS.raw_input_path),
        silver_output_path=os.getenv(
            "SILVER_OUTPUT_PATH", LOCAL_DEFAULTS.silver_output_path
        ),
        gold_output_path=os.getenv("GOLD_OUTPUT_PATH", LOCAL_DEFAULTS.gold_output_path),
    )
