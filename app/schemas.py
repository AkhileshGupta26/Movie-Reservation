from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class TokenWithRefresh(Token):
    refresh_token: str


class LoginResponse(BaseModel):
    user: UserOut
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class SeatOut(BaseModel):
    id: int
    row_label: Optional[str]
    seat_number: Optional[int]
    seat_type: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class SeatStatusOut(BaseModel):
    id: int
    row_label: Optional[str]
    seat_number: Optional[int]
    seat_type: Optional[str]
    status: str  # 'available', 'held', 'booked'


class HoldSeatsRequest(BaseModel):
    seat_ids: list[int]


class HoldSeatsResponse(BaseModel):
    reservation_id: int
    expires_at: datetime


class ConfirmReservationResponse(BaseModel):
    status: str
    reservation_id: int


# Admin Schemas

class MovieCreate(BaseModel):
    title: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    poster_url: Optional[str] = None
    genre: Optional[str] = None


class MovieOut(MovieCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AuditoriumCreate(BaseModel):
    name: str
    capacity: int
    extra_metadata: Optional[str] = None


class AuditoriumOut(AuditoriumCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


class SeatCreate(BaseModel):
    row_label: str
    seat_number: int
    seat_type: str = 'regular'
    price_modifier: Decimal = 0


class SeatCreateBatch(BaseModel):
    rows: int
    seats_per_row: int
    seat_type: str = 'regular'
    price_modifier: Decimal = 0


class ShowtimeCreate(BaseModel):
    movie_id: int
    auditorium_id: int
    starts_at: datetime
    ends_at: datetime
    base_price: Decimal


class ShowtimeOut(ShowtimeCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)
