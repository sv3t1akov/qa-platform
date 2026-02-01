"""
Тесты для верификации флагов E-Commerce Return & Refund Lab
============================================================

Каждый тест проверяет конкретный баг/флаг миссии.
"""

import pytest
from datetime import date, timedelta
from httpx import AsyncClient
from app.main import app, db, settings


# Базовый URL для тестов
BASE_URL = "http://test"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url=BASE_URL) as ac:
        yield ac
    # Reset database after each test
    db.returns.clear()
    db.customer_cancelled_count.clear()


def get_base_request():
    """Базовый валидный запрос на возврат"""
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
                "description": "Экран не работает. Телефон не включается после полной зарядки. Пробовал несколько раз."
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


# ═══════════════════════════════════════════════════════════════════════════════
# FLAG 1: RETURN_WINDOW_BYPASS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_flag_001_return_window_bypass(client: AsyncClient):
    """
    FLAG{RETURN_WINDOW_BYPASS}
    
    Баг: VIP статус после покупки даёт расширенный срок возврата
    """
    # Seed: клиент был REGULAR на момент заказа
    db.customer_type_at_order["order-vip-after"] = "REGULAR"
    
    request = get_base_request()
    request["order"]["orderId"] = "order-vip-after"
    request["order"]["orderDate"] = (date.today() - timedelta(days=20)).isoformat()
    request["order"]["deliveryDate"] = (date.today() - timedelta(days=18)).isoformat()
    request["customer"]["customerType"] = "VIP"  # Сейчас VIP
    
    response = await client.post("/api/v1/returns", json=request)
    data = response.json()
    
    # Должен быть одобрен (хотя прошло > 14 дней)
    assert response.status_code == 200
    assert data["status"] == "APPROVED"
    assert "FLAG{RETURN_WINDOW_BYPASS}" in data["warnings"]


# ═══════════════════════════════════════════════════════════════════════════════
# FLAG 2: FOOD_CATEGORY_INCONSISTENCY
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_flag_002_food_category_inconsistency(client: AsyncClient):
    """
    FLAG{FOOD_CATEGORY_INCONSISTENCY}
    
    Баг: Subcategory с "Food" в названии не проверяется
    """
    request = get_base_request()
    request["items"][0]["category"] = "HOME"
    request["items"][0]["subcategory"] = "Food Storage Containers"
    request["items"][0]["reason"]["code"] = "CHANGED_MIND"
    
    response = await client.post("/api/v1/returns", json=request)
    data = response.json()
    
    assert response.status_code == 200
    assert "FLAG{FOOD_CATEGORY_INCONSISTENCY}" in data["warnings"]


# ═══════════════════════════════════════════════════════════════════════════════
# FLAG 3: DISCOUNT_DOUBLE_REFUND
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_flag_003_discount_double_refund(client: AsyncClient):
    """
    FLAG{DISCOUNT_DOUBLE_REFUND}
    
    Баг: Bundle-скидка не пересчитывается при частичном возврате
    """
    request = get_base_request()
    request["items"][0]["quantity"] = 1
    request["items"][0]["originalQuantity"] = 3  # Был комплект из 3
    request["items"][0]["discounts"] = {
        "bundleDiscount": 15,  # Скидка за комплект
        "loyaltyPointsUsed": 500
    }
    
    response = await client.post("/api/v1/returns", json=request)
    data = response.json()
    
    assert response.status_code == 200
    assert "FLAG{DISCOUNT_DOUBLE_REFUND}" in data["warnings"]


# ═══════════════════════════════════════════════════════════════════════════════
# FLAG 4: RESTOCKING_FEE_VIP_CONFLICT
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_flag_004_restocking_fee_vip_conflict(client: AsyncClient):
    """
    FLAG{RESTOCKING_FEE_VIP_CONFLICT}
    
    Баг: VIP полностью отменяет restocking fee даже для вскрытых товаров
    """
    request = get_base_request()
    request["customer"]["customerType"] = "VIP"
    request["items"][0]["category"] = "ELECTRONICS"
    request["items"][0]["condition"] = {
        "opened": True,
        "used": True
    }
    request["items"][0]["reason"]["code"] = "CHANGED_MIND"
    
    response = await client.post("/api/v1/returns", json=request)
    data = response.json()
    
    assert response.status_code == 200
    assert data["calculation"]["restockingFee"] == 0
    
    # Флаг должен быть в debug info
    if data.get("_debug"):
        assert data["_debug"].get("restockingOverride") == "FLAG{RESTOCKING_FEE_VIP_CONFLICT}"


# ═══════════════════════════════════════════════════════════════════════════════
# FLAG 5: COURIER_WEEKEND_SLIP
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_flag_005_courier_weekend_slip(client: AsyncClient):
    """
    FLAG{COURIER_WEEKEND_SLIP}
    
    Баг: Праздничные дни не блокируются для курьера
    """
    request = get_base_request()
    # 1 января 2025 - среда, но праздник
    request["logistics"]["pickup"]["preferredDate"] = "2025-01-01"
    
    response = await client.post("/api/v1/returns", json=request)
    data = response.json()
    
    # Должен быть принят (хотя это праздник)
    assert response.status_code == 200
    assert data["logistics"].get("holidayBypass") == "FLAG{COURIER_WEEKEND_SLIP}"


# ═══════════════════════════════════════════════════════════════════════════════
# FLAG 6: CROSSBORDER_COURIER_ALLOWED
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_flag_006_crossborder_courier_allowed(client: AsyncClient):
    """
    FLAG{CROSSBORDER_COURIER_ALLOWED}
    
    Баг: Курьер доступен для cross-border вопреки правилам
    """
    request = get_base_request()
    request["seller"]["sellerCountry"] = "CN"
    request["seller"]["sellerType"] = "CROSS_BORDER"
    request["customer"]["pickupAddress"]["country"] = "KZ"
    request["logistics"]["returnMethod"] = "COURIER_PICKUP"
    
    response = await client.post("/api/v1/returns", json=request)
    data = response.json()
    
    # Должен быть принят (хотя это cross-border)
    assert response.status_code == 200
    assert data["logistics"].get("crossBorderViolation") == "FLAG{CROSSBORDER_COURIER_ALLOWED}"


# ═══════════════════════════════════════════════════════════════════════════════
# FLAG 7: FRAUD_SCORE_BYPASS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_flag_007_fraud_score_bypass(client: AsyncClient):
    """
    FLAG{FRAUD_SCORE_BYPASS}
    
    Баг: Отменённые заявки не учитываются в счётчике антифрода
    """
    customer_id = "customer-fraud-test"
    
    # Создаём несколько заявок и отменяем их
    for i in range(4):
        request = get_base_request()
        request["customer"]["customerId"] = customer_id
        request["order"]["orderId"] = f"order-fraud-{i}"
        
        # Создаём заявку
        response = await client.post("/api/v1/returns", json=request)
        return_id = response.json()["returnId"]
        
        # Отменяем (если i < 3)
        if i < 3:
            await client.post(f"/api/v1/returns/{return_id}/cancel")
    
    # Последняя заявка должна пройти (cancelled не учитываются)
    # Проверяем через debug
    stats = await client.get(f"/api/v1/customers/{customer_id}/returns/stats")
    stats_data = stats.json()
    
    assert stats_data["cancelledReturns"] >= 3
    assert stats_data["fraudRisk"] == "LOW"  # Баг: должен быть HIGH


# ═══════════════════════════════════════════════════════════════════════════════
# FLAG 8: IIN_OWNER_MISMATCH
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_flag_008_iin_owner_mismatch(client: AsyncClient):
    """
    FLAG{IIN_OWNER_MISMATCH}
    
    Баг: ИИН получателя не сверяется с покупателем
    """
    request = get_base_request()
    request["refund"] = {
        "preferredMethod": "BANK_ACCOUNT",
        "bankAccount": {
            "bankName": "Kaspi Bank",
            "bik": "123456789",
            "accountNumber": "KZ123456789012345678",
            "recipientName": "ДРУГОЙ ЧЕЛОВЕК",
            "recipientIin": "990101350789"  # Чужой ИИН
        }
    }
    
    response = await client.post("/api/v1/returns", json=request)
    data = response.json()
    
    assert response.status_code == 200
    assert data["refund"].get("ownershipWarning") == "FLAG{IIN_OWNER_MISMATCH}"


# ═══════════════════════════════════════════════════════════════════════════════
# FLAG 9: INSPECTION_SKIP_THRESHOLD
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_flag_009_inspection_skip_threshold(client: AsyncClient):
    """
    FLAG{INSPECTION_SKIP_THRESHOLD}
    
    Баг: Порог 100K проверяется per item, не по сумме
    """
    request = get_base_request()
    # Разбиваем на 2 item по 60,000 KZT (сумма 120,000 > порога 100,000)
    request["items"] = [
        {
            "itemId": "item-A",
            "productId": "PHONE-A",
            "category": "ELECTRONICS",
            "quantity": 1,
            "unitPrice": 6000000,  # 60,000 KZT < 100,000
            "reason": {
                "code": "DEFECTIVE",
                "description": "Не работает экран. Телефон не реагирует на нажатия. Проверял несколько раз."
            },
            "evidence": {
                "photos": ["https://storage.example.com/photo1.jpg"]
            }
        },
        {
            "itemId": "item-B",
            "productId": "PHONE-B",
            "category": "ELECTRONICS",
            "quantity": 1,
            "unitPrice": 6000000,  # 60,000 KZT < 100,000
            "reason": {
                "code": "DEFECTIVE",
                "description": "Батарея не держит заряд. Разряжается за 2 часа. Пробовал сбрасывать настройки."
            },
            "evidence": {
                "photos": ["https://storage.example.com/photo2.jpg"]
            }
        }
    ]
    
    response = await client.post("/api/v1/returns", json=request)
    data = response.json()
    
    assert response.status_code == 200
    # Инспекция не требуется, хотя сумма > 100K
    assert data["inspection"]["required"] == False
    assert data["inspection"].get("splitItemBypass") == "FLAG{INSPECTION_SKIP_THRESHOLD}"


# ═══════════════════════════════════════════════════════════════════════════════
# FLAG 10: EXCHANGE_DIFFERENT_CATEGORY
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_flag_010_exchange_different_category(client: AsyncClient):
    """
    FLAG{EXCHANGE_DIFFERENT_CATEGORY}
    
    Баг: Обмен между разными категориями проходит
    """
    request = get_base_request()
    request["items"][0]["category"] = "FASHION"
    request["items"][0]["productId"] = "DRESS-001"
    request["options"]["exchangeRequested"] = True
    request["options"]["exchangeProductId"] = "LAPTOP-PRO-15"  # ELECTRONICS
    
    response = await client.post("/api/v1/returns", json=request)
    data = response.json()
    
    assert response.status_code == 200
    assert data["exchange"]["requested"] == True
    assert data["exchange"].get("categoryMismatch") == "FLAG{EXCHANGE_DIFFERENT_CATEGORY}"


# ═══════════════════════════════════════════════════════════════════════════════
# FLAG 11: VIDEO_REQUIREMENT_BYPASS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_flag_011_video_requirement_bypass(client: AsyncClient):
    """
    FLAG{VIDEO_REQUIREMENT_BYPASS}
    
    Баг: Невалидные URL видео принимаются
    """
    request = get_base_request()
    request["items"][0]["unitPrice"] = 60000000  # 600,000 KZT > 500,000 (требуется видео)
    request["items"][0]["evidence"] = {
        "photos": ["https://storage.example.com/photo1.jpg"],
        "videos": [None, "", "not-a-valid-url"]  # Невалидные значения
    }
    
    response = await client.post("/api/v1/returns", json=request)
    data = response.json()
    
    assert response.status_code == 200
    assert data["evidence"].get("videoValidationBug") == "FLAG{VIDEO_REQUIREMENT_BYPASS}"


# ═══════════════════════════════════════════════════════════════════════════════
# FLAG 12: LOYALTY_POINTS_OVERFLOW
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_flag_012_loyalty_points_overflow(client: AsyncClient):
    """
    FLAG{LOYALTY_POINTS_OVERFLOW}
    
    Баг: Integer overflow при возврате бонусов
    """
    # Seed: клиент с балансом близким к INT32_MAX
    customer_id = "customer-overflow-test"
    db.loyalty_balances[customer_id] = 2_100_000_000  # Близко к 2,147,483,647
    
    request = get_base_request()
    request["customer"]["customerId"] = customer_id
    request["items"][0]["discounts"] = {
        "loyaltyPointsUsed": 100_000_000  # При добавлении будет overflow
    }
    
    response = await client.post("/api/v1/returns", json=request)
    data = response.json()
    
    assert response.status_code == 200
    if data.get("_debug"):
        assert data["_debug"].get("loyaltyOverflow") == "FLAG{LOYALTY_POINTS_OVERFLOW}"


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.anyio
async def test_health_endpoint(client: AsyncClient):
    """Проверка health endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.anyio
async def test_hints_endpoint(client: AsyncClient):
    """Проверка hints endpoint"""
    response = await client.get("/api/v1/hints")
    assert response.status_code == 200
    assert response.json()["objective"] == "Find 12 hidden flags (bugs) in this API"


@pytest.mark.anyio
async def test_flags_list_requires_secret(client: AsyncClient):
    """Проверка что /flags/list требует секрет"""
    response = await client.get("/api/v1/flags/list")
    assert response.status_code == 403


@pytest.mark.anyio
async def test_flags_list_with_secret(client: AsyncClient):
    """Проверка /flags/list с секретом"""
    response = await client.get(
        "/api/v1/flags/list",
        headers={"X-Platform-Secret": "dev-secret"}
    )
    assert response.status_code == 200
    assert response.json()["total_flags"] == 12
