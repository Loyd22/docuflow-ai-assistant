from app.db.database import SessionLocal


def get_db():
    # Create a new database session.
    db = SessionLocal()

    try:
        # Give the database session to the route/service using it.
        yield db
    finally:
        # Always close the database session after the request is done.
        db.close()