from typing import Optional

from pydantic import BaseModel


class TranslatorMetadata(BaseModel):
    uid: str
    name: Optional[str] = None
    description: Optional[str] = None


class TranslatorConfiguration(BaseModel):
    metadata: TranslatorMetadata
