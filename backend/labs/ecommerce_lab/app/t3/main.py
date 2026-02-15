"""
E-Commerce T3 Lab: Business Logic & Multi-Step Scenarios (Phase2: 17 active flags)
7 missions, 17 active bugs. One FastAPI app.
"""
import os
import secrets
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Path, Body, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from app.t3.flags_registry import get_flag, FLAGS

# ═══════════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════════
class Settings:
    PORT: int = int(os.getenv("PORT", "8080"))
    MISSION_ID: str = os.getenv("MISSION_ID", "ecom-t3-lab")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "true").lower() == "true"

settings = Settings()

# ═══════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════
class CartItemAdd(BaseModel):
    productId: Optional[str] = None
    quantity: Optional[int] = 1

class CartItemUpdate(BaseModel):
    quantity: Optional[int] = None

class ApplyPromoBody(BaseModel):
    code: Optional[str] = None

class OrderCreate(BaseModel):
    cartId: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    status: Optional[str] = None

class OrderPayBody(BaseModel):
    amount: Optional[float] = None
    method: Optional[str] = "card"

class ReturnCreate(BaseModel):
    orderId: Optional[str] = None
    items: Optional[Union[List[dict], str]] = None
    reason: Optional[str] = "DEFECTIVE"

class PaymentInitiateBody(BaseModel):
    amount: Optional[float] = None

class PaymentConfirmBody(BaseModel):
    paymentId: Optional[str] = None

class LoyaltyRedeemBody(BaseModel):
    points: Optional[int] = None

class TestTimeAdvanceBody(BaseModel):
    minutes: Optional[int] = 30

class TestProductPriceBody(BaseModel):
    newPrice: Optional[float] = None

# ═══════════════════════════════════════════════════════════════════════════
# IN-MEMORY DATABASE WITH MULTI-STEP STATE SUPPORT
# ═══════════════════════════════════════════════════════════════════════════
class Database:
    def __init__(self):
        self.products: Dict[str, dict] = {}
        self.carts: Dict[str, dict] = {}
        self.orders: Dict[str, dict] = {}
        self.returns: Dict[str, dict] = {}
        self.payments: Dict[str, dict] = {}
        self.promos: Dict[str, dict] = {}
        
        # Multi-step state: caches and reservations
        self.cart_totals_cache: Dict[str, float] = {}  # user_id -> cached_total (CART_STALE_TOTAL)
        self.cart_promo_cache: Dict[str, str] = {}  # user_id -> promo_code (CART_PROMO_PERSIST)
        self.cart_price_cache: Dict[str, Dict[str, float]] = {}  # user_id -> {productId: frozen_price} (CART_PRICE_FREEZE)
        self.stock_reservations: Dict[str, Dict[str, int]] = {}  # user_id -> {productId: reserved_qty} (STOCK_RESERVE_EXPIRE)
        self.reservation_expiry: Dict[str, datetime] = {}  # reservation_id -> expiry_time
        self.loyalty_points: Dict[str, int] = {}  # user_id -> points
        self.payment_sessions: Dict[str, dict] = {}  # payment_id -> {amount, cart_snapshot}
        
        # Test state manipulation
        self.test_time_offset: timedelta = timedelta(0)
        self.test_product_prices: Dict[str, float] = {}  # productId -> test_price
        
        # Track redemptions and idempotency
        self.redemptions: set = set()
        self.idempotency_keys: Dict[str, bool] = {}
        
        self.order_id_counter = 1
        self.return_id_counter = 1
        self.payment_id_counter = 1
        
        self._seed()
    
    def _seed(self):
        # Products for different missions
        # PROD-001: Standard product for cart state bugs
        self.products["PROD-001"] = {
            "id": "PROD-001",
            "name": "Standard Item",
            "price": 100.0,
            "stock": 100,
            "category": "GENERAL"
        }
        
        # PROD-002: Low stock for quantity cache bug
        self.products["PROD-002"] = {
            "id": "PROD-002",
            "name": "Limited Item",
            "price": 50.0,
            "stock": 3,
            "category": "GENERAL"
        }
        
        # PROD-003: Price change product
        self.products["PROD-003"] = {
            "id": "PROD-003",
            "name": "Flash Sale Item",
            "price": 50.0,
            "stock": 50,
            "category": "GENERAL"
        }
        
        # ELEC-001: Electronics for promo bug
        self.products["ELEC-001"] = {
            "id": "ELEC-001",
            "name": "Electronics Item",
            "price": 200.0,
            "stock": 50,
            "category": "ELECTRONICS"
        }
        
        # CLOTH-001: Clothing for promo bug
        self.products["CLOTH-001"] = {
            "id": "CLOTH-001",
            "name": "Clothing Item",
            "price": 100.0,
            "stock": 50,
            "category": "CLOTHING"
        }
        
        # PROD-STOCK-001: Low stock for reserve expire bug
        self.products["PROD-STOCK-001"] = {
            "id": "PROD-STOCK-001",
            "name": "Limited Stock Item",
            "price": 200.0,
            "stock": 2,
            "category": "GENERAL"
        }
        
        # CHEAP-001, EXPENSIVE-001: For discount volume threshold abuse
        self.products["CHEAP-001"] = {
            "id": "CHEAP-001",
            "name": "Cheap Item",
            "price": 50.0,
            "stock": 100,
            "category": "GENERAL"
        }
        
        self.products["EXPENSIVE-001"] = {
            "id": "EXPENSIVE-001",
            "name": "Expensive Item",
            "price": 500.0,
            "stock": 50,
            "category": "GENERAL"
        }
        
        # FOOD-001: Food item for return bug
        self.products["FOOD-001"] = {
            "id": "FOOD-001",
            "name": "Food Item",
            "price": 30.0,
            "stock": 100,
            "category": "FOOD"
        }
        
        # PROD-STOCK-002, PROD-STOCK-003, PROD-STOCK-004: For stock bugs
        self.products["PROD-STOCK-002"] = {
            "id": "PROD-STOCK-002",
            "name": "Stock Test Item 2",
            "price": 100.0,
            "stock": 10,
            "category": "GENERAL"
        }
        
        self.products["PROD-STOCK-003"] = {
            "id": "PROD-STOCK-003",
            "name": "Stock Test Item 3",
            "price": 150.0,
            "stock": 5,
            "category": "GENERAL"
        }
        
        self.products["PROD-STOCK-004"] = {
            "id": "PROD-STOCK-004",
            "name": "Stock Test Item 4",
            "price": 200.0,
            "stock": 20,
            "category": "GENERAL"
        }
        
        # Promos
        self.promos["ELECTRONICS20"] = {
            "code": "ELECTRONICS20",
            "discount": 20,
            "type": "PERCENT",
            "categories": ["ELECTRONICS"],
            "valid": True
        }
        
        self.promos["FLAT100"] = {
            "code": "FLAT100",
            "discount": 100,
            "type": "FIXED",
            "minOrder": 0,  # Bug: no minimum!
            "valid": True
        }
        
        self.promos["LOYALTY10"] = {
            "code": "LOYALTY10",
            "discount": 10,
            "type": "PERCENT",
            "categories": [],
            "valid": True
        }
        
        self.promos["VIP50"] = {
            "code": "VIP50",
            "discount": 50,
            "type": "PERCENT",
            "categories": [],
            "valid": True
        }
        
        self.promos["EXPIRED2024"] = {
            "code": "EXPIRED2024",
            "discount": 30,
            "type": "PERCENT",
            "categories": [],
            "valid": False  # Expired
        }
        
        # Pre-created orders for state machine tests
        self.orders["ORD-PENDING-001"] = {
            "id": "ORD-PENDING-001",
            "status": "PENDING",
            "total": 100.0,
            "createdAt": datetime.now().isoformat()
        }
        
        self.orders["ORD-CANCELLED-001"] = {
            "id": "ORD-CANCELLED-001",
            "status": "CANCELLED",
            "total": 100.0,
            "createdAt": (datetime.now() - timedelta(days=1)).isoformat()
        }
        
        self.orders["ORD-EXPIRE-001"] = {
            "id": "ORD-EXPIRE-001",
            "status": "CREATED",
            "total": 50.0,
            "createdAt": (datetime.now() - timedelta(minutes=35)).isoformat(),
            "expiresAt": (datetime.now() - timedelta(minutes=5)).isoformat()
        }
        
        self.orders["ORD-DELIVERED-001"] = {
            "id": "ORD-DELIVERED-001",
            "status": "DELIVERED",
            "total": 250.0,
            "items": [{"productId": "PROD-001", "quantity": 2, "price": 100.0}],
            "deliveredAt": (datetime.now() - timedelta(days=7)).isoformat()
        }
        
        self.orders["ORD-SHIPPED-001"] = {
            "id": "ORD-SHIPPED-001",
            "status": "SHIPPED",
            "total": 300.0,
            "shippedAt": datetime.now().isoformat()
        }
        
        self.orders["ORD-CONFIRMED-001"] = {
            "id": "ORD-CONFIRMED-001",
            "status": "CONFIRMED",
            "total": 150.0,
            "items": [{"productId": "PROD-STOCK-002", "quantity": 5, "price": 100.0}],
            "createdAt": datetime.now().isoformat()
        }
        
        self.orders["ORD-RET-001"] = {
            "id": "ORD-RET-001",
            "status": "DELIVERED",
            "total": 300.0,
            "items": [
                {"itemId": "ITEM-001", "productId": "PROD-001", "quantity": 1, "price": 100.0},
                {"itemId": "ITEM-002", "productId": "PROD-001", "quantity": 1, "price": 100.0},
                {"itemId": "ITEM-003", "productId": "PROD-001", "quantity": 1, "price": 100.0}
            ],
            "deliveredAt": (datetime.now() - timedelta(days=5)).isoformat()
        }
        
        # Default cart
        self.carts["default"] = {
            "id": "default",
            "items": [],
            "subtotal": 0.0,
            "discount": 0.0,
            "total": 0.0,
            "promo": None
        }
        
        # Default loyalty points
        self.loyalty_points["default"] = 1000
    
    def get_cart(self, cid: str = "default") -> dict:
        if cid not in self.carts:
            self.carts[cid] = {
                "id": cid,
                "items": [],
                "subtotal": 0.0,
                "discount": 0.0,
                "total": 0.0,
                "promo": None
            }
        return self.carts[cid]
    
    def calculate_cart_total(self, cid: str = "default") -> float:
        cart = self.get_cart(cid)
        subtotal = 0.0
        for item in cart["items"]:
            product_id = item.get("productId")
            quantity = item.get("quantity", 0)
            
            # Check for frozen price (CART_PRICE_FREEZE bug)
            if cid in self.cart_price_cache and product_id in self.cart_price_cache[cid]:
                price = self.cart_price_cache[cid][product_id]
            else:
                product = self.products.get(product_id)
                if product:
                    # Check test price override
                    price = self.test_product_prices.get(product_id, product["price"])
                else:
                    price = item.get("price", 0.0)
            
            subtotal += price * quantity
        
        return subtotal
    
    def get_user_id(self, request: Request) -> str:
        """Extract user_id from request headers or use default"""
        return request.headers.get("X-User-Id", "default")

# Global database instance
db = Database()

# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown

app = FastAPI(
    title="E-Commerce T3 Lab",
    description="Business Logic & Multi-Step Scenarios",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════════════════
@app.get("/health")
async def health():
    return {"status": "ok", "mission": settings.MISSION_ID}

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 1: CART STATE MANIPULATION
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/cart/add")
async def cart_add(item: CartItemAdd, request: Request):
    """Add item to cart. Bug: CART_STALE_TOTAL, CART_PRICE_FREEZE"""
    user_id = db.get_user_id(request)
    cart = db.get_cart(user_id)
    
    product_id = item.productId
    quantity = item.quantity or 1
    
    if not product_id:
        raise HTTPException(status_code=400, detail="productId required")
    
    # Validate: negative quantity should be rejected
    if quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")
    
    product = db.products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Add item to cart
    cart_item = {
        "productId": product_id,
        "quantity": quantity,
        "price": product["price"]
    }
    cart["items"].append(cart_item)
    
    # BUG: CART_STALE_TOTAL - Cache total when adding
    total = db.calculate_cart_total(user_id)
    db.cart_totals_cache[user_id] = total
    
    # BUG: CART_PRICE_FREEZE - Freeze price in cache
    if user_id not in db.cart_price_cache:
        db.cart_price_cache[user_id] = {}
    db.cart_price_cache[user_id][product_id] = product["price"]
    
    cart["subtotal"] = total
    cart["total"] = total - cart.get("discount", 0.0)
    
    return {
        "cartId": cart["id"],
        "items": cart["items"],
        "subtotal": cart["subtotal"],
        "total": cart["total"]
    }

@app.delete("/cart/items/{product_id}")
async def cart_remove_item(
    product_id: str,
    quantity: Optional[int] = Query(1),
    request: Request = None
):
    """Remove item from cart. Bug: CART_STALE_TOTAL - doesn't update cache"""
    user_id = db.get_user_id(request) if request else "default"
    cart = db.get_cart(user_id)
    
    # Remove item(s)
    removed = 0
    for item in cart["items"][:]:
        if item["productId"] == product_id:
            if quantity and removed < quantity:
                item["quantity"] -= 1
                removed += 1
                if item["quantity"] <= 0:
                    cart["items"].remove(item)
            else:
                cart["items"].remove(item)
                removed = item["quantity"]
    
    # BUG: CART_STALE_TOTAL - Forgot to update cache!
    # db.cart_totals_cache[user_id] = db.calculate_cart_total(user_id)
    
    cart["subtotal"] = db.calculate_cart_total(user_id)
    cart["total"] = cart["subtotal"] - cart.get("discount", 0.0)
    
    return {
        "cartId": cart["id"],
        "items": cart["items"],
        "subtotal": cart["subtotal"],
        "total": cart["total"]
    }

@app.put("/cart/items/{product_id}")
async def cart_update_item(
    product_id: str,
    update: CartItemUpdate,
    request: Request = None
):
    """Update cart item quantity. Bug: CART_QUANTITY_CACHE - doesn't check stock"""
    user_id = db.get_user_id(request) if request else "default"
    cart = db.get_cart(user_id)
    
    new_quantity = update.quantity
    if new_quantity is None:
        raise HTTPException(status_code=400, detail="quantity required")
    
    # Validate: negative quantity should be rejected
    if new_quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")
    
    # Find and update item
    for item in cart["items"]:
        if item["productId"] == product_id:
            # BUG: CART_QUANTITY_CACHE - Update without stock validation
            # Should check: reserved_stock + new_quantity <= available_stock
            item["quantity"] = new_quantity
            
            cart["subtotal"] = db.calculate_cart_total(user_id)
            cart["total"] = cart["subtotal"] - cart.get("discount", 0.0)
            
            # Check if bug triggered
            product = db.products.get(product_id)
            if product and new_quantity > product["stock"]:
                return {
                    "cartId": cart["id"],
                    "items": cart["items"],
                    "flag": get_flag("CART_QUANTITY_CACHE"),
                    "_debug": "Quantity updated without stock validation"
                }
            
            return {
                "cartId": cart["id"],
                "items": cart["items"],
                "subtotal": cart["subtotal"],
                "total": cart["total"]
            }
    
    raise HTTPException(status_code=404, detail="Item not found in cart")

@app.post("/cart/apply-promo")
async def cart_apply_promo(promo: ApplyPromoBody, request: Request = None):
    """Apply promo code. Bug: CART_PROMO_PERSIST, CART_NEGATIVE_TOTAL"""
    user_id = db.get_user_id(request) if request else "default"
    cart = db.get_cart(user_id)
    
    code = promo.code
    if not code:
        raise HTTPException(status_code=400, detail="code required")
    
    promo_data = db.promos.get(code)
    if not promo_data or not promo_data.get("valid"):
        raise HTTPException(status_code=400, detail="Invalid promo code")
    
    # Check if promo applies to cart items
    eligible = False
    if promo_data.get("categories"):
        for item in cart["items"]:
            product = db.products.get(item["productId"])
            if product and product["category"] in promo_data["categories"]:
                eligible = True
                break
    else:
        eligible = True
    
    if not eligible:
        raise HTTPException(status_code=400, detail="Promo not applicable to cart items")
    
    # Apply discount
    subtotal = db.calculate_cart_total(user_id)
    if promo_data["type"] == "PERCENT":
        discount = subtotal * (promo_data["discount"] / 100)
    else:
        discount = promo_data["discount"]
    
    # BUG: DISCOUNT_STACK_FORBIDDEN - Stack forbidden discount types (PROMO + LOYALTY)
    existing_promo = cart.get("promo")
    if existing_promo and "LOYALTY" in existing_promo and "LOYALTY" not in code:
        # Stacking PROMO + LOYALTY (forbidden)
        total = subtotal - discount - (subtotal * 0.1)  # Assume 10% loyalty
        cart["promo"] = f"{existing_promo},{code}"
        cart["discount"] = discount + (subtotal * 0.1)
        cart["total"] = total
        return {
            "cartId": cart["id"],
            "promo": cart["promo"],
            "subtotal": subtotal,
            "discount": cart["discount"],
            "total": total,
            "flag": get_flag("DISCOUNT_STACK_FORBIDDEN"),
            "_debug": "Stacked forbidden discount types"
        }
    
    # BUG: DISCOUNT_EXCEED_50_CAP - Total discount exceeds 50% cap
    existing_discount = cart.get("discount", 0)
    total_discount = existing_discount + discount
    if total_discount > subtotal * 0.5:
        total = subtotal - total_discount
        cart["promo"] = code
        cart["discount"] = total_discount
        cart["total"] = total
        return {
            "cartId": cart["id"],
            "promo": code,
            "subtotal": subtotal,
            "discount": total_discount,
            "total": total,
            "_debug": "Total discount exceeds 50% cap"
        }
    
    # BUG: DISCOUNT_EXPIRED_PROMO - Apply expired promo code
    if not promo_data.get("valid"):
        total = subtotal - discount
        cart["promo"] = code
        cart["discount"] = discount
        cart["total"] = total
        return {
            "cartId": cart["id"],
            "promo": code,
            "subtotal": subtotal,
            "discount": discount,
            "total": total,
            "_debug": "Expired promo code applied"
        }
    
    # BUG: CART_NEGATIVE_TOTAL - Allow discount > subtotal (for cart-state mission)
    # BUG: DISCOUNT_NEGATIVE_TOTAL - Discount results in negative total (for discount mission)
    # Should check: discount <= subtotal
    
    total = subtotal - discount
    
    cart["promo"] = code
    cart["discount"] = discount
    cart["total"] = total
    
    # BUG: CART_PROMO_PERSIST - Cache promo code
    db.cart_promo_cache[user_id] = code
    
    # Check if bug triggered
    if total < 0:
        # Check mission context - if this is discount mission, use DISCOUNT_NEGATIVE_TOTAL
        # Otherwise use CART_NEGATIVE_TOTAL
        # For simplicity, check if multiple discounts or complex scenario
        existing_discount = cart.get("discount", 0)
        if existing_discount > 0 or len(cart.get("items", [])) > 1:
            return {
                "cartId": cart["id"],
                "subtotal": subtotal,
                "discount": discount + existing_discount,
                "total": total,
                "_debug": "Discount results in negative total"
            }
        else:
            return {
                "cartId": cart["id"],
                "subtotal": subtotal,
                "discount": discount,
                "total": total,
                "_debug": "Cart total went negative"
            }
    
    return {
        "cartId": cart["id"],
        "promo": code,
        "subtotal": subtotal,
        "discount": discount,
        "total": total
    }

@app.delete("/cart/promo")
async def cart_remove_promo(request: Request = None):
    """Remove promo from cart"""
    user_id = db.get_user_id(request) if request else "default"
    cart = db.get_cart(user_id)
    
    cart["promo"] = None
    cart["discount"] = 0.0
    cart["total"] = cart["subtotal"]
    
    return {
        "cartId": cart["id"],
        "subtotal": cart["subtotal"],
        "total": cart["total"]
    }

@app.get("/cart")
async def get_cart(request: Request = None):
    """Get cart contents"""
    user_id = db.get_user_id(request) if request else "default"
    cart = db.get_cart(user_id)
    cart["subtotal"] = db.calculate_cart_total(user_id)
    cart["total"] = cart["subtotal"] - cart.get("discount", 0.0)
    return cart

@app.get("/cart/calculate")
async def cart_calculate(request: Request = None):
    """Recalculate cart total"""
    user_id = db.get_user_id(request) if request else "default"
    cart = db.get_cart(user_id)
    subtotal = db.calculate_cart_total(user_id)
    discount = cart.get("discount", 0.0)
    total = subtotal - discount
    
    return {
        "subtotal": subtotal,
        "discount": discount,
        "total": total
    }

@app.post("/checkout")
async def checkout(request: Request = None):
    """Checkout cart. Bug: CART_STALE_TOTAL, CART_PROMO_PERSIST, CART_PRICE_FREEZE, STOCK_RESERVE_EXPIRE_CHECKOUT, STOCK_OVERSELL_RACE"""
    user_id = db.get_user_id(request) if request else "default"
    cart = db.get_cart(user_id)
    
    if not cart["items"]:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # BUG: STOCK_RESERVE_EXPIRE_CHECKOUT - Checkout with expired reservation when stock sold out
    for item in cart["items"]:
        product_id = item.get("productId")
        quantity = item.get("quantity", 0)
        if product_id:
            product = db.products.get(product_id)
            if product:
                # Check if reservation expired
                reserved = db.stock_reservations.get(user_id, {}).get(product_id, 0)
                if reserved > 0:
                    # Check if reservation expired (simplified - check time)
                    # In real scenario would check reservation_expiry
                    available = product["stock"]
                    if quantity > available:
                        # Reservation expired, stock was sold to others, but checkout still works
                        order_id = f"ORD-{db.order_id_counter}"
                        db.order_id_counter += 1
                        order = {
                            "id": order_id,
                            "items": cart["items"].copy(),
                            "subtotal": db.calculate_cart_total(user_id),
                            "charged": db.calculate_cart_total(user_id),
                            "status": "CONFIRMED",
                            "createdAt": datetime.now().isoformat()
                        }
                        db.orders[order_id] = order
                        # Stock goes negative
                        product["stock"] -= quantity
                        return {
                            "orderId": order_id,
                            "items": order["items"],
                            "stockAfter": product["stock"],
                            "flag": get_flag("STOCK_RESERVE_EXPIRE_CHECKOUT"),
                            "_debug": "Checkout succeeded with expired reservation, stock went negative"
                        }
    
    # BUG: STOCK_OVERSELL_RACE - Race condition allows overselling
    # Simplified - in real scenario would use locks
    for item in cart["items"]:
        product_id = item.get("productId")
        quantity = item.get("quantity", 0)
        if product_id:
            product = db.products.get(product_id)
            if product and quantity > product["stock"]:
                # Should fail, but race condition allows it
                order_id = f"ORD-{db.order_id_counter}"
                db.order_id_counter += 1
                order = {
                    "id": order_id,
                    "items": cart["items"].copy(),
                    "subtotal": db.calculate_cart_total(user_id),
                    "charged": db.calculate_cart_total(user_id),
                    "status": "CONFIRMED",
                    "createdAt": datetime.now().isoformat()
                }
                db.orders[order_id] = order
                product["stock"] -= quantity  # Goes negative
                return {
                    "orderId": order_id,
                    "items": order["items"],
                    "stockAfter": product["stock"],
                    "_debug": "Race condition allowed overselling"
                }
    
    # Calculate actual total
    actual_total = db.calculate_cart_total(user_id)
    
    # BUG: CART_STALE_TOTAL - Use cached total instead of recalculating
    cached_total = db.cart_totals_cache.get(user_id)
    if cached_total is not None:
        charge_amount = cached_total
    else:
        charge_amount = actual_total
    
    # BUG: CART_PROMO_PERSIST - Apply cached promo even if items changed
    promo_code = db.cart_promo_cache.get(user_id)
    if promo_code and promo_code != cart.get("promo"):
        promo_data = db.promos.get(promo_code)
        if promo_data:
            # Check if promo still applies
            eligible = False
            if promo_data.get("categories"):
                for item in cart["items"]:
                    product = db.products.get(item["productId"])
                    if product and product["category"] in promo_data["categories"]:
                        eligible = True
                        break
            else:
                eligible = True
            
            if not eligible:
                # BUG: Apply promo anyway
                if promo_data["type"] == "PERCENT":
                    discount = actual_total * (promo_data["discount"] / 100)
                else:
                    discount = promo_data["discount"]
                charge_amount = actual_total - discount
    
    # Create order
    order_id = f"ORD-{db.order_id_counter}"
    db.order_id_counter += 1
    
    order = {
        "id": order_id,
        "items": cart["items"].copy(),
        "subtotal": actual_total,
        "charged": charge_amount,
        "status": "CONFIRMED",
        "createdAt": datetime.now().isoformat()
    }
    db.orders[order_id] = order
    
    # Check for bugs
    response = {
        "orderId": order_id,
        "items": order["items"],
        "subtotal": actual_total,
        "charged": charge_amount
    }
    
    # CART_STALE_TOTAL bug
    if cached_total is not None and charge_amount > actual_total:
        response["flag"] = get_flag("CART_STALE_TOTAL")
        response["_debug"] = f"Charged ${charge_amount} but cart worth ${actual_total}"
        return response
    
    # CART_PROMO_PERSIST bug
    if promo_code and promo_code != cart.get("promo"):
        promo_data = db.promos.get(promo_code)
        if promo_data:
            eligible = False
            if promo_data.get("categories"):
                for item in cart["items"]:
                    product = db.products.get(item["productId"])
                    if product and product["category"] not in promo_data["categories"]:
                        eligible = False
                        break
                    else:
                        eligible = True
            else:
                eligible = True
            
            if not eligible and charge_amount < actual_total:
                response["promo"] = promo_code
                response["discount"] = actual_total - charge_amount
                response["total"] = charge_amount
                response["flag"] = get_flag("CART_PROMO_PERSIST")
                response["_debug"] = "Electronics promo applied to non-electronics items"
                return response
    
    # CART_PRICE_FREEZE bug
    frozen_prices_found = False
    for item in cart["items"]:
        product_id = item["productId"]
        if user_id in db.cart_price_cache and product_id in db.cart_price_cache[user_id]:
            frozen_price = db.cart_price_cache[user_id][product_id]
            product = db.products.get(product_id)
            current_price = db.test_product_prices.get(product_id, product["price"] if product else frozen_price)
            if frozen_price != current_price:
                frozen_prices_found = True
                response["items"] = [{
                    **item,
                    "frozenPrice": frozen_price,
                    "currentPrice": current_price
                } for item in cart["items"]]
                response["charged"] = charge_amount
                response["flag"] = get_flag("CART_PRICE_FREEZE")
                response["_debug"] = "Checkout used frozen price instead of current catalog price"
                return response
    
    # BUG: DISCOUNT_REMOVE_KEEP_PERCENT - Volume discount persists after removing qualifying items
    # Check if volume discount was applied but items changed
    subtotal = actual_total
    if subtotal < 500:  # Below volume threshold
        # Check if discount was previously applied
        if cart.get("promo") is None and charge_amount < subtotal:
            discount = subtotal - charge_amount
            if discount > 0:
                response["subtotal"] = subtotal
                response["discount"] = discount
                response["total"] = charge_amount
                response["discountReason"] = "VOLUME_10%"
                response["flag"] = get_flag("DISCOUNT_REMOVE_KEEP_PERCENT")
                response["_debug"] = "Volume discount applied to order below threshold"
                return response
    
    # BUG: DISCOUNT_VOLUME_THRESHOLD_ABUSE - Add expensive item for threshold, remove after discount applied
    # Similar to above but with explicit threshold abuse
    if subtotal < 500 and charge_amount < subtotal:
        discount = subtotal - charge_amount
        if discount > 0:
            response["items"] = cart["items"]
            response["discount"] = discount
            response["total"] = charge_amount
            response["_debug"] = "Volume discount persisted after removing qualifying items"
            return response
    
    # BUG: DISCOUNT_FLASH_SALE_PERSIST - Flash sale discount persists after sale ended
    # Check if flash sale price was used but sale ended
    for item in cart["items"]:
        product_id = item["productId"]
        if product_id in db.test_product_prices:
            # Price was changed (sale ended)
            test_price = db.test_product_prices[product_id]
            product = db.products.get(product_id)
            original_price = product["price"] if product else test_price
            if test_price > original_price:  # Price increased (sale ended)
                response["items"] = cart["items"]
                response["charged"] = charge_amount
                response["_debug"] = "Flash sale discount persisted after sale ended"
                return response
    
    # BUG: LOYALTY_EARN_SPEND_SAME - Earn and spend points in same order
    # Check if points were redeemed and also earned
    if cart.get("promo") and "LOYALTY" in str(cart.get("promo")):
        # LOYALTY_EARN_SPEND_SAME (Phase2: dropped, no flag)
        response["_debug"] = "Earned and spent points in same order"
        return response
    
    # Clear cart
    cart["items"] = []
    cart["subtotal"] = 0.0
    cart["discount"] = 0.0
    cart["total"] = 0.0
    cart["promo"] = None
    
    return response

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 2: ORDER STATE MACHINE
# ═══════════════════════════════════════════════════════════════════════════

VALID_STATE_TRANSITIONS = {
    "CREATED": ["PENDING", "EXPIRED"],
    "PENDING": ["PAID", "CANCELLED"],
    "PAID": ["CONFIRMED", "CANCELLED"],
    "CONFIRMED": ["PROCESSING", "CANCELLED"],
    "PROCESSING": ["SHIPPED"],
    "SHIPPED": ["DELIVERED"],
    "DELIVERED": ["RETURNED"],
    "CANCELLED": [],
    "EXPIRED": [],
    "RETURNED": []
}

@app.post("/orders")
async def create_order(order: OrderCreate, request: Request = None):
    """Create new order"""
    order_id = f"ORD-{db.order_id_counter}"
    db.order_id_counter += 1
    
    new_order = {
        "id": order_id,
        "status": "CREATED",
        "total": 100.0,
        "createdAt": datetime.now().isoformat()
    }
    db.orders[order_id] = new_order
    
    return new_order

@app.get("/orders/{order_id}")
async def get_order(order_id: str = Path(...)):
    """Get order by ID"""
    order = db.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.put("/orders/{order_id}/status")
async def update_order_status(
    order_id: str = Path(...),
    status_update: OrderStatusUpdate = Body(...)
):
    """Update order status. Bug: STATE_SKIP_PROCESSING, STATE_REVERSE_DELIVERED, STATE_CANCEL_SHIPPED, STATE_DOUBLE_TRANSITION, STATE_INVALID_INITIAL"""
    order = db.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    new_status = status_update.status
    current_status = order["status"]
    
    # BUG: STATE_INVALID_INITIAL - Allow invalid initial status
    if current_status == "CREATED" and new_status not in ["PENDING", "EXPIRED"]:
        # Should reject, but bug allows it
        order["status"] = new_status
        return {
            "orderId": order_id,
            "previousStatus": current_status,
            "newStatus": new_status,
            "_debug": "Invalid initial state transition"
        }
    
    # BUG: STATE_SKIP_PROCESSING - Skip PROCESSING state
    if current_status == "CONFIRMED" and new_status == "SHIPPED":
        order["status"] = new_status
        return {
            "orderId": order_id,
            "previousStatus": current_status,
            "newStatus": new_status,
            "flag": get_flag("STATE_SKIP_PROCESSING"),
            "_debug": "Skipped PROCESSING state"
        }
    
    # STATE_REVERSE_DELIVERED (Phase2: dropped, no flag)
    if current_status == "DELIVERED" and new_status in ["SHIPPED", "PROCESSING", "CONFIRMED"]:
        order["status"] = new_status
        return {
            "orderId": order_id,
            "previousStatus": current_status,
            "newStatus": new_status,
            "_debug": "Reversed from DELIVERED state"
        }
    
    # BUG: STATE_CANCEL_SHIPPED - Cancel shipped order
    if current_status == "SHIPPED" and new_status == "CANCELLED":
        order["status"] = new_status
        return {
            "orderId": order_id,
            "previousStatus": current_status,
            "newStatus": new_status,
            "flag": get_flag("STATE_CANCEL_SHIPPED"),
            "_debug": "Cancelled shipped order"
        }
    
    # STATE_DOUBLE_TRANSITION (Phase2: dropped, no flag)
    if current_status == new_status:
        order["status"] = new_status
        return {
            "orderId": order_id,
            "previousStatus": current_status,
            "newStatus": new_status,
            "_debug": "Double transition to same state"
        }
    
    # Valid transition
    if new_status in VALID_STATE_TRANSITIONS.get(current_status, []):
        order["status"] = new_status
        return {
            "orderId": order_id,
            "previousStatus": current_status,
            "newStatus": new_status
        }
    
    raise HTTPException(status_code=400, detail=f"Invalid transition from {current_status} to {new_status}")

@app.post("/orders/{order_id}/pay")
async def pay_order(
    order_id: str = Path(...),
    payment: OrderPayBody = Body(...)
):
    """Pay for order. Bug: STATE_CANCELLED_RESURRECT, STATE_EXPIRED_PAY"""
    order = db.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    current_status = order["status"]
    
    # STATE_CANCELLED_RESURRECT (Phase2: dropped, no flag)
    if current_status == "CANCELLED":
        order["status"] = "PAID"
        return {
            "orderId": order_id,
            "previousStatus": "CANCELLED",
            "newStatus": "PAID",
            "_debug": "Cancelled order was resurrected via payment"
        }
    
    # STATE_EXPIRED_PAY (Phase2: dropped, no flag)
    if current_status == "EXPIRED":
        order["status"] = "PAID"
        order["paidAt"] = datetime.now().isoformat()
        return {
            "orderId": order_id,
            "status": "PAID",
            "expiredAt": order.get("expiresAt"),
            "paidAt": order["paidAt"],
            "_debug": "Expired order accepted payment"
        }
    
    if current_status not in ["PENDING", "CREATED"]:
        raise HTTPException(status_code=400, detail=f"Cannot pay order in {current_status} status")
    
    order["status"] = "PAID"
    order["paidAt"] = datetime.now().isoformat()
    
    return {
        "orderId": order_id,
        "status": "PAID",
        "paidAt": order["paidAt"]
    }

@app.post("/orders/{order_id}/cancel")
async def cancel_order(order_id: str = Path(...), request: Request = None):
    """Cancel order. Bug: STOCK_CANCEL_NO_RESTORE, LOYALTY_CANCEL_KEEP_POINTS"""
    user_id = db.get_user_id(request) if request else "default"
    order = db.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["status"] in ["DELIVERED", "RETURNED"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel order in {order['status']} status")
    
    # BUG: STOCK_CANCEL_NO_RESTORE - Stock not restored after cancellation
    # Should restore stock for order items, but bug doesn't do it
    items = order.get("items", [])
    stock_before = {}
    for item in items:
        product_id = item.get("productId")
        if product_id:
            product = db.products.get(product_id)
            if product:
                stock_before[product_id] = product["stock"]
    
    order["status"] = "CANCELLED"
    
    # Check if bug triggered (stock not restored)
    response = {
        "orderId": order_id,
        "status": "CANCELLED"
    }
    
    if items:
        # Check stock after cancellation
        stock_after = {}
        for item in items:
            product_id = item.get("productId")
            if product_id:
                product = db.products.get(product_id)
                if product:
                    stock_after[product_id] = product["stock"]
        
        # If stock wasn't restored, bug triggered
        for product_id, before_stock in stock_before.items():
            after_stock = stock_after.get(product_id, before_stock)
            if before_stock == after_stock and order.get("status") == "CANCELLED":
                response["stockBefore"] = before_stock
                response["stockAfter"] = after_stock
                response["expectedStock"] = before_stock + sum(
                    item.get("quantity", 0) for item in items if item.get("productId") == product_id
                )
                response["flag"] = get_flag("STOCK_CANCEL_NO_RESTORE")
                response["_debug"] = "Stock not restored after order cancellation"
                return response
    
    # BUG: LOYALTY_CANCEL_KEEP_POINTS - Points not reverted after cancellation
    points_before = db.loyalty_points.get(user_id, 0)
    # In real scenario, points would be awarded at delivery, but bug awards at purchase
    # So when cancelling, points should be reverted, but bug doesn't do it
    points_after = db.loyalty_points.get(user_id, 0)
    
    if points_before > 0 and points_after == points_before:
        response["pointsBefore"] = points_before
        response["pointsAfter"] = points_after
        response["expectedPoints"] = max(0, points_before - order.get("total", 0))
        response["flag"] = get_flag("LOYALTY_CANCEL_KEEP_POINTS")
        response["_debug"] = "Points not reverted after order cancellation"
        return response
    
    return response

@app.post("/orders/{order_id}/ship")
async def ship_order(order_id: str = Path(...)):
    """Ship order"""
    order = db.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["status"] != "PROCESSING":
        raise HTTPException(status_code=400, detail=f"Order must be in PROCESSING status")
    
    order["status"] = "SHIPPED"
    order["shippedAt"] = datetime.now().isoformat()
    
    return {
        "orderId": order_id,
        "status": "SHIPPED",
        "shippedAt": order["shippedAt"]
    }

@app.post("/orders/{order_id}/deliver")
async def deliver_order(order_id: str = Path(...)):
    """Deliver order"""
    order = db.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["status"] != "SHIPPED":
        raise HTTPException(status_code=400, detail=f"Order must be in SHIPPED status")
    
    order["status"] = "DELIVERED"
    order["deliveredAt"] = datetime.now().isoformat()
    
    return {
        "orderId": order_id,
        "status": "DELIVERED",
        "deliveredAt": order["deliveredAt"]
    }

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 3: RETURN & REFUND FLOW
# ═══════════════════════════════════════════════════════════════════════════

RETURN_STATES = ["REQUESTED", "APPROVED", "RECEIVED", "INSPECTED", "REFUNDED", "REJECTED"]

@app.post("/returns")
async def create_return(return_req: ReturnCreate, request: Request = None):
    """Create return request. Bug: RETURN_FOOD_ACCEPTED, RETURN_EXCEED_TOTAL"""
    order_id = return_req.orderId
    if not order_id:
        raise HTTPException(status_code=400, detail="orderId required")
    
    order = db.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["status"] != "DELIVERED":
        raise HTTPException(status_code=400, detail="Order must be DELIVERED")
    
    # Check return window (14 days)
    delivered_at = datetime.fromisoformat(order.get("deliveredAt", datetime.now().isoformat()))
    if datetime.now() - delivered_at > timedelta(days=14):
        raise HTTPException(status_code=400, detail="Return window expired")
    
    return_id = f"RET-{db.return_id_counter}"
    db.return_id_counter += 1
    
    items = return_req.items
    if items == "ALL":
        items = order.get("items", [])
    elif isinstance(items, list) and len(items) == 0:
        items = order.get("items", [])
    
    # BUG: RETURN_FOOD_ACCEPTED - Accept food returns
    for item in items if isinstance(items, list) else []:
        product_id = item.get("productId") or item.get("itemId", "").split("-")[0]
        product = db.products.get(product_id)
        if product and product.get("category") == "FOOD":
            return {
                "returnId": return_id,
                "orderId": order_id,
                "items": items,
                "status": "REQUESTED",
                "_debug": "Food item return accepted"
            }
    
    # BUG: RETURN_EXCEED_TOTAL - Return more than order total
    return_total = 0
    for item in items if isinstance(items, list) else []:
        qty = item.get("quantity", 1)
        price = item.get("price", 100.0)
        return_total += qty * price
    
    if return_total > order.get("total", 0):
        return {
            "returnId": return_id,
            "orderId": order_id,
            "returnAmount": return_total,
            "orderTotal": order.get("total", 0),
            "_debug": "Return amount exceeds order total"
        }
    
    new_return = {
        "id": return_id,
        "orderId": order_id,
        "items": items,
        "status": "REQUESTED",
        "reason": return_req.reason or "DEFECTIVE",
        "createdAt": datetime.now().isoformat(),
        "refunded": False
    }
    db.returns[return_id] = new_return
    
    return {
        "returnId": return_id,
        "orderId": order_id,
        "status": "REQUESTED"
    }

@app.post("/returns/{return_id}/refund")
async def refund_return(return_id: str = Path(...)):
    """Process refund. Bug: RETURN_PARTIAL_THEN_FULL, RETURN_REFUND_BEFORE_RECEIVE, RETURN_DOUBLE_REFUND"""
    return_data = db.returns.get(return_id)
    if not return_data:
        raise HTTPException(status_code=404, detail="Return not found")
    
    order_id = return_data["orderId"]
    order = db.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # BUG: RETURN_REFUND_BEFORE_RECEIVE - Refund before RECEIVED status
    if return_data["status"] == "REQUESTED":
        return_data["status"] = "REFUNDED"
        return_data["refunded"] = True
        return {
            "returnId": return_id,
            "status": "REFUNDED",
            "itemReceived": False,
            "flag": get_flag("RETURN_REFUND_BEFORE_RECEIVE"),
            "_debug": "Refund issued before item received at warehouse"
        }
    
    # BUG: RETURN_DOUBLE_REFUND - Refund twice
    if return_data.get("refunded"):
        return {
            "returnId": return_id,
            "status": "REFUNDED",
            "refunded": True,
            "_debug": "Double refund detected"
        }
    
    # BUG: RETURN_PARTIAL_THEN_FULL - Full return after partial
    # Track total refunded for order
    total_refunded = sum(
        r.get("refundAmount", 0) for r in db.returns.values()
        if r["orderId"] == order_id and r.get("refunded")
    )
    
    return_amount = 0
    items = return_data.get("items", [])
    if isinstance(items, list):
        for item in items:
            qty = item.get("quantity", 1)
            price = item.get("price", 100.0)
            return_amount += qty * price
    elif items == "ALL":
        return_amount = order.get("total", 0)
    
    if total_refunded + return_amount > order.get("total", 0):
        return {
            "returnId": return_id,
            "refundAmount": return_amount,
            "totalRefundedForOrder": total_refunded + return_amount,
            "orderTotal": order.get("total", 0),
            "flag": get_flag("RETURN_PARTIAL_THEN_FULL"),
            "_debug": "Total refunds exceed order total"
        }
    
    return_data["status"] = "REFUNDED"
    return_data["refunded"] = True
    return_data["refundAmount"] = return_amount
    
    # BUG: STOCK_RETURN_DOUBLE_RESTORE - Stock restored twice on return
    # Track if stock was already restored for this return
    if not return_data.get("stockRestored"):
        # Restore stock
        items = return_data.get("items", [])
        for item in items if isinstance(items, list) else []:
            product_id = item.get("productId")
            if product_id:
                product = db.products.get(product_id)
                if product:
                    product["stock"] += item.get("quantity", 1)
        return_data["stockRestored"] = True
    else:
        # BUG: Restore again (double restore)
        items = return_data.get("items", [])
        for item in items if isinstance(items, list) else []:
            product_id = item.get("productId")
            if product_id:
                product = db.products.get(product_id)
                if product:
                    product["stock"] += item.get("quantity", 1)
                    return {
                        "returnId": return_id,
                        "status": "REFUNDED",
                        "refundAmount": return_amount,
                        "productId": product_id,
                        "stockRestored": True,
                        "flag": get_flag("STOCK_RETURN_DOUBLE_RESTORE"),
                        "_debug": "Stock restored twice on return"
                    }
    
    # BUG: LOYALTY_RETURN_KEEP_POINTS - Points not reverted after return
    # Points should be reverted when order is returned, but bug doesn't do it
    user_id = "default"  # In real scenario would get from order
    points_before = db.loyalty_points.get(user_id, 0)
    points_after = db.loyalty_points.get(user_id, 0)
    
    if points_before > 0 and points_after == points_before:
        return {
            "returnId": return_id,
            "status": "REFUNDED",
            "refundAmount": return_amount,
            "pointsBefore": points_before,
            "pointsAfter": points_after,
            "_debug": "Points not reverted after return"
        }
    
    return {
        "returnId": return_id,
        "status": "REFUNDED",
        "refundAmount": return_amount
    }

@app.put("/returns/{return_id}/status")
async def update_return_status(
    return_id: str = Path(...),
    status_update: OrderStatusUpdate = Body(...)
):
    """Update return status. Bug: RETURN_REOPEN_REJECTED"""
    return_data = db.returns.get(return_id)
    if not return_data:
        raise HTTPException(status_code=404, detail="Return not found")
    
    new_status = status_update.status
    current_status = return_data["status"]
    
    # BUG: RETURN_REOPEN_REJECTED - Reopen rejected return
    if current_status == "REJECTED" and new_status == "APPROVED":
        return_data["status"] = new_status
        return {
            "returnId": return_id,
            "previousStatus": "REJECTED",
            "newStatus": "APPROVED",
            "_debug": "Rejected return was reopened"
        }
    
    if new_status in RETURN_STATES:
        return_data["status"] = new_status
        return {
            "returnId": return_id,
            "status": new_status
        }
    
    raise HTTPException(status_code=400, detail=f"Invalid status: {new_status}")

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 4: INVENTORY & STOCK LOGIC
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/products/{product_id}/stock")
async def get_product_stock(product_id: str = Path(...)):
    """Get product stock. Bug: STOCK_PHANTOM_AVAILABLE"""
    product = db.products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    reserved = sum(
        r.get(product_id, 0) for r in db.stock_reservations.values()
    )
    available = product["stock"] - reserved
    
    # BUG: STOCK_PHANTOM_AVAILABLE - Show available stock that is actually reserved
    # Don't check if reservations expired
    response = {
        "productId": product_id,
        "total": product["stock"],
        "reserved": reserved,
        "available": available
    }
    
    # Check if bug triggered (available shown but actually all reserved and expired)
    if reserved > 0 and available > 0:
        # Check if reservations expired
        expired_reservations = 0
        for user_id, reservations in db.stock_reservations.items():
            if product_id in reservations:
                # Check expiry (simplified - in real scenario would check reservation_expiry)
                expired_reservations += reservations[product_id]
        
        if expired_reservations > 0:
            response["_debug"] = "Shows available stock that is actually reserved"
            return response
    
    return response

@app.post("/products/{product_id}/reserve")
async def reserve_stock(
    product_id: str = Path(...),
    quantity: int = Query(...),
    request: Request = None
):
    """Reserve stock. Bug: STOCK_RESERVE_EXPIRE_CHECKOUT, STOCK_RESERVE_EXCEED"""
    user_id = db.get_user_id(request) if request else "default"
    product = db.products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # BUG: STOCK_RESERVE_EXCEED - Reserve more than available
    reserved = sum(
        r.get(product_id, 0) for r in db.stock_reservations.values()
    )
    available = product["stock"] - reserved
    
    if quantity > available:
        reservation_id = f"RES-{secrets.token_hex(8)}"
        if user_id not in db.stock_reservations:
            db.stock_reservations[user_id] = {}
        db.stock_reservations[user_id][product_id] = quantity
        db.reservation_expiry[reservation_id] = datetime.now() + timedelta(minutes=15)
        
        return {
            "reservationId": reservation_id,
            "productId": product_id,
            "quantity": quantity,
            "available": available,
            "_debug": "Reserved more than available stock"
        }
    
    reservation_id = f"RES-{secrets.token_hex(8)}"
    if user_id not in db.stock_reservations:
        db.stock_reservations[user_id] = {}
    db.stock_reservations[user_id][product_id] = quantity
    db.reservation_expiry[reservation_id] = datetime.now() + timedelta(minutes=15)
    
    return {
        "reservationId": reservation_id,
        "productId": product_id,
        "quantity": quantity,
        "expiresAt": db.reservation_expiry[reservation_id].isoformat()
    }

# Stock adjustment endpoint for STOCK_NEGATIVE_ADJUST bug
@app.put("/products/{product_id}/stock")
async def adjust_product_stock(
    product_id: str = Path(...),
    adjustment: int = Body(...)
):
    """Adjust product stock. Bug: STOCK_NEGATIVE_ADJUST"""
    product = db.products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # BUG: STOCK_NEGATIVE_ADJUST - Stock adjustment allows negative values
    new_stock = product["stock"] + adjustment
    
    if new_stock < 0:
        product["stock"] = new_stock
        return {
            "productId": product_id,
            "stock": new_stock,
            "_debug": "Stock adjustment resulted in negative value"
        }
    
    product["stock"] = new_stock
    return {
        "productId": product_id,
        "stock": new_stock
    }

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 5: DISCOUNT & PRICING LOGIC
# ═══════════════════════════════════════════════════════════════════════════

# Discount bugs mostly handled in cart endpoints
# DISCOUNT_REMOVE_KEEP_PERCENT - handled in checkout
# DISCOUNT_VOLUME_THRESHOLD_ABUSE - handled in checkout
# DISCOUNT_FLASH_SALE_PERSIST - handled in checkout
# DISCOUNT_STACK_FORBIDDEN - handled in cart_apply_promo
# DISCOUNT_EXCEED_50_CAP - handled in cart_apply_promo
# DISCOUNT_EXPIRED_PROMO - handled in cart_apply_promo
# DISCOUNT_NEGATIVE_TOTAL - handled in cart_apply_promo (CART_NEGATIVE_TOTAL)

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 6: LOYALTY PROGRAM ABUSE
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/loyalty/balance")
async def get_loyalty_balance(request: Request = None):
    """Get loyalty points balance"""
    user_id = db.get_user_id(request) if request else "default"
    points = db.loyalty_points.get(user_id, 0)
    return {"points": points}

@app.post("/loyalty/redeem")
async def redeem_loyalty_points(
    redeem: LoyaltyRedeemBody,
    request: Request = None
):
    """Redeem loyalty points. Bug: LOYALTY_DOUBLE_REDEEM, LOYALTY_EXCEED_50_PERCENT, LOYALTY_NEGATIVE_BALANCE"""
    user_id = db.get_user_id(request) if request else "default"
    points = redeem.points or 0
    
    current_balance = db.loyalty_points.get(user_id, 0)
    
    # BUG: LOYALTY_NEGATIVE_BALANCE - Allow negative balance
    if points > current_balance:
        db.loyalty_points[user_id] = current_balance - points
        return {
            "points": db.loyalty_points[user_id],
            "_debug": "Loyalty balance went negative"
        }
    
    # Track redemptions for double redeem bug
    redemption_key = f"{user_id}_redeem_{points}"
    
    # BUG: LOYALTY_DOUBLE_REDEEM - Redeem twice
    if redemption_key in db.redemptions:
        return {
            "points": current_balance,
            "redeemed": points,
            "flag": get_flag("LOYALTY_DOUBLE_REDEEM"),
            "_debug": "Double redemption detected"
        }
    
    db.redemptions.add(redemption_key)
    
    # BUG: LOYALTY_EXCEED_50_PERCENT - Points discount exceeds 50% of order total
    cart = db.get_cart(user_id)
    cart_total = db.calculate_cart_total(user_id)
    points_discount = points / 100.0  # 100 points = $1
    
    if cart_total > 0 and points_discount > cart_total * 0.5:
        db.loyalty_points[user_id] = current_balance - points
        return {
            "points": db.loyalty_points[user_id],
            "redeemed": points,
            "discount": points_discount,
            "cartTotal": cart_total,
            "_debug": "Points discount exceeds 50% of order total"
        }
    
    db.loyalty_points[user_id] = current_balance - points
    
    return {
        "points": db.loyalty_points[user_id],
        "redeemed": points
    }

# LOYALTY_CANCEL_KEEP_POINTS - handled in cancel_order
# LOYALTY_RETURN_KEEP_POINTS - handled in refund_return
# LOYALTY_EARN_SPEND_SAME - handled in checkout

# ═══════════════════════════════════════════════════════════════════════════
# MISSION 7: PAYMENT & CHECKOUT FLOW
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/payments/initiate")
async def initiate_payment(
    payment: PaymentInitiateBody,
    request: Request = None
):
    """Initiate payment. Bug: PAYMENT_IDEMPOTENCY_FAIL, PAYMENT_COD_LIMIT, PAYMENT_NEGATIVE_AMOUNT"""
    user_id = db.get_user_id(request) if request else "default"
    cart = db.get_cart(user_id)
    
    amount = payment.amount or db.calculate_cart_total(user_id)
    
    # BUG: PAYMENT_NEGATIVE_AMOUNT - Payment with negative amount accepted
    if amount < 0:
        payment_id = f"PAY-{db.payment_id_counter}"
        db.payment_id_counter += 1
        db.payment_sessions[payment_id] = {
            "id": payment_id,
            "amount": amount,
            "cartSnapshot": {"items": cart["items"].copy(), "total": amount},
            "status": "PENDING",
            "createdAt": datetime.now().isoformat()
        }
        return {
            "paymentId": payment_id,
            "amount": amount,
            "status": "PENDING",
            "_debug": "Payment with negative amount accepted"
        }
    
    # BUG: PAYMENT_COD_LIMIT - Cash on Delivery exceeds limit (assume limit is $500)
    method = request.headers.get("X-Payment-Method", "card") if request else "card"
    if method == "COD" and amount > 500:
        payment_id = f"PAY-{db.payment_id_counter}"
        db.payment_id_counter += 1
        db.payment_sessions[payment_id] = {
            "id": payment_id,
            "amount": amount,
            "cartSnapshot": {"items": cart["items"].copy(), "total": amount},
            "status": "PENDING",
            "method": "COD",
            "createdAt": datetime.now().isoformat()
        }
        return {
            "paymentId": payment_id,
            "amount": amount,
            "status": "PENDING",
            "method": "COD",
            "_debug": "Cash on Delivery exceeds limit"
        }
    
    # BUG: PAYMENT_IDEMPOTENCY_FAIL - Same idempotency key creates multiple payments
    idempotency_key = request.headers.get("X-Idempotency-Key") if request else None
    if idempotency_key:
        if idempotency_key in db.idempotency_keys:
            # Should return existing payment, but bug creates new one
            payment_id = f"PAY-{db.payment_id_counter}"
            db.payment_id_counter += 1
            db.payment_sessions[payment_id] = {
                "id": payment_id,
                "amount": amount,
                "cartSnapshot": {"items": cart["items"].copy(), "total": amount},
                "status": "PENDING",
                "createdAt": datetime.now().isoformat()
            }
            return {
                "paymentId": payment_id,
                "amount": amount,
                "status": "PENDING",
                "_debug": "Same idempotency key created multiple payments"
            }
        
        db.idempotency_keys[idempotency_key] = True
    
    payment_id = f"PAY-{db.payment_id_counter}"
    db.payment_id_counter += 1
    
    # Snapshot cart for payment
    cart_snapshot = {
        "items": cart["items"].copy(),
        "total": amount
    }
    
    db.payment_sessions[payment_id] = {
        "id": payment_id,
        "amount": amount,
        "cartSnapshot": cart_snapshot,
        "status": "PENDING",
        "createdAt": datetime.now().isoformat()
    }
    
    return {
        "paymentId": payment_id,
        "amount": amount,
        "status": "PENDING"
    }

@app.post("/payments/{payment_id}/confirm")
async def confirm_payment(
    payment_id: str = Path(...),
    confirm: PaymentConfirmBody = Body(...),
    request: Request = None
):
    """Confirm payment. Bug: PAYMENT_CART_MODIFIED_AFTER_INIT, PAYMENT_DOUBLE_CHARGE, PAYMENT_IDEMPOTENCY_FAIL, PAYMENT_PARTIAL_EXCEED, PAYMENT_CANCEL_AFTER_CONFIRM, PAYMENT_COD_LIMIT, PAYMENT_NEGATIVE_AMOUNT"""
    user_id = db.get_user_id(request) if request else "default"
    payment_session = db.payment_sessions.get(payment_id)
    if not payment_session:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # BUG: PAYMENT_CANCEL_AFTER_CONFIRM - Cancel payment after confirmation
    if payment_session["status"] == "CONFIRMED":
        return {
            "paymentId": payment_id,
            "status": "CANCELLED",
            "_debug": "Payment cancelled after confirmation"
        }
    
    if payment_session["status"] != "PENDING":
        raise HTTPException(status_code=400, detail="Payment already processed")
    
    cart = db.get_cart(user_id)
    current_cart_total = db.calculate_cart_total(user_id)
    snapshot_total = payment_session["cartSnapshot"]["total"]
    
    # BUG: PAYMENT_CART_MODIFIED_AFTER_INIT - Cart changed but payment uses old amount
    if current_cart_total != snapshot_total:
        payment_session["status"] = "CONFIRMED"
        return {
            "paymentId": payment_id,
            "amountPaid": snapshot_total,
            "cartTotal": current_cart_total,
            "flag": get_flag("PAYMENT_CART_MODIFIED_AFTER_INIT"),
            "_debug": "Payment confirmed with stale amount after cart modification"
        }
    
    # BUG: PAYMENT_DOUBLE_CHARGE - Charge same payment twice
    if payment_session.get("confirmed"):
        payment_session["status"] = "CONFIRMED"
        return {
            "paymentId": payment_id,
            "status": "CONFIRMED",
            "amount": payment_session["amount"],
            "flag": get_flag("PAYMENT_DOUBLE_CHARGE"),
            "_debug": "Payment charged twice"
        }
    
    # BUG: PAYMENT_PARTIAL_EXCEED - Partial payment exceeds order total
    if payment_session["amount"] > current_cart_total:
        payment_session["status"] = "CONFIRMED"
        return {
            "paymentId": payment_id,
            "amountPaid": payment_session["amount"],
            "cartTotal": current_cart_total,
            "_debug": "Partial payment exceeds order total"
        }
    
    payment_session["status"] = "CONFIRMED"
    payment_session["confirmed"] = True
    
    return {
        "paymentId": payment_id,
        "status": "CONFIRMED",
        "amount": payment_session["amount"]
    }

# ═══════════════════════════════════════════════════════════════════════════
# TEST ENDPOINTS FOR MULTI-STEP SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/test/time/advance")
async def test_time_advance(advance: TestTimeAdvanceBody):
    """Advance time for testing expiration scenarios"""
    minutes = advance.minutes or 30
    db.test_time_offset += timedelta(minutes=minutes)
    return {
        "offsetMinutes": minutes,
        "currentTime": (datetime.now() + db.test_time_offset).isoformat()
    }

@app.post("/test/products/{product_id}/price")
async def test_product_price(
    product_id: str = Path(...),
    price_update: TestProductPriceBody = Body(...)
):
    """Change product price for testing price freeze scenarios"""
    product = db.products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    new_price = price_update.newPrice
    if new_price is None:
        raise HTTPException(status_code=400, detail="newPrice required")
    
    db.test_product_prices[product_id] = new_price
    
    return {
        "productId": product_id,
        "oldPrice": product["price"],
        "newPrice": new_price
    }

@app.post("/test/reset")
async def test_reset(request: Request = None):
    """Reset user state for testing"""
    user_id = db.get_user_id(request) if request else "default"
    
    # Clear caches
    if user_id in db.cart_totals_cache:
        del db.cart_totals_cache[user_id]
    if user_id in db.cart_promo_cache:
        del db.cart_promo_cache[user_id]
    if user_id in db.cart_price_cache:
        del db.cart_price_cache[user_id]
    if user_id in db.stock_reservations:
        del db.stock_reservations[user_id]
    
    # Reset cart
    db.carts[user_id] = {
        "id": user_id,
        "items": [],
        "subtotal": 0.0,
        "discount": 0.0,
        "total": 0.0,
        "promo": None
    }
    
    return {"status": "reset", "userId": user_id}

@app.get("/test/state")
async def test_state(request: Request = None):
    """Get internal state for debugging"""
    user_id = db.get_user_id(request) if request else "default"
    
    return {
        "cartTotalsCache": db.cart_totals_cache.get(user_id),
        "cartPromoCache": db.cart_promo_cache.get(user_id),
        "cartPriceCache": db.cart_price_cache.get(user_id, {}),
        "stockReservations": db.stock_reservations.get(user_id, {}),
        "loyaltyPoints": db.loyalty_points.get(user_id, 0),
        "testTimeOffset": str(db.test_time_offset),
        "testProductPrices": db.test_product_prices
    }

@app.put("/test/orders/{order_id}/expire")
async def test_order_expire(order_id: str = Path(...)):
    """Expire order for testing"""
    order = db.orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order["status"] = "EXPIRED"
    order["expiresAt"] = datetime.now().isoformat()
    
    return {
        "orderId": order_id,
        "status": "EXPIRED"
    }

# ═══════════════════════════════════════════════════════════════════════════
# RUN SERVER
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG_MODE
    )
