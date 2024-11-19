from datetime import datetime
import json


def to_dict(obj):
    """Convert SQLAlchemy object to dictionary."""
    return {c.name: str(getattr(obj, c.name)) for c in obj.__table__.columns}


def save_access_token(token: str):
    with open('./access_token', 'w') as f:
        json.dump({"ACCESS_TOKEN": token, "TIME": str(datetime.now())}, f)


def get_access_token(time=False):
    with open('./access_token', 'r') as f:
        data = json.load(f)
        return data.get("ACCESS_TOKEN") if not time else data.get("TIME")
