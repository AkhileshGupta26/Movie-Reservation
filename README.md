# Movie Reservation (scaffold)

This repository is a minimal FastAPI scaffold for a movie reservation service.

Structure created:

movie-reservation/
- Dockerfile
- docker-compose.yml
- .env.example
- requirements.txt
- alembic.ini
- README.md
- app/
  - __init__.py
  - main.py
  - config.py
  - database.py
  - models.py
  - schemas.py
  - crud.py
  - auth.py
  - deps.py
  - migrations/

Quick start (development):
1. Copy `.env.example` to `.env` and adjust values.
2. Run with Docker Compose:

   docker-compose up --build

3. Open http://localhost:8000/docs for the interactive API docs.

Notes:
- Alembic migration directory created. Initialize and manage migrations with alembic commands.
- This is a scaffold; add endpoints, auth, and business logic as needed.
