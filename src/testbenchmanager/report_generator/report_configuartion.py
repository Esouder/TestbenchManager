from pathlib import Path
from typing import Any

from pydantic import BaseModel


class ReportConfiguration(BaseModel):
    working_directory: Path
    # publishers must perform their own validation 
    publishers: dict[str, dict[str,Any]] = {}
