from db.models import ActivateGroup
from tortoise.exceptions import DoesNotExist

async def add_group(chat_id: int, password: str):
    await ActivateGroup.get_or_create(
        chat_id=chat_id,
        defaults={"activated": False, "password": password}
    )

async def activate_group(chat_id: int, password: str) -> bool:
    try:
        group = await ActivateGroup.get(chat_id=chat_id)
        if group.password == password:
            group.activated = True
            await group.save()
            return True
        else:
            return False
    except DoesNotExist:
        return False

async def check_group(chat_id: int) -> dict:
    try:
        group = await ActivateGroup.get(chat_id=chat_id)
        return {"activated": group.activated, "password": group.password}
    except DoesNotExist:
        return {"activated": False, "password": None}

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
