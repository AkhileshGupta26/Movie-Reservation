from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash
from datetime import datetime

# minimal: create user

def create_user(db: Session, user_in: schemas.UserCreate):
    user = models.User(name=user_in.name, email=user_in.email, password_hash=get_password_hash(user_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# fetch by email

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


# ADMIN CRUD OPERATIONS

# Movies
def create_movie(db: Session, movie_in: schemas.MovieCreate):
    movie = models.Movie(**movie_in.dict())
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie


def get_movies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Movie).offset(skip).limit(limit).all()


def get_movie(db: Session, movie_id: int):
    return db.query(models.Movie).filter(models.Movie.id == movie_id).first()


def update_movie(db: Session, movie_id: int, movie_in: schemas.MovieCreate):
    movie = get_movie(db, movie_id)
    if not movie:
        return None
    for key, value in movie_in.dict().items():
        setattr(movie, key, value)
    db.commit()
    db.refresh(movie)
    return movie


def delete_movie(db: Session, movie_id: int):
    movie = get_movie(db, movie_id)
    if movie:
        db.delete(movie)
        db.commit()
    return movie


# Auditoriums
def create_auditorium(db: Session, auditorium_in: schemas.AuditoriumCreate):
    auditorium = models.Auditorium(**auditorium_in.dict())
    db.add(auditorium)
    db.commit()
    db.refresh(auditorium)
    return auditorium


def get_auditoriums(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Auditorium).offset(skip).limit(limit).all()


def get_auditorium(db: Session, auditorium_id: int):
    return db.query(models.Auditorium).filter(models.Auditorium.id == auditorium_id).first()


def update_auditorium(db: Session, auditorium_id: int, auditorium_in: schemas.AuditoriumCreate):
    auditorium = get_auditorium(db, auditorium_id)
    if not auditorium:
        return None
    for key, value in auditorium_in.dict().items():
        setattr(auditorium, key, value)
    db.commit()
    db.refresh(auditorium)
    return auditorium


def delete_auditorium(db: Session, auditorium_id: int):
    auditorium = get_auditorium(db, auditorium_id)
    if auditorium:
        db.delete(auditorium)
        db.commit()
    return auditorium


# Seats
def create_seat(db: Session, seat_in: schemas.SeatCreate):
    seat = models.Seat(**seat_in.dict())
    db.add(seat)
    db.commit()
    db.refresh(seat)
    return seat


def create_seats_batch(db: Session, auditorium_id: int, rows: int, seats_per_row: int, 
                       seat_type: str = 'regular', price_modifier: float = 0):
    """Create multiple seats for an auditorium in batch."""
    seats = []
    for row in range(1, rows + 1):
        row_label = chr(64 + row)  # A, B, C, etc.
        for seat_num in range(1, seats_per_row + 1):
            seat = models.Seat(
                auditorium_id=auditorium_id,
                row_label=row_label,
                seat_number=seat_num,
                seat_type=seat_type,
                price_modifier=price_modifier
            )
            seats.append(seat)
    db.add_all(seats)
    db.commit()
    return seats


def get_seats_by_auditorium(db: Session, auditorium_id: int):
    return db.query(models.Seat).filter(models.Seat.auditorium_id == auditorium_id).all()


def get_seat(db: Session, seat_id: int):
    return db.query(models.Seat).filter(models.Seat.id == seat_id).first()


def delete_seat(db: Session, seat_id: int):
    seat = get_seat(db, seat_id)
    if seat:
        db.delete(seat)
        db.commit()
    return seat


# Showtimes
def create_showtime(db: Session, showtime_in: schemas.ShowtimeCreate):
    # Check for overlaps with same auditorium
    overlapping = db.query(models.Showtime).filter(
        models.Showtime.auditorium_id == showtime_in.auditorium_id,
        models.Showtime.starts_at < showtime_in.ends_at,
        models.Showtime.ends_at > showtime_in.starts_at
    ).first()
    
    if overlapping:
        return None  # Overlap detected
    
    showtime = models.Showtime(**showtime_in.dict())
    db.add(showtime)
    db.commit()
    db.refresh(showtime)
    return showtime


def get_showtimes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Showtime).offset(skip).limit(limit).all()


def get_showtime(db: Session, showtime_id: int):
    return db.query(models.Showtime).filter(models.Showtime.id == showtime_id).first()


def update_showtime(db: Session, showtime_id: int, showtime_in: schemas.ShowtimeCreate):
    showtime = get_showtime(db, showtime_id)
    if not showtime:
        return None
    
    # Check for overlaps (excluding current showtime)
    overlapping = db.query(models.Showtime).filter(
        models.Showtime.id != showtime_id,
        models.Showtime.auditorium_id == showtime_in.auditorium_id,
        models.Showtime.starts_at < showtime_in.ends_at,
        models.Showtime.ends_at > showtime_in.starts_at
    ).first()
    
    if overlapping:
        return None  # Overlap detected
    
    for key, value in showtime_in.dict().items():
        setattr(showtime, key, value)
    db.commit()
    db.refresh(showtime)
    return showtime


def delete_showtime(db: Session, showtime_id: int):
    showtime = get_showtime(db, showtime_id)
    if showtime:
        db.delete(showtime)
        db.commit()
    return showtime
