# Movie Reservation System - Full Stack Guide

## 🎬 Project Overview

Complete movie reservation system with:
- ✅ **Backend**: FastAPI + PostgreSQL + Redis
- ✅ **Frontend**: React + TypeScript + Tailwind CSS
- ✅ **Authentication**: JWT tokens
- ✅ **Booking**: Two-phase reservation with Redis holds
- ✅ **Admin**: Full CRUD management

## 📁 Project Structure

```
movie-reservation/
├── app/                          # Backend FastAPI application
│   ├── main.py                  # 40+ endpoints
│   ├── models.py                # 8 database models
│   ├── schemas.py               # 26+ Pydantic schemas
│   ├── crud.py                  # Database operations
│   ├── auth.py                  # JWT & password hashing
│   ├── config.py                # Pydantic settings
│   ├── database.py              # SQLAlchemy setup
│   ├── redis_client.py          # Redis connection
│   └── migrations/              # Alembic migrations
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   ├── lib/                 # API client
│   │   ├── store/               # Zustand state
│   │   ├── App.tsx              # Main app
│   │   └── main.tsx             # Entry point
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── tests/                        # Backend tests
├── docker-compose.yml            # Services setup
├── Dockerfile                    # Backend container
├── requirements.txt              # Python dependencies
└── README.md                     # Project summary

```

## 🚀 Quick Start

### 1. Backend Setup

```bash
# Navigate to project root
cd "C:\Users\akhil\Desktop\Movie Reservation\movie-reservation"

# Create virtual environment (if not exists)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/test_auth.py -v

# Start development server
uvicorn app.main:app --reload
```

Backend runs at: http://localhost:8000
API docs: http://localhost:8000/docs

### 2. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend runs at: http://localhost:3000

### 3. Docker Setup (Optional)

```bash
# Start all services (PostgreSQL, Redis, FastAPI)
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔐 Authentication Flow

1. **Signup**
   - POST `/auth/signup` with name, email, password
   - Creates user with Argon2-hashed password
   
2. **Login**
   - POST `/auth/login` with email, password
   - Returns: `{ access_token, refresh_token, user }`
   - Access token: 30-minute expiry
   - Refresh token: 7-day expiry

3. **Refresh**
   - POST `/auth/refresh` with refresh_token
   - Returns new access_token

## 🎫 Booking System

### Two-Phase Process

1. **Hold Phase (Redis)**
   - POST `/showtimes/{id}/holds` with seat_ids
   - Seats reserved for 10 minutes
   - Prevents overbooking

2. **Confirmation Phase (Database)**
   - POST `/reservations/{id}/confirm`
   - Creates atomic BookedSeat entry
   - UniqueConstraint prevents double-booking

## 👨‍💼 Admin Features

### Movies
- `POST /admin/movies` - Add movie
- `GET /admin/movies` - List movies
- `PUT /admin/movies/{id}` - Update movie
- `DELETE /admin/movies/{id}` - Delete movie

### Auditoriums
- `POST /admin/auditoriums` - Add auditorium
- `GET /admin/auditoriums` - List auditoriums
- `PUT /admin/auditoriums/{id}` - Update
- `DELETE /admin/auditoriums/{id}` - Delete

### Showtimes
- `POST /admin/showtimes` - Add showtime (with overlap check)
- `GET /admin/showtimes` - List showtimes
- `PUT /admin/showtimes/{id}` - Update (with overlap check)
- `DELETE /admin/showtimes/{id}` - Delete

### Seats
- `POST /admin/auditoriums/{id}/seats/batch` - Create batch
- `GET /admin/auditoriums/{id}/seats` - Get seats
- `DELETE /admin/seats/{id}` - Delete seat

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_auth.py::test_signup_and_login -v

# With coverage
pytest tests/ --cov=app
```

## 🔧 Configuration

### Backend (.env)

```env
DATABASE_URL=postgresql://user:password@localhost:5432/movie_db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
HOLD_TTL_SECONDS=600
```

### Frontend

Proxy configured in `frontend/vite.config.ts`:
- API calls to `/api/*` → `http://localhost:8000/*`

## 📊 Database Schema

### Tables
1. **User** - Users with roles (user, admin)
2. **Movie** - Movies with metadata
3. **Auditorium** - Theater auditoriums
4. **Seat** - Theater seats with pricing
5. **Showtime** - Movie showtimes with scheduling
6. **Reservation** - User reservations
7. **ReservationSeat** - Junction table
8. **BookedSeat** - Atomic booked seats (UniqueConstraint)

## 🎨 Frontend Features

### Pages
- **Login** - User authentication
- **Signup** - New user registration
- **Movies** - Browse and book showtimes
- **Admin** - Manage movies, auditoriums, showtimes

### Components
- **Navbar** - Navigation with user info
- **Protected Routes** - JWT-based access control
- **Seat Grid** - Interactive seat selection
- **Forms** - Create/update entities

### Styling
- **Tailwind CSS** - Utility-first CSS framework
- **Dark Theme** - Modern dark UI
- **Glassmorphism** - Glass effect components
- **Gradients** - Purple/pink accent colors

## 🔄 API Integration

Frontend uses Axios with:
- Automatic JWT token injection
- Token refresh on 401
- Error handling
- Request/response interceptors

```typescript
// Auto-refreshes token when expired
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Refresh token automatically
    }
  }
)
```

## 📦 Dependencies

### Backend
- **fastapi** - Web framework
- **sqlalchemy==1.4.49** - ORM
- **pydantic-settings** - Configuration
- **passlib[argon2]** - Password hashing
- **python-jose** - JWT tokens
- **redis** - Session cache
- **alembic** - Migrations
- **pytest** - Testing

### Frontend
- **react** - UI library
- **react-router-dom** - Navigation
- **typescript** - Type safety
- **tailwindcss** - Styling
- **zustand** - State management
- **axios** - HTTP client
- **lucide-react** - Icons
- **vite** - Build tool

## 🚢 Deployment

### Backend
1. Set production environment variables
2. Run database migrations: `alembic upgrade head`
3. Deploy with: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### Frontend
1. Build: `npm run build`
2. Deploy `dist/` folder to static hosting
3. Configure API proxy to backend

### Docker
```bash
docker-compose up -d
```

Services:
- Web: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## 🐛 Troubleshooting

### Backend Issues

**"Connection refused" to PostgreSQL**
- Check docker-compose is running: `docker-compose ps`
- Verify DATABASE_URL in .env

**"email-validator missing"**
- Run: `pip install email-validator`

**"Tests fail with encoding error"**
- Set: `$env:PYTHONIOENCODING = 'utf-8'`

### Frontend Issues

**"Cannot find module errors"**
- Run: `npm install`
- Delete node_modules and reinstall if persistent

**"API calls failing"**
- Check backend is running: `http://localhost:8000/docs`
- Verify proxy in vite.config.ts

**"CORS errors"**
- Backend should have CORS enabled for localhost:3000
- Check app/main.py for CORSMiddleware

## 📚 Documentation

- **Backend API**: http://localhost:8000/docs (Swagger UI)
- **Frontend Code**: See `frontend/README.md`
- **Project Summary**: See `PROJECT_SUMMARY.md`

## ✨ Next Steps

1. ✅ **Customize Branding**
   - Update logo in Navbar
   - Modify color scheme in Tailwind config

2. ✅ **Add Features**
   - Email notifications
   - Payment processing
   - Analytics dashboard
   - User reviews/ratings

3. ✅ **Optimize**
   - Add caching headers
   - Implement pagination
   - Add rate limiting
   - Enable GZIP compression

4. ✅ **Security**
   - Use strong JWT_SECRET
   - Enable HTTPS in production
   - Add rate limiting
   - Implement CSRF protection

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review API documentation at `/docs`
3. Check test files for usage examples
4. Review component props in code

## 📄 License

MIT License - Feel free to use for personal or commercial projects.

---

**Happy Booking! 🎬🍿**
