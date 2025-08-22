from pydantic import BaseModel
from typing import Optional, List, Any


class CollectResponse(BaseModel):
    rows_collected: int
    rows_added: int
    last_timestamp: Optional[str]


class PreprocessResponse(BaseModel):
    success: bool
    features_csv: Optional[str]
    feature_cols_pkl: Optional[str]
    feature_scaler_pkl: Optional[str]


class ForecastResponse(BaseModel):
    success: bool
    forecast_csv: Optional[str]
    message: Optional[str]


class JobStatus(BaseModel):
    id: str
    status: str
    created_at: str
    updated_at: str
    steps: List[dict]
    error: Optional[str]
    meta: dict[str, Any]


