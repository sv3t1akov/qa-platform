"""
Booking Domain T1 Lab: HTTP Contract & Basic Validation
========================================================
4 missions, 13 active bugs. One FastAPI app, one base_url.

Based on BOOKING_T1_SPEC_v2.md
"""
import os
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Path, Body, Header, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
import uvicorn

from app.flags_registry import get_flag, FLAGS

# ═══════════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════════
class Settings:
    PORT: int = int(os.getenv("PORT", "8080"))
    MISSION_ID: str = os.getenv("MISSION_ID", "booking-t1-lab")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "true").lower() == "true"

settings = Settings()

# ═══════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════

class GuestInfo(BaseModel):
    adults: int = Field(..., ge=1)
    children: Optional[int] = Field(0, ge=0)

class BookingCreate(BaseModel):
    roomId: Optional[str] = None
    checkIn: Optional[str] = None
    checkOut: Optional[str] = None
    guests: Optional[GuestInfo] = None
    totalPrice: Optional[float] = None  # Mass assignment bug
    guestInfo: Optional[Dict[str, Any]] = None

class GuestUpdate(BaseModel):
    firstName: Optional[Union[str, int, bool]] = None
    lastName: Optional[Union[str, int, bool]] = None
    email: Optional[str] = None
    phone: Optional[str] = None

# ═══════════════════════════════════════════════════════════════════════════
# IN-MEMORY DATABASE
# ═══════════════════════════════════════════════════════════════════════════

class Database:
    def __init__(self):
        self.properties: Dict[int, dict] = {}
        self.rooms: Dict[int, dict] = {}
        self.bookings: Dict[str, dict] = {}
        self.guests: Dict[str, dict] = {}
        self.booking_counter = 1
        self._seed()
    
    def _seed(self):
        # Seed 50 properties
        for i in range(1, 51):
            self.properties[i] = {
                "id": i,
                "name": f"Hotel {i}",
                "type": "HOTEL",
                "stars": (i % 5) + 1,
                "address": f"Street {i}, City",
                "description": f"Description for Hotel {i}"
            }
        
        # Seed 200+ rooms
        room_id = 1
        for prop_id in range(1, 51):
            rooms_per_property = 4 if prop_id <= 10 else 3
            for _ in range(rooms_per_property):
                self.rooms[room_id] = {
                    "id": room_id,
                    "propertyId": prop_id,
                    "name": f"Room {room_id}",
                    "pricePerNight": 10000 + (room_id * 100),
                    "currency": "KZT",
                    "capacity": 2 if room_id % 3 == 0 else 3,
                    # Hidden fields for HIDDEN_FIELDS bug
                    "internalCost": 5000 + (room_id * 50),
                    "marginPercent": round((10000 + (room_id * 100) - (5000 + (room_id * 50))) / (5000 + (room_id * 50)) * 100, 1),
                    "supplierCode": f"SUPPLIER-{room_id}"
                }
                room_id += 1
        
        # Seed some bookings
        # Important: book-2026-00050 belongs to guest_bob (for IDOR bug)
        for i in range(1, 31):
            booking_id = f"book-2026-{str(i).zfill(5)}"
            guest_id = f"guest_alice" if i <= 10 else f"guest_bob" if i <= 20 else f"guest_charlie"
            self.bookings[booking_id] = {
                "id": booking_id,
                "roomId": f"room-{i % 20 + 1}",
                "guestId": guest_id,
                "guestEmail": f"{guest_id.replace('guest_', '')}@example.com",
                "checkIn": "2026-03-15",
                "checkOut": "2026-03-18",
                "status": "CONFIRMED" if i <= 15 else "PENDING",
                "totalPrice": 30000 + (i * 1000),
                "nights": 3
            }
        
        # Add specific booking for IDOR bug (book-2026-00050 belongs to guest_bob)
        self.bookings["book-2026-00050"] = {
            "id": "book-2026-00050",
            "roomId": "room-42",
            "guestId": "guest_bob",
            "guestEmail": "bob@example.com",
            "checkIn": "2026-03-15",
            "checkOut": "2026-03-18",
            "status": "CONFIRMED",
            "totalPrice": 280000,
            "nights": 3
        }
        
        # Seed guest profiles
        self.guests["guest_alice"] = {
            "id": "guest_alice",
            "firstName": "Alice",
            "lastName": "Smith",
            "email": "alice@example.com",
            "phone": "+77001234567"
        }
        self.guests["guest_bob"] = {
            "id": "guest_bob",
            "firstName": "Bob",
            "lastName": "Johnson",
            "email": "bob@example.com",
            "phone": "+77007654321"
        }
    
    def get_property(self, prop_id: int) -> Optional[dict]:
        return self.properties.get(prop_id)
    
    def get_room(self, room_id: int) -> Optional[dict]:
        return self.rooms.get(room_id)
    
    def get_booking(self, booking_id: str) -> Optional[dict]:
        return self.bookings.get(booking_id)
    
    def create_booking(self, room_id: str, check_in: str, check_out: str, guests: dict, guest_id: str, total_price: Optional[float] = None) -> dict:
        booking_id = f"book-2026-{str(self.booking_counter).zfill(5)}"
        self.booking_counter += 1
        
        # Calculate price if not provided
        room = None
        for r in self.rooms.values():
            if str(r["id"]) == room_id.replace("room-", ""):
                room = r
                break
        
        calculated_price = total_price
        if calculated_price is None and room:
            from datetime import datetime
            check_in_date = datetime.strptime(check_in, "%Y-%m-%d").date()
            check_out_date = datetime.strptime(check_out, "%Y-%m-%d").date()
            nights = (check_out_date - check_in_date).days
            calculated_price = room["pricePerNight"] * nights
        
        booking = {
            "id": booking_id,
            "roomId": room_id,
            "guestId": guest_id,
            "guestEmail": f"{guest_id}@example.com",
            "checkIn": check_in,
            "checkOut": check_out,
            "status": "PENDING",
            "totalPrice": calculated_price,
            "nights": (datetime.strptime(check_out, "%Y-%m-%d").date() - datetime.strptime(check_in, "%Y-%m-%d").date()).days
        }
        self.bookings[booking_id] = booking
        return booking
    
    def get_guest(self, guest_id: str) -> Optional[dict]:
        return self.guests.get(guest_id)
    
    def update_guest(self, guest_id: str, data: dict) -> dict:
        if guest_id not in self.guests:
            self.guests[guest_id] = {"id": guest_id}
        self.guests[guest_id].update(data)
        return self.guests[guest_id]

db = Database()

# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Booking T1 Lab starting (13 active flags)")
    yield
    print("Booking T1 Lab shutdown")

app = FastAPI(title="Booking T1 Lab", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ═══════════════════════════════════════════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════════════════════════════════════════
@app.get("/health")
async def health():
    return {"status": "healthy", "mission": settings.MISSION_ID, "bugs": 13}

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 1: Properties & Rooms API
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/properties")
async def list_properties():
    """List all properties"""
    return {
        "data": list(db.properties.values()),
        "total": len(db.properties)
    }

@app.get("/api/v1/properties/{property_id}")
async def get_property(property_id: int = Path(...)):
    """
    Get property by ID
    """
    # NEGATIVE_ID: negative ID bypasses validation
    if property_id < 0:
        return {
            "id": property_id,
            "name": "INTERNAL_TEST_PROPERTY",
            "type": "SYSTEM",
            "flag": get_flag("NEGATIVE_ID"),
        }
    
    prop = db.get_property(property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop

@app.get("/api/v1/rooms/{room_id}")
async def get_room(room_id: int = Path(...)):
    """
    Get room by ID
    """
    # BOUNDARY_OVERFLOW: very large numbers cause unhandled error
    if room_id > 9999999999999999:
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "Database error occurred",
                "flag": get_flag("BOUNDARY_OVERFLOW"),
            }
        )
    
    room = db.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # HIDDEN_FIELDS: internal fields exposed (always, per spec)
    response = dict(room)
    # Include internal fields in response (bug)
    response["flag"] = get_flag("HIDDEN_FIELDS")
    
    return response

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 2: Availability API
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/rooms/{room_id}/availability")
async def check_availability(
    room_id: int = Path(...),
    checkIn: str = Query(...),
    checkOut: str = Query(...),
    adults: int = Query(2, ge=1)
):
    """
    Check room availability
    """
    room = db.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    try:
        check_in_date = datetime.strptime(checkIn, "%Y-%m-%d").date()
        check_out_date = datetime.strptime(checkOut, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    today = date.today()
    
    # DATE_PAST: past dates accepted
    if check_in_date < today:
        nights = (check_out_date - check_in_date).days
        price = room["pricePerNight"] * nights
        return {
            "roomId": room_id,
            "checkIn": checkIn,
            "checkOut": checkOut,
            "available": True,
            "totalPrice": price,
            "flag": get_flag("DATE_PAST"),
        }
    
    # DATE_REVERSED: checkout before checkin
    if check_out_date < check_in_date:
        nights = (check_out_date - check_in_date).days  # Negative
        price = room["pricePerNight"] * nights  # Negative price
        return {
            "roomId": room_id,
            "checkIn": checkIn,
            "checkOut": checkOut,
            "nights": nights,
            "available": True,
            "totalPrice": price,
            "flag": get_flag("DATE_REVERSED"),
        }
    
    # ZERO_DURATION: same dates
    if check_in_date == check_out_date:
        return {
            "roomId": room_id,
            "checkIn": checkIn,
            "checkOut": checkOut,
            "nights": 0,
            "available": True,
            "totalPrice": 0,
            "flag": get_flag("ZERO_DURATION"),
        }
    
    # CAPACITY_EXCEEDED: guest count exceeds capacity
    room_capacity = room.get("capacity", 2)
    if adults > room_capacity:
        return {
            "roomId": room_id,
            "available": True,
            "requestedGuests": adults,
            "roomCapacity": room_capacity,
            "flag": get_flag("CAPACITY_EXCEEDED"),
        }
    
    # Normal case
    nights = (check_out_date - check_in_date).days
    price = room["pricePerNight"] * nights
    return {
        "roomId": room_id,
        "checkIn": checkIn,
        "checkOut": checkOut,
        "nights": nights,
        "available": True,
        "totalPrice": price
    }

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 3: Bookings API
# ═══════════════════════════════════════════════════════════════════════════

def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """Extract user ID from Authorization header"""
    if authorization and authorization.startswith("Bearer "):
        # Simple token parsing - in real app would verify JWT
        token = authorization.replace("Bearer ", "")
        if token.startswith("guest_"):
            return token
    return "guest_alice"  # Default user

@app.post("/api/v1/bookings")
async def create_booking(
    data: BookingCreate = Body(...),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Create a new booking
    """
    user_id = get_current_user_id(authorization)
    
    # MISSING_REQUIRED: empty roomId accepted
    if data.roomId == "" or data.roomId is None:
        booking = db.create_booking(
            room_id=None,
            check_in=data.checkIn or "2026-03-15",
            check_out=data.checkOut or "2026-03-18",
            guests=data.guests.dict() if data.guests else {"adults": 2},
            guest_id=user_id
        )
        booking["roomId"] = None
        booking["status"] = "PENDING"
        booking["flag"] = get_flag("MISSING_REQUIRED")
        return JSONResponse(status_code=201, content=booking)
    
    # WRONG_STATUS_CODE: negative adults returns 200 with error in body
    if data.guests and data.guests.adults < 0:
        return JSONResponse(
            status_code=200,  # Should be 400
            content={
                "success": False,
                "error": "Invalid guest count",
                "flag": get_flag("WRONG_STATUS_CODE"),
            }
        )
    
    # PRICE_OVERRIDE: client-provided price accepted
    if data.totalPrice is not None:
        booking = db.create_booking(
            room_id=data.roomId,
            check_in=data.checkIn or "2026-03-15",
            check_out=data.checkOut or "2026-03-18",
            guests=data.guests.dict() if data.guests else {"adults": 2},
            guest_id=user_id,
            total_price=data.totalPrice
        )
        # Calculate what price should be
        room = None
        for r in db.rooms.values():
            if str(r["id"]) == data.roomId.replace("room-", ""):
                room = r
                break
        
        calculated_price = booking["totalPrice"]
        if room:
            check_in_date = datetime.strptime(data.checkIn or "2026-03-15", "%Y-%m-%d").date()
            check_out_date = datetime.strptime(data.checkOut or "2026-03-18", "%Y-%m-%d").date()
            nights = (check_out_date - check_in_date).days
            calculated_price = room["pricePerNight"] * nights
        
        booking["calculatedPrice"] = calculated_price
        booking["flag"] = get_flag("PRICE_OVERRIDE")
        return JSONResponse(status_code=201, content=booking)
    
    # Normal case
    booking = db.create_booking(
        room_id=data.roomId,
        check_in=data.checkIn or "2026-03-15",
        check_out=data.checkOut or "2026-03-18",
        guests=data.guests.dict() if data.guests else {"adults": 2},
        guest_id=user_id
    )
    return JSONResponse(status_code=201, content=booking)

@app.get("/api/v1/bookings/{booking_id}")
async def get_booking(
    booking_id: str = Path(...),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Get booking by ID
    """
    user_id = get_current_user_id(authorization)
    booking = db.get_booking(booking_id)
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # IDOR_ACCESS: no authorization check for specific booking
    # booking_id "book-2026-00050" belongs to guest_bob
    # If current user is guest_alice, they should get 403, but bug allows access
    booking_owner = booking.get("guestId", "")
    
    # Bug: for specific booking ID, skip authorization check
    if booking_id == "book-2026-00050" and booking_owner != user_id:
        booking["flag"] = get_flag("IDOR_ACCESS")
        return booking
    
    # Normal case - check authorization
    if booking_owner != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return booking

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 4: Guest Profile API
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/guests/me")
async def get_my_profile(authorization: Optional[str] = Header(None, alias="Authorization")):
    """Get current user's profile"""
    user_id = get_current_user_id(authorization)
    guest = db.get_guest(user_id)
    if not guest:
        # Create default profile
        guest = {"id": user_id, "firstName": "", "lastName": "", "email": ""}
        db.guests[user_id] = guest
    return guest

@app.put("/api/v1/guests/me")
async def update_my_profile(
    data: GuestUpdate = Body(...),
    authorization: Optional[str] = Header(None, alias="Authorization")
):
    """
    Update current user's profile
    """
    user_id = get_current_user_id(authorization)
    guest = db.get_guest(user_id)
    if not guest:
        guest = {"id": user_id}
        db.guests[user_id] = guest
    
    update_data = {}
    
    # TYPE_COERCION: non-string values coerced to strings
    if data.firstName is not None:
        if not isinstance(data.firstName, str):
            # Coerce to string without validation
            update_data["firstName"] = str(data.firstName)
            guest = db.update_guest(user_id, update_data)
            guest["flag"] = get_flag("TYPE_COERCION")
            return guest
        update_data["firstName"] = data.firstName
    
    if data.lastName is not None:
        if not isinstance(data.lastName, str):
            update_data["lastName"] = str(data.lastName)
            guest = db.update_guest(user_id, update_data)
            guest["flag"] = get_flag("TYPE_COERCION")
            return guest
        update_data["lastName"] = data.lastName
    
    # INVALID_FORMAT: invalid email format accepted
    if data.email is not None:
        # Simple check - if doesn't contain @, it's invalid
        if "@" not in data.email and data.email != "":
            update_data["email"] = data.email
            guest = db.update_guest(user_id, update_data)
            guest["flag"] = get_flag("INVALID_FORMAT")
            return guest
        update_data["email"] = data.email
    
    guest = db.update_guest(user_id, update_data)
    return guest

# ═══════════════════════════════════════════════════════════════════════════
# RUN SERVER
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
