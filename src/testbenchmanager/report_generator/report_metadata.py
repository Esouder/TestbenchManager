from datetime import datetime

from pydantic import BaseModel


class ReportMetadata(BaseModel):
    uid: str
    name: str
    operator: str | list[str] | None = None
    start_time: datetime
    end_time: datetime | None = None

