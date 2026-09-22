from datetime import datetime
from pydantic import BaseModel


class RouteOut(BaseModel):
    id: int
    name: str
    max_weight_kg: float
    max_volume_l: float
    max_cold_volume_l: float
    model_config = {"from_attributes": True}


class RouteUpdate(BaseModel):
    max_weight_kg: float | None = None
    max_volume_l: float | None = None
    max_cold_volume_l: float | None = None


class StopOut(BaseModel):
    id: int
    route_id: int
    seq: int
    name: str
    weight_kg: float
    volume_l: float
    is_cold: bool
    model_config = {"from_attributes": True}


class StopColdUpdate(BaseModel):
    is_cold: bool


class BagItemOut(BaseModel):
    stop_id: int
    stop_name: str
    weight_kg: float
    volume_l: float
    is_cold: bool


class BagOut(BaseModel):
    id: int
    route_id: int
    bag_index: int
    weight_kg: float
    volume_l: float
    is_cold: bool
    items: list[BagItemOut] = []
    model_config = {"from_attributes": True}


class RejectOut(BaseModel):
    id: int
    route_id: int
    stop_id: int
    stop_name: str
    reason: str
    is_cold: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class PackRequest(BaseModel):
    route_id: int


class WeightOut(BaseModel):
    bag_id: int
    bag_index: int
    route_id: int
    weight_kg: float
    volume_l: float
    is_cold: bool
    fill_weight_pct: float
    fill_volume_pct: float
