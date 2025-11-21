from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import engine, Base, get_db
from .config import settings
from fastapi import Body
from .auth import verify_password, create_access_token, create_refresh_token, decode_token
from .redis_client import redis_client
from datetime import datetime, timedelta

# create tables (dev only)
Base.metadata.create_all(bind=engine)

app = FastAPI(title='Movie Reservation API - Starter')

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://192.168.1.6:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post('/auth/signup', response_model=schemas.UserOut)
def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email already registered')
    user = crud.create_user(db, user_in)
    return user


@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/auth/login', response_model=schemas.LoginResponse)
def login(form_data: schemas.LoginIn, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, form_data.email)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect email or password')
    access_token = create_access_token({'sub': str(user.id)})
    refresh_token = create_refresh_token({'sub': str(user.id)})
    return {
        'user': user,
        'access_token': access_token,
        'refresh_token': refresh_token
    }

@app.post('/auth/refresh', response_model=schemas.Token)
def refresh_token(body: dict = Body(...), db: Session = Depends(get_db)):
    # body expected to be {'refresh_token': '<token>'}
    token = body.get('refresh_token') if isinstance(body, dict) else None
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Missing refresh_token')
    data = decode_token(token)
    if not data or data.get('type') != 'refresh' or 'sub' not in data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')
    user_id = int(data.get('sub'))
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    access_token = create_access_token({'sub': str(user.id)})
    return {'access_token': access_token, 'token_type': 'bearer'}


@app.get('/showtimes/{showtime_id}/seats', response_model=list[schemas.SeatStatusOut])
def get_seats(showtime_id: int, db: Session = Depends(get_db)):
    """Get all seats for a showtime with their status (available, held, booked)."""
    seats = db.query(models.Seat).all()

    booked = db.query(models.BookedSeat.seat_id).filter(models.BookedSeat.showtime_id == showtime_id).all()
    booked_ids = {s[0] for s in booked}

    held_ids = set()
    if redis_client:
        held_keys = redis_client.keys(f'hold:{showtime_id}:*')
        held_ids = {int(k.split(':')[-1]) for k in held_keys}

    response = []
    for s in seats:
        status = 'available'
        if s.id in booked_ids:
            status = 'booked'
        elif s.id in held_ids:
            status = 'held'
        response.append({
            'id': s.id,
            'row_label': s.row_label,
            'seat_number': s.seat_number,
            'seat_type': s.seat_type,
            'status': status
        })
    return response


@app.post('/showtimes/{showtime_id}/holds', response_model=schemas.HoldSeatsResponse)
def hold_seats(showtime_id: int, req: schemas.HoldSeatsRequest, db: Session = Depends(get_db)):
    """Hold seats for a user. Returns reservation_id and expiry time."""
    # For now, use a simple check — in production, extract from auth header
    # This is a simplified example; normally you'd use get_current_user dependency
    
    seat_ids = req.seat_ids
    
    # Check seats exist
    seats = db.query(models.Seat).filter(models.Seat.id.in_(seat_ids)).all()
    if len(seats) != len(seat_ids):
        raise HTTPException(status_code=400, detail='Invalid seat selection')

    # Check booked
    booked = db.query(models.BookedSeat.seat_id).filter(
        models.BookedSeat.showtime_id == showtime_id,
        models.BookedSeat.seat_id.in_(seat_ids)
    ).all()
    if booked:
        raise HTTPException(status_code=409, detail='Some seats already booked')

    # Check held (redis)
    if redis_client:
        for sid in seat_ids:
            if redis_client.get(f'hold:{showtime_id}:{sid}'):
                raise HTTPException(status_code=409, detail='Some seats are held')

    # Create temporary reservation (no user_id for demo, can be added with auth)
    reservation = models.Reservation(
        user_id=None,  # Would be current_user.id in production
        showtime_id=showtime_id,
        status='held',
        total_price=0,
        expires_at=datetime.utcnow() + timedelta(seconds=settings.HOLD_TTL_SECONDS)
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    # Reserve in Redis with TTL
    if redis_client:
        for sid in seat_ids:
            redis_client.setex(
                f'hold:{showtime_id}:{sid}',
                settings.HOLD_TTL_SECONDS,
                reservation.id
            )

    return {'reservation_id': reservation.id, 'expires_at': reservation.expires_at}


@app.post('/reservations/{reservation_id}/confirm', response_model=schemas.ConfirmReservationResponse)
def confirm_reservation(reservation_id: int, db: Session = Depends(get_db)):
    """Confirm a held reservation by moving seats from hold to booked_seats."""
    reservation = db.query(models.Reservation).filter(
        models.Reservation.id == reservation_id,
        models.Reservation.status == 'held'
    ).first()

    if not reservation:
        raise HTTPException(status_code=404, detail='Reservation not found or not in held state')

    # Get held seats from Redis
    held_seats = []
    if redis_client:
        pattern = f'hold:{reservation.showtime_id}:*'
        keys = redis_client.keys(pattern)
        held_seats = [int(k.split(':')[-1]) for k in keys if redis_client.get(k) == str(reservation_id)]

    if not held_seats:
        raise HTTPException(status_code=400, detail='Hold expired or no seats held')

    # Finalize booking inside transaction
    try:
        for sid in held_seats:
            booked = models.BookedSeat(
                showtime_id=reservation.showtime_id,
                seat_id=sid,
                reservation_id=reservation.id
            )
            db.add(booked)
        reservation.status = 'confirmed'
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=409, detail='Seat already booked by someone else')

    # Clear Redis holds
    if redis_client:
        for sid in held_seats:
            redis_client.delete(f'hold:{reservation.showtime_id}:{sid}')

    return {'status': 'confirmed', 'reservation_id': reservation.id}


# ============================================================
# ADMIN CRUD ENDPOINTS
# ============================================================

# MOVIES
@app.post('/admin/movies', response_model=schemas.MovieOut)
def create_movie(movie_in: schemas.MovieCreate, db: Session = Depends(get_db)):
    """Create a new movie."""
    movie = crud.create_movie(db, movie_in)
    return movie


@app.get('/admin/movies', response_model=list[schemas.MovieOut])
def list_movies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all movies with pagination."""
    movies = crud.get_movies(db, skip=skip, limit=limit)
    return movies


@app.get('/admin/movies/{movie_id}', response_model=schemas.MovieOut)
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    """Get a specific movie."""
    movie = crud.get_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail='Movie not found')
    return movie


@app.put('/admin/movies/{movie_id}', response_model=schemas.MovieOut)
def update_movie(movie_id: int, movie_in: schemas.MovieCreate, db: Session = Depends(get_db)):
    """Update a movie."""
    movie = crud.update_movie(db, movie_id, movie_in)
    if not movie:
        raise HTTPException(status_code=404, detail='Movie not found')
    return movie


@app.delete('/admin/movies/{movie_id}')
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    """Delete a movie."""
    movie = crud.delete_movie(db, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail='Movie not found')
    return {'status': 'deleted', 'id': movie_id}


# AUDITORIUMS
@app.post('/admin/auditoriums', response_model=schemas.AuditoriumOut)
def create_auditorium(auditorium_in: schemas.AuditoriumCreate, db: Session = Depends(get_db)):
    """Create a new auditorium."""
    auditorium = crud.create_auditorium(db, auditorium_in)
    return auditorium


@app.get('/admin/auditoriums', response_model=list[schemas.AuditoriumOut])
def list_auditoriums(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all auditoriums with pagination."""
    auditoriums = crud.get_auditoriums(db, skip=skip, limit=limit)
    return auditoriums


@app.get('/admin/auditoriums/{auditorium_id}', response_model=schemas.AuditoriumOut)
def get_auditorium(auditorium_id: int, db: Session = Depends(get_db)):
    """Get a specific auditorium."""
    auditorium = crud.get_auditorium(db, auditorium_id)
    if not auditorium:
        raise HTTPException(status_code=404, detail='Auditorium not found')
    return auditorium


@app.put('/admin/auditoriums/{auditorium_id}', response_model=schemas.AuditoriumOut)
def update_auditorium(auditorium_id: int, auditorium_in: schemas.AuditoriumCreate, db: Session = Depends(get_db)):
    """Update an auditorium."""
    auditorium = crud.update_auditorium(db, auditorium_id, auditorium_in)
    if not auditorium:
        raise HTTPException(status_code=404, detail='Auditorium not found')
    return auditorium


@app.delete('/admin/auditoriums/{auditorium_id}')
def delete_auditorium(auditorium_id: int, db: Session = Depends(get_db)):
    """Delete an auditorium."""
    auditorium = crud.delete_auditorium(db, auditorium_id)
    if not auditorium:
        raise HTTPException(status_code=404, detail='Auditorium not found')
    return {'status': 'deleted', 'id': auditorium_id}


# SEATS
@app.post('/admin/auditoriums/{auditorium_id}/seats/batch')
def create_seats_batch(auditorium_id: int, batch_in: schemas.SeatCreateBatch, db: Session = Depends(get_db)):
    """Create seats in batch for an auditorium."""
    auditorium = crud.get_auditorium(db, auditorium_id)
    if not auditorium:
        raise HTTPException(status_code=404, detail='Auditorium not found')
    
    seats = crud.create_seats_batch(
        db,
        auditorium_id=auditorium_id,
        rows=batch_in.rows,
        seats_per_row=batch_in.seats_per_row,
        seat_type=batch_in.seat_type,
        price_modifier=batch_in.price_modifier
    )
    return {'status': 'created', 'count': len(seats), 'auditorium_id': auditorium_id}


@app.get('/admin/auditoriums/{auditorium_id}/seats', response_model=list[schemas.SeatOut])
def get_auditorium_seats(auditorium_id: int, db: Session = Depends(get_db)):
    """Get all seats for an auditorium."""
    auditorium = crud.get_auditorium(db, auditorium_id)
    if not auditorium:
        raise HTTPException(status_code=404, detail='Auditorium not found')
    seats = crud.get_seats_by_auditorium(db, auditorium_id)
    return seats


@app.delete('/admin/seats/{seat_id}')
def delete_seat(seat_id: int, db: Session = Depends(get_db)):
    """Delete a seat."""
    seat = crud.delete_seat(db, seat_id)
    if not seat:
        raise HTTPException(status_code=404, detail='Seat not found')
    return {'status': 'deleted', 'id': seat_id}


# SHOWTIMES
@app.post('/admin/showtimes', response_model=schemas.ShowtimeOut)
def create_showtime(showtime_in: schemas.ShowtimeCreate, db: Session = Depends(get_db)):
    """Create a new showtime with overlap validation."""
    showtime = crud.create_showtime(db, showtime_in)
    if not showtime:
        raise HTTPException(status_code=409, detail='Showtime overlaps with existing showtime in same auditorium')
    return showtime


@app.get('/admin/showtimes', response_model=list[schemas.ShowtimeOut])
def list_showtimes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all showtimes with pagination."""
    showtimes = crud.get_showtimes(db, skip=skip, limit=limit)
    return showtimes


@app.get('/admin/showtimes/{showtime_id}', response_model=schemas.ShowtimeOut)
def get_showtime(showtime_id: int, db: Session = Depends(get_db)):
    """Get a specific showtime."""
    showtime = crud.get_showtime(db, showtime_id)
    if not showtime:
        raise HTTPException(status_code=404, detail='Showtime not found')
    return showtime


@app.put('/admin/showtimes/{showtime_id}', response_model=schemas.ShowtimeOut)
def update_showtime(showtime_id: int, showtime_in: schemas.ShowtimeCreate, db: Session = Depends(get_db)):
    """Update a showtime with overlap validation."""
    showtime = crud.update_showtime(db, showtime_id, showtime_in)
    if not showtime:
        raise HTTPException(status_code=409, detail='Showtime overlaps with existing showtime in same auditorium')
    return showtime


@app.delete('/admin/showtimes/{showtime_id}')
def delete_showtime(showtime_id: int, db: Session = Depends(get_db)):
    """Delete a showtime."""
    showtime = crud.delete_showtime(db, showtime_id)
    if not showtime:
        raise HTTPException(status_code=404, detail='Showtime not found')
    return {'status': 'deleted', 'id': showtime_id}
