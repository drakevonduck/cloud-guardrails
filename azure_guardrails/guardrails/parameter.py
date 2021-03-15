import json


class Parameter:
    """
    Parameter properties

    https://docs.microsoft.com/en-us/azure/governance/policy/concepts/definition-structure#parameter-properties
    """

    def __init__(self, name: str, parameter_json: dict):
        self.name = name
        self.type = parameter_json.get("type")
        # Do some weird stuff because in this case, [] vs None has different implications
        if "defaultValue" in str(parameter_json):
            default_value = parameter_json.get("defaultValue", None)
            if default_value:
                self.default_value = default_value
            else:
                if self.type == "Array":
                    self.default_value = []
                else:
                    self.default_value = None

        self.default_value = parameter_json.get("defaultValue", None)
        self.allowed_values = parameter_json.get("allowedValues", None)

        # Metadata
        self.metadata_json = parameter_json.get("metadata")
        self.description = self.metadata_json.get("description")
        self.display_name = self.metadata_json.get("displayName")
        self.schema = self.metadata_json.get("schema", None)
        self.category = self.metadata_json.get("category", None)
        self.strong_type = self.metadata_json.get("strongType", None)
        self.assign_permissions = self.metadata_json.get("assignPermissions", None)

    def __repr__(self):
        return json.dumps(self.json())

    def json(self) -> dict:
        result = dict(
            name=self.name,
            type=self.type,
            description=self.description,
            display_name=self.display_name,
        )
        # Return default value only if it has a value, or if it is an empty list or empty string
        if self.default_value or self.default_value == [] or self.default_value == "":
            result["default_value"] = self.default_value
        if self.allowed_values:
            result["allowed_values"] = self.allowed_values
        if self.category:
            result["category"] = self.category
        if self.strong_type:
            result["strong_type"] = self.strong_type
        if self.assign_permissions:
            result["assign_permissions"] = self.assign_permissions
        return result

    @staticmethod
    def _allowed_values(parameter_json):
        allowed_values = parameter_json.get("allowedValues", None)
        allowed_values = [x.lower() for x in allowed_values]
        return allowed_values
