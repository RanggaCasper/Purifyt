import os
from typing import List, Optional, Dict
import pandas as pd
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.modules.settings.repository import AppSettingRepository

logger = get_logger(__name__)

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

ALLOWED_DB_FIELDS = {
    "video_id",
    "title",
    "channel_name",
    "date",
    "author",
    "comment",
    "label",
    "clean_comment",
    "predicted_label",
}

class KaggleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _configure_credentials(self) -> None:
        values = await AppSettingRepository(self.db).get_many(["KAGGLE_USERNAME", "KAGGLE_KEY"])
        username = (values.get("KAGGLE_USERNAME") or "").strip()
        key = (values.get("KAGGLE_KEY") or "").strip()
        if username and key:
            os.environ["KAGGLE_USERNAME"] = username
            os.environ["KAGGLE_KEY"] = key

    async def import_dataset(
        self,
        dataset_slug: str,
        column_mapping: Optional[Dict[str, str]] = None,
    ) -> dict:
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

        await self._configure_credentials()

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

        effective_map = self._build_mapping(columns_found, column_mapping)
        rows = self._map_rows(df, effective_map, dataset_slug)

        return {
            "rows": rows,
            "source_url": f"https://www.kaggle.com/datasets/{dataset_slug}",
            "columns_found": columns_found,
            "column_mapping": effective_map,
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
    def _build_mapping(
        columns: List[str],
        manual_mapping: Optional[Dict[str, str]] = None,
    ) -> dict:
        """Build {csv_col -> db_field} mapping from auto-detect plus manual overrides."""
        mapping = {}
        lowered = {c.lower().strip(): c for c in columns}

        for csv_alias, db_field in DEFAULT_COLUMN_MAP.items():
            if csv_alias in lowered:
                mapping[lowered[csv_alias]] = db_field

        for db_field, csv_col in (manual_mapping or {}).items():
            db_field = db_field.strip()
            csv_key = csv_col.strip().lower()
            if not db_field or not csv_key:
                continue
            if db_field not in ALLOWED_DB_FIELDS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported target field '{db_field}'. Allowed fields: {sorted(ALLOWED_DB_FIELDS)}",
                )
            if csv_key not in lowered:
                raise HTTPException(
                    status_code=400,
                    detail=f"Column '{csv_col}' was not found in Kaggle CSV. Columns found: {columns}",
                )
            mapping[lowered[csv_key]] = db_field

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
