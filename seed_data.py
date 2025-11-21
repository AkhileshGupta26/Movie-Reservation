#!/usr/bin/env python
"""
Seed script to populate the database with sample movies, auditoriums, seats, and showtimes.
Run this after the backend server is running.
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def add_movie(title, description, duration, genre, poster_url):
    """Add a movie to the database."""
    payload = {
        "title": title,
        "description": description,
        "duration_minutes": duration,
        "genre": genre,
        "poster_url": poster_url
    }
    response = requests.post(f"{BASE_URL}/admin/movies", json=payload)
    if response.status_code == 200:
        movie = response.json()
        print(f"✓ Added movie: {title} (ID: {movie['id']})")
        return movie
    else:
        print(f"✗ Failed to add movie: {response.text}")
        return None

def add_auditorium(name, capacity):
    """Add an auditorium to the database."""
    payload = {
        "name": name,
        "capacity": capacity
    }
    response = requests.post(f"{BASE_URL}/admin/auditoriums", json=payload)
    if response.status_code == 200:
        auditorium = response.json()
        print(f"✓ Added auditorium: {name} (ID: {auditorium['id']}, Capacity: {capacity})")
        return auditorium
    else:
        print(f"✗ Failed to add auditorium: {response.text}")
        return None

def add_seats(auditorium_id, rows, seats_per_row, seat_type="regular", price_modifier=0):
    """Add seats to an auditorium."""
    payload = {
        "rows": rows,
        "seats_per_row": seats_per_row,
        "seat_type": seat_type,
        "price_modifier": price_modifier
    }
    response = requests.post(f"{BASE_URL}/admin/auditoriums/{auditorium_id}/seats/batch", json=payload)
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Added {result['count']} seats to auditorium {auditorium_id}")
        return result
    else:
        print(f"✗ Failed to add seats: {response.text}")
        return None

def add_showtime(movie_id, auditorium_id, starts_at, ends_at, base_price):
    """Add a showtime to the database."""
    payload = {
        "movie_id": movie_id,
        "auditorium_id": auditorium_id,
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
        "base_price": base_price
    }
    response = requests.post(f"{BASE_URL}/admin/showtimes", json=payload)
    if response.status_code == 200:
        showtime = response.json()
        print(f"✓ Added showtime (ID: {showtime['id']}) - Movie: {movie_id}, Auditorium: {auditorium_id}")
        return showtime
    else:
        print(f"✗ Failed to add showtime: {response.text}")
        return None

def main():
    print("🎬 Seeding movie reservation database...\n")
    
    # Add movies
    print("📽️  Adding movies...")
    movie1 = add_movie(
        title="The Quantum Paradox",
        description="A mind-bending sci-fi thriller about parallel universes.",
        duration=148,
        genre="Sci-Fi",
        poster_url="https://via.placeholder.com/300x450?text=Quantum+Paradox"
    )
    
    movie2 = add_movie(
        title="Midnight in Paris",
        description="A romantic comedy about a writer who travels back in time.",
        duration=100,
        genre="Romance",
        poster_url="https://via.placeholder.com/300x450?text=Midnight+Paris"
    )
    
    movie3 = add_movie(
        title="Shattered Dreams",
        description="An intense drama about second chances and redemption.",
        duration=134,
        genre="Drama",
        poster_url="https://via.placeholder.com/300x450?text=Shattered+Dreams"
    )
    
    # Add auditoriums
    print("\n🏛️  Adding auditoriums...")
    auditorium1 = add_auditorium(name="Screen A (Premium)", capacity=150)
    auditorium2 = add_auditorium(name="Screen B (Standard)", capacity=100)
    auditorium3 = add_auditorium(name="Screen C (Small)", capacity=50)
    
    # Add seats to auditoriums
    if auditorium1:
        print("\n🪑 Adding seats to Screen A...")
        add_seats(auditorium1['id'], rows=10, seats_per_row=15, seat_type="regular", price_modifier=0)
    
    if auditorium2:
        print("\n🪑 Adding seats to Screen B...")
        add_seats(auditorium2['id'], rows=8, seats_per_row=12, seat_type="regular", price_modifier=0)
    
    if auditorium3:
        print("\n🪑 Adding seats to Screen C...")
        add_seats(auditorium3['id'], rows=5, seats_per_row=10, seat_type="regular", price_modifier=0)
    
    # Add showtimes
    print("\n⏰ Adding showtimes...")
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    
    # Tomorrow showtimes
    if movie1 and auditorium1:
        showtime1_start = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        showtime1_end = showtime1_start + timedelta(minutes=movie1['duration_minutes'] + 20)
        add_showtime(movie1['id'], auditorium1['id'], showtime1_start, showtime1_end, 15.00)
    
    if movie2 and auditorium2:
        showtime2_start = tomorrow.replace(hour=16, minute=30, second=0, microsecond=0)
        showtime2_end = showtime2_start + timedelta(minutes=movie2['duration_minutes'] + 20)
        add_showtime(movie2['id'], auditorium2['id'], showtime2_start, showtime2_end, 12.50)
    
    if movie3 and auditorium1:
        showtime3_start = tomorrow.replace(hour=19, minute=0, second=0, microsecond=0)
        showtime3_end = showtime3_start + timedelta(minutes=movie3['duration_minutes'] + 20)
        add_showtime(movie3['id'], auditorium1['id'], showtime3_start, showtime3_end, 15.00)
    
    # Day after tomorrow showtimes
    day_after_tomorrow = now + timedelta(days=2)
    
    if movie1 and auditorium2:
        showtime4_start = day_after_tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)
        showtime4_end = showtime4_start + timedelta(minutes=movie1['duration_minutes'] + 20)
        add_showtime(movie1['id'], auditorium2['id'], showtime4_start, showtime4_end, 12.50)
    
    if movie2 and auditorium3:
        showtime5_start = day_after_tomorrow.replace(hour=20, minute=0, second=0, microsecond=0)
        showtime5_end = showtime5_start + timedelta(minutes=movie2['duration_minutes'] + 20)
        add_showtime(movie2['id'], auditorium3['id'], showtime5_start, showtime5_end, 10.00)
    
    print("\n✅ Database seeding complete!\n")

if __name__ == "__main__":
    main()
