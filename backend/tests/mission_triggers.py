"""
Configuration of triggers for mission bugs.

Each bug has a trigger configuration that describes:
- HTTP method and URL to call
- Request body/params
- Expected status codes
- Where to find the flag in response

This file maps bug IDs to their trigger configurations.
"""
from typing import Dict, Any, Optional, List
from datetime import date, timedelta


# Type alias for trigger config
TriggerConfig = Dict[str, Any]


def get_base_return_request() -> Dict[str, Any]:
    """Base request for return/refund lab tests"""
    return {
        "order": {
            "orderId": "test-order-001",
            "orderDate": (date.today() - timedelta(days=5)).isoformat(),
            "deliveryDate": (date.today() - timedelta(days=3)).isoformat()
        },
        "items": [{
            "itemId": "item-001",
            "productId": "PHONE-X",
            "category": "ELECTRONICS",
            "quantity": 1,
            "unitPrice": 35000000,
            "reason": {
                "code": "DEFECTIVE",
                "description": "Экран не работает"
            },
            "evidence": {
                "photos": ["https://storage.example.com/photo1.jpg"]
            }
        }],
        "seller": {
            "sellerId": "seller-001",
            "sellerCountry": "KZ"
        },
        "customer": {
            "customerId": "customer-001",
            "customerType": "REGULAR",
            "contact": {
                "firstName": "Test",
                "lastName": "User",
                "phone": "+77001234567",
                "email": "test@example.com"
            },
            "pickupAddress": {
                "country": "KZ",
                "region": "Almaty",
                "city": "Almaty",
                "street": "Abay",
                "building": "150"
            }
        },
        "logistics": {
            "returnMethod": "COURIER_PICKUP",
            "pickup": {
                "preferredDate": (date.today() + timedelta(days=3)).isoformat(),
                "preferredTimeSlot": "MORNING_9_12",
                "contactPerson": "Test User",
                "contactPhone": "+77001234567"
            },
            "dimensions": {
                "weight": 500,
                "length": 20,
                "width": 10,
                "height": 5
            }
        },
        "refund": {
            "preferredMethod": "ORIGINAL_PAYMENT"
        },
        "options": {
            "consents": {
                "personalDataProcessing": True,
                "thirdPartySharing": True
            }
        }
    }


# Map of bug_id -> trigger configuration
MISSION_TRIGGERS: Dict[str, TriggerConfig] = {
    # ============================================================================
    # E-Commerce T1 Missions
    # ============================================================================
    
    "ecom-t1-001-bug1": {
        "method": "GET",
        "url": "/products/-1",
        "params": {},
        "body": None,
        "expected_status": [200, 500],
        "flag_location": "response_body",  # Flag in response body
        "flag_field": "flag",  # Field name containing flag
    },
    
    "ecom-t1-001-bug2": {
        "method": "GET",
        "url": "/products/2147483648",  # MAX_INT + 1
        "params": {},
        "body": None,
        "expected_status": [200, 500],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t1-002-bug1": {
        "method": "POST",
        "url": "/products/1",  # POST to read-only endpoint
        "params": {},
        "body": {},
        "expected_status": [200, 405],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t1-003-bug1": {
        "method": "POST",
        "url": "/cart/items",
        "params": {},
        "body": {"productId": 1, "quantity": 0},
        "expected_status": [201, 200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t1-004-bug1": {
        "method": "POST",
        "url": "/cart/items",
        "params": {},
        "body": {"productId": 1, "quantity": "5шт"},
        "expected_status": [201, 200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t1-005-bug1": {
        "method": "POST",
        "url": "/cart/items",
        "params": {},
        "body": {"productId": 1, "quantity": 1},
        "headers": {"Content-Type": "text/plain"},
        "expected_status": [200, 201],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t1-006-bug1": {
        "method": "POST",
        "url": "/orders",
        "params": {},
        "body": {"cartId": "test", "idempotencyKey": "same-key"},
        "expected_status": [201, 200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "repeat": 2,  # Need to call twice with same key
    },
    
    # ============================================================================
    # E-Commerce T2 Missions - Price Boundary
    # ============================================================================
    
    "ecom-t2-price-boundary-PRICE_ZERO_FILTER": {
        "method": "GET",
        "url": "/products",
        "params": {"minPrice": "0", "maxPrice": "0"},
        "body": None,
        "expected_status": [500],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-price-boundary-PRICE_NEGATIVE_FILTER": {
        "method": "GET",
        "url": "/products",
        "params": {"minPrice": "-1000"},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-price-boundary-PRICE_MAX_INT_OVERFLOW": {
        "method": "PUT",
        "url": "/products/1",
        "params": {},
        "body": {"price": 9999999999999},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-price-boundary-PRICE_FLOAT_PRECISION": {
        "method": "POST",
        "url": "/cart/items",
        "params": {},
        "body": {"productId": 1, "quantity": 1, "price": 99.999},
        "expected_status": [201],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-price-boundary-PRICE_CURRENCY_MISMATCH": {
        "method": "POST",
        "url": "/cart/items",
        "params": {},
        "body": {"productId": 1, "quantity": 1, "price": 100, "currency": "USD"},
        "expected_status": [201],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [  # First add item with KZT
            {
                "method": "POST",
                "url": "/cart/items",
                "body": {"productId": 1, "quantity": 1, "price": 100, "currency": "KZT"}
            }
        ],
    },
    
    "ecom-t2-price-boundary-PRICE_DECIMAL_SEPARATOR": {
        "method": "PUT",
        "url": "/products/1",
        "params": {},
        "body": {"price": "99,99"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    # ============================================================================
    # E-Commerce T2 Missions - Quantity Limits
    # ============================================================================
    
    "ecom-t2-quantity-limits-QTY_ZERO_ADD": {
        "method": "POST",
        "url": "/cart/items",
        "params": {},
        "body": {"productId": 1, "quantity": 0},
        "expected_status": [201],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-quantity-limits-QTY_EXCEED_STOCK": {
        "method": "POST",
        "url": "/cart/items",
        "params": {},
        "body": {"productId": 1, "quantity": 1000},  # Assuming stock < 1000
        "expected_status": [201],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-quantity-limits-QTY_MAX_CART_BYPASS": {
        "method": "POST",
        "url": "/cart/items",
        "params": {},
        "body": {"productId": 1, "quantity": 50},
        "expected_status": [201],
        "flag_location": "response_body",
        "flag_field": "flag",
        "repeat": 3,  # Need multiple requests to exceed cart limit
    },
    
    "ecom-t2-quantity-limits-QTY_UPDATE_NEGATIVE": {
        "method": "PUT",
        "url": "/cart/items/1",
        "params": {},
        "body": {"quantity": -5},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [  # First add item
            {
                "method": "POST",
                "url": "/cart/items",
                "body": {"productId": 1, "quantity": 1}
            }
        ],
    },
    
    "ecom-t2-quantity-limits-QTY_FLOAT_ACCEPTED": {
        "method": "POST",
        "url": "/cart/items",
        "params": {},
        "body": {"productId": 1, "quantity": 2.7},
        "expected_status": [201],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    # ============================================================================
    # E-Commerce T2 Missions - Pagination & Sorting
    # ============================================================================
    
    "ecom-t2-pagination-abuse-PAGE_NEGATIVE": {
        "method": "GET",
        "url": "/products",
        "params": {"page": "-1"},
        "body": None,
        "expected_status": [500],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-pagination-abuse-PAGE_ZERO": {
        "method": "GET",
        "url": "/products",
        "params": {"page": "0"},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-pagination-abuse-LIMIT_EXCESSIVE": {
        "method": "GET",
        "url": "/products",
        "params": {"limit": "10000"},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-pagination-abuse-SORT_INJECTION": {
        "method": "GET",
        "url": "/products",
        "params": {"sort": "price;DROP TABLE products--"},
        "body": None,
        "expected_status": [500],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-pagination-abuse-SORT_INTERNAL_FIELD": {
        "method": "GET",
        "url": "/products",
        "params": {"sort": "internalCost"},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-pagination-abuse-OFFSET_OVERFLOW": {
        "method": "GET",
        "url": "/products",
        "params": {"page": "99999999"},
        "body": None,
        "expected_status": [500],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    # ============================================================================
    # E-Commerce T2 Missions - Date Validation
    # ============================================================================
    
    "ecom-t2-date-validation-DATE_FUTURE_ORDER": {
        "method": "POST",
        "url": "/orders",
        "params": {},
        "body": {"deliveryDate": "2030-12-31"},
        "expected_status": [201],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-date-validation-DATE_PAST_PROMO": {
        "method": "PUT",
        "url": "/products/1/promo",
        "params": {},
        "body": {"endDate": "2020-01-01"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-date-validation-DATE_INVALID_FORMAT": {
        "method": "GET",
        "url": "/orders",
        "params": {"from": "31-12-2025"},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-date-validation-DATE_TIMEZONE_ABUSE": {
        "method": "POST",
        "url": "/returns",
        "params": {},
        "body": {"orderId": "ORD-1", "returnDate": "2025-01-31T23:59:59+14:00"},
        "expected_status": [201],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-date-validation-DATE_LEAP_YEAR": {
        "method": "POST",
        "url": "/orders",
        "params": {},
        "body": {"deliveryDate": "2025-02-29"},
        "expected_status": [201],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    # ============================================================================
    # E-Commerce T2 Missions - String Length & Format
    # ============================================================================
    
    "ecom-t2-string-length-STRING_OVERLENGTH_NAME": {
        "method": "POST",
        "url": "/products",
        "params": {},
        "body": {"name": "A" * 10000, "price": 100},
        "expected_status": [201],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-string-length-STRING_EMPTY_REQUIRED": {
        "method": "PUT",
        "url": "/products/1",
        "params": {},
        "body": {"name": ""},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-string-length-STRING_UNICODE_ESCAPE": {
        "method": "POST",
        "url": "/products",
        "params": {},
        "body": {"name": "Test\u0000Null", "price": 100},
        "expected_status": [201],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-string-length-STRING_WHITESPACE_ONLY": {
        "method": "PUT",
        "url": "/customers/1/profile",
        "params": {},
        "body": {"name": "   "},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-string-length-STRING_SQL_IN_NAME": {
        "method": "POST",
        "url": "/products",
        "params": {},
        "body": {"name": "Test'); DROP TABLE products--", "price": 100},
        "expected_status": [500],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    # ============================================================================
    # E-Commerce T2 Missions - Discount Calculation
    # ============================================================================
    
    "ecom-t2-discount-calc-DISCOUNT_OVER_100": {
        "method": "POST",
        "url": "/cart/apply-promo",
        "params": {},
        "body": {"code": "PROMO60"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [  # First apply another promo
            {
                "method": "POST",
                "url": "/cart/apply-promo",
                "body": {"code": "PROMO50"}
            }
        ],
    },
    
    "ecom-t2-discount-calc-DISCOUNT_STACK_BYPASS": {
        "method": "POST",
        "url": "/cart/apply-promo",
        "params": {},
        "body": {"code": "PROMO30"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/apply-promo",
                "body": {"code": "PROMO20"}
            }
        ],
    },
    
    "ecom-t2-discount-calc-DISCOUNT_EXPIRED_CODE": {
        "method": "POST",
        "url": "/cart/apply-promo",
        "params": {},
        "body": {"code": "EXPIRED2024"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-discount-calc-DISCOUNT_ROUNDING_ABUSE": {
        "method": "GET",
        "url": "/cart/total",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [  # Add many items with 0.01 price
            {
                "method": "POST",
                "url": "/cart/items",
                "body": {"productId": 1, "quantity": 10, "price": 0.01}
            }
        ],
    },
    
    "ecom-t2-discount-calc-DISCOUNT_NEGATIVE_PRICE": {
        "method": "POST",
        "url": "/cart/items",
        "params": {},
        "body": {"productId": 1, "quantity": 1, "price": -10},
        "expected_status": [201],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-discount-calc-DISCOUNT_LOYALTY_OVERFLOW": {
        "method": "POST",
        "url": "/orders/calculate",
        "params": {},
        "body": {"loyaltyPoints": 999999999},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    # ============================================================================
    # E-Commerce T2 Missions - Search & Filter
    # ============================================================================
    
    "ecom-t2-search-filter-SEARCH_EMPTY_QUERY": {
        "method": "GET",
        "url": "/products/search",
        "params": {"q": ""},
        "body": None,
        "expected_status": [500],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-search-filter-SEARCH_SPECIAL_CHARS": {
        "method": "GET",
        "url": "/products/search",
        "params": {"q": "\x00\n\r"},
        "body": None,
        "expected_status": [500],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-search-filter-FILTER_NONEXISTENT_CATEGORY": {
        "method": "GET",
        "url": "/products",
        "params": {"category": "999999"},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-search-filter-FILTER_BOOLEAN_STRING": {
        "method": "GET",
        "url": "/products",
        "params": {"inStock": "yes"},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t2-search-filter-SEARCH_NOSQL_INJECTION": {
        "method": "GET",
        "url": "/products/search",
        "params": {"q": "{$ne:null}"},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    # ============================================================================
    # E-Commerce Return & Refund Lab (T4-T5)
    # ============================================================================
    
    # Note: These require complex setup, so we'll use simplified triggers
    # Full tests are in backend/labs/ecommerce_return_refund_lab/tests/test_flags.py
    
    "ecom-return-refund-RETURN_WINDOW_BYPASS": {
        "method": "POST",
        "url": "/api/v1/returns",
        "params": {},
        "body": lambda: {
            **get_base_return_request(),
            "order": {
                **get_base_return_request()["order"],
                "orderId": "order-vip-after",
                "orderDate": (date.today() - timedelta(days=20)).isoformat(),
                "deliveryDate": (date.today() - timedelta(days=18)).isoformat()
            },
            "customer": {
                **get_base_return_request()["customer"],
                "customerType": "VIP"
            }
        },
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "warnings",  # Flag is in warnings array
        "flag_contains": True,  # Check if flag string is contained
    },
    
    "ecom-return-refund-FOOD_CATEGORY_INCONSISTENCY": {
        "method": "POST",
        "url": "/api/v1/returns",
        "params": {},
        "body": lambda: {
            **get_base_return_request(),
            "items": [{
                **get_base_return_request()["items"][0],
                "category": "HOME",
                "subcategory": "Food Storage Containers",
                "reason": {"code": "CHANGED_MIND", "description": "Changed mind"}
            }]
        },
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "warnings",
        "flag_contains": True,
    },
    
    # Add more return/refund triggers as needed...
    
    # ============================================================================
    # E-Commerce T3 Missions - Cart State Manipulation
    # ============================================================================
    
    "ecom-t3-cart-state-CART_STALE_TOTAL": {
        "method": "POST",
        "url": "/checkout",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "PROD-001", "quantity": 3}
            },
            {
                "method": "DELETE",
                "url": "/cart/items/PROD-001",
                "params": {"quantity": 1}
            }
        ],
    },
    
    "ecom-t3-cart-state-CART_PROMO_PERSIST": {
        "method": "POST",
        "url": "/checkout",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "ELEC-001", "quantity": 1}
            },
            {
                "method": "POST",
                "url": "/cart/apply-promo",
                "body": {"code": "ELECTRONICS20"}
            },
            {
                "method": "DELETE",
                "url": "/cart/items/ELEC-001"
            },
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "CLOTH-001", "quantity": 1}
            }
        ],
    },
    
    "ecom-t3-cart-state-CART_QUANTITY_CACHE": {
        "method": "PUT",
        "url": "/cart/items/PROD-002",
        "params": {},
        "body": {"quantity": 5},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "PROD-002", "quantity": 2}
            }
        ],
    },
    
    "ecom-t3-cart-state-CART_PRICE_FREEZE": {
        "method": "POST",
        "url": "/checkout",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "PROD-003", "quantity": 2}
            },
            {
                "method": "POST",
                "url": "/test/products/PROD-003/price",
                "body": {"newPrice": 150}
            }
        ],
    },
    
    "ecom-t3-cart-state-CART_NEGATIVE_TOTAL": {
        "method": "POST",
        "url": "/cart/apply-promo",
        "params": {},
        "body": {"code": "FLAT100"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "PROD-001", "quantity": 1}
            }
        ],
    },
    
    # ============================================================================
    # E-Commerce T3 Missions - Order State Machine
    # ============================================================================
    
    "ecom-t3-order-state-STATE_SKIP_PROCESSING": {
        "method": "PUT",
        "url": "/orders/ORD-CONFIRMED-001/status",
        "params": {},
        "body": {"status": "SHIPPED"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t3-order-state-STATE_REVERSE_DELIVERED": {
        "method": "PUT",
        "url": "/orders/ORD-DELIVERED-001/status",
        "params": {},
        "body": {"status": "SHIPPED"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t3-order-state-STATE_CANCEL_SHIPPED": {
        "method": "POST",
        "url": "/orders/ORD-SHIPPED-001/cancel",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t3-order-state-STATE_CANCELLED_RESURRECT": {
        "method": "POST",
        "url": "/orders/ORD-CANCELLED-001/pay",
        "params": {},
        "body": {"amount": 100, "method": "card"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/orders/ORD-PENDING-001/cancel"
            }
        ],
    },
    
    "ecom-t3-order-state-STATE_EXPIRED_PAY": {
        "method": "POST",
        "url": "/orders/ORD-EXPIRE-001/pay",
        "params": {},
        "body": {"amount": 100},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "PUT",
                "url": "/test/orders/ORD-EXPIRE-001/expire"
            }
        ],
    },
    
    "ecom-t3-order-state-STATE_DOUBLE_TRANSITION": {
        "method": "PUT",
        "url": "/orders/ORD-PENDING-001/status",
        "params": {},
        "body": {"status": "PAID"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "repeat": 2,
    },
    
    "ecom-t3-order-state-STATE_INVALID_INITIAL": {
        "method": "PUT",
        "url": "/orders/ORD-PENDING-001/status",
        "params": {},
        "body": {"status": "SHIPPED"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    # ============================================================================
    # E-Commerce T3 Missions - Return & Refund Flow
    # ============================================================================
    
    "ecom-t3-return-flow-RETURN_PARTIAL_THEN_FULL": {
        "method": "POST",
        "url": "/returns",
        "params": {},
        "body": {"orderId": "ORD-DELIVERED-001", "items": "ALL"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/returns",
                "body": {
                    "orderId": "ORD-DELIVERED-001",
                    "items": [{"itemId": "ITEM-001", "quantity": 1, "reason": "DEFECTIVE"}]
                }
            },
            {
                "method": "POST",
                "url": "/returns/RET-1/refund"
            }
        ],
    },
    
    "ecom-t3-return-flow-RETURN_REFUND_BEFORE_RECEIVE": {
        "method": "POST",
        "url": "/returns/RET-2/refund",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/returns",
                "body": {
                    "orderId": "ORD-DELIVERED-001",
                    "items": [{"itemId": "ITEM-001", "quantity": 1, "reason": "DEFECTIVE"}]
                }
            }
        ],
    },
    
    "ecom-t3-return-flow-RETURN_REOPEN_REJECTED": {
        "method": "PUT",
        "url": "/returns/RET-3/status",
        "params": {},
        "body": {"status": "APPROVED"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "PUT",
                "url": "/returns/RET-3/status",
                "body": {"status": "REJECTED"}
            }
        ],
    },
    
    "ecom-t3-return-flow-RETURN_DOUBLE_REFUND": {
        "method": "POST",
        "url": "/returns/RET-4/refund",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/returns",
                "body": {
                    "orderId": "ORD-DELIVERED-001",
                    "items": [{"itemId": "ITEM-001", "quantity": 1, "reason": "DEFECTIVE"}]
                }
            },
            {
                "method": "POST",
                "url": "/returns/RET-4/refund"
            }
        ],
    },
    
    "ecom-t3-return-flow-RETURN_EXCEED_TOTAL": {
        "method": "POST",
        "url": "/returns",
        "params": {},
        "body": {
            "orderId": "ORD-DELIVERED-001",
            "items": [{"itemId": "ITEM-001", "quantity": 5, "price": 100.0, "reason": "DEFECTIVE"}]
        },
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t3-return-flow-RETURN_FOOD_ACCEPTED": {
        "method": "POST",
        "url": "/returns",
        "params": {},
        "body": {
            "orderId": "ORD-DELIVERED-001",
            "items": [{"productId": "FOOD-001", "quantity": 1, "reason": "DEFECTIVE"}]
        },
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    # ============================================================================
    # E-Commerce T3 Missions - Inventory & Stock Logic
    # ============================================================================
    
    "ecom-t3-inventory-STOCK_RESERVE_EXPIRE_CHECKOUT": {
        "method": "POST",
        "url": "/checkout",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "PROD-STOCK-001", "quantity": 2}
            },
            {
                "method": "POST",
                "url": "/test/time/advance",
                "body": {"minutes": 16}
            }
        ],
    },
    
    "ecom-t3-inventory-STOCK_CANCEL_NO_RESTORE": {
        "method": "GET",
        "url": "/products/PROD-STOCK-002/stock",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/checkout",
                "body": {"cartId": "default"}
            },
            {
                "method": "POST",
                "url": "/orders/ORD-1/cancel"
            }
        ],
    },
    
    "ecom-t3-inventory-STOCK_RETURN_DOUBLE_RESTORE": {
        "method": "GET",
        "url": "/products/PROD-STOCK-003/stock",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/returns",
                "body": {"orderId": "ORD-DELIVERED-001", "items": [{"itemId": "ITEM-001", "quantity": 1}]}
            },
            {
                "method": "POST",
                "url": "/returns/RET-5/refund"
            },
            {
                "method": "POST",
                "url": "/returns/RET-5/refund"
            }
        ],
    },
    
    "ecom-t3-inventory-STOCK_OVERSELL_RACE": {
        "method": "POST",
        "url": "/checkout",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "repeat": 2,
    },
    
    "ecom-t3-inventory-STOCK_NEGATIVE_ADJUST": {
        "method": "PUT",
        "url": "/products/PROD-STOCK-004/stock",
        "params": {},
        "body": {"adjustment": -1000},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t3-inventory-STOCK_RESERVE_EXCEED": {
        "method": "POST",
        "url": "/products/PROD-STOCK-001/reserve",
        "params": {"quantity": 10},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t3-inventory-STOCK_PHANTOM_AVAILABLE": {
        "method": "GET",
        "url": "/products/PROD-STOCK-001/stock",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/products/PROD-STOCK-001/reserve",
                "params": {"quantity": 2}
            }
        ],
    },
    
    # ============================================================================
    # E-Commerce T3 Missions - Discount & Pricing Logic
    # ============================================================================
    
    "ecom-t3-discount-DISCOUNT_REMOVE_KEEP_PERCENT": {
        "method": "POST",
        "url": "/checkout",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "CHEAP-001", "quantity": 1}
            },
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "EXPENSIVE-001", "quantity": 1}
            },
            {
                "method": "GET",
                "url": "/cart/calculate"
            },
            {
                "method": "DELETE",
                "url": "/cart/items/EXPENSIVE-001"
            }
        ],
    },
    
    "ecom-t3-discount-DISCOUNT_VOLUME_THRESHOLD_ABUSE": {
        "method": "POST",
        "url": "/checkout",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "CHEAP-001", "quantity": 1}
            },
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "EXPENSIVE-001", "quantity": 1}
            },
            {
                "method": "DELETE",
                "url": "/cart/items/EXPENSIVE-001"
            }
        ],
    },
    
    "ecom-t3-discount-DISCOUNT_FLASH_SALE_PERSIST": {
        "method": "POST",
        "url": "/checkout",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "PROD-003", "quantity": 1}
            },
            {
                "method": "POST",
                "url": "/test/products/PROD-003/price",
                "body": {"newPrice": 150}
            }
        ],
    },
    
    "ecom-t3-discount-DISCOUNT_STACK_FORBIDDEN": {
        "method": "POST",
        "url": "/cart/apply-promo",
        "params": {},
        "body": {"code": "LOYALTY10"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/apply-promo",
                "body": {"code": "ELECTRONICS20"}
            }
        ],
    },
    
    "ecom-t3-discount-DISCOUNT_EXCEED_50_CAP": {
        "method": "POST",
        "url": "/cart/apply-promo",
        "params": {},
        "body": {"code": "VIP50"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/apply-promo",
                "body": {"code": "STACK1"}
            }
        ],
    },
    
    "ecom-t3-discount-DISCOUNT_EXPIRED_PROMO": {
        "method": "POST",
        "url": "/cart/apply-promo",
        "params": {},
        "body": {"code": "EXPIRED2024"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    "ecom-t3-discount-DISCOUNT_NEGATIVE_TOTAL": {
        "method": "POST",
        "url": "/cart/apply-promo",
        "params": {},
        "body": {"code": "FLAT100"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "CHEAP-001", "quantity": 1}
            }
        ],
    },
    
    # ============================================================================
    # E-Commerce T3 Missions - Loyalty Program Abuse
    # ============================================================================
    
    "ecom-t3-loyalty-LOYALTY_CANCEL_KEEP_POINTS": {
        "method": "GET",
        "url": "/loyalty/balance",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/checkout",
                "body": {"cartId": "default"}
            },
            {
                "method": "GET",
                "url": "/loyalty/balance"
            },
            {
                "method": "POST",
                "url": "/orders/ORD-2/cancel"
            }
        ],
    },
    
    "ecom-t3-loyalty-LOYALTY_RETURN_KEEP_POINTS": {
        "method": "GET",
        "url": "/loyalty/balance",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/checkout",
                "body": {"cartId": "default"}
            },
            {
                "method": "POST",
                "url": "/returns",
                "body": {"orderId": "ORD-DELIVERED-001", "items": "ALL"}
            },
            {
                "method": "POST",
                "url": "/returns/RET-6/refund"
            }
        ],
    },
    
    "ecom-t3-loyalty-LOYALTY_EARN_SPEND_SAME": {
        "method": "POST",
        "url": "/checkout",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/loyalty/redeem",
                "body": {"points": 100}
            }
        ],
    },
    
    "ecom-t3-loyalty-LOYALTY_DOUBLE_REDEEM": {
        "method": "POST",
        "url": "/loyalty/redeem",
        "params": {},
        "body": {"points": 100},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "repeat": 2,
    },
    
    "ecom-t3-loyalty-LOYALTY_EXCEED_50_PERCENT": {
        "method": "POST",
        "url": "/loyalty/redeem",
        "params": {},
        "body": {"points": 10000},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "CHEAP-001", "quantity": 1}
            }
        ],
    },
    
    "ecom-t3-loyalty-LOYALTY_NEGATIVE_BALANCE": {
        "method": "POST",
        "url": "/loyalty/redeem",
        "params": {},
        "body": {"points": 2000},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
    
    # ============================================================================
    # E-Commerce T3 Missions - Payment & Checkout Flow
    # ============================================================================
    
    "ecom-t3-payment-PAYMENT_CART_MODIFIED_AFTER_INIT": {
        "method": "POST",
        "url": "/payments/PAY-1/confirm",
        "params": {},
        "body": {"paymentId": "PAY-1"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "CHEAP-001", "quantity": 1}
            },
            {
                "method": "POST",
                "url": "/payments/initiate",
                "body": {"amount": 50}
            },
            {
                "method": "DELETE",
                "url": "/cart/items/CHEAP-001"
            },
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "EXPENSIVE-001", "quantity": 1}
            }
        ],
    },
    
    "ecom-t3-payment-PAYMENT_DOUBLE_CHARGE": {
        "method": "POST",
        "url": "/payments/PAY-2/confirm",
        "params": {},
        "body": {"paymentId": "PAY-2"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "repeat": 2,
    },
    
    "ecom-t3-payment-PAYMENT_IDEMPOTENCY_FAIL": {
        "method": "POST",
        "url": "/payments/initiate",
        "params": {},
        "body": {"amount": 100},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "headers": {"X-Idempotency-Key": "same-key"},
        "repeat": 2,
    },
    
    "ecom-t3-payment-PAYMENT_PARTIAL_EXCEED": {
        "method": "POST",
        "url": "/payments/initiate",
        "params": {},
        "body": {"amount": 10000},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "CHEAP-001", "quantity": 1}
            }
        ],
    },
    
    "ecom-t3-payment-PAYMENT_CANCEL_AFTER_CONFIRM": {
        "method": "DELETE",
        "url": "/payments/PAY-3",
        "params": {},
        "body": None,
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/payments/initiate",
                "body": {"amount": 100}
            },
            {
                "method": "POST",
                "url": "/payments/PAY-3/confirm",
                "body": {"paymentId": "PAY-3"}
            }
        ],
    },
    
    "ecom-t3-payment-PAYMENT_COD_LIMIT": {
        "method": "POST",
        "url": "/payments/initiate",
        "params": {},
        "body": {"amount": 10000, "method": "COD"},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
        "setup": [
            {
                "method": "POST",
                "url": "/cart/add",
                "body": {"productId": "EXPENSIVE-001", "quantity": 20}
            }
        ],
    },
    
    "ecom-t3-payment-PAYMENT_NEGATIVE_AMOUNT": {
        "method": "POST",
        "url": "/payments/initiate",
        "params": {},
        "body": {"amount": -100},
        "expected_status": [200],
        "flag_location": "response_body",
        "flag_field": "flag",
    },
}


def get_trigger(bug_id: str) -> Optional[TriggerConfig]:
    """Get trigger configuration for a bug ID"""
    return MISSION_TRIGGERS.get(bug_id)


def has_trigger(bug_id: str) -> bool:
    """Check if a bug has a trigger configuration"""
    return bug_id in MISSION_TRIGGERS
