# ⚡ Quick Reference Card

## 🚀 Get Started (90 seconds)

### Windows
```bash
cd "C:\Users\akhil\Desktop\Movie Reservation\movie-reservation"
.\setup.bat
```

### Linux/Mac
```bash
cd ~/path/to/movie-reservation
chmod +x setup.sh
./setup.sh
```

---

## 📍 Access Your App

| What | URL | When |
|------|-----|------|
| **Frontend** | http://localhost:3000 | After `npm run dev` |
| **API Docs** | http://localhost:8000/docs | After `uvicorn app.main:app --reload` |
| **ReDoc** | http://localhost:8000/redoc | After backend is running |

---

## 🎯 Running the App

### Terminal 1 - Backend
```bash
# Activate venv
.venv\Scripts\activate          # Windows
# or
source .venv/bin/activate       # Linux/Mac

# Run backend
uvicorn app.main:app --reload
```

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

### Or use Docker
```bash
docker-compose up -d
```

---

## 📚 Documentation Quick Links

| Need | File |
|------|------|
| **Quick start** | `GETTING_STARTED.md` |
| **Complete guide** | `FULL_STACK_GUIDE.md` |
| **All features** | `PROJECT_SUMMARY.md` |
| **Frontend info** | `FRONTEND_SUMMARY.md` |
| **File structure** | `FILE_STRUCTURE.md` |
| **Project status** | `PROJECT_COMPLETE.md` |
| **API reference** | http://localhost:8000/docs |

---

## 🔐 Default Credentials

**No default users!** Create one:
1. Visit http://localhost:3000
2. Click "Sign Up"
3. Fill in the form
4. Login with your credentials

**For admin access:**
1. Create account normally
2. Manually set `role = 'admin'` in database
3. Access admin panel at `/admin`

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_auth.py::test_signup_and_login -v

# With coverage
pytest tests/ --cov=app
```

---

## 🔧 Common Commands

### Python Backend
```bash
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Start dev server
uvicorn app.main:app --reload

# Run linting
pylint app/

# Format code
black app/
```

### React Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview build
npm run preview

# Lint code
npm run lint

# Type check
npm run type-check
```

### Database Migrations
```bash
# Generate new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# View current version
alembic current
```

### Docker
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild
docker-compose up -d --build
```

---

## 📊 API Endpoints Quick Reference

### Auth (3)
```
POST /auth/signup                   # Register
POST /auth/login                    # Login
POST /auth/refresh                  # Refresh token
```

### Booking (3)
```
GET /showtimes/{id}/seats          # Get seats
POST /showtimes/{id}/holds         # Book seats
POST /reservations/{id}/confirm    # Confirm
```

### Admin (24+)
```
# Movies
POST /admin/movies
GET /admin/movies
GET /admin/movies/{id}
PUT /admin/movies/{id}
DELETE /admin/movies/{id}

# Auditoriums
POST /admin/auditoriums
GET /admin/auditoriums
GET /admin/auditoriums/{id}
PUT /admin/auditoriums/{id}
DELETE /admin/auditoriums/{id}

# Showtimes
POST /admin/showtimes
GET /admin/showtimes
GET /admin/showtimes/{id}
PUT /admin/showtimes/{id}
DELETE /admin/showtimes/{id}

# Seats
POST /admin/auditoriums/{id}/seats/batch
GET /admin/auditoriums/{id}/seats
DELETE /admin/seats/{id}
```

---

## 🏗️ Project Structure

```
movie-reservation/
├── app/                    ← Backend code
├── frontend/              ← React code
├── tests/                 ← Test files
├── docker-compose.yml     ← Services
├── requirements.txt       ← Python packages
├── setup.bat              ← Windows setup
├── setup.sh               ← Linux/Mac setup
├── GETTING_STARTED.md     ← Read this first
├── FULL_STACK_GUIDE.md    ← Complete guide
└── PROJECT_SUMMARY.md     ← Features
```

---

## ⚙️ Environment Variables

Create `.env` file:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/movie_db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
HOLD_TTL_SECONDS=600
```

**Defaults work for local dev!**

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 3000 in use | Kill process or change port in vite.config.ts |
| Port 8000 in use | Kill process or change port in uvicorn command |
| npm: command not found | Install Node.js from nodejs.org |
| python: command not found | Install Python 3.11+ from python.org |
| PostgreSQL connection error | Run `docker-compose up -d` or check credentials |
| Redis connection error | Run `docker-compose up -d` or check REDIS_URL |

---

## 📦 Key Dependencies

### Backend (Python)
- fastapi - Web framework
- sqlalchemy - Database ORM
- pydantic-settings - Config
- python-jose - JWT tokens
- passlib[argon2] - Password hashing
- redis - Cache client
- alembic - Migrations
- pytest - Testing

### Frontend (Node.js)
- react - UI library
- typescript - Type safety
- vite - Build tool
- tailwindcss - Styling
- react-router-dom - Navigation
- zustand - State management
- axios - HTTP client

---

## ✅ Verification Checklist

After setup, verify:
- [ ] Backend running on :8000
- [ ] Frontend running on :3000
- [ ] Can load http://localhost:3000
- [ ] Can access http://localhost:8000/docs
- [ ] Can sign up new user
- [ ] Can login
- [ ] Tests pass with `pytest tests/ -v`

---

## 🚀 Deployment Checklist

Before deploying:
- [ ] Update `.env` with production values
- [ ] Set strong JWT_SECRET
- [ ] Use production PostgreSQL
- [ ] Use production Redis
- [ ] Run migrations: `alembic upgrade head`
- [ ] Build frontend: `npm run build`
- [ ] Test everything locally first

---

## 📖 Documentation Map

```
START HERE → GETTING_STARTED.md
     ↓
Learn basics & run locally
     ↓
Explore code → Read source files
     ↓
Customize → Follow examples
     ↓
Deploy → Read FULL_STACK_GUIDE.md
     ↓
Go live!
```

---

## 🎯 Common Tasks

### Add a new movie
1. Go to http://localhost:3000/admin
2. Click "Add movie"
3. Fill form and submit

### Create a showtime
1. Admin → Showtimes tab
2. Click "Add showtime"
3. Select movie, auditorium, date/time

### Book a movie
1. Login at http://localhost:3000
2. Go to Movies
3. Select showtime
4. Choose seats
5. Click "Book"

### Check API
1. Go to http://localhost:8000/docs
2. Expand endpoint
3. Click "Try it out"
4. Fill parameters
5. Execute

---

## 🎬 You're All Set!

```
✅ Backend: Ready
✅ Frontend: Ready
✅ Database: Ready
✅ Tests: Passing
✅ Documentation: Complete

Ready to code! 🚀
```

**Next:** Run setup and visit http://localhost:3000

Happy coding! 🎨🎬
