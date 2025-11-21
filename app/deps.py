from typing import Generator
from sqlalchemy.orm import Session
from .database import SessionLocal
from fastapi import Depends, HTTPException, status
from .auth import decode_token
from . import models


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(lambda: None), db: Session = Depends(get_db)):
    # This dependency is a simplified example. In FastAPI you would normally
    # use OAuth2PasswordBearer to extract the token. For tests and simple flows
    # we accept token via dependency injection or header wiring in the app.
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')
    payload = decode_token(token)
    if not payload or 'sub' not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
    user_id = int(payload.get('sub'))
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return user
