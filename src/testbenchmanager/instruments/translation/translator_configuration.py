"""Translator configuration models."""

from typing import Annotated, Optional

from pydantic import AliasChoices, BaseModel, Field


class TranslatorMetadata(BaseModel):
    """Configuration Model for Translator Metadata"""

    uid: str
    name: Optional[str] = None
    description: Optional[str] = None


class TranslatorConfiguration(BaseModel):
    """Base Configuration Model for Translators"""

    metadata: TranslatorMetadata
    class_name: Annotated[
        str, Field(validation_alias=AliasChoices("class", "class_name"))
    ]

    # pylint: disable=too-few-public-methods
    # This is internal pydantic configuration. Has to be like this.
    class Config:
        """
        Pydantic internals to allow for additional data not in the above definition to be retained.
        This is required, since we will attempt to transform it from this generic configuration
        model to the concrete implementation stored in class_name.
        """

        extra = "allow"
