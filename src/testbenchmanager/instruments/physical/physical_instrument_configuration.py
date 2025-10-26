"""Physical Instrument Configuration Model"""

from typing import Annotated, Any, Optional

from pydantic import AliasChoices, BaseModel, Field, model_validator


class PhysicalInstrumentConfiguration(BaseModel):
    """
    Configuration Model of a physical instrument
    """

    uid: str
    name: Optional[str] = None
    module_name: Annotated[str, Field(alias="module")]
    class_name: Annotated[str, Field(alias="class")]
    arguments: dict[str, Any] = {}

    @model_validator(mode="before")
    @classmethod
    # Stupid pydantic internal typing, I hate you. You are 'Any', IDC.
    def _normalize_module_name(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize the module and class names, so that they can be optionally provided entirely in
        the class_name field as fully qualified class names, e.g. 'module.submodule.class'.

        Args:
            data (dict[str, Any]): Input data to model to normalize.

        Returns:
            dict: Normalized data, or original data if no normalization was needed or possible, to
            be handled by pydantic as usual.
        """

        module_model_field = cls.model_fields.get("module_name")
        class_model_field = cls.model_fields.get("class_name")
        if module_model_field is None or class_model_field is None:
            # Abort normalization if model fields are not available
            return data

        if module_model_field.alias is None or class_model_field.alias is None:
            # Abort normalization if model field aliases are not available
            # This should never happen, unless we fuck with the field definitions above.
            return data

        class_name = data.get(class_model_field.alias)
        module_name = data.get(module_model_field.alias)
        if isinstance(class_name, str) and "." in class_name and not module_name:
            parts = class_name.rsplit(".", 1)
            data["module"] = parts[0]
            data["class"] = parts[1]
        return data
