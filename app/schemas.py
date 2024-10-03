from pydantic import BaseModel
from datetime import date, datetime, time, timedelta


class CreationRequest(BaseModel):
    long_url: str
    expiration_minutes: int = 60


class CreationResponse(CreationRequest):
    expiration_time: datetime
    creation_time: datetime
    short_url: str
    is_active: bool

class InfoResponse(BaseModel):
    long_url: str
    remaining_time: str
    expiration_time: datetime
    creation_time: datetime
    short_url: str
    is_active: bool