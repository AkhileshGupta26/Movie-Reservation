from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Numeric, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default='user')
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Movie(Base):
    __tablename__ = 'movies'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer)
    poster_url = Column(String)
    genre = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Auditorium(Base):
    __tablename__ = 'auditoriums'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    extra_metadata = Column(Text)  # JSON as text; can switch to JSONB with PG specific type


class Seat(Base):
    __tablename__ = 'seats'
    id = Column(Integer, primary_key=True, index=True)
    auditorium_id = Column(Integer, ForeignKey('auditoriums.id', ondelete='CASCADE'))
    row_label = Column(String)
    seat_number = Column(Integer)
    seat_type = Column(String, default='regular')
    price_modifier = Column(Numeric, default=0)
    auditorium = relationship('Auditorium')


class Showtime(Base):
    __tablename__ = 'showtimes'
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey('movies.id', ondelete='CASCADE'))
    auditorium_id = Column(Integer, ForeignKey('auditoriums.id', ondelete='CASCADE'))
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    base_price = Column(Numeric, nullable=False)
    movie = relationship('Movie')
    auditorium = relationship('Auditorium')


class Reservation(Base):
    __tablename__ = 'reservations'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    showtime_id = Column(Integer, ForeignKey('showtimes.id'))
    status = Column(String, nullable=False)
    total_price = Column(Numeric, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)


class ReservationSeat(Base):
    __tablename__ = 'reservation_seats'
    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey('reservations.id', ondelete='CASCADE'))
    seat_id = Column(Integer, ForeignKey('seats.id'))
    price_at_booking = Column(Numeric, nullable=False)


class BookedSeat(Base):
    __tablename__ = 'booked_seats'
    id = Column(Integer, primary_key=True, index=True)
    showtime_id = Column(Integer, ForeignKey('showtimes.id', ondelete='CASCADE'))
    seat_id = Column(Integer, ForeignKey('seats.id', ondelete='CASCADE'))
    reservation_id = Column(Integer, ForeignKey('reservations.id', ondelete='CASCADE'))

    __table_args__ = (
        UniqueConstraint('showtime_id', 'seat_id', name='uq_showtime_seat'),
    )
