# 🏗️ SYSTEM ARCHITECTURE & DECISION MATRIX

---

## 📊 Current vs Improved Architecture

### Current Architecture (Simple)

```
┌─────────────────────────────────────────────────────────┐
│                   React Frontend                         │
│              (Token Storage, UI)                         │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                        │
│                                                          │
│  ├─ /auth/signup, /auth/login                          │
│  ├─ /movies, /showtimes, /seats                        │
│  ├─ /hold_seats, /confirm_reservation                  │
│  ├─ /admin/* (no auth check)                           │
│  └─ /reservations (mixed logic)                        │
│                                                          │
└────┬─────────────────────────────────────────────────┬──┘
     │                                                 │
     ▼                                                 ▼
┌──────────────┐                                   ┌──────────┐
│  SQLite DB   │                                   │  Redis   │
│              │                                   │ (holds)  │
└──────────────┘                                   └──────────┘

Issues:
❌ No role separation
❌ Mixed concerns
❌ Hard to scale
❌ Inconsistent error handling
❌ Seat logic fragmented
```

### Improved Architecture (Modular)

```
┌──────────────────────────────────────────────────────────────┐
│                    React Frontend                            │
│                                                              │
│  ├─ LoginPage (role: user/admin)                            │
│  ├─ UserPages (Movies, Showtimes, Bookings)                │
│  ├─ AdminPages (Dashboard, CRUD, Reports)                  │
│  └─ Auth Store (with role tracking)                        │
└────────────────────┬─────────────────────────────────────┬──┘
                     │ HTTP /api/v1                        │
                     ▼                                      ▼
        ┌────────────────────────────────────────────────────┐
        │            FastAPI Backend (Versioned)             │
        │                                                    │
        │  ┌─ api/v1/auth/                                  │
        │  │  └─ Separate user/admin signup                 │
        │  │                                                 │
        │  ├─ api/v1/movies/                                │
        │  │  ├─ user_routes.py (GET only + search)         │
        │  │  └─ admin_routes.py (Full CRUD)                │
        │  │                                                 │
        │  ├─ api/v1/showtimes/                             │
        │  │  ├─ user_routes.py (GET + seat status)         │
        │  │  └─ admin_routes.py (CRUD + scheduling)        │
        │  │                                                 │
        │  ├─ api/v1/bookings/                              │
        │  │  └─ Hold, Confirm, Cancel, History             │
        │  │                                                 │
        │  └─ api/v1/admin/                                 │
        │     └─ Dashboard + Reports                        │
        │                                                    │
        │  Services Layer (Business Logic)                   │
        │  ├─ BookingService (hold/confirm/cancel)          │
        │  ├─ PricingService (dynamic pricing)              │
        │  ├─ NotificationService (email alerts)            │
        │  └─ PaymentService (integrate Stripe)             │
        │                                                    │
        │  CRUD Layer (Database Ops)                         │
        │  ├─ movies.py                                      │
        │  ├─ showtimes.py                                  │
        │  ├─ reservations.py                               │
        │  └─ seats.py                                      │
        │                                                    │
        │  deps.py (Auth & Permissions)                     │
        │  ├─ get_current_user()                            │
        │  ├─ get_admin_user()                              │
        │  └─ get_optional_user()                           │
        │                                                    │
        │  exceptions.py (Consistent Error Handling)        │
        │  ├─ NotFoundException                             │
        │  ├─ UnauthorizedException                         │
        │  ├─ SeatAlreadyBookedException                    │
        │  └─ HoldExpiredException                          │
        │                                                    │
        └────────────────┬──────────────────────────────┬──┘
                         │                              │
              ┌──────────┴────────┐                     │
              ▼                   ▼                     ▼
        ┌──────────────┐  ┌──────────────┐      ┌──────────┐
        │ PostgreSQL   │  │    Redis     │      │ Stripe   │
        │   (primary)  │  │  (caching &  │      │(payment) │
        │              │  │  seat holds) │      │          │
        └──────────────┘  └──────────────┘      └──────────┘

Benefits:
✅ Clear role separation (user/admin)
✅ Modular by feature
✅ Easy to scale
✅ Consistent error handling
✅ Business logic isolated
✅ Easy to add features
```

---

## 🔄 Data Flow Comparison

### Current: User Booking Flow

```
Frontend Form Submit
       │
       ▼
POST /showtimes/{id}/holds
       │
       ├─ Check seats exist? (DB query)
       ├─ Check booked? (DB query)
       ├─ Check held? (Redis check)
       ├─ Create reservation (DB)
       ├─ Add reservation_seats (DB)
       ├─ Set Redis holds (Redis)
       │
       ▼
Response with reservation_id
```

### Improved: User Booking Flow (Service Layer)

```
Frontend Form Submit
       │
       ▼
POST /api/v1/bookings/hold
       │
       ├─ get_current_user() [deps]
       │  └─ Validate JWT + get User from DB
       │
       ▼
BookingService.hold_seats()
       │
       ├─ Validate seats [exception if not found]
       ├─ Validate showtime [exception if not found]
       ├─ Check conflicts [exception if booked/held]
       ├─ Calculate pricing
       ├─ Create Reservation + ReservationSeats (atomic transaction)
       ├─ Set Redis holds with TTL
       ├─ Return response with pricing breakdown
       │
       ▼
Response with:
{
  "reservation_id": 42,
  "expires_at": "2024-11-21T10:15:00Z",
  "total_price": 250.00,
  "seats": [
    {"id": 5, "row": "A", "seat": "5", "price": 125.00},
    {"id": 6, "row": "A", "seat": "6", "price": 125.00}
  ]
}
```

---

## 🎯 DECISION MATRIX: Which Features to Implement First?

| Feature | Priority | Effort | Impact | User Value | Recommendation |
|---------|----------|--------|--------|-----------|-----------------|
| **Role-Based Auth** | HIGH | Medium | Critical | High | ✅ **FIRST** |
| **Service Layer** | HIGH | High | Critical | High | ✅ **2nd** |
| **Better Error Handling** | HIGH | Low | High | Medium | ✅ **3rd** |
| **API Versioning** | MEDIUM | Low | Medium | Low | ✅ **4th** |
| **Payment Integration** | HIGH | High | Critical | High | 5th (after core) |
| **Email Notifications** | MEDIUM | Medium | High | High | 6th (after core) |
| **Admin Dashboard/Reports** | MEDIUM | Medium | High | High | 7th |
| **Cancellation & Refunds** | MEDIUM | Medium | High | High | 8th |
| **Booking History** | MEDIUM | Low | Medium | High | 9th |
| **Search & Filters** | LOW | Low | Low | High | 10th (quick win) |
| **Reviews & Ratings** | LOW | Low | Low | Medium | Later |
| **Dynamic Pricing** | LOW | High | Low | Low | Later |

---

## 🚀 Recommended Implementation Timeline

### Sprint 1: Foundation (Week 1-2)
**Focus:** Security & Core Functionality
```
├─ Role-Based Authentication
│  ├─ Enums (UserRole, ReservationStatus, SeatType)
│  ├─ Separate signup endpoints
│  ├─ Role-based dependencies
│  └─ Test user/admin flows
│
├─ Custom Exception Handling
│  ├─ Create exceptions.py
│  ├─ Update all endpoints to use custom exceptions
│  └─ Ensure consistent error responses
│
└─ Database Audit Trail
   ├─ Add audit fields (created_by, updated_at, is_deleted)
   └─ Soft deletes for all entities

**Deliverable:** Secure auth system with role separation
**Testing:** All endpoints return proper errors + roles enforced
**Deployment:** Security patch
```

### Sprint 2: Service Layer & Business Logic (Week 3)
**Focus:** Clean Code & Maintainability
```
├─ Booking Service
│  ├─ Centralize hold/confirm/cancel logic
│  ├─ Add pricing calculation
│  └─ Handle edge cases (expiry, conflicts)
│
├─ CRUD Reorganization
│  ├─ Generic CRUD base class
│  ├─ Implement for each entity
│  └─ Remove duplicate code
│
└─ API Endpoints
   ├─ Separate user/admin routes
   └─ Add missing endpoints (cancel, history)

**Deliverable:** Modular code with centralized business logic
**Testing:** Unit tests for services + integration tests
**Deployment:** Refactoring with behavior preservation
```

### Sprint 3: Scalability & Features (Week 4)
**Focus:** User Experience & Admin Tools
```
├─ API Versioning
│  ├─ Create /api/v1/ structure
│  ├─ Plan for /api/v2/ compatibility
│  └─ Document endpoint changes
│
├─ Admin Dashboard
│  ├─ Revenue reports
│  ├─ Occupancy analytics
│  └─ Booking management
│
├─ Frontend Role-Based UI
│  ├─ Separate login flows
│  ├─ Admin vs User pages
│  └─ Protected routes by role
│
└─ Payment Integration
   ├─ Stripe/Razorpay integration
   ├─ Payment status tracking
   └─ Refund handling

**Deliverable:** Fully featured, role-based system
**Testing:** E2E tests for user/admin flows
**Deployment:** Major release with backward compatibility
```

### Sprint 4: Polish & Scale (Week 5)
**Focus:** Production Readiness
```
├─ Notifications
│  ├─ Email confirmations
│  ├─ Hold expiry alerts
│  └─ Booking receipts
│
├─ Testing & Documentation
│  ├─ Comprehensive API docs
│  ├─ Deployment guide
│  └─ Code comments & type hints
│
└─ Monitoring & Observability
   ├─ Error logging
   ├─ Performance metrics
   └─ User analytics

**Deliverable:** Production-ready system
**Testing:** Full regression suite + load testing
**Deployment:** Release to production
```

---

## 💡 Quick Decision Guide

### "Should I implement this feature?"

**Ask these questions:**

1. **Does it unblock other features?**
   - YES → Do it first
   - NO → Check question 2

2. **Is it essential for security?**
   - YES → Do it immediately
   - NO → Check question 3

3. **Is it expected by users?**
   - YES → Do it soon
   - NO → Check question 4

4. **Can it be added incrementally?**
   - YES → Build MVP, enhance later
   - NO → Plan carefully before starting

5. **How much effort?**
   - < 4 hours → Do it now
   - 4-16 hours → Schedule it
   - > 16 hours → Break into smaller tasks

---

## 🔍 Code Quality Checklist

### Before Implementing Each Feature

- [ ] Write schema/model changes first
- [ ] Write tests before implementation
- [ ] Add docstrings to all functions
- [ ] Handle all error cases
- [ ] Add input validation
- [ ] Test with invalid inputs
- [ ] Check permissions (auth/role)
- [ ] Update Swagger docs
- [ ] Verify backward compatibility
- [ ] Performance test with large datasets

### Before Deployment

- [ ] All tests passing (unit + integration)
- [ ] No console errors/warnings
- [ ] Database migrations tested
- [ ] Rollback plan documented
- [ ] Team review completed
- [ ] Deployment checklist verified

---

## 📈 Performance Optimization Roadmap

| Layer | Current | Optimize | Tool/Technique |
|-------|---------|----------|-----------------|
| **Database** | No indexing | Add indexes on frequently queried fields | `sqlalchemy.Index` |
| **API** | No caching | Cache movie/showtime lists | Redis with TTL |
| **Seats** | Full scan each query | Materialized view or Redis cache | Redis sorted set |
| **Search** | Linear search | Full-text search index | PostgreSQL FTS |
| **Pagination** | No limits | Cursor-based pagination | Keyset pagination |
| **Auth** | JWT decode on each request | Token validation cache | Redis token cache |

---

## 🛠️ Tech Debt & Refactoring

### Current Technical Debt
- ❌ Mixed concerns (routing + logic + data)
- ❌ No error standardization
- ❌ Unclear role enforcement
- ❌ Fragmented seat management logic
- ❌ Hard-coded values in endpoints

### Refactoring Strategy
1. **Extract business logic** → Services
2. **Centralize error handling** → exceptions.py
3. **Separate routes** → by feature + role
4. **Create dependencies** → for auth/auth
5. **Consolidate CRUD** → base class

### Refactoring Effort
```
High-Value, Low-Effort:
  ✓ Create exceptions.py (2 hours)
  ✓ Extract services (6 hours)
  ✓ Add role checks (2 hours)

Medium-Effort, High-Value:
  ✓ API reorganization (8 hours)
  ✓ CRUD cleanup (4 hours)

Lower-Priority:
  • Caching optimization (later)
  • Full-text search (when needed)
  • Microservices (when scaling)
```

---

## 📋 Migration Checklist: From Current to Improved

```
Phase 1: Safety (Backward Compatible)
├─ ✓ Add new code alongside old
├─ ✓ Both endpoints coexist
├─ ✓ Database migration scripts
├─ ✓ A/B test if possible
└─ Rollback: Keep old code active

Phase 2: Gradual Migration
├─ ✓ Frontend points to /api/v1/
├─ ✓ Old endpoints deprecated but working
├─ ✓ Monitor old endpoint usage
├─ ✓ Remove deprecated endpoints after 2 weeks
└─ Rollback: Easy since old code still available

Phase 3: Full Migration
├─ ✓ Remove old endpoints
├─ ✓ Update documentation
├─ ✓ Archive old code in git
└─ Rollback: Can restore from git if critical bugs found
```

---

## 🎓 Learning Resources for Each Component

### Authentication & Authorization
- [ ] JWT Best Practices: https://tools.ietf.org/html/rfc8725
- [ ] OWASP Authentication Guide
- [ ] FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/

### Service-Oriented Design
- [ ] Clean Architecture: Robert C. Martin
- [ ] Domain-Driven Design: Eric Evans
- [ ] Dependency Injection Pattern

### Testing
- [ ] pytest Documentation
- [ ] Test Pyramid (unit, integration, E2E)
- [ ] Mock Objects: unittest.mock

### Database Optimization
- [ ] SQL Query Optimization
- [ ] Indexing Strategies
- [ ] Transaction Isolation Levels

---

## 🎯 Success Metrics

### Technical Metrics
- Code coverage: **> 80%**
- Response time: **< 200ms** (p95)
- Error rate: **< 0.5%**
- Uptime: **> 99.5%**

### User Metrics
- Booking completion rate: **> 85%**
- Hold expiry rate: **< 10%**
- Customer support tickets: **< 5/day**

### Team Metrics
- Feature delivery: **1-2 per sprint**
- Bug fix time: **< 24 hours**
- Code review cycle: **< 4 hours**

---

## ❓ FAQ: Common Questions

### Q: How long will refactoring take?
**A:** ~3-4 weeks for full implementation. Can be done incrementally (~1 week for core auth + services).

### Q: Will it break existing functionality?
**A:** No - migration can be backward compatible. Keep both old and new endpoints during transition.

### Q: Should I use PostgreSQL or SQLite?
**A:** SQLite for dev, PostgreSQL for production. Use Alembic for migrations on both.

### Q: How do I handle the role-based frontend?
**A:** Separate routes (`/user`, `/admin`). Show menu based on `current_user.role`.

### Q: What about admin vs staff vs user roles?
**A:** Add staff role in `UserRoleEnum`. Use dependency `get_staff_or_admin()` for staff-only endpoints.

### Q: How to handle concurrent bookings?
**A:** Database unique constraint + Redis TTL ensures atomicity. No race conditions.

### Q: Should payments be sync or async?
**A:** Use async background task. Store payment status in DB. Webhook from Stripe for confirmation.

---

