import os
from typing import List, Optional
import pandas as pd
from fastapi import HTTPException

from app.config.logging_config import get_logger
from app.config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Auto-detection: common CSV column names -> DB field names
DEFAULT_COLUMN_MAP = {
    "video_id": "video_id",
    "title": "title",
    "channel_name": "channel_name",
    "date": "date",
    "tanggal": "date",
    "author": "author",
    "comment": "comment",
    "komentar": "comment",
    "label": "label",
    "clean_comment": "clean_comment",
    "komentar_clean": "clean_comment",
    "predicted_label": "predicted_label",
}

class KaggleService:
    def __init__(self):
        if settings.KAGGLE_USERNAME and settings.KAGGLE_KEY:
            os.environ["KAGGLE_USERNAME"] = settings.KAGGLE_USERNAME
            os.environ["KAGGLE_KEY"] = settings.KAGGLE_KEY

    async def import_dataset(self, dataset_slug: str) -> dict:
        """
        Download a Kaggle dataset via kagglehub, auto-detect the CSV and
        column mapping, and return structured rows.

        Returns:
            {
                "rows": [list of dicts ready for Comment model],
                "source_url": str,
                "columns_found": [list of CSV column names],
                "total_rows": int,
            }
        """
        try:
            import kagglehub
        except ImportError:
            logger.error("[KAGGLE] kagglehub not installed")
            raise HTTPException(
                status_code=500,
                detail="kagglehub is not installed. Run: pip install kagglehub",
            )

        try:
            dataset_path = kagglehub.dataset_download(dataset_slug)
            logger.info("[KAGGLE] Downloaded dataset '%s' → %s", dataset_slug, dataset_path)
        except Exception as e:
            logger.error("[KAGGLE] Download failed for '%s': %s", dataset_slug, e)
            raise HTTPException(
                status_code=400,
                detail=f"Failed to download Kaggle dataset '{dataset_slug}': {e}",
            )

        csv_path = self._find_csv(dataset_path)
        if csv_path is None:
            files_found = []
            for root, _, files in os.walk(dataset_path):
                for f in files:
                    files_found.append(os.path.relpath(os.path.join(root, f), dataset_path))
            raise HTTPException(
                status_code=400,
                detail=f"No suitable CSV found. Files in dataset: {files_found}",
            )

        df = pd.read_csv(csv_path, low_memory=False)
        columns_found = list(df.columns)

        effective_map = self._build_mapping(columns_found)
        rows = self._map_rows(df, effective_map, dataset_slug)

        return {
            "rows": rows,
            "source_url": f"https://www.kaggle.com/datasets/{dataset_slug}",
            "columns_found": columns_found,
            "total_rows": len(rows),
        }

    @staticmethod
    def _find_csv(directory: str) -> Optional[str]:
        """Find the largest CSV file in the dataset directory."""
        csvs = []
        for root, _, files in os.walk(directory):
            for f in files:
                if f.lower().endswith(".csv"):
                    csvs.append(os.path.join(root, f))
        if csvs:
            return max(csvs, key=os.path.getsize)
        return None

    @staticmethod
    def _build_mapping(columns: List[str]) -> dict:
        """Auto-detect {csv_col -> db_field} mapping using DEFAULT_COLUMN_MAP."""
        mapping = {}
        lowered = {c.lower().strip(): c for c in columns}

        for csv_alias, db_field in DEFAULT_COLUMN_MAP.items():
            if csv_alias in lowered:
                mapping[lowered[csv_alias]] = db_field

        return mapping

    @staticmethod
    def _map_rows(df: pd.DataFrame, mapping: dict, dataset_slug: str) -> List[dict]:
        rows = []
        for _, row in df.iterrows():
            record = {
                "video_id": "",
                "title": None,
                "channel_name": None,
                "date": None,
                "author": None,
                "comment": None,
                "label": None,
                "clean_comment": None,
                "predicted_label": None,
                "source_detail": f"kaggle:{dataset_slug}",
            }
            for csv_col, db_field in mapping.items():
                value = row.get(csv_col)
                if pd.isna(value):
                    value = None
                elif db_field == "date" and value is not None:
                    try:
                        value = pd.to_datetime(value)
                        if pd.isna(value):
                            value = None
                    except Exception:
                        value = None
                else:
                    value = str(value) if value is not None else None
                record[db_field] = value

            # Skip rows without video_id
            if not record["video_id"]:
                record["video_id"] = "unknown"

            rows.append(record)
        return rows