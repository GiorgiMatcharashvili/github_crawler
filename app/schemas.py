import os

from marshmallow import Schema, fields, ValidationError, validates

VALID_TYPES = os.environ.get('VALID_TYPES', 'Repositories,Issues,Wikis').split(',')


class InputSchema(Schema):
    """Schema for validating input data."""

    keywords = fields.List(fields.String(), required=True)
    proxies = fields.List(fields.String(), required=True)
    type = fields.String(required=True)

    @validates("keywords")
    def validate_keywords(self, keywords):
        """Validate keywords."""
        if not keywords:
            raise ValidationError("keywords cannot be empty")

        for keyword in keywords:
            if not keyword:
                raise ValidationError("keyword cannot be empty")

    @validates("proxies")
    def validate_proxies(self, proxies):
        """Validate proxies."""
        if not proxies:
            raise ValidationError("proxies cannot be empty")

        for proxy in proxies:
            if not proxy:
                raise ValidationError("proxy cannot be empty")

    @validates("type")
    def validate_type(self, type_value):
        """Validate type."""
        if not type_value:
            raise ValidationError("type cannot be empty")

        if type_value not in VALID_TYPES:
            raise ValidationError(f"Unknown type: {type_value}")
