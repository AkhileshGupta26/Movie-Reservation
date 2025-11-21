# 🎬 Movie Reservation System

A complete full-stack movie reservation and booking system built with **FastAPI** backend and **React** frontend.

## ✨ Features

✅ **User Authentication** - Signup, login, refresh tokens, logout  
✅ **Movie Browsing** - View available movies and showtimes  
✅ **Seat Selection** - Interactive seat map with hold/confirm flow  
✅ **Booking System** - Reserve seats with 10-minute hold timeout  
✅ **Admin Dashboard** - Full CRUD for movies, auditoriums, showtimes, seats, bookings  
✅ **Real-time Updates** - Redis-backed seat management  
✅ **Token Persistence** - Automatic login restoration on page reload  
✅ **Modern UI** - React with TypeScript and Tailwind CSS  
✅ **Production Ready** - Error handling, validation, comprehensive docs  

## 🚀 Quick Start

### Backend
```bash
cd movie-reservation
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Backend runs at: **http://127.0.0.1:8000**

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at: **http://localhost:3000**

### Test Credentials
- Email: `test@example.com`
- Password: `password123`

## 📁 Project Structure

```
movie-reservation/
├── app/
│   ├── main.py           # FastAPI app with 40+ endpoints
│   ├── models.py         # SQLAlchemy database models
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── auth.py           # JWT and password hashing
│   ├── crud.py           # Database operations
│   └── config.py         # Environment configuration
├── frontend/
│   ├── src/
│   │   ├── pages/        # Login, Signup, Movies, Admin
│   │   ├── components/   # Navbar, layout components
│   │   ├── lib/          # Axios API client
│   │   └── store/        # Zustand state management
│   └── vite.config.ts
├── requirements.txt      # Python dependencies
└── README.md
```

## 🔌 API Endpoints

**Authentication:**
- `POST /auth/signup` - Create account
- `POST /auth/login` - Login with credentials
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout

**Movies & Showtimes:**
- `GET /movies` - List all movies
- `GET /showtimes` - List all showtimes
- `POST /showtimes/{id}` - Get specific showtime with seats

**Bookings:**
- `POST /reservations` - Create reservation (hold seats)
- `POST /reservations/{id}/confirm` - Confirm booking
- `GET /reservations` - List user's reservations

**Admin (Full CRUD):**
- Movies: `GET`, `POST`, `PUT`, `DELETE`
- Auditoriums: `GET`, `POST`, `PUT`, `DELETE`
- Seats: `GET`, `POST`, `DELETE` (batch operations)
- Showtimes: `GET`, `POST`, `PUT`, `DELETE`

## 🛠️ Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- SQLAlchemy 1.4 - ORM
- PostgreSQL/SQLite - Database
- Redis - Session/seat management
- JWT - Authentication
- Argon2 - Password hashing
- Alembic - Database migrations

**Frontend:**
- React 18 - UI library
- TypeScript - Type safety
- Vite - Build tool
- Zustand - State management
- Tailwind CSS - Styling
- Axios - HTTP client
- React Router - Navigation

## 🐳 Docker Support

Run with Docker Compose:
```bash
docker-compose up --build
```

## 📚 Documentation

- **START_HERE.md** - Getting started guide
- **FULL_STACK_GUIDE.md** - Architecture overview
- **QUICK_REFERENCE.md** - API quick reference
- **PROJECT_COMPLETE.md** - Feature checklist

## 🎓 Learning Resources

This project demonstrates:
- Full-stack development (FastAPI + React)
- Database design with relationships
- JWT authentication flow
- State management with localStorage
- API design (REST principles)
- Responsive UI design
- Docker containerization

## 📝 License

MIT

## 👤 Author

Created by Akhil Gupta

---

**Ready to use?** Start the servers and visit http://localhost:3000
