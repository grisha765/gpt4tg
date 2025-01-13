from tortoise import fields
from tortoise.models import Model

"""
class UserOption(Model):
    id = fields.IntField(pk=True)
    user_id = fields.BigIntField()
    username = fields.CharField(max_length=8)

    class Meta:
        table = "username"
        unique_together = ("user_id", "username")
"""

class ActivateGroup(Model):
    id = fields.IntField(pk=True)
    chat_id = fields.BigIntField(unique=True)
    activated = fields.BooleanField()
    password = fields.CharField(max_length=10)

    class Meta: #type: ignore
        table = "activate_group"
        unique_together = ("chat_id", "password")

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
