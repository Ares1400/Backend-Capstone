# Tise Restaurant Management & Food Ordering System — API Backend

A full-featured Django REST API for managing restaurants, menus, orders, payments, deliveries, and reviews.

---

## Tech Stack
- **Django 5** + **Django REST Framework**
- **PostgreSQL** (SQLite fallback available)
- **JWT Auth** via `djangorestframework-simplejwt`
- **Paystack** payment gateway
- **Swagger/ReDoc** API documentation via `drf-yasg`

---

## Quick Start

### 1. Install
```bash
cd restaurant_api
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your PostgreSQL and Paystack credentials
# Set USE_SQLITE=True to skip PostgreSQL setup during development
```

### 3. Create the Database (PostgreSQL)
```sql
-- In psql:
CREATE DATABASE restaurant_db;
```

### 4. Run Migrations & Create Admin
```bash
python manage.py migrate
python manage.py createsuperuser
```
> After creating the superuser, open `/admin/`, find your user, and set **role = admin**.

### 5. Run the Server
```bash
python manage.py runserver
```

### 6. API Docs
- Swagger UI: http://localhost:8000/swagger/
- ReDoc:      http://localhost:8000/redoc/
- Django Admin: http://localhost:8000/admin/

---

## User Roles
| Role | Capabilities |
|------|-------------|
| **Customer** | Browse restaurants/menu, manage cart, place orders, pay, review |
| **Restaurant Owner** | Register restaurant, manage menu, accept & advance orders |
| **Delivery Rider** | Manage assigned deliveries, update delivery status |
| **Admin** | Approve restaurants, manage users, access analytics |

> Admin accounts cannot be self-registered. Create one via `createsuperuser` or the Django shell.

---

## API Endpoints

### Authentication — `/api/auth/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register/` | None | Register (customer, restaurant_owner, or delivery_rider) |
| POST | `/login/` | None | Login — returns JWT access + refresh tokens |
| POST | `/logout/` | Bearer | Blacklist refresh token |
| POST | `/refresh/` | None | Refresh access token |
| GET/PATCH | `/profile/` | Bearer | View or update own profile |
| POST | `/change-password/` | Bearer | Change password while logged in |
| POST | `/reset-password/` | None | Request password reset email |
| POST | `/reset-password/confirm/` | None | Confirm password reset with token |
| GET | `/verify-email/<token>/` | None | Verify email address |

### Restaurants — `/api/restaurants/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | None | Browse approved & active restaurants |
| POST | `/register/` | Restaurant Owner | Submit a new restaurant for admin approval |
| GET | `/mine/` | Restaurant Owner | View own restaurants (any status) |
| GET/PATCH/DELETE | `/{id}/` | Bearer | Get, update or delete a restaurant |
| GET | `/admin/restaurants/pending/` | Admin | List pending restaurant applications |
| PATCH | `/admin/restaurants/{id}/approve/` | Admin | Approve a restaurant |
| PATCH | `/admin/restaurants/{id}/reject/` | Admin | Reject a restaurant |
| PATCH | `/admin/restaurants/{id}/suspend/` | Admin | Suspend an active restaurant |

### Menu — `/api/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET/POST | `/categories/` | Bearer | List or create food categories (Admin creates) |
| GET/PUT/PATCH/DELETE | `/categories/{id}/` | Bearer | Get, update or delete a category |
| GET | `/foods/` | None | Browse all available food items |
| POST | `/foods/` | Restaurant Owner | Create a food item |
| GET/PUT/PATCH/DELETE | `/foods/{id}/` | Bearer | Get, update or delete a food item |

### Cart — `/api/cart/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Customer | View cart with items and totals |
| POST | `/` | Customer | Add a food item to cart |
| PATCH/DELETE | `/{item_id}/` | Customer | Update quantity or remove cart item |
| DELETE | `/clear/` | Customer | Clear the entire cart |

### Orders — `/api/orders/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Bearer | List orders (scoped to role) |
| POST | `/` | Customer | Checkout — convert cart into an order |
| GET | `/{id}/` | Bearer | Get order detail |
| PATCH | `/{id}/status/` | Bearer | Advance order through its lifecycle |

### Payments — `/api/payments/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Bearer | List own payments |
| POST | `/` | Customer | Initiate Paystack or cash-on-delivery payment |
| POST | `/verify/` | Customer | Verify Paystack payment after redirect |
| GET | `/{id}/receipt/` | Bearer | Get payment receipt |

### Deliveries — `/api/deliveries/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Bearer | List deliveries (scoped to role) |
| POST | `/` | Restaurant Owner | Create and assign a delivery to a rider |
| GET | `/{id}/` | Bearer | Get delivery detail |
| PATCH | `/{id}/status/` | Rider | Update delivery status (picked_up / delivered) |

### Reviews — `/api/reviews/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET/POST | `/` | Bearer | List or submit a review (only on delivered orders) |

### Favorites — `/api/favorites/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET/POST | `/` | Bearer | List or save favorite food items / restaurants |
| DELETE | `/{id}/` | Bearer | Remove a favorite |

### Notifications — `/api/notifications/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | Bearer | List notifications |
| GET/DELETE | `/{id}/` | Bearer | Read or delete a single notification |

### Analytics — `/api/admin/`
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/analytics/` | Admin | Platform-wide dashboard stats |
| GET | `/restaurants/{id}/analytics/` | Admin or Owner | Restaurant-level stats |

---

## Order Status Workflow
```
pending → accepted → preparing → out_for_delivery → delivered
   ↓           ↓
cancelled   cancelled
```
> Status transitions are enforced server-side. Invalid jumps (e.g. `pending → delivered`) are rejected.

---

## Paystack Payment Flow
1. `POST /api/payments/` with `{ "order": <id>, "method": "paystack" }`
2. Redirect the user to the `paystack_authorization_url` returned in the response
3. After payment, call `POST /api/payments/verify/` with the `reference` to confirm
4. Payment status flips to `successful` and a notification is auto-created

Use `{ "method": "cash" }` for cash-on-delivery instead.

---

## Running Tests
```bash
# Django test runner:
python manage.py test tests

# Or with pytest (recommended):
pytest
```

---

## Project Structure
```
restaurant_api/
├── config/           # Django settings, root URLs, wsgi/asgi
├── apps/
│   ├── users/        # Custom user model, JWT auth, password reset
│   ├── restaurants/  # Restaurant registration + admin approval
│   ├── menu/         # Categories + food items
│   ├── cart/         # Customer cart and cart items
│   ├── orders/       # Checkout, order lifecycle
│   ├── payments/     # Paystack + cash-on-delivery integration
│   ├── deliveries/   # Rider assignment, delivery tracking
│   ├── reviews/      # Ratings for food items and restaurants
│   ├── favorites/    # Saved food items and restaurants
│   ├── notifications/# In-app notification log (signal-driven)
│   └── core/         # Shared permissions, responses, analytics
├── tests/            # Full automated test suite
├── docs/             # ER diagram + Postman collection
├── manage.py
├── requirements.txt
└── .env.example
```
