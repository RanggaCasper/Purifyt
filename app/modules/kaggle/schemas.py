from typing import Dict, Optional

from pydantic import BaseModel, Field


class KaggleImportRequest(BaseModel):
    dataset_slug: str = Field(
        ...,
        description="Kaggle dataset slug, e.g. 'username/dataset-name'",
    )
    dataset_name: Optional[str] = Field(
        None,
        description="Name for the dataset (auto-generated if empty)",
    )
    column_mapping: Optional[Dict[str, str]] = Field(
        None,
        description="Manual mapping from database field to Kaggle CSV column, e.g. {'comment': 'text'}",
    )
