from tortoise import fields
from tortoise.models import Model

class ActivateGroup(Model):
    id = fields.IntField(pk=True)
    chat_id = fields.BigIntField(unique=True)
    activated = fields.BooleanField()
    password = fields.CharField(max_length=10)

    class Meta: #type: ignore
        table = "activate_group"
        unique_together = ("chat_id", "password")

class UserName(Model):
    id = fields.IntField(pk=True)
    user_id = fields.BigIntField(unique=True)
    username = fields.CharField(max_length=32)
    custom = fields.BooleanField()

    class Meta: #type: ignore
        table = "username"
        unique_together = ("user_id", "username")

class Chat(Model):
    id = fields.IntField(pk=True)
    chat_id = fields.BigIntField(index=True)
    message_id = fields.BigIntField(unique=True)
    username = fields.CharField(max_length=32)
    message_text = fields.TextField()
    reply_to_message_id = fields.BigIntField(null=True)

    class Meta: #type: ignore
        table = "chat"

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
