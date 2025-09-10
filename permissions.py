def is_owner(user_id: int, config) -> bool:
    try:
        return int(user_id) == int(config.owner_id)
    except Exception:
        return False
