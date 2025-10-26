from typing import Annotated, Optional

from pydantic import AliasChoices, BaseModel, Field


class TranslatorMetadata(BaseModel):
    uid: str
    name: Optional[str] = None
    description: Optional[str] = None


class TranslatorConfiguration(BaseModel):
    metadata: TranslatorMetadata
    class_name: Annotated[str, Field(validation_alias=AliasChoices("class", "class_name"))]

    class Config:
        extra = "allow"
        
