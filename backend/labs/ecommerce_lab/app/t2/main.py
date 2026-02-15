"""
E-Commerce T2 Lab: Boundary Values & Data Formats (Phase2: 20 active flags)
8 missions, 20 active bugs. One FastAPI app, one base_url.
"""
import os
import re
import random
from pathlib import Path
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Path, Body, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from app.t2.flags_registry import get_flag, FLAGS

# ═══════════════════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════════════════
class Settings:
    PORT: int = int(os.getenv("PORT", "8080"))
    MISSION_ID: str = os.getenv("MISSION_ID", "ecom-t2-lab")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "true").lower() == "true"

settings = Settings()

# ═══════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════
class ProductUpdate(BaseModel):
    price: Optional[Union[int, float, str]] = None
    name: Optional[str] = None

class CartItemAdd(BaseModel):
    productId: Optional[int] = None
    quantity: Optional[Union[int, float]] = 1
    price: Optional[Union[int, float]] = None
    currency: Optional[str] = "KZT"

class CartItemUpdate(BaseModel):
    quantity: Optional[Union[int, float]] = None

class OrderCreate(BaseModel):
    cartId: Optional[str] = None
    deliveryDate: Optional[str] = None

class ReturnCreate(BaseModel):
    orderId: Optional[str] = None
    returnDate: Optional[str] = None

class PromoUpdate(BaseModel):
    endDate: Optional[str] = None
    startDate: Optional[str] = None

class ProductCreate(BaseModel):
    name: Optional[str] = None
    price: Optional[Union[int, float]] = None
    category: Optional[str] = None

class ProfileUpdate(BaseModel):
    name: Optional[str] = None

class ApplyPromoBody(BaseModel):
    code: Optional[str] = None

class OrdersCalculateBody(BaseModel):
    loyaltyPoints: Optional[int] = None

# ═══════════════════════════════════════════════════════════════════════════
# IN-MEMORY DATABASE
# ═══════════════════════════════════════════════════════════════════════════
INT32_MAX = 2**31 - 1
CART_LIMIT = 100
MAX_PAGE_SIZE = 100  # intended cap (bug: LIMIT_EXCESSIVE ignores it)
ALLOWED_SORT_FIELDS = ["id", "name", "price", "created_at"]
INTERNAL_SORT_FIELDS = ["internalCost"]  # bug: SORT_INTERNAL_FIELD

class Database:
    def __init__(self):
        self.products: Dict[int, dict] = {}
        self.carts: Dict[str, dict] = {}
        self.orders: List[dict] = []
        self.returns: List[dict] = []
        self.promos: Dict[str, dict] = {}
        self.cart_item_id = 0
        self._seed()

    def _seed(self):
        # Products 1-1000; some with edge prices/stock
        for i in range(1, 1001):
            price = 1000 + i * 10
            if i == 990:
                price = 0
            elif i == 991:
                price = 1  # penny
            elif i == 992:
                price = 99
            elif i == 993:
                price = 99999999
            elif i == 994:
                price = INT32_MAX
            stock = 100
            if i == 980:
                stock = 0
            elif i == 981:
                stock = 1
            elif i == 982:
                stock = 5
            self.products[i] = {
                "id": i,
                "name": f"Product {i}",
                "price": price,
                "internalCost": 50 + i,  # internal field for SORT_INTERNAL_FIELD bug
                "category": "ELECTRONICS" if i % 3 == 0 else "FASHION",
                "stock": stock,
                "created_at": "2025-01-01T00:00:00Z",
            }
        # Promos: EXPIRED2024, ACTIVE10, etc.
        self.promos = {
            "EXPIRED2024": {"discount": 20, "valid_until": "2024-12-31", "valid": False},
            "ACTIVE10": {"discount": 10, "valid_until": "2026-12-31", "valid": True},
            "VIP50": {"discount": 50, "valid_until": "2026-12-31", "valid": True},
            "STACK1": {"discount": 60, "valid_until": "2026-12-31", "valid": True},
            "STACK2": {"discount": 50, "valid_until": "2026-12-31", "valid": True},
        }
        # Default cart for session
        self.carts["default"] = {"id": "default", "items": [], "total_discount_percent": 0, "subtotal": 0}

    def get_products_list(self) -> List[dict]:
        return list(self.products.values())

    def get_product(self, pid: int) -> Optional[dict]:
        return self.products.get(pid)

    def update_product_price(self, pid: int, price: Union[int, float, str]) -> dict:
        p = self.products.get(pid)
        if not p:
            return None
        if isinstance(price, str):
            # PRICE_DECIMAL_SEPARATOR: "99,99" -> 99 (drop fraction)
            if "," in price:
                price = int(price.split(",")[0].strip() or 0)
            else:
                try:
                    price = float(price)
                except ValueError:
                    price = 0
        # Simulate INT overflow
        if isinstance(price, (int, float)) and price > INT32_MAX:
            price = -2147483648  # wraparound
        p["price"] = int(price) if isinstance(price, float) and price == int(price) else price
        return p

    def get_cart(self, cid: str = "default") -> dict:
        if cid not in self.carts:
            self.carts[cid] = {"id": cid, "items": [], "total_discount_percent": 0, "subtotal": 0}
        return self.carts[cid]

    def cart_total_items(self, cid: str = "default") -> int:
        cart = self.get_cart(cid)
        return sum(item.get("quantity", 0) for item in cart["items"])

    def add_cart_item(self, product_id: int, quantity: Union[int, float], price: Optional[float] = None, currency: str = "KZT", cid: str = "default") -> dict:
        self.cart_item_id += 1
        item = {
            "id": self.cart_item_id,
            "productId": product_id,
            "quantity": quantity,
            "price": price,
            "currency": currency,
        }
        cart = self.get_cart(cid)
        cart["items"].append(item)
        return item

    def update_cart_item(self, item_id: int, quantity: Union[int, float], cid: str = "default") -> Optional[dict]:
        cart = self.get_cart(cid)
        for item in cart["items"]:
            if item["id"] == item_id:
                item["quantity"] = quantity
                return item
        return None

    def get_cart_item(self, item_id: int, cid: str = "default") -> Optional[dict]:
        cart = self.get_cart(cid)
        for item in cart["items"]:
            if item["id"] == item_id:
                return item
        return None

    def add_order(self, delivery_date: Optional[str] = None, order_id: Optional[str] = None) -> dict:
        oid = order_id or f"ORD-{len(self.orders)+1}"
        order = {"id": oid, "deliveryDate": delivery_date, "createdAt": datetime.now().isoformat()}
        self.orders.append(order)
        return order

    def add_return(self, order_id: str, return_date: str) -> dict:
        r = {"id": f"RET-{len(self.returns)+1}", "orderId": order_id, "returnDate": return_date}
        self.returns.append(r)
        return r

    def set_promo(self, product_id: int, end_date: str) -> dict:
        p = self.products.get(product_id)
        if not p:
            return None
        p["promoEndDate"] = end_date
        return p

    def create_product(self, name: str, price: float, category: str = "OTHER") -> dict:
        pid = max(self.products.keys(), default=0) + 1
        self.products[pid] = {
            "id": pid, "name": name, "price": price, "internalCost": 0,
            "category": category, "stock": 100, "created_at": datetime.now().isoformat(),
        }
        return self.products[pid]

    def update_product_full(self, pid: int, name: Optional[str] = None, price: Optional[float] = None) -> Optional[dict]:
        p = self.products.get(pid)
        if not p:
            return None
        if name is not None:
            p["name"] = name
        if price is not None:
            p["price"] = price
        return p

db = Database()

# ═══════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("E-Commerce T2 Lab starting (Phase2: 20 active flags)")
    yield
    print("E-Commerce T2 Lab shutdown")

app = FastAPI(title="E-Commerce T2 Lab", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ═══════════════════════════════════════════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════════════════════════════════════════
@app.get("/health")
async def health():
    return {"status": "healthy", "mission": settings.MISSION_ID, "bugs": 20}

# ═══════════════════════════════════════════════════════════════════════════
# 3.1 PRICE BOUNDARY
# ═══════════════════════════════════════════════════════════════════════════
@app.get("/products")
async def list_products(
    minPrice: Optional[float] = Query(None),
    maxPrice: Optional[float] = Query(None),
    page: int = Query(1),
    limit: int = Query(20, ge=1),
    sort: str = Query("id"),
    order: str = Query("asc"),
    category: Optional[int] = Query(None),
    inStock: Optional[str] = Query(None),
):
    # PRICE_ZERO_FILTER: minPrice=0&maxPrice=0 -> 200 with empty list (bug = zero filter accepted, flag only on success)
    if minPrice is not None and maxPrice is not None and minPrice == 0 and maxPrice == 0:
        return {"data": {"items": [], "total": 0, "page": page, "limit": limit}, "flag": get_flag("PRICE_ZERO_FILTER"), "_debug": "Zero price filter accepted"}
    # PRICE_NEGATIVE_FILTER (Phase2: dropped, no flag)
    applied_negative = False
    if minPrice is not None and minPrice < 0:
        applied_negative = True
        minPrice = None  # bug: ignore negative, apply no filter
    items = db.get_products_list()
    if minPrice is not None:
        items = [p for p in items if p.get("price", 0) >= minPrice]
    if maxPrice is not None:
        items = [p for p in items if p.get("price", 0) <= maxPrice]
    filter_bugs = []
    if category is not None and category >= 999999:
        filter_bugs.append(("FILTER_NONEXISTENT_CATEGORY", get_flag("FILTER_NONEXISTENT_CATEGORY")))
    if inStock is not None and inStock.lower() not in ("true", "false", "1", "0"):
        filter_bugs.append(("FILTER_BOOLEAN_STRING", get_flag("FILTER_BOOLEAN_STRING")))
    if category is not None and category < 999999:
        items = [p for p in items if p.get("category") == str(category) or p.get("id") % max(1, min(category, 100)) == 0]
    # PAGE_NEGATIVE: page=-1 -> 500 (handled below in pagination)
    # PAGE_ZERO: page=0 -> empty array (off-by-one)
    # LIMIT_EXCESSIVE: limit=10000 -> return 10000 (no cap)
    # SORT_INJECTION: sort=price;DROP TABLE-- -> 500 without flag (Error != Flag per credo)
    if "; DROP" in sort.upper() or ";DROP" in sort.upper() or "--" in sort:
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "Invalid sort parameter"}})
    # SORT_INTERNAL_FIELD: sort=internalCost -> 200, sort by internal field
    if sort in INTERNAL_SORT_FIELDS:
        items = sorted(items, key=lambda p: p.get("internalCost", 0), reverse=(order.lower() == "desc"))
    elif sort in ALLOWED_SORT_FIELDS:
        items = sorted(items, key=lambda p: p.get(sort, 0), reverse=(order.lower() == "desc"))
    else:
        items = sorted(items, key=lambda p: p.get("id", 0), reverse=(order.lower() == "desc"))
    # PAGE_NEGATIVE / OFFSET_OVERFLOW: per credo flag only on "exploitation" (200 with wrong data), not in 500
    total = len(items)
    if page == -1:
        # PAGE_NEGATIVE (Phase2: dropped, no flag)
        offset = 0
        result_items = items[0:limit]
        return {"data": {"items": result_items, "total": total, "page": page, "limit": limit}, "_debug": "Negative page accepted"}
    if page > 10000000:
        # OFFSET_OVERFLOW (Phase2: dropped, no flag)
        result_items = []
        return {"data": {"items": result_items, "total": total, "page": page, "limit": limit}, "_debug": "Offset overflow accepted"}
    # page=0 -> off-by-one: use offset 0 but effectively show nothing if we treat page 0 as invalid
    offset = (page - 1) * limit if page >= 1 else 0
    if page == 0:
        result_items = []
        payload = {"items": result_items, "total": total, "page": page, "limit": limit}
        out = {"data": payload}
        out["flag"] = get_flag("PAGE_ZERO")
        out["_debug"] = "Page zero off-by-one"
        if applied_negative:
            out["_debug"] = "Negative filter ignored"
        elif filter_bugs:
            out["flag"] = filter_bugs[0][1]
            out["_debug"] = "Filter bypassed"
        return out
    result_items = items[offset : offset + limit]
    payload = {"items": result_items, "total": total, "page": page, "limit": limit}
    out = {"data": payload}
    if applied_negative:
        out["_debug"] = "Negative filter ignored"
    elif filter_bugs:
        out["flag"] = filter_bugs[0][1]
        out["_debug"] = "Filter bypassed"
    elif limit > MAX_PAGE_SIZE:
        out["flag"] = get_flag("LIMIT_EXCESSIVE")
        out["_debug"] = "Excessive limit accepted"
    return out

@app.put("/products/{product_id}")
async def update_product(product_id: int, data: ProductUpdate):
    p = db.get_product(product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    # STRING_EMPTY_REQUIRED: name="" -> 200 with flag
    if data.name is not None and data.name == "":
        db.update_product_full(product_id, name="")
        p = db.get_product(product_id)
        return {**p, "flag": get_flag("STRING_EMPTY_REQUIRED"), "_debug": "Empty name accepted"}
    if data.name is not None:
        db.update_product_full(product_id, name=data.name)
    if data.price is None:
        return db.get_product(product_id)
    # PRICE_DECIMAL_SEPARATOR: price="99,99" -> 200, price=99 (fraction dropped)
    new_price = data.price
    if isinstance(new_price, str) and "," in new_price:
        try:
            new_price = int(new_price.split(",")[0].strip())
        except ValueError:
            new_price = 99
        updated = db.update_product_price(product_id, new_price)
        return {**updated, "flag": get_flag("PRICE_DECIMAL_SEPARATOR"), "_debug": "Decimal separator dropped fraction"}
    # PRICE_MAX_INT_OVERFLOW (Phase2: dropped, no flag)
    if isinstance(new_price, (int, float)) and new_price > INT32_MAX:
        updated = db.update_product_price(product_id, 9999999999999)
        if updated and updated.get("price") == -2147483648:
            return {**updated, "_debug": "Integer overflow"}
    updated = db.update_product_price(product_id, new_price)
    return updated

@app.post("/products")
async def create_product_admin(data: ProductCreate):
    name = (data.name or "Product").strip()
    price = float(data.price or 0)
    # STRING_OVERLENGTH_NAME: name = "A"*10000 -> 201 with flag
    if len(name) > 255:
        prod = db.create_product(name[:255], price, data.category or "OTHER")
        return JSONResponse(status_code=201, content={**prod, "flag": get_flag("STRING_OVERLENGTH_NAME"), "_debug": "Name truncated"})
    # STRING_UNICODE_ESCAPE (Phase2: dropped, no flag)
    if "\u0000" in name or "\x00" in name:
        prod = db.create_product(name, price, data.category or "OTHER")
        return JSONResponse(status_code=201, content={**prod, "_debug": "Null byte in name"})
    # STRING_SQL_IN_NAME (Phase2: injection dropped from T2, no flag)
    if "');" in name or "DROP TABLE" in name.upper() or "--" in name:
        prod = db.create_product(name, price, data.category or "OTHER")
        return JSONResponse(status_code=201, content={**prod, "_debug": "SQL-like name accepted"})
    prod = db.create_product(name, price, data.category or "OTHER")
    return JSONResponse(status_code=201, content=prod)

# ═══════════════════════════════════════════════════════════════════════════
# 3.2 QUANTITY LIMITS & 3.6 CART
# ═══════════════════════════════════════════════════════════════════════════
@app.post("/cart/items")
async def add_cart_item(data: CartItemAdd, request: Request, cartId: str = Query("default")):
    product_id = data.productId or 1
    quantity = data.quantity
    price = data.price
    currency = data.currency or "KZT"
    # Validate: negative quantity should be rejected
    if quantity is not None and quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")
    # QTY_ZERO_ADD (Phase2: dropped, no flag)
    if quantity == 0:
        item = db.add_cart_item(product_id, 0, price, currency, cartId)
        return JSONResponse(status_code=201, content={**item, "_debug": "Zero quantity accepted"})
    # QTY_FLOAT_ACCEPTED: quantity=2.7 -> 201 with flag
    if isinstance(quantity, float) and quantity != int(quantity):
        item = db.add_cart_item(product_id, quantity, price, currency, cartId)
        return JSONResponse(status_code=201, content={**item, "flag": get_flag("QTY_FLOAT_ACCEPTED"), "_debug": "Float quantity accepted"})
    qty_int = int(quantity) if quantity else 0
    # QTY_EXCEED_STOCK (Phase2: dropped, no flag)
    prod = db.get_product(product_id)
    if prod and prod.get("stock", 0) < qty_int and qty_int > 0:
        item = db.add_cart_item(product_id, qty_int, price, currency, cartId)
        return JSONResponse(status_code=201, content={**item, "_debug": "Exceeded stock"})
    # QTY_MAX_CART_BYPASS: total cart > 100 but we still add
    current_total = db.cart_total_items(cartId)
    if current_total + qty_int > CART_LIMIT:
        item = db.add_cart_item(product_id, qty_int, price, currency, cartId)
        return JSONResponse(status_code=201, content={**item, "flag": get_flag("QTY_MAX_CART_BYPASS"), "_debug": "Cart limit bypassed"})
    # PRICE_FLOAT_PRECISION: price=99.999 -> store as-is, flag in response
    if price is not None and isinstance(price, float) and round(price, 2) != price:
        item = db.add_cart_item(product_id, qty_int, price, currency, cartId)
        return JSONResponse(status_code=201, content={**item, "flag": get_flag("PRICE_FLOAT_PRECISION"), "_debug": "Float precision not rounded"})
    # PRICE_CURRENCY_MISMATCH (Phase2: dropped, no flag)
    cart = db.get_cart(cartId)
    has_other_currency = any(it.get("currency") and it.get("currency") != currency for it in cart["items"])
    item = db.add_cart_item(product_id, qty_int, price, currency, cartId)
    if has_other_currency or (cart["items"] and cart["items"][0].get("currency") != currency):
        return JSONResponse(status_code=201, content={**item, "_debug": "Currency mismatch"})
    # DISCOUNT_NEGATIVE_PRICE (Phase2: dropped, no flag)
    if price is not None and price < 0:
        return JSONResponse(status_code=201, content={**item, "_debug": "Negative price accepted"})
    return JSONResponse(status_code=201, content=item)

@app.put("/cart/items/{item_id}")
async def update_cart_item(item_id: int, data: CartItemUpdate, cartId: str = Query("default")):
    qty = data.quantity
    # QTY_UPDATE_NEGATIVE: quantity=-5 -> 200 with flag
    if qty is not None and qty < 0:
        db.update_cart_item(item_id, qty, cartId)
        cart = db.get_cart(cartId)
        total = sum(it.get("quantity", 0) * it.get("price", 0) for it in cart["items"])
        return {"id": item_id, "quantity": qty, "total": total, "flag": get_flag("QTY_UPDATE_NEGATIVE"), "_debug": "Negative quantity accepted"}
    if qty is not None:
        db.update_cart_item(item_id, qty, cartId)
    item = db.get_cart_item(item_id, cartId)
    if not item:
        raise HTTPException(404, "Cart item not found")
    return item

@app.get("/products/{product_id}/stock")
async def get_stock(product_id: int):
    p = db.get_product(product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    return {"productId": product_id, "stock": p.get("stock", 0)}

# ═══════════════════════════════════════════════════════════════════════════
# 3.4 DATE VALIDATION
# ═══════════════════════════════════════════════════════════════════════════
def _parse_date(s: str):
    if not s:
        return None
    try:
        if "T" in s:
            return datetime.fromisoformat(s.replace("Z", "+00:00"))
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except Exception:
        try:
            return datetime.strptime(s[:10], "%d-%m-%Y")
        except Exception:
            return None

@app.post("/orders")
async def create_order(data: OrderCreate):
    delivery_date = data.deliveryDate
    # DATE_FUTURE_ORDER (Phase2: dropped, no flag)
    if delivery_date:
        d = _parse_date(delivery_date)
        if d and d.date() > date(2026, 12, 31):
            order = db.add_order(delivery_date=delivery_date)
            return JSONResponse(status_code=201, content={**order, "_debug": "Future date accepted"})
        # DATE_LEAP_YEAR (Phase2: dropped, no flag)
        if delivery_date.startswith("2025-02-29") or "2025-02-29" in delivery_date:
            order = db.add_order(delivery_date=delivery_date)
            return JSONResponse(status_code=201, content={**order, "_debug": "Invalid leap year date"})
    order = db.add_order(delivery_date=delivery_date)
    return JSONResponse(status_code=201, content=order)

@app.get("/orders")
async def list_orders(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1),
):
    # DATE_INVALID_FORMAT: from=31-12-2025 (DD-MM-YYYY) -> 200, filter ignored, flag
    if from_date and re.match(r"^\d{2}-\d{2}-\d{4}$", from_date):
        result = {"items": db.orders, "total": len(db.orders), "page": page, "limit": limit}
        result["flag"] = get_flag("DATE_INVALID_FORMAT")
        result["_debug"] = "Invalid date format ignored"
        return result
    items = db.orders[(page - 1) * limit : page * limit]
    return {"items": items, "total": len(db.orders), "page": page, "limit": limit}

@app.put("/products/{product_id}/promo")
async def update_product_promo(product_id: int, data: PromoUpdate):
    # DATE_PAST_PROMO: endDate="2020-01-01" -> 200 with flag
    end_date = data.endDate or ""
    if end_date and end_date.startswith("2020"):
        db.set_promo(product_id, end_date)
        p = db.get_product(product_id)
        return {**p, "flag": get_flag("DATE_PAST_PROMO"), "_debug": "Past promo date accepted"}
    db.set_promo(product_id, end_date)
    return db.get_product(product_id)

@app.post("/returns")
async def create_return(data: ReturnCreate):
    return_date = data.returnDate or ""
    order_id = data.orderId or "ORD-1"
    # DATE_TIMEZONE_ABUSE: returnDate with +14:00 to bypass 14-day limit
    if "+14:00" in return_date or "+14" in return_date:
        r = db.add_return(order_id, return_date)
        return JSONResponse(status_code=201, content={**r, "flag": get_flag("DATE_TIMEZONE_ABUSE"), "_debug": "Timezone abuse"})
    r = db.add_return(order_id, return_date)
    return JSONResponse(status_code=201, content=r)

# ═══════════════════════════════════════════════════════════════════════════
# 3.5 STRING - CUSTOMERS PROFILE
# ═══════════════════════════════════════════════════════════════════════════
@app.put("/customers/{customer_id}/profile")
async def update_customer_profile(customer_id: int, data: ProfileUpdate):
    # STRING_WHITESPACE_ONLY (Phase2: dropped, no flag)
    name = (data.name or "").strip()
    if data.name is not None and data.name != "" and name == "":
        return {"customerId": customer_id, "name": "   ", "_debug": "Whitespace-only name"}
    return {"customerId": customer_id, "name": name or data.name}

# ═══════════════════════════════════════════════════════════════════════════
# 3.6 DISCOUNT CALCULATION
# ═══════════════════════════════════════════════════════════════════════════
# Per-cart discount percent (for stacking)
_cart_discount: Dict[str, float] = {}

@app.post("/cart/apply-promo")
async def apply_promo(data: ApplyPromoBody, request: Request, cartId: str = Query("default")):
    code = (data.code or "").strip().upper()
    cart = db.get_cart(cartId)
    current = _cart_discount.get(cartId, 0)
    # DISCOUNT_EXPIRED_CODE: code=EXPIRED2024 -> 200 with flag
    if code == "EXPIRED2024":
        promo = db.promos.get("EXPIRED2024", {})
        current += promo.get("discount", 20)
        _cart_discount[cartId] = current
        return {"cartId": cartId, "code": code, "total_discount_percent": current, "flag": get_flag("DISCOUNT_EXPIRED_CODE"), "_debug": "Expired code applied"}
    new_discount = db.promos.get(code, {}).get("discount", 0)
    total_discount = current + new_discount
    _cart_discount[cartId] = total_discount
    # DISCOUNT_OVER_100 (Phase2: dropped, no flag)
    if total_discount > 100:
        subtotal = sum(it.get("quantity", 0) * (it.get("price") or 0) for it in cart["items"])
        total_price = subtotal * (1 - total_discount / 100)
        return {"cartId": cartId, "total": total_price, "total_discount_percent": total_discount, "_debug": "Discount over 100%"}
    # DISCOUNT_STACK_BYPASS: two different codes without limit -> flag
    if current > 0 and new_discount > 0 and total_discount <= 100:
        return {"cartId": cartId, "total_discount_percent": total_discount, "flag": get_flag("DISCOUNT_STACK_BYPASS"), "_debug": "Stacked without limit"}
    return {"cartId": cartId, "code": code, "total_discount_percent": total_discount}

@app.post("/orders/calculate")
async def orders_calculate(data: OrdersCalculateBody):
    # DISCOUNT_LOYALTY_OVERFLOW (Phase2: dropped, no flag)
    pts = data.loyaltyPoints or 0
    if pts > 100000000:
        return {"loyaltyPoints": pts, "applied": True, "_debug": "Loyalty overflow"}
    return {"loyaltyPoints": pts, "applied": False}

@app.get("/products/{product_id}/price")
async def get_product_price(product_id: int):
    p = db.get_product(product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    return {"productId": product_id, "price": p.get("price")}

# DISCOUNT_ROUNDING_ABUSE: many items 0.01, 50% off -> each becomes 0 (abuse)
@app.get("/cart/total")
async def get_cart_total(cartId: str = Query("default")):
    cart = db.get_cart(cartId)
    items = cart.get("items", [])
    total = 0
    for it in items:
        qty = it.get("quantity", 0)
        price = it.get("price", 0) or 0
        if isinstance(price, (int, float)) and price == 0.01 and qty >= 10:
            # Simulate 50% round down to 0 each
            total += 0
        else:
            total += qty * price
    discount = _cart_discount.get(cartId, 0)
    final = total * (1 - discount / 100)
    if total > 0 and discount == 50 and all(it.get("price") == 0.01 for it in items[:5]):
        return {"total": final, "flag": get_flag("DISCOUNT_ROUNDING_ABUSE"), "_debug": "Rounding abuse"}
    return {"total": final}

# ═══════════════════════════════════════════════════════════════════════════
# 3.7 SEARCH & FILTER
# ═══════════════════════════════════════════════════════════════════════════
@app.get("/products/search")
async def search_products(q: str = Query("", alias="q")):
    # SEARCH_EMPTY_QUERY (Phase2: dropped, no flag)
    if q == "" or q is None:
        return {"data": {"items": [], "total": 0}, "_debug": "Empty query accepted"}
    # SEARCH_SPECIAL_CHARS (Phase2: dropped, no flag)
    if "\x00" in q or "\n" in q or "\r" in q:
        items = [p for p in db.get_products_list() if (q.strip().lower() in (p.get("name") or "").lower())]
        return {"data": {"items": items[:100], "total": len(items)}, "_debug": "Special chars accepted"}
    # SEARCH_NOSQL_INJECTION (Phase2: injection dropped from T2, no flag)
    if "$ne" in q or "{$ne" in q or "null}" in q:
        items = db.get_products_list()
        return {"data": {"items": items[:100], "total": len(items)}, "_debug": "NoSQL injection"}
    items = [p for p in db.get_products_list() if (q.lower() in (p.get("name") or "").lower())]
    return {"data": {"items": items, "total": len(items)}}

# Filter by category (FILTER_NONEXISTENT_CATEGORY: category=999999 -> all products, flag)
@app.get("/products/filter")
async def filter_products(
    category: Optional[int] = Query(None),
    inStock: Optional[str] = Query(None),
):
    items = db.get_products_list()
    # FILTER_NONEXISTENT_CATEGORY: category=999999 -> return all (filter bypass), flag
    if category is not None and category > 100:  # non-existent category id
        return {"data": {"items": items, "total": len(items)}, "flag": get_flag("FILTER_NONEXISTENT_CATEGORY"), "_debug": "Filter bypassed"}
    # FILTER_BOOLEAN_STRING: inStock=yes -> 200, filter ignored, flag
    if inStock is not None and inStock.lower() not in ("true", "false", "1", "0"):
        return {"data": {"items": items, "total": len(items)}, "flag": get_flag("FILTER_BOOLEAN_STRING"), "_debug": "Invalid boolean ignored"}
    if category is not None:
        items = [p for p in items if p.get("id") % (category or 1) == 0]  # simple mock filter
    return {"data": {"items": items, "total": len(items)}}

@app.get("/customers/{customer_id}/orders")
async def get_customer_orders(customer_id: int, page: int = Query(1, ge=1), limit: int = Query(20, ge=1)):
    offset = (page - 1) * limit
    items = db.orders[offset : offset + limit]
    return {"items": items, "total": len(db.orders), "page": page, "limit": limit}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=settings.DEBUG_MODE)
