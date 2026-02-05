from pathlib import Path
from typing import Any

from pydantic import BaseModel


class ReportConfigurationMetadata(BaseModel):
    name: str | None = None
    description: str | None = None


class ReportConfiguration(BaseModel):
    metadata: ReportConfigurationMetadata = ReportConfigurationMetadata()
    working_directory: Path | None = None
    # publishers must perform their own validation
    publishers: dict[str, dict[str, Any]] = {}
