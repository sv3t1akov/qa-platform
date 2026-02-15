# Booking Domain T1 Lab

HTTP Contract & Basic Validation - 4 missions, 13 active bugs.

## Overview

This lab implements the Booking T1 domain according to `BOOKING_T1_SPEC_v2.md`:
- **Mission 1:** Properties & Rooms API (3 flags)
- **Mission 2:** Availability API (4 flags)
- **Mission 3:** Bookings API (4 flags)
- **Mission 4:** Guest Profile API (2 flags)

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Deploying to Fly.io

```bash
# Login to Fly.io
fly auth login

# Deploy
fly deploy
```

## API Endpoints

### Mission 1: Properties & Rooms
- `GET /api/v1/properties` - List all properties
- `GET /api/v1/properties/{id}` - Get property by ID
- `GET /api/v1/rooms/{id}` - Get room by ID

### Mission 2: Availability
- `GET /api/v1/rooms/{id}/availability?checkIn=YYYY-MM-DD&checkOut=YYYY-MM-DD&adults=N` - Check availability

### Mission 3: Bookings
- `POST /api/v1/bookings` - Create booking
- `GET /api/v1/bookings/{id}` - Get booking by ID

### Mission 4: Guest Profile
- `GET /api/v1/guests/me` - Get current user profile
- `PUT /api/v1/guests/me` - Update current user profile

## Flags

All 13 flags are registered in `app/flags_registry.py` and match the specification exactly.

## Testing

The lab includes seed data:
- 50 properties
- 200+ rooms
- 30 bookings
- 2 guest profiles

Use Authorization header: `Bearer guest_alice` or `Bearer guest_bob` for testing.
