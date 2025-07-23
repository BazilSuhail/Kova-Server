# app/schemas/user_schema.py

from marshmallow import Schema, fields, validate

class PreferencesSchema(Schema):
    theme = fields.Str(required=True, validate=validate.OneOf(["light", "dark"]))
    notificationsEnabled = fields.Bool(required=True)

class UserSchema(Schema):
    userId = fields.Str(required=True)
    name = fields.Str(required=True)
    email = fields.Email(required=True)
    profilePicture = fields.Url(required=False)
    preferences = fields.Nested(PreferencesSchema)
    createdAt = fields.DateTime(required=False)
