"""
Alembic database migration environment configuration.
Run from the backend directory:
    alembic init alembic
    alembic revision --autogenerate -m "initial"
    alembic upgrade head
"""

# This file serves as documentation for setting up Alembic.
# The actual database tables are created automatically on app startup via:
#     Base.metadata.create_all(bind=engine)
# in main.py's startup_event.

# To set up Alembic migrations for production:
# 1. cd backend
# 2. alembic init alembic
# 3. Edit alembic/env.py to import your models and use your DATABASE_URL
# 4. alembic revision --autogenerate -m "initial migration"
# 5. alembic upgrade head
