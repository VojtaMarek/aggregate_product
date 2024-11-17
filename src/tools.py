def to_dict(obj):
    """Convert SQLAlchemy object to dictionary."""
    return {c.name: str(getattr(obj, c.name)) for c in obj.__table__.columns}