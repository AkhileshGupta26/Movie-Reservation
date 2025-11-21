# 📋 QUICK REFERENCE: Design Improvements Summary

**Prepared for:** Movie Reservation System  
**Tech Stack:** FastAPI + React + SQLAlchemy + Redis + PostgreSQL  
**Date:** November 2024

---

## 1️⃣ AUTHENTICATION & ROLE SEPARATION

### Problem ❌
```
Current: Single signup/login, role field ignored, no permission checks
Result: Anyone can call /admin/* endpoints
```

### Solution ✅
```
Separate flows:
  POST /api/v1/auth/user/signup      → Role: user
  POST /api/v1/auth/admin/signup     → Requires admin_secret
  POST /api/v1/auth/login            → Returns user object with role

Dependencies:
  @Depends(get_current_user)         → Any authenticated user
  @Depends(get_admin_user)           → Only admins (403 otherwise)
  @Depends(get_optional_user)        → Auth optional (None if not logged in)

Result: Role-based access control enforced on every endpoint
```

---

## 2️⃣ DATABASE SCHEMA

### Key Additions
```python
# Enums (type safety)
UserRoleEnum: USER | ADMIN | STAFF
ReservationStatusEnum: HELD | CONFIRMED | CANCELLED | COMPLETED
SeatTypeEnum: REGULAR | PREMIUM | WHEELCHAIR | COUPLE

# Audit Trail (all tables)
created_at, updated_at, created_by, is_deleted

# Improved Reservation Model
id, user_id, showtime_id, status, total_price,
hold_expires_at, confirmed_at, payment_method, payment_id

# Unified Seat Booking (remove BookedSeat table)
Use: Reservation (HELD) → Reservation (CONFIRMED)
     No need for separate BookedSeat table
```

### New Indexes
```sql
-- For performance
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_showtime_movie ON showtimes(movie_id);
CREATE INDEX idx_reservation_user ON reservations(user_id);
CREATE INDEX idx_reservation_status ON reservations(status);
```

---

## 3️⃣ API STRUCTURE

### Before
```
POST   /auth/signup
POST   /auth/login
GET    /movies
POST   /admin/movies
PUT    /movies/1
DELETE /movies/1
GET    /showtimes/1/seats
POST   /showtimes/1/holds
```

### After (Organized, Versioned)
```
/api/v1/
├─ /auth/
│  ├─ POST user/signup
│  ├─ POST admin/signup
│  ├─ POST login
│  └─ POST refresh
│
├─ /movies/
│  ├─ GET (all)
│  ├─ GET {id}
│  └─ POST search?genre=...
│
├─ /showtimes/
│  ├─ GET (all)
│  ├─ GET {id}
│  ├─ GET {id}/seats
│  └─ GET movie/{movie_id}
│
├─ /bookings/
│  ├─ POST hold (create reservation)
│  ├─ POST {id}/confirm
│  ├─ POST {id}/cancel
│  ├─ GET my (user's bookings)
│  └─ GET {id} (details)
│
└─ /admin/
   ├─ /movies/ (POST, PUT, DELETE)
   ├─ /showtimes/ (POST, PUT, DELETE)
   ├─ /auditoriums/ (POST, PUT, DELETE)
   ├─ /seats/ (POST batch, PUT, DELETE)
   ├─ /bookings/ (GET all, detailed view)
   └─ /reports/
      ├─ GET revenue
      ├─ GET occupancy
      └─ GET user-stats
```

---

## 4️⃣ ERROR HANDLING

### Before (Generic)
```python
raise HTTPException(status_code=400, detail='Invalid seat selection')
raise HTTPException(status_code=409, detail='Some seats already booked')
raise HTTPException(status_code=404, detail='Reservation not found')
```

### After (Specific & Structured)
```python
# Custom exceptions (app/exceptions.py)
raise NotFoundException("Seat")
raise SeatAlreadyBookedException()
raise SeatAlreadyHeldException()
raise HoldExpiredException()
raise ForbiddenException("Admin role required")

# Response Structure (consistent)
{
  "status": "error",
  "status_code": 409,
  "detail": "One or more seats are already booked",
  "error_code": "SEAT_BOOKED",
  "timestamp": "2024-11-21T10:15:00Z"
}
```

---

## 5️⃣ SERVICE LAYER

### Before (Logic in Endpoints)
```python
@app.post('/showtimes/{id}/holds')
def hold_seats(showtime_id, req, db):
    # Check seats
    # Check booked
    # Check held
    # Create reservation
    # Add to Redis
    # ... 30 lines of code
```

### After (Logic Isolated)
```python
# File: app/services/booking_service.py
class BookingService:
    @staticmethod
    def hold_seats(user, showtime_id, seat_ids, db) -> dict:
        # All booking logic here
        # Returns: {reservation_id, expires_at, total_price}

# File: app/api/v1/bookings/routes.py
@router.post('/hold')
def hold_seats_endpoint(
    user: User = Depends(get_current_user),
    req: HoldSeatsRequest,
    db: Session = Depends(get_db)
):
    # Just calls service
    result = BookingService.hold_seats(user, req.showtime_id, req.seat_ids, db)
    return result
```

**Benefits:** Reusable, testable, maintainable

---

## 6️⃣ FOLDER STRUCTURE

### Current
```
app/
├─ main.py (363 lines, too large)
├─ models.py
├─ schemas.py
├─ crud.py
├─ auth.py
└─ ...
```

### Improved (Modular)
```
app/
├─ main.py (50 lines, just setup)
├─ config.py
├─ models.py
├─ schemas.py
├─ exceptions.py (new)
├─ deps.py (new - auth dependencies)
│
├─ api/v1/
│  ├─ router.py (combines all routers)
│  ├─ auth/
│  │  ├─ routes.py
│  │  └─ service.py
│  ├─ movies/
│  │  ├─ user_routes.py
│  │  ├─ admin_routes.py
│  │  └─ service.py
│  ├─ bookings/
│  │  ├─ routes.py
│  │  └─ service.py
│  └─ admin/
│     ├─ routes.py
│     └─ service.py
│
├─ crud/
│  ├─ base.py (generic CRUD)
│  ├─ movies.py
│  ├─ showtimes.py
│  ├─ reservations.py
│  └─ seats.py
│
├─ services/
│  ├─ booking_service.py
│  ├─ pricing_service.py
│  ├─ payment_service.py
│  └─ notification_service.py
│
└─ utils/
   ├─ validators.py
   └─ helpers.py
```

---

## 7️⃣ BOOKING FLOW COMPARISON

### Current (Complex)
```
Frontend
  ↓ POST /showtimes/1/holds
Backend (no user extracted from token)
  ├─ Query seats from DB
  ├─ Check BookedSeat table
  ├─ Check Redis for holds
  ├─ Create Reservation (user_id=None ❌)
  ├─ Create ReservationSeat entries
  ├─ Set Redis holds
  ├─ Return reservation_id
  └─ Issues: Lost user context, unclear pricing, no expiry tracking
```

### Improved (Clear & Atomic)
```
Frontend (with token in Authorization header)
  ↓ POST /api/v1/bookings/hold
Backend (with authentication)
  ├─ get_current_user() extracts User from JWT
  ├─ BookingService.hold_seats() does:
  │  ├─ Validate seats exist (error if not)
  │  ├─ Validate showtime exists (error if not)
  │  ├─ Check if already booked/held (error if yes)
  │  ├─ Calculate total price with modifiers
  │  ├─ Create Reservation (with user_id ✓)
  │  ├─ Create ReservationSeat mappings (prices tracked)
  │  ├─ Set Redis holds with TTL
  │  └─ Return: {id, expires_at, total_price, seats[]}
  └─ Atomic transaction, clear pricing, automatic expiry
```

---

## 8️⃣ SECURITY IMPROVEMENTS

### Authentication
```
✓ JWT with type tracking (access vs refresh)
✓ Token expiry properly validated
✓ Separate token generation with different TTLs
✓ Refresh token rotation ready
```

### Authorization
```
✓ Role checking on every admin endpoint
✓ Custom exceptions for access denied (403)
✓ User can only see/modify own bookings
✓ Admin can see all bookings/reports
```

### Data Validation
```
✓ All inputs validated with Pydantic
✓ Seat IDs checked for duplicates
✓ Showtime times validated (end > start)
✓ Prices positive, seats > 0
```

### Rate Limiting
```
# Add to future phase
@limiter.limit("5/minute")
@app.post("/auth/login")
def login(...):
    pass

# Prevents brute force attacks
```

---

## 9️⃣ MISSING FEATURES (Priority)

| # | Feature | Why | Effort | Impact |
|---|---------|-----|--------|--------|
| 1 | User Cancellation | Required for UX | Low | High |
| 2 | Booking History | User expectation | Low | High |
| 3 | Email Notifications | Confirmation emails | Med | High |
| 4 | Payment Integration | Revenue | High | Critical |
| 5 | Admin Dashboard | Analytics | Med | High |
| 6 | Search/Filters | Discoverability | Low | Med |
| 7 | Wishlist | Engagement | Low | Low |
| 8 | Reviews & Ratings | Social proof | Med | Low |
| 9 | Promotional Codes | Revenue | Med | Med |
| 10 | Dynamic Pricing | Optimization | High | Low |

---

## 🔟 IMPLEMENTATION PRIORITY

### Week 1-2: Foundation (MUST DO)
```
[ ] 1. Add role-based auth (separate signup/login)
[ ] 2. Create exceptions.py for error handling
[ ] 3. Add deps.py for permission checks
[ ] 4. Update models with enums & audit fields
[ ] 5. Create BookingService (centralize logic)
```

### Week 3-4: Scale (SHOULD DO)
```
[ ] 1. API versioning (/api/v1/)
[ ] 2. Separate routes by feature + role
[ ] 3. CRUD cleanup & reorganization
[ ] 4. Admin dashboard (reports)
[ ] 5. User cancellation & history
```

### Week 5+: Polish (NICE TO HAVE)
```
[ ] 1. Payment integration
[ ] 2. Email notifications
[ ] 3. Advanced search/filters
[ ] 4. Dynamic pricing
[ ] 5. Load testing & optimization
```

---

## 1️⃣1️⃣ COMPARISON TABLE

| Aspect | Current | Improved |
|--------|---------|----------|
| **Auth** | Single flow, no checks | Separate user/admin, enforced |
| **Errors** | Generic HTTP | Specific, structured |
| **Code Org** | Monolithic | Modular by feature |
| **Service Logic** | In endpoints | Isolated in services |
| **Role Check** | None | Every admin endpoint |
| **API** | Flat | Versioned, organized |
| **Testing** | Hard | Easy (services, mocks) |
| **Scalability** | Limited | Easy to extend |
| **User Info** | Lost (user_id=None) | Tracked via JWT |
| **Pricing** | Not detailed | Line item tracking |
| **Audit Trail** | None | Full history |
| **Soft Deletes** | None | Supported |

---

## 1️⃣2️⃣ MIGRATION STRATEGY

### Step 1: Add New Code (No changes to existing)
```bash
# New files, old endpoints untouched
app/exceptions.py (new)
app/deps.py (new)
app/services/booking_service.py (new)
app/api/v1/ (new)

# Old endpoints still work
GET /movies → still works
POST /admin/movies → still works
```

### Step 2: Update Frontend (Point to new endpoints)
```javascript
// Old
api.post('/movies', movieData)

// New
api.post('/api/v1/admin/movies', movieData)
```

### Step 3: Monitor & Deprecate
```
// Old endpoint: still works but logs warning
GET /movies → logs "DEPRECATED: use /api/v1/movies"

// Old endpoint: still works, 200 OK
GET /admin/movies → still works, works with old auth logic
```

### Step 4: Remove (After 2-4 weeks)
```
// Only when frontend fully migrated
DELETE /movies → 404
DELETE /admin/movies → 404

// But /api/v1/* always available
GET /api/v1/movies → works
GET /api/v1/admin/movies → works
```

---

## 1️⃣3️⃣ TESTING CHECKLIST

```
Auth:
  ✓ User signup works
  ✓ Admin signup requires secret
  ✓ Login returns role
  ✓ Token refresh works
  ✓ Admin endpoints blocked for users
  ✓ User endpoints work with token

Bookings:
  ✓ Hold seats creates reservation
  ✓ Can't hold already booked seats
  ✓ Can't hold held seats
  ✓ Confirm moves to confirmed state
  ✓ Expired holds can't be confirmed
  ✓ Cancel reverses the hold
  ✓ Cancel refunds payment

Errors:
  ✓ Invalid seat IDs → 422
  ✓ Booked seats → 409
  ✓ User not found → 401
  ✓ Admin endpoint for user → 403
  ✓ Missing auth header → 401
  ✓ Expired token → 401
```

---

## 1️⃣4️⃣ QUICK WINS (Easy, High Value)

| Task | Time | Value | Do It |
|------|------|-------|-------|
| Add exceptions.py | 2 hrs | High | ✓ |
| Add deps.py | 3 hrs | High | ✓ |
| Separate auth signup | 2 hrs | High | ✓ |
| Add role checks to endpoints | 3 hrs | High | ✓ |
| BookingService | 4 hrs | High | ✓ |
| API versioning | 2 hrs | Med | ✓ |
| Booking cancellation | 2 hrs | High | ✓ |
| Booking history | 2 hrs | High | ✓ |

**Total: ~20 hours for huge improvements**

---

## 1️⃣5️⃣ NEXT STEPS

### For You:
1. **Review** this document (architecture guide, implementation guide)
2. **Decide** which improvements to implement
3. **Start** with Foundation phase (auth + services)
4. **Test** each phase thoroughly
5. **Deploy** incrementally

### For Your Team:
1. **Share** these documents
2. **Discuss** implementation order
3. **Assign** tasks by sprint
4. **Schedule** code reviews
5. **Plan** deployment strategy

### For Your Codebase:
1. **Create** branches for each feature
2. **Keep** old code working (backward compatible)
3. **Write** tests before changes
4. **Document** changes in git commits
5. **Monitor** after deployment

---

**Status:** Ready for Implementation  
**Estimated Timeline:** 4-5 weeks for full implementation  
**Complexity:** Medium (no major rewrites, incremental improvements)  
**Risk:** Low (backward compatible, can rollback)

---

**Questions? Need clarification on any section? Let me know!**
