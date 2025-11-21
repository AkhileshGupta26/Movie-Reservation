from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create an in-memory SQLite database for tests BEFORE importing app
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=__import__('sqlalchemy.pool', fromlist=['StaticPool']).StaticPool
)

from app.database import Base, get_db
from app.main import app
from app import models

# Create all tables in test database
Base.metadata.create_all(bind=test_engine)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_signup_and_login():
    # signup
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "secret"
    }
    r = client.post('/auth/signup', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data['email'] == 'test@example.com'

    # login
    r = client.post('/auth/login', json={"email": "test@example.com", "password": "secret"})
    assert r.status_code == 200
    tokens = r.json()
    assert 'access_token' in tokens
    assert 'refresh_token' in tokens
