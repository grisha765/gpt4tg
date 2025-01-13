import re
from db.models import UserName
from tortoise.exceptions import DoesNotExist

async def set_username(user_id: int, username: str) -> bool:
    if not (5 <= len(username) <= 32):
        return False
    if not re.fullmatch(r"[a-zа-яё0-9]+", username, re.IGNORECASE):
        return False

    existing_user = await UserName.filter(username=username).first()

    if existing_user:
        if existing_user.user_id != user_id:
            if existing_user.custom:
                await existing_user.delete()
            else:
                return False

    user_record = await UserName.filter(user_id=user_id).first()

    if user_record:
        user_record.username = username
        user_record.custom = True
        await user_record.save()
    else:
        await UserName.create(user_id=user_id, username=username, custom=False)

    return True


async def check_username(user_id: int):
    try:
        user_record = await UserName.get(user_id=user_id)
        return user_record.username
    except DoesNotExist:
        return False

async def reset_username(user_id: int) -> bool:
    try:
        user_record = await UserName.get(user_id=user_id)
        await user_record.delete()
        return True
    except DoesNotExist:
        return False

if __name__ == "__main__":
    raise RuntimeError("This module should be run only via main.py")
