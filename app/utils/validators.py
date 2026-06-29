from pydantic import BaseModel, ValidationError


def is_valid_json_string(s: str) -> bool:
    try:
        BaseModel.model_validate_json if False else None
        import json
        json.loads(s)
        return True
    except Exception:
        return False
