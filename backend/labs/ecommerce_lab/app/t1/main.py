"""
E-Commerce Domain: Return & Refund Pipeline
============================================
Комплексная advanced миссия для QA Training Platform

Миссия: ECOM-ADV-001
Флагов: 12
Сложность: T4-T5

Автор: QA Training Platform
Версия: 1.0.0
"""

import os
import re
import json
import hashlib
import secrets
from pathlib import Path as PathLib
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Request, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator, root_validator, EmailStr
import uvicorn


# ═══════════════════════════════════════════════════════════════════════════════
# КОНФИГУРАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════════

class Settings:
    SESSION_ID: str = os.getenv("SESSION_ID", "local-dev")
    USER_ID: str = os.getenv("USER_ID", "dev-user")
    MISSION_ID: str = os.getenv("MISSION_ID", "ecom-return-refund")
    FLAGS_SEED: str = os.getenv("FLAGS_SEED", "dev_seed_12345")
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "true").lower() == "true"
    
settings = Settings()


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class Marketplace(str, Enum):
    MEGAMART = "MEGAMART"
    PARTNER_STORE = "PARTNER_STORE"
    MOBILE_APP = "MOBILE_APP"

class PaymentMethod(str, Enum):
    CARD = "CARD"
    CASH = "CASH"
    CREDIT = "CREDIT"
    INSTALLMENT = "INSTALLMENT"
    MIXED = "MIXED"

class Currency(str, Enum):
    KZT = "KZT"
    RUB = "RUB"
    USD = "USD"

class Category(str, Enum):
    ELECTRONICS = "ELECTRONICS"
    FASHION = "FASHION"
    HOME = "HOME"
    BEAUTY = "BEAUTY"
    FOOD = "FOOD"
    JEWELRY = "JEWELRY"
    KIDS = "KIDS"
    SPORTS = "SPORTS"
    BOOKS = "BOOKS"
    HEALTH = "HEALTH"
    AUTOMOTIVE = "AUTOMOTIVE"
    GARDEN = "GARDEN"

class Completeness(str, Enum):
    COMPLETE = "COMPLETE"
    MISSING_PARTS = "MISSING_PARTS"
    MISSING_ACCESSORIES = "MISSING_ACCESSORIES"
    MISSING_DOCS = "MISSING_DOCS"

class DamageType(str, Enum):
    COSMETIC = "COSMETIC"
    FUNCTIONAL = "FUNCTIONAL"
    BOTH = "BOTH"

class ReasonCode(str, Enum):
    DEFECTIVE = "DEFECTIVE"
    WRONG_ITEM = "WRONG_ITEM"
    NOT_AS_DESCRIBED = "NOT_AS_DESCRIBED"
    CHANGED_MIND = "CHANGED_MIND"
    ARRIVED_LATE = "ARRIVED_LATE"
    DAMAGED_IN_DELIVERY = "DAMAGED_IN_DELIVERY"
    WRONG_SIZE = "WRONG_SIZE"
    WRONG_COLOR = "WRONG_COLOR"
    ALLERGIC_REACTION = "ALLERGIC_REACTION"
    DUPLICATE_ORDER = "DUPLICATE_ORDER"
    QUALITY_ISSUE = "QUALITY_ISSUE"
    MISSING_PARTS = "MISSING_PARTS"
    EXPIRED = "EXPIRED"
    COUNTERFEIT = "COUNTERFEIT"
    OTHER = "OTHER"

class SellerType(str, Enum):
    MARKETPLACE = "MARKETPLACE"
    MERCHANT = "MERCHANT"
    OFFICIAL_STORE = "OFFICIAL_STORE"
    CROSS_BORDER = "CROSS_BORDER"

class ContractType(str, Enum):
    FBO = "FBO"
    FBS = "FBS"
    DBS = "DBS"

class CustomerType(str, Enum):
    REGULAR = "REGULAR"
    PREMIUM = "PREMIUM"
    VIP = "VIP"
    EMPLOYEE = "EMPLOYEE"
    TESTER = "TESTER"

class ReturnMethod(str, Enum):
    COURIER_PICKUP = "COURIER_PICKUP"
    DROP_OFF_POINT = "DROP_OFF_POINT"
    POST_OFFICE = "POST_OFFICE"
    SELLER_ADDRESS = "SELLER_ADDRESS"
    LOCKER = "LOCKER"

class TimeSlot(str, Enum):
    MORNING_9_12 = "MORNING_9_12"
    DAY_12_15 = "DAY_12_15"
    AFTERNOON_15_18 = "AFTERNOON_15_18"
    EVENING_18_22 = "EVENING_18_22"
    ANY = "ANY"

class RefundMethod(str, Enum):
    ORIGINAL_PAYMENT = "ORIGINAL_PAYMENT"
    BANK_CARD = "BANK_CARD"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    WALLET = "WALLET"
    LOYALTY_POINTS = "LOYALTY_POINTS"

class WalletType(str, Enum):
    KASPI = "KASPI"
    JUSAN = "JUSAN"
    HALYK = "HALYK"
    QIWI = "QIWI"
    PAYPAL = "PAYPAL"

class Channel(str, Enum):
    WEB = "WEB"
    MOBILE_IOS = "MOBILE_IOS"
    MOBILE_ANDROID = "MOBILE_ANDROID"
    CALL_CENTER = "CALL_CENTER"
    CHAT_BOT = "CHAT_BOT"
    API = "API"

class ReturnStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PICKUP_SCHEDULED = "PICKUP_SCHEDULED"
    PICKUP_FAILED = "PICKUP_FAILED"
    IN_TRANSIT = "IN_TRANSIT"
    RECEIVED = "RECEIVED"
    INSPECTION_IN_PROGRESS = "INSPECTION_IN_PROGRESS"
    INSPECTION_PASSED = "INSPECTION_PASSED"
    INSPECTION_FAILED = "INSPECTION_FAILED"
    REFUND_PENDING = "REFUND_PENDING"
    REFUND_PROCESSING = "REFUND_PROCESSING"
    REFUND_COMPLETED = "REFUND_COMPLETED"
    REFUND_FAILED = "REFUND_FAILED"
    EXCHANGE_PROCESSING = "EXCHANGE_PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DISPUTED = "DISPUTED"
    EXPIRED = "EXPIRED"


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS - REQUEST
# ═══════════════════════════════════════════════════════════════════════════════

class OrderInfo(BaseModel):
    orderId: str = Field(..., description="UUID заказа")
    orderDate: date = Field(..., description="Дата заказа")
    orderNumber: Optional[str] = Field(None, description="Номер заказа ORD-XXXXXXXX")
    deliveryDate: Optional[date] = Field(None, description="Дата получения")
    marketplace: Optional[Marketplace] = Marketplace.MEGAMART
    invoiceNumber: Optional[str] = None
    paymentMethod: Optional[PaymentMethod] = PaymentMethod.CARD
    originalCurrency: Optional[Currency] = Currency.KZT

class Discounts(BaseModel):
    promoCode: Optional[str] = None
    promoDiscount: Optional[float] = Field(0, ge=0, le=100)
    loyaltyPointsUsed: Optional[int] = Field(0, ge=0)
    loyaltyDiscount: Optional[float] = Field(0, ge=0)
    sellerDiscount: Optional[float] = Field(0, ge=0, le=100)
    flashSaleDiscount: Optional[float] = Field(0, ge=0, le=100)
    bundleDiscount: Optional[float] = Field(0, ge=0, le=100)
    firstOrderDiscount: Optional[float] = Field(0, ge=0, le=100)
    employeeDiscount: Optional[float] = Field(0, ge=0, le=100)

class ItemCondition(BaseModel):
    opened: Optional[bool] = False
    used: Optional[bool] = False
    damaged: Optional[bool] = False
    damageDescription: Optional[str] = Field(None, max_length=500)
    damageType: Optional[DamageType] = None
    completeness: Optional[Completeness] = Completeness.COMPLETE
    missingItems: Optional[List[str]] = Field(default_factory=list, max_items=10)
    hasOriginalPackaging: Optional[bool] = True
    hasOriginalTags: Optional[bool] = True
    sealIntact: Optional[bool] = True

class ReturnReason(BaseModel):
    code: ReasonCode = Field(..., description="Код причины возврата")
    description: str = Field(..., min_length=50, max_length=2000)
    reportedDefect: Optional[str] = None
    defectConfirmedBySupport: Optional[bool] = False
    supportTicketId: Optional[str] = None

class PhotoLocation(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)

class Evidence(BaseModel):
    photos: List[str] = Field(..., min_items=1, max_items=10)
    videos: Optional[List[str]] = Field(default_factory=list, max_items=3)
    photosTakenAt: Optional[List[datetime]] = None
    photosLocation: Optional[PhotoLocation] = None
    unboxingVideoRequired: Optional[bool] = False
    unboxingVideoUrl: Optional[str] = None

class ReturnItem(BaseModel):
    itemId: str = Field(..., description="UUID позиции")
    productId: str = Field(..., description="SKU товара")
    productName: Optional[str] = None
    barcode: Optional[str] = None
    category: Category
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    isFragile: Optional[bool] = False
    isHazardous: Optional[bool] = False
    quantity: int = Field(..., ge=1, le=100)
    originalQuantity: Optional[int] = Field(None, ge=1)
    unitPrice: int = Field(..., gt=0, description="Цена в тиынах/копейках")
    currency: Optional[Currency] = Currency.KZT
    taxAmount: Optional[int] = Field(0, ge=0)
    taxRate: Optional[float] = Field(12.0, ge=0, le=100)
    discounts: Optional[Discounts] = None
    condition: Optional[ItemCondition] = None
    reason: ReturnReason
    evidence: Evidence

class SellerInfo(BaseModel):
    sellerId: str
    sellerName: Optional[str] = None
    sellerType: Optional[SellerType] = SellerType.MARKETPLACE
    sellerCountry: str = Field(..., min_length=2, max_length=2)
    sellerRating: Optional[float] = Field(None, ge=1.0, le=5.0)
    contractType: Optional[ContractType] = ContractType.FBO
    returnPolicy: Optional[str] = "STANDARD"
    sellerWarehouseId: Optional[str] = None
    sellerContactEmail: Optional[str] = None

class ContactInfo(BaseModel):
    firstName: str = Field(..., min_length=1, max_length=100)
    lastName: str = Field(..., min_length=1, max_length=100)
    middleName: Optional[str] = None
    phone: str = Field(..., pattern=r"^\+7\d{10}$")
    email: EmailStr
    preferredContact: Optional[str] = "PHONE"
    language: Optional[str] = "ru"

class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class PickupAddress(BaseModel):
    country: str = Field(..., min_length=2, max_length=2)
    region: str
    city: str
    district: Optional[str] = None
    street: str
    building: str
    apartment: Optional[str] = None
    floor: Optional[int] = Field(None, ge=1, le=200)
    entrance: Optional[str] = None
    intercom: Optional[str] = None
    postalCode: Optional[str] = Field(None, pattern=r"^\d{6}$")
    coordinates: Optional[Coordinates] = None
    addressNotes: Optional[str] = Field(None, max_length=200)
    addressVerified: Optional[bool] = False

class CustomerInfo(BaseModel):
    customerId: str
    customerType: Optional[CustomerType] = CustomerType.REGULAR
    registrationDate: Optional[date] = None
    verifiedAccount: Optional[bool] = False
    contact: ContactInfo
    pickupAddress: PickupAddress

class PickupInfo(BaseModel):
    preferredDate: date
    preferredTimeSlot: Optional[TimeSlot] = TimeSlot.ANY
    alternativeDate: Optional[date] = None
    alternativeTimeSlot: Optional[TimeSlot] = None
    contactPerson: str
    contactPhone: str = Field(..., pattern=r"^\+7\d{10}$")
    waitingTime: Optional[int] = Field(15, ge=5, le=60)
    callBeforeArrival: Optional[bool] = True

class DropOffInfo(BaseModel):
    pointId: Optional[str] = None
    pointAddress: Optional[str] = None
    pointWorkingHours: Optional[str] = None
    expectedDate: Optional[date] = None

class PackagingInfo(BaseModel):
    originalPackaging: Optional[bool] = True
    needPackaging: Optional[bool] = False
    fragile: Optional[bool] = False
    specialPackaging: Optional[str] = "STANDARD"

class Dimensions(BaseModel):
    weight: int = Field(..., gt=0, description="Вес в граммах")
    length: int = Field(..., gt=0, description="Длина в см")
    width: int = Field(..., gt=0, description="Ширина в см")
    height: int = Field(..., gt=0, description="Высота в см")
    volumetricWeight: Optional[int] = None

class LogisticsInfo(BaseModel):
    returnMethod: ReturnMethod
    preferredCarrier: Optional[str] = "ANY"
    pickup: Optional[PickupInfo] = None
    dropOff: Optional[DropOffInfo] = None
    packaging: Optional[PackagingInfo] = None
    dimensions: Dimensions

class BankCard(BaseModel):
    cardNumber: Optional[str] = None
    cardToken: Optional[str] = None
    cardHolder: Optional[str] = None
    cardType: Optional[str] = None
    cardBank: Optional[str] = None

class BankAccount(BaseModel):
    bankName: Optional[str] = None
    bik: Optional[str] = Field(None, pattern=r"^\d{8,9}$")
    accountNumber: Optional[str] = Field(None, pattern=r"^[A-Z]{2}\d{18,20}$|^\d{20}$")
    recipientName: Optional[str] = None
    recipientIin: Optional[str] = Field(None, pattern=r"^\d{12}$")
    correspondentAccount: Optional[str] = None

class WalletInfo(BaseModel):
    walletType: Optional[WalletType] = None
    walletId: Optional[str] = None
    walletVerified: Optional[bool] = False

class PartialRefund(BaseModel):
    requestedAmount: Optional[int] = None
    reason: Optional[str] = None
    agreedWithSeller: Optional[bool] = False

class RefundInfo(BaseModel):
    preferredMethod: RefundMethod
    bankCard: Optional[BankCard] = None
    bankAccount: Optional[BankAccount] = None
    wallet: Optional[WalletInfo] = None
    partial: Optional[PartialRefund] = None

class Consents(BaseModel):
    personalDataProcessing: bool = Field(..., description="Обязательное согласие")
    thirdPartySharing: Optional[bool] = False
    marketingCommunications: Optional[bool] = False
    qualitySurvey: Optional[bool] = False

class Options(BaseModel):
    exchangeRequested: Optional[bool] = False
    exchangeProductId: Optional[str] = None
    exchangeVariant: Optional[str] = None
    exchangePriceDifference: Optional[int] = None
    urgentProcessing: Optional[bool] = False
    insuranceClaim: Optional[bool] = False
    insuranceClaimNumber: Optional[str] = None
    giftReturn: Optional[bool] = False
    giftGiverId: Optional[str] = None
    consents: Consents

class SourceInfo(BaseModel):
    entryPoint: Optional[str] = "ORDER_DETAILS"
    supportTicketId: Optional[str] = None
    chatSessionId: Optional[str] = None
    agentId: Optional[str] = None
    campaignId: Optional[str] = None

class AuditInfo(BaseModel):
    createdBy: Optional[str] = None
    createdAt: Optional[datetime] = None
    modifiedBy: Optional[str] = None
    modifiedAt: Optional[datetime] = None

class Metadata(BaseModel):
    channel: Optional[Channel] = Channel.WEB
    deviceId: Optional[str] = None
    appVersion: Optional[str] = None
    osVersion: Optional[str] = None
    userAgent: Optional[str] = None
    ipAddress: Optional[str] = None
    sessionId: Optional[str] = None
    requestId: Optional[str] = None
    language: Optional[str] = "ru"
    timezone: Optional[str] = "Asia/Almaty"
    source: Optional[SourceInfo] = None
    audit: Optional[AuditInfo] = None


class ReturnRequest(BaseModel):
    """Полная структура запроса на возврат (127 параметров)"""
    order: OrderInfo
    items: List[ReturnItem] = Field(..., min_items=1, max_items=50)
    seller: SellerInfo
    customer: CustomerInfo
    logistics: LogisticsInfo
    refund: RefundInfo
    options: Options
    metadata: Optional[Metadata] = None


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS - RESPONSE
# ═══════════════════════════════════════════════════════════════════════════════

class CalculationResult(BaseModel):
    itemsSubtotal: int = 0
    itemsWithDiscounts: int = 0
    appliedDiscounts: int = 0
    loyaltyPointsRefund: int = 0
    loyaltyPointsDeduction: int = 0
    shippingRefund: int = 0
    returnShippingFee: int = 0
    restockingFee: int = 0
    restockingFeeRate: float = 0
    insuranceDeduction: int = 0
    partialRefundAdjustment: int = 0
    taxRefund: int = 0
    totalRefund: int = 0
    currency: str = "KZT"
    exchangeRate: Optional[float] = None
    calculatedAt: datetime = None
    validUntil: datetime = None
    # Debug fields for flags
    _discountAnomaly: Optional[str] = None
    categoryOverride: Optional[str] = None

class LogisticsResult(BaseModel):
    carrier: Optional[str] = None
    trackingNumber: Optional[str] = None
    trackingUrl: Optional[str] = None
    pickupDate: Optional[date] = None
    pickupTimeSlot: Optional[str] = None
    pickupStatus: Optional[str] = None
    pickupAttempts: int = 0
    estimatedDeliveryToWarehouse: Optional[date] = None
    actualDeliveryDate: Optional[datetime] = None
    warehouseId: Optional[str] = None
    # Debug fields for flags
    holidayBypass: Optional[str] = None
    crossBorderViolation: Optional[str] = None

class InspectionResult(BaseModel):
    required: bool = False
    status: Optional[str] = None
    inspectedAt: Optional[datetime] = None
    inspectorId: Optional[str] = None
    findings: Optional[Dict[str, Any]] = None
    adjustedRefundAmount: Optional[int] = None
    adjustmentReason: Optional[str] = None
    appealDeadline: Optional[datetime] = None
    # Debug fields for flags
    splitItemBypass: Optional[str] = None

class RefundResult(BaseModel):
    status: Optional[str] = None
    method: Optional[str] = None
    transactionId: Optional[str] = None
    processedAt: Optional[datetime] = None
    expectedAt: Optional[datetime] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    failureReason: Optional[str] = None
    retryCount: int = 0
    # Debug fields for flags
    ownershipWarning: Optional[str] = None

class ExchangeResult(BaseModel):
    requested: bool = False
    status: Optional[str] = None
    newProductId: Optional[str] = None
    newProductName: Optional[str] = None
    priceDifference: Optional[int] = None
    paymentRequired: Optional[bool] = None
    paymentStatus: Optional[str] = None
    newTrackingNumber: Optional[str] = None
    # Debug fields for flags
    categoryMismatch: Optional[str] = None

class EvidenceResult(BaseModel):
    photosValidated: bool = True
    videosValidated: bool = True
    # Debug fields for flags
    videoValidationBug: Optional[str] = None

class DebugInfo(BaseModel):
    processingTimeMs: int = 0
    validationDetails: Dict[str, Any] = {}
    integrationResponses: Dict[str, Any] = {}
    flags: List[str] = []
    restockingOverride: Optional[str] = None
    fraudCheckResult: Optional[str] = None
    loyaltyOverflow: Optional[str] = None

class StatusHistoryEntry(BaseModel):
    status: str
    timestamp: datetime
    actor: str
    reason: Optional[str] = None

class ReturnResponse(BaseModel):
    returnId: str
    returnNumber: str
    status: ReturnStatus
    statusHistory: List[StatusHistoryEntry] = []
    createdAt: datetime
    updatedAt: datetime
    expiresAt: Optional[datetime] = None
    calculation: CalculationResult
    logistics: LogisticsResult
    inspection: InspectionResult
    refund: RefundResult
    exchange: ExchangeResult
    evidence: EvidenceResult
    warnings: List[str] = []
    errors: List[str] = []
    _debug: Optional[DebugInfo] = None


# ═══════════════════════════════════════════════════════════════════════════════
# FLAG REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

class FlagRegistry:
    """Регистр флагов с генерацией уникальных значений"""
    
    def __init__(self, seed: str, mission_id: str):
        self.seed = seed
        self.mission_id = mission_id
        
        self.flags = {
            "return_window_bypass": {
                "id": "FLAG-001",
                "name": "Return Window Bypass",
                "description": "VIP статус после покупки даёт расширенный срок",
                "severity": "HIGH",
                "points": 150,
                "tier": "T4"
            },
            "food_category_inconsistency": {
                "id": "FLAG-002",
                "name": "Food Category Inconsistency",
                "description": "Subcategory с 'Food' проходит проверку",
                "severity": "MEDIUM",
                "points": 100,
                "tier": "T3"
            },
            "discount_double_refund": {
                "id": "FLAG-003",
                "name": "Discount Double Refund",
                "description": "Bundle-скидка не пересчитывается при частичном возврате",
                "severity": "HIGH",
                "points": 150,
                "tier": "T4"
            },
            "restocking_fee_vip_conflict": {
                "id": "FLAG-004",
                "name": "Restocking Fee VIP Conflict",
                "description": "VIP полностью отменяет fee даже для вскрытых товаров",
                "severity": "HIGH",
                "points": 150,
                "tier": "T4"
            },
            "courier_weekend_slip": {
                "id": "FLAG-005",
                "name": "Courier Weekend Slip",
                "description": "Праздничные дни не блокируются",
                "severity": "MEDIUM",
                "points": 100,
                "tier": "T3"
            },
            "crossborder_courier_allowed": {
                "id": "FLAG-006",
                "name": "CrossBorder Courier Allowed",
                "description": "Курьер доступен для cross-border вопреки правилам",
                "severity": "HIGH",
                "points": 150,
                "tier": "T4"
            },
            "fraud_score_bypass": {
                "id": "FLAG-007",
                "name": "Fraud Score Bypass",
                "description": "Отменённые заявки не учитываются в счётчике",
                "severity": "CRITICAL",
                "points": 200,
                "tier": "T5"
            },
            "iin_owner_mismatch": {
                "id": "FLAG-008",
                "name": "IIN Owner Mismatch",
                "description": "ИИН получателя не сверяется с покупателем",
                "severity": "CRITICAL",
                "points": 200,
                "tier": "T5"
            },
            "inspection_skip_threshold": {
                "id": "FLAG-009",
                "name": "Inspection Skip Threshold",
                "description": "Порог 100K проверяется per item, не по сумме",
                "severity": "HIGH",
                "points": 150,
                "tier": "T4"
            },
            "exchange_different_category": {
                "id": "FLAG-010",
                "name": "Exchange Different Category",
                "description": "Обмен между разными категориями проходит",
                "severity": "MEDIUM",
                "points": 100,
                "tier": "T3"
            },
            "video_requirement_bypass": {
                "id": "FLAG-011",
                "name": "Video Requirement Bypass",
                "description": "Невалидные URL видео принимаются",
                "severity": "MEDIUM",
                "points": 100,
                "tier": "T3"
            },
            "loyalty_points_overflow": {
                "id": "FLAG-012",
                "name": "Loyalty Points Overflow",
                "description": "Integer overflow при возврате бонусов",
                "severity": "CRITICAL",
                "points": 200,
                "tier": "T5"
            }
        }
    
    def get_flag(self, bug_key: str) -> str:
        """Генерирует уникальный флаг для данного бага"""
        if bug_key not in self.flags:
            return "FLAG{INVALID_BUG_KEY}"
        
        raw = f"{self.mission_id}:{bug_key}:{self.seed}"
        short_hash = hashlib.sha256(raw.encode()).hexdigest()[:8]
        
        # Формат: FLAG{SNAKE_CASE_NAME}
        flag_name = bug_key.upper()
        return f"FLAG{{{flag_name}}}"
    
    def get_flag_info(self, bug_key: str) -> dict:
        return self.flags.get(bug_key, {})
    
    def get_all_flags(self) -> Dict[str, str]:
        """Возвращает все флаги (для верификации)"""
        return {key: self.get_flag(key) for key in self.flags}


# ═══════════════════════════════════════════════════════════════════════════════
# IN-MEMORY DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

class Database:
    """Простая in-memory база данных для состояния"""
    
    def __init__(self):
        self.returns: Dict[str, dict] = {}
        self.customer_returns_count: Dict[str, int] = {}  # customerId -> count in 30 days
        self.customer_cancelled_count: Dict[str, int] = {}  # Для FLAG-007
        self.customer_type_at_order: Dict[str, CustomerType] = {}  # orderId -> customerType
        self.loyalty_balances: Dict[str, int] = {}  # customerId -> balance
        self.products: Dict[str, dict] = {}  # productId -> product info
        self.products_catalog: Dict[int, dict] = {}  # id 1-1000 для T1 (Ghost Product)
        self.idempotency_request_count: Dict[str, int] = {}  # X-Idempotency-Key -> count (T1.6)

        # Seed some test data
        self._seed_data()
        self._load_products_catalog()

    def _fill_products_catalog_fallback(self):
        """Встроенный каталог 1–1000: генерирует полные данные товаров с реалистичными полями."""
        import random
        
        # Категории и их параметры
        categories = ["ELECTRONICS", "FASHION", "HOME", "BEAUTY", "FOOD"]
        category_ranges = {
            "ELECTRONICS": (50000, 500000),
            "FASHION": (5000, 150000),
            "HOME": (10000, 300000),
            "BEAUTY": (2000, 50000),
            "FOOD": (500, 20000),
        }
        
        for pid in range(1, 1001):
            category = random.choice(categories)
            price_min, price_max = category_ranges[category]
            price = random.randint(price_min, price_max)
            sku = f"{category[:4]}-{pid:03d}"
            rating = round(random.uniform(3.5, 5.0), 1)
            review_count = random.randint(0, 500)
            in_stock = random.random() < 0.75
            
            self.products_catalog[pid] = {
                "id": pid,
                "productId": str(pid),
                "sku": sku,
                "name": f"Product {pid}",
                "description": f"Качественный товар категории {category}",
                "price": price,
                "currency": "KZT",
                "category": category,
                "inStock": in_stock,
                "rating": rating,
                "reviewCount": review_count,
            }

    def _load_products_catalog(self):
        """Сначала заполняем встроенным каталогом (гарантированный ответ), затем опционально подставляем имена из products_1_1000.txt."""
        import random
        
        self._fill_products_catalog_fallback()
        lab_root = PathLib(__file__).resolve().parent.parent
        products_file = lab_root / "products_1_1000.txt"
        if not products_file.exists():
            return
        try:
            raw = products_file.read_text(encoding="utf-8").strip().splitlines()
        except Exception:
            return
        
        # Категории и их параметры для генерации
        categories = ["ELECTRONICS", "FASHION", "HOME", "BEAUTY", "FOOD"]
        category_ranges = {
            "ELECTRONICS": (50000, 500000),
            "FASHION": (5000, 150000),
            "HOME": (10000, 300000),
            "BEAUTY": (2000, 50000),
            "FOOD": (500, 20000),
        }
        
        for line in raw:
            line = line.strip()
            if ":" not in line:
                continue
            idx = line.index(":")
            try:
                pid = int(line[:idx].strip())
                name = line[idx + 1 :].strip()
                if 1 <= pid <= 1000:
                    # Генерируем полные данные, используя имя из файла
                    category = random.choice(categories)
                    price_min, price_max = category_ranges[category]
                    price = random.randint(price_min, price_max)
                    sku = f"{category[:4]}-{pid:03d}"
                    rating = round(random.uniform(3.5, 5.0), 1)
                    review_count = random.randint(0, 500)
                    in_stock = random.random() < 0.75
                    
                    self.products_catalog[pid] = {
                        "id": pid,
                        "productId": str(pid),
                        "sku": sku,
                        "name": name,
                        "description": f"Качественный товар категории {category}",
                        "price": price,
                        "currency": "KZT",
                        "category": category,
                        "inStock": in_stock,
                        "rating": rating,
                        "reviewCount": review_count,
                    }
            except ValueError:
                continue

    def _seed_data(self):
        """Заполняем тестовыми данными"""
        # Тестовые продукты для обмена (returns API)
        self.products = {
            "LAPTOP-PRO-15": {
                "productId": "LAPTOP-PRO-15",
                "name": "Laptop Pro 15",
                "category": Category.ELECTRONICS,
                "price": 450000,
                "available": True
            },
            "DRESS-001": {
                "productId": "DRESS-001",
                "name": "Summer Dress",
                "category": Category.FASHION,
                "price": 25000,
                "available": True
            },
            "PHONE-X": {
                "productId": "PHONE-X",
                "name": "Phone X",
                "category": Category.ELECTRONICS,
                "price": 350000,
                "available": True
            }
        }
        
        # Тестовые типы клиентов на момент заказа (для FLAG-001)
        self.customer_type_at_order = {
            "order-vip-after": CustomerType.REGULAR,  # Был REGULAR, стал VIP
            "order-always-vip": CustomerType.VIP,
        }
        
        # Баланс лояльности
        self.loyalty_balances = {
            "customer-overflow": 2_000_000_000,  # Близко к INT32_MAX
        }

db = Database()


# ═══════════════════════════════════════════════════════════════════════════════
# MOCK EXTERNAL SERVICES
# ═══════════════════════════════════════════════════════════════════════════════

class ExternalServices:
    """Mock внешних сервисов"""
    
    # Праздничные дни Казахстана 2025
    HOLIDAYS_KZ_2025 = [
        date(2025, 1, 1), date(2025, 1, 2),  # Новый год
        date(2025, 3, 8),  # 8 марта
        date(2025, 3, 21), date(2025, 3, 22), date(2025, 3, 23),  # Наурыз
        date(2025, 5, 1),  # День труда
        date(2025, 5, 7),  # День защитника
        date(2025, 5, 9),  # День Победы
        date(2025, 7, 6),  # День столицы
        date(2025, 8, 30),  # День Конституции
        date(2025, 12, 16), date(2025, 12, 17),  # День Независимости
    ]
    
    # Малые города (population < 100,000)
    SMALL_CITIES = ["Аксу", "Балхаш", "Жезказган", "Кентау", "Сатпаев", "Риддер"]
    
    @classmethod
    def is_holiday(cls, check_date: date) -> bool:
        """Проверка на праздничный день"""
        return check_date in cls.HOLIDAYS_KZ_2025
    
    @classmethod
    def is_weekend(cls, check_date: date) -> bool:
        """Проверка на выходной (сб/вс)"""
        return check_date.weekday() >= 5  # 5=Saturday, 6=Sunday
    
    @classmethod
    def is_small_city(cls, city: str) -> bool:
        """Проверка на малый город"""
        return city in cls.SMALL_CITIES
    
    @classmethod
    async def check_fraud_score(cls, customer_id: str) -> dict:
        """Mock проверка антифрод"""
        # БАГ FLAG-007: Считаем только COMPLETED возвраты
        completed_count = db.customer_returns_count.get(customer_id, 0)
        # НЕ учитываем cancelled
        
        return {
            "customerId": customer_id,
            "returnsLast30Days": completed_count,
            "fraudRisk": "HIGH" if completed_count >= 3 else "LOW",
            "autoApprovalAllowed": completed_count < 3
        }
    
    @classmethod
    async def validate_iin(cls, iin: str) -> dict:
        """Mock валидация ИИН"""
        # БАГ FLAG-008: Только форматная проверка, не проверяем владельца
        is_valid_format = bool(re.match(r'^\d{12}$', iin))
        
        # Простая проверка контрольной суммы (упрощённая)
        if is_valid_format:
            # В реальности здесь сложный алгоритм
            checksum_valid = True
        else:
            checksum_valid = False
        
        return {
            "iin": iin,
            "formatValid": is_valid_format,
            "checksumValid": checksum_valid,
            "ownerVerified": False  # БАГ: Не проверяем владельца!
        }
    
    @classmethod
    async def get_product_info(cls, product_id: str) -> Optional[dict]:
        """Получить информацию о продукте"""
        return db.products.get(product_id)
    
    @classmethod
    async def calculate_shipping_cost(cls, dimensions: Dimensions, 
                                      return_method: ReturnMethod,
                                      weight_kg: float) -> int:
        """Расчёт стоимости доставки"""
        base_cost = 1500  # Базовая стоимость
        
        if weight_kg > 30:
            base_cost += 3000  # Доп. стоимость за тяжёлый груз
        
        if return_method == ReturnMethod.COURIER_PICKUP:
            base_cost += 500
        
        return base_cost


# ═══════════════════════════════════════════════════════════════════════════════
# BUSINESS LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

class ReturnProcessor:
    """Основная бизнес-логика обработки возвратов"""
    
    def __init__(self, flag_registry: FlagRegistry):
        self.flags = flag_registry
    
    async def validate_return_window(self, request: ReturnRequest) -> tuple[bool, List[str]]:
        """
        Валидация срока возврата
        
        BR-101: 14 дней для обычных товаров
        BR-102: 7 дней для ELECTRONICS
        BR-108: 30 дней для VIP
        
        БАГ FLAG-001: VIP статус проверяется на момент возврата, не покупки
        """
        warnings = []
        delivery_date = request.order.deliveryDate or request.order.orderDate
        days_since_delivery = (date.today() - delivery_date).days
        
        # Определяем максимальный срок
        max_days = 14  # По умолчанию
        
        # Проверяем категории
        has_electronics = any(item.category == Category.ELECTRONICS for item in request.items)
        if has_electronics:
            max_days = 7  # BR-102
        
        # БАГ FLAG-001: Проверяем VIP статус НА МОМЕНТ ВОЗВРАТА, а не покупки
        if request.customer.customerType == CustomerType.VIP:
            # Проверяем, был ли клиент VIP на момент заказа
            original_type = db.customer_type_at_order.get(request.order.orderId)
            
            if original_type and original_type != CustomerType.VIP:
                # Клиент стал VIP после покупки - это баг!
                max_days = 30  # Даём 30 дней (неправильно!)
                warnings.append(self.flags.get_flag("return_window_bypass"))
                warnings.append("VIP status applied retroactively")
            else:
                max_days = 30  # BR-108
        
        is_valid = days_since_delivery <= max_days
        
        if not is_valid:
            warnings.append(f"Return window expired: {days_since_delivery} days > {max_days} max")
        
        return is_valid, warnings
    
    async def validate_category(self, request: ReturnRequest) -> tuple[bool, List[str]]:
        """
        Валидация категорий товаров
        
        BR-103: FOOD не возвращается
        BR-104: JEWELRY только при браке
        BR-105: BEAUTY только если не вскрыта
        
        БАГ FLAG-002: Проверяется только category, не subcategory
        """
        warnings = []
        errors = []
        
        for item in request.items:
            # BR-103: FOOD
            if item.category == Category.FOOD:
                if item.reason.code != ReasonCode.DEFECTIVE:
                    errors.append(f"Item {item.itemId}: FOOD category cannot be returned")
            
            # БАГ FLAG-002: Не проверяем subcategory на "Food"
            if item.subcategory and "food" in item.subcategory.lower():
                # Должны были отклонить, но пропускаем
                warnings.append(self.flags.get_flag("food_category_inconsistency"))
            
            # BR-104: JEWELRY
            if item.category == Category.JEWELRY:
                if item.reason.code not in [ReasonCode.DEFECTIVE, ReasonCode.COUNTERFEIT]:
                    errors.append(f"Item {item.itemId}: JEWELRY requires defect reason")
            
            # BR-105: BEAUTY
            if item.category == Category.BEAUTY:
                if item.condition and item.condition.opened:
                    if item.reason.code != ReasonCode.DEFECTIVE:
                        errors.append(f"Item {item.itemId}: Opened BEAUTY cannot be returned")
        
        return len(errors) == 0, warnings + errors
    
    async def calculate_refund(self, request: ReturnRequest) -> CalculationResult:
        """
        Расчёт суммы возврата
        
        BR-201: По цене покупки
        BR-202: Промокод НЕ возвращается
        BR-203: Бонусы возвращаются
        BR-206-208: Restocking fee
        
        БАГ FLAG-003: Bundle-скидка не пересчитывается
        БАГ FLAG-004: VIP полностью отменяет restocking fee
        БАГ FLAG-012: Integer overflow бонусов
        """
        result = CalculationResult(
            calculatedAt=datetime.now(),
            validUntil=datetime.now() + timedelta(hours=24)
        )
        
        items_subtotal = 0
        total_promo_discount = 0
        total_loyalty_used = 0
        total_bundle_discount = 0
        restocking_fee = 0
        
        for item in request.items:
            item_total = item.unitPrice * item.quantity
            items_subtotal += item_total
            
            if item.discounts:
                # Промокод (не возвращается по BR-202)
                promo_amount = int(item_total * item.discounts.promoDiscount / 100)
                total_promo_discount += promo_amount
                
                # Бонусы (возвращаются по BR-203)
                total_loyalty_used += item.discounts.loyaltyPointsUsed or 0
                
                # БАГ FLAG-003: Bundle скидка не пересчитывается при частичном возврате
                if item.discounts.bundleDiscount > 0:
                    if item.quantity < (item.originalQuantity or item.quantity):
                        # Частичный возврат - должны пересчитать bundle
                        # НО МЫ ЭТОГО НЕ ДЕЛАЕМ - возвращаем полную скидку!
                        bundle_amount = int(item_total * item.discounts.bundleDiscount / 100)
                        total_bundle_discount += bundle_amount
                        result._discountAnomaly = self.flags.get_flag("discount_double_refund")
            
            # Restocking fee
            if item.reason.code == ReasonCode.CHANGED_MIND:
                fee_rate = 0
                
                # BR-206: 10% для ELECTRONICS
                if item.category == Category.ELECTRONICS:
                    fee_rate = 10
                
                # BR-207: 15% для вскрытых товаров
                if item.condition and item.condition.opened:
                    fee_rate = 15
                
                # БАГ FLAG-004: VIP полностью отменяет fee (даже для вскрытых)
                if request.customer.customerType == CustomerType.VIP:
                    if fee_rate > 0 and item.condition and item.condition.opened:
                        result._debug = result._debug or DebugInfo()
                        result._debug.restockingOverride = self.flags.get_flag("restocking_fee_vip_conflict")
                    fee_rate = 0  # BR-208
                
                restocking_fee += int(item_total * fee_rate / 100)
                result.restockingFeeRate = fee_rate
        
        # Расчёт возврата бонусов
        loyalty_refund = total_loyalty_used
        
        # БАГ FLAG-012: Integer overflow
        customer_balance = db.loyalty_balances.get(request.customer.customerId, 0)
        new_balance = customer_balance + loyalty_refund
        
        if new_balance > 2_147_483_647:  # INT32_MAX
            # Overflow!
            new_balance = new_balance - 4_294_967_296  # Wrap around
            result._debug = result._debug or DebugInfo()
            result._debug.loyaltyOverflow = self.flags.get_flag("loyalty_points_overflow")
        
        # Возврат доставки (только для определённых причин)
        shipping_refund = 0
        refundable_reasons = [ReasonCode.DEFECTIVE, ReasonCode.WRONG_ITEM, ReasonCode.DAMAGED_IN_DELIVERY]
        if any(item.reason.code in refundable_reasons for item in request.items):
            shipping_refund = 1500  # Фиксированная сумма
        
        # Итоговый расчёт
        result.itemsSubtotal = items_subtotal
        result.appliedDiscounts = total_promo_discount + total_bundle_discount
        result.itemsWithDiscounts = items_subtotal - total_promo_discount
        result.loyaltyPointsRefund = loyalty_refund
        result.shippingRefund = shipping_refund
        result.restockingFee = restocking_fee
        result.taxRefund = int(items_subtotal * 0.12)  # 12% НДС
        
        result.totalRefund = (
            result.itemsWithDiscounts - 
            result.restockingFee + 
            result.shippingRefund
        )
        
        return result
    
    async def validate_logistics(self, request: ReturnRequest) -> tuple[bool, LogisticsResult]:
        """
        Валидация логистики
        
        BR-302: Cross-border только DROP_OFF
        BR-303: Нет курьера в выходные
        BR-304: Нет вечернего слота в малых городах
        BR-305: Крупногабарит только COURIER
        BR-306: Дата от завтра до +14 дней
        
        БАГ FLAG-005: Праздники не проверяются
        БАГ FLAG-006: Cross-border проверка неполная
        """
        result = LogisticsResult()
        errors = []
        
        logistics = request.logistics
        
        # БАГ FLAG-006: Проверяем только seller.sellerCountry, не сравниваем с customer
        is_cross_border = request.seller.sellerType == SellerType.CROSS_BORDER
        
        if is_cross_border and logistics.returnMethod == ReturnMethod.COURIER_PICKUP:
            # Должны были отклонить по BR-302, но не проверяем страну покупателя
            if request.seller.sellerCountry != request.customer.pickupAddress.country:
                result.crossBorderViolation = self.flags.get_flag("crossborder_courier_allowed")
                # НЕ отклоняем - это баг!
        
        # Проверка даты для курьера
        if logistics.returnMethod == ReturnMethod.COURIER_PICKUP and logistics.pickup:
            pickup_date = logistics.pickup.preferredDate
            
            # BR-306: Диапазон дат
            tomorrow = date.today() + timedelta(days=1)
            max_date = date.today() + timedelta(days=14)
            
            if pickup_date < tomorrow:
                errors.append("Pickup date must be at least tomorrow")
            if pickup_date > max_date:
                errors.append("Pickup date must be within 14 days")
            
            # BR-303: Проверяем только выходные
            if ExternalServices.is_weekend(pickup_date):
                errors.append("Courier pickup not available on weekends")
            
            # БАГ FLAG-005: НЕ проверяем праздники!
            if ExternalServices.is_holiday(pickup_date):
                # Должны были отклонить, но не делаем этого
                result.holidayBypass = self.flags.get_flag("courier_weekend_slip")
            
            # BR-304: Вечерний слот в малых городах
            if (logistics.pickup.preferredTimeSlot == TimeSlot.EVENING_18_22 and
                ExternalServices.is_small_city(request.customer.pickupAddress.city)):
                errors.append("Evening slot not available in small cities")
            
            result.pickupDate = pickup_date
            result.pickupTimeSlot = logistics.pickup.preferredTimeSlot
        
        # BR-305: Крупногабарит
        dims = logistics.dimensions
        is_oversized = dims.length > 150 or dims.width > 150 or dims.height > 150
        
        if is_oversized and logistics.returnMethod != ReturnMethod.COURIER_PICKUP:
            errors.append("Oversized items require courier pickup")
        
        return len(errors) == 0, result
    
    async def validate_inspection_required(self, request: ReturnRequest) -> InspectionResult:
        """
        Определение необходимости инспекции
        
        BR-401: Обязательна для товаров > 100,000 KZT
        BR-402: Обязательна при damaged=true
        
        БАГ FLAG-009: Проверяется per item, не по сумме
        """
        result = InspectionResult()
        
        # БАГ FLAG-009: Проверяем каждый item отдельно
        total_amount = sum(item.unitPrice * item.quantity for item in request.items)
        max_item_price = max(item.unitPrice for item in request.items)
        
        inspection_required = False
        
        # Проверяем per item (БАГ!)
        if max_item_price > 10000000:  # 100,000 KZT в тиынах
            inspection_required = True
        
        # Но реально сумма может быть > 100,000
        if total_amount > 10000000 and not inspection_required:
            # Обошли порог разбиением на items!
            result.splitItemBypass = self.flags.get_flag("inspection_skip_threshold")
        
        # BR-402: damaged
        if any(item.condition and item.condition.damaged for item in request.items):
            inspection_required = True
        
        result.required = inspection_required
        result.status = "PENDING" if inspection_required else "SKIPPED"
        
        return result
    
    async def validate_exchange(self, request: ReturnRequest) -> ExchangeResult:
        """
        Валидация обмена
        
        BR-701: Только та же категория
        BR-704: Недоступно для cross-border
        
        БАГ FLAG-010: Категория не проверяется
        """
        result = ExchangeResult()
        
        if not request.options.exchangeRequested:
            return result
        
        result.requested = True
        
        # Получаем информацию о товаре для обмена
        exchange_product_id = request.options.exchangeProductId
        if not exchange_product_id:
            result.status = "REJECTED"
            return result
        
        exchange_product = await ExternalServices.get_product_info(exchange_product_id)
        if not exchange_product:
            result.status = "REJECTED"
            return result
        
        result.newProductId = exchange_product_id
        result.newProductName = exchange_product.get("name")
        
        # БАГ FLAG-010: НЕ проверяем категорию!
        original_categories = [item.category for item in request.items]
        new_category = exchange_product.get("category")
        
        if new_category and new_category not in original_categories:
            # Должны были отклонить по BR-701, но не делаем
            result.categoryMismatch = self.flags.get_flag("exchange_different_category")
        
        # Расчёт разницы в цене
        original_total = sum(item.unitPrice * item.quantity for item in request.items)
        new_price = exchange_product.get("price", 0)
        
        result.priceDifference = new_price - original_total
        result.paymentRequired = result.priceDifference > 0
        result.status = "APPROVED"
        
        return result
    
    async def validate_evidence(self, request: ReturnRequest) -> EvidenceResult:
        """
        Валидация доказательств
        
        BR-106: Видео обязательно для > 500,000 KZT
        
        БАГ FLAG-011: Невалидные URL принимаются
        """
        result = EvidenceResult()
        
        total_amount = sum(item.unitPrice * item.quantity for item in request.items)
        video_required = total_amount > 50000000  # 500,000 KZT
        
        for item in request.items:
            evidence = item.evidence
            
            # Проверяем фото
            if not evidence.photos or len(evidence.photos) == 0:
                result.photosValidated = False
            
            # БАГ FLAG-011: Проверяем только длину массива, не валидность URL
            if video_required:
                if evidence.videos:
                    # Проверяем length > 0, но не валидность содержимого!
                    has_video = len(evidence.videos) > 0
                    
                    # Проверяем содержимое (но пропускаем пустые/null)
                    valid_videos = [v for v in evidence.videos if v and v.strip()]
                    
                    if has_video and len(valid_videos) == 0:
                        # Массив не пустой, но все элементы невалидные
                        result.videoValidationBug = self.flags.get_flag("video_requirement_bypass")
                        result.videosValidated = True  # БАГ: считаем валидным!
        
        return result
    
    async def validate_refund_method(self, request: ReturnRequest) -> RefundResult:
        """
        Валидация метода возврата
        
        BR-502: ИИН должен совпадать с покупателем
        
        БАГ FLAG-008: Проверяется только формат ИИН
        """
        result = RefundResult()
        refund = request.refund
        
        result.method = refund.preferredMethod.value
        
        if refund.preferredMethod == RefundMethod.BANK_ACCOUNT:
            if refund.bankAccount and refund.bankAccount.recipientIin:
                # БАГ FLAG-008: Только форматная валидация
                iin_validation = await ExternalServices.validate_iin(refund.bankAccount.recipientIin)
                
                if iin_validation["formatValid"] and iin_validation["checksumValid"]:
                    # Принимаем! Не проверяем, принадлежит ли ИИН покупателю
                    
                    # Проверяем, отличается ли ИИН от ожидаемого
                    # В реальности здесь была бы проверка с данными покупателя
                    expected_iin = "000000000000"  # Placeholder
                    
                    if refund.bankAccount.recipientIin != expected_iin:
                        result.ownershipWarning = self.flags.get_flag("iin_owner_mismatch")
                
                result.status = "PENDING"
            else:
                result.status = "INVALID"
        else:
            result.status = "PENDING"
        
        return result
    
    async def check_fraud(self, request: ReturnRequest) -> tuple[bool, Optional[str]]:
        """
        Антифрод проверка
        
        BR-601: > 3 возвратов за 30 дней
        
        БАГ FLAG-007: Учитываются только COMPLETED
        """
        customer_id = request.customer.customerId
        
        # БАГ FLAG-007: Используем только completed count
        fraud_check = await ExternalServices.check_fraud_score(customer_id)
        
        if not fraud_check["autoApprovalAllowed"]:
            return False, None
        
        # Проверяем, были ли отменённые заявки
        cancelled_count = db.customer_cancelled_count.get(customer_id, 0)
        
        # Если много отменённых + текущая = должны были заблокировать
        total_attempts = fraud_check["returnsLast30Days"] + cancelled_count
        
        if total_attempts >= 3 and fraud_check["autoApprovalAllowed"]:
            # Обошли антифрод через отмены!
            return True, self.flags.get_flag("fraud_score_bypass")
        
        return True, None
    
    async def process_return(self, request: ReturnRequest) -> ReturnResponse:
        """Основной метод обработки возврата"""
        
        # Генерируем ID
        return_id = secrets.token_hex(8)
        return_number = f"RET-{return_id[:8].upper()}"
        
        # Результаты валидации
        warnings = []
        errors = []
        debug_info = DebugInfo() if settings.DEBUG_MODE else None
        
        # 1. Проверка срока возврата
        window_valid, window_warnings = await self.validate_return_window(request)
        warnings.extend(window_warnings)
        
        # 2. Проверка категорий
        category_valid, category_messages = await self.validate_category(request)
        if not category_valid:
            errors.extend([m for m in category_messages if "cannot be returned" in m])
        warnings.extend([m for m in category_messages if "FLAG" in m])
        
        # 3. Расчёт возврата
        calculation = await self.calculate_refund(request)
        if calculation._discountAnomaly:
            warnings.append(calculation._discountAnomaly)
        if debug_info and calculation._debug:
            debug_info.restockingOverride = calculation._debug.restockingOverride
            debug_info.loyaltyOverflow = calculation._debug.loyaltyOverflow
        
        # 4. Валидация логистики
        logistics_valid, logistics_result = await self.validate_logistics(request)
        if logistics_result.holidayBypass:
            warnings.append(logistics_result.holidayBypass)
        if logistics_result.crossBorderViolation:
            warnings.append(logistics_result.crossBorderViolation)
        
        # 5. Определение инспекции
        inspection_result = await self.validate_inspection_required(request)
        if inspection_result.splitItemBypass:
            warnings.append(inspection_result.splitItemBypass)
        
        # 6. Валидация обмена
        exchange_result = await self.validate_exchange(request)
        if exchange_result.categoryMismatch:
            warnings.append(exchange_result.categoryMismatch)
        
        # 7. Валидация доказательств
        evidence_result = await self.validate_evidence(request)
        if evidence_result.videoValidationBug:
            warnings.append(evidence_result.videoValidationBug)
        
        # 8. Валидация метода возврата
        refund_result = await self.validate_refund_method(request)
        if refund_result.ownershipWarning:
            warnings.append(refund_result.ownershipWarning)
        
        # 9. Антифрод проверка
        fraud_passed, fraud_flag = await self.check_fraud(request)
        if fraud_flag:
            if debug_info:
                debug_info.fraudCheckResult = fraud_flag
        
        # Определяем статус
        if errors:
            status = ReturnStatus.REJECTED
        elif not window_valid:
            status = ReturnStatus.REJECTED
        else:
            status = ReturnStatus.APPROVED
        
        # Формируем ответ
        now = datetime.now()
        
        response = ReturnResponse(
            returnId=return_id,
            returnNumber=return_number,
            status=status,
            statusHistory=[
                StatusHistoryEntry(
                    status=status.value,
                    timestamp=now,
                    actor="SYSTEM",
                    reason="Initial processing"
                )
            ],
            createdAt=now,
            updatedAt=now,
            expiresAt=now + timedelta(days=30),
            calculation=calculation,
            logistics=logistics_result,
            inspection=inspection_result,
            refund=refund_result,
            exchange=exchange_result,
            evidence=evidence_result,
            warnings=warnings,
            errors=errors,
            _debug=debug_info
        )
        
        # Сохраняем в "базу"
        db.returns[return_id] = {
            "response": response.dict(),
            "request": request.dict(),
            "created_at": now
        }
        
        return response


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APPLICATION
# ═══════════════════════════════════════════════════════════════════════════════

# Создаём registry и processor
flag_registry = FlagRegistry(settings.FLAGS_SEED, settings.MISSION_ID)
processor = ReturnProcessor(flag_registry)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle handler"""
    print(f"🚀 Starting E-Commerce Return Lab")
    print(f"   Session: {settings.SESSION_ID}")
    print(f"   Mission: {settings.MISSION_ID}")
    print(f"   Flags to find: 12")
    yield
    print("👋 Shutting down lab")


app = FastAPI(
    title="MegaMart Returns API",
    description="""
# E-Commerce Return & Refund Pipeline

Система обработки возвратов товаров маркетплейса MegaMart.

## 🎯 Миссия

Найдите **12 скрытых флагов** в этом API. Флаги имеют формат `FLAG{SNAKE_CASE_NAME}`.

## 📋 Endpoints

- `POST /returns` - Создание заявки на возврат
- `GET /returns/{id}` - Получение статуса заявки
- `GET /returns` - История возвратов
- `POST /returns/{id}/cancel` - Отмена заявки
- `GET /returns/{id}/refund-calculation` - Расчёт суммы возврата

## 💡 Подсказки

1. Изучите бизнес-требования внимательно
2. Проверьте граничные значения
3. Ищите конфликты в требованиях
4. Тестируйте различные комбинации параметров
    """,
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


# ═══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "session_id": settings.SESSION_ID,
        "mission": settings.MISSION_ID,
        "flags_to_find": 12,
        "debug_mode": settings.DEBUG_MODE
    }


@app.get("/api/v1/hints")
async def get_hints():
    """Подсказки для студентов"""
    return {
        "mission": "E-Commerce: Return & Refund Pipeline",
        "objective": "Find 12 hidden flags (bugs) in this API",
        "difficulty": "T4-T5 (Advanced)",
        "categories": {
            "Business Logic": 4,
            "Validation Bypass": 3,
            "Security Issues": 3,
            "Conflicting Requirements": 2
        },
        "hints": [
            "💡 What happens if customer becomes VIP after purchase?",
            "💡 Check subcategory names carefully",
            "💡 How are bundle discounts calculated on partial returns?",
            "💡 Are holidays treated the same as weekends?",
            "💡 What exactly triggers inspection requirement?",
            "💡 Is the IIN owner actually verified?",
        ],
        "endpoints_to_test": [
            "POST /api/v1/returns",
            "GET /api/v1/returns/{id}",
            "POST /api/v1/returns/{id}/cancel",
            "GET /api/v1/returns/{id}/refund-calculation"
        ],
        "documentation": "/docs"
    }


@app.post("/api/v1/returns", response_model=ReturnResponse)
async def create_return(request: ReturnRequest):
    """
    Создание заявки на возврат
    
    Принимает полную структуру ReturnRequest (127 параметров)
    и выполняет валидацию по бизнес-требованиям.
    
    **Найдите скрытые баги в логике валидации!**
    """
    return await processor.process_return(request)


@app.get("/api/v1/returns/{return_id}")
async def get_return(return_id: str):
    """Получение статуса заявки на возврат"""
    if return_id not in db.returns:
        raise HTTPException(status_code=404, detail="Return not found")
    
    return db.returns[return_id]["response"]


@app.get("/api/v1/returns")
async def list_returns(
    customer_id: Optional[str] = Query(None),
    status: Optional[ReturnStatus] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Получение списка возвратов"""
    results = list(db.returns.values())
    
    if customer_id:
        results = [r for r in results 
                   if r["request"].get("customer", {}).get("customerId") == customer_id]
    
    if status:
        results = [r for r in results 
                   if r["response"].get("status") == status.value]
    
    return {
        "total": len(results),
        "limit": limit,
        "offset": offset,
        "items": results[offset:offset + limit]
    }


@app.post("/api/v1/returns/{return_id}/cancel")
async def cancel_return(return_id: str):
    """
    Отмена заявки на возврат
    
    **Обратите внимание:** Отменённые заявки могут влиять на антифрод-проверки
    """
    if return_id not in db.returns:
        raise HTTPException(status_code=404, detail="Return not found")
    
    return_data = db.returns[return_id]
    current_status = return_data["response"]["status"]
    
    # Можно отменить только в определённых статусах
    cancellable_statuses = [
        ReturnStatus.DRAFT.value,
        ReturnStatus.PENDING_REVIEW.value,
        ReturnStatus.APPROVED.value,
        ReturnStatus.PICKUP_SCHEDULED.value
    ]
    
    if current_status not in cancellable_statuses:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel return in status {current_status}"
        )
    
    # Обновляем статус
    return_data["response"]["status"] = ReturnStatus.CANCELLED.value
    return_data["response"]["updatedAt"] = datetime.now().isoformat()
    
    # Увеличиваем счётчик отменённых (для FLAG-007)
    customer_id = return_data["request"].get("customer", {}).get("customerId")
    if customer_id:
        db.customer_cancelled_count[customer_id] = \
            db.customer_cancelled_count.get(customer_id, 0) + 1
    
    return {
        "returnId": return_id,
        "status": ReturnStatus.CANCELLED.value,
        "message": "Return cancelled successfully",
        "note": "Cancelled returns are tracked for fraud prevention"
    }


@app.get("/api/v1/returns/{return_id}/refund-calculation")
async def get_refund_calculation(return_id: str):
    """Получение расчёта суммы возврата"""
    if return_id not in db.returns:
        raise HTTPException(status_code=404, detail="Return not found")
    
    return db.returns[return_id]["response"]["calculation"]


@app.post("/api/v1/returns/{return_id}/decision")
async def make_decision(
    return_id: str,
    decision: str = Body(..., embed=True),
    reason: Optional[str] = Body(None, embed=True)
):
    """Принятие решения по возврату (manual review)"""
    if return_id not in db.returns:
        raise HTTPException(status_code=404, detail="Return not found")
    
    if decision not in ["APPROVE", "REJECT"]:
        raise HTTPException(status_code=400, detail="Invalid decision")
    
    return_data = db.returns[return_id]
    
    new_status = ReturnStatus.APPROVED if decision == "APPROVE" else ReturnStatus.REJECTED
    return_data["response"]["status"] = new_status.value
    return_data["response"]["updatedAt"] = datetime.now().isoformat()
    
    # Добавляем в историю
    return_data["response"]["statusHistory"].append({
        "status": new_status.value,
        "timestamp": datetime.now().isoformat(),
        "actor": "SUPPORT",
        "reason": reason
    })
    
    return {
        "returnId": return_id,
        "status": new_status.value,
        "decidedAt": datetime.now().isoformat()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AUXILIARY ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

# T1 миссии: флаги для тренировочных багов (ECOMMERCE_TRAINING_MISSIONS_T1_T5)
# ВАЖНО: Все флаги должны быть в ВЕРХНЕМ регистре для соответствия системе валидации
T1_FLAG_IDOR_NEGATIVE_ID = "FLAG{IDOR_NEGATIVE_ID_A1B2C3}"
T1_FLAG_INTEGER_OVERFLOW = "FLAG{INTEGER_OVERFLOW_D4E5F6}"
T1_FLAG_METHOD_CONFUSION = "FLAG{METHOD_CONFUSION_ALLOWED}"
T1_FLAG_QUANTITY_ZERO = "FLAG{QUANTITY_ZERO_ACCEPTED}"
T1_FLAG_STRING_QUANTITY = "FLAG{STRING_QUANTITY_PARSED}"
T1_FLAG_CONTENT_TYPE_BYPASS = "FLAG{CONTENT_TYPE_BYPASS}"
T1_FLAG_IDEMPOTENCY_IGNORED = "FLAG{IDEMPOTENCY_IGNORED}"
# T2 флаги
T2_FLAG_BOUNDARY_OFF_BY_ONE = "FLAG{BOUNDARY_OFF_BY_ONE}"


def _resolve_product(product_id: str):
    """
    Логика GET товара по id. Всегда возвращает JSONResponse или выбрасывает HTTPException.
    Синхронная функция без await — ответ сразу, без 502 из-за таймаутов/сериализации.
    
    Новая логика согласно анализу:
    - ID 1-1000: возвращаем реалистичные данные БЕЗ флагов
    - ID > 1000 и <= MAX_INT: нормальная ошибка 404 БЕЗ флага
    - ID < 0: БАГ - возвращаем 200 с внутренними данными + флаг IDOR
    - ID > MAX_INT: БАГ - возвращаем 500 с флагом Overflow
    """
    MAX_INT = 2**31 - 1
    
    try:
        pid = int(product_id)
    except ValueError:
        # Не числовой ID - проверяем в других продуктах
        product = db.products.get(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        # Сериализуем вручную: enum → value, чтобы не ломать ответ
        body = {
            "productId": product.get("productId"),
            "name": product.get("name"),
            "category": getattr(product.get("category"), "value", product.get("category")),
            "price": product.get("price"),
            "available": product.get("available", True),
        }
        return JSONResponse(status_code=200, content=body)

    # Валидный диапазон: возвращаем данные БЕЗ флага
    if 1 <= pid <= 1000:
        product = db.products_catalog.get(pid)
        if product:
            return JSONResponse(status_code=200, content=dict(product))
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Несуществующий ID > 1000: нормальная ошибка БЕЗ флага
    if pid > 1000 and pid <= MAX_INT:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "NOT_FOUND",
                "message": f"Product with id {pid} not found"
            }
        )
    
    # БАГ 1: Отрицательный ID (IDOR)
    if pid < 0:
        return JSONResponse(
            status_code=200,
            content={
                "id": pid,
                "sku": "INTERNAL-001",
                "name": "Test Product (DO NOT USE)",
                "price": 0,
                "category": "INTERNAL",
                "flag": T1_FLAG_IDOR_NEGATIVE_ID,
                "_debug": "Bug: Negative ID not validated"
            }
        )
    
    # БАГ 2: Integer Overflow — per credo flag only on exploitation (200 with wrong data), not in 500
    if pid > MAX_INT:
        # Bug = overflow accepted and returns wrong product (e.g. wraparound id)
        wrong_id = 1
        product = db.products_catalog.get(wrong_id)
        body = dict(product) if product else {"id": wrong_id, "sku": "OVERFLOW", "name": "Wrong product", "price": 0, "category": "INTERNAL"}
        body["flag"] = T1_FLAG_INTEGER_OVERFLOW
        body["_debug"] = "Integer overflow in product_id parsing"
        return JSONResponse(status_code=200, content=body)


@app.get("/api/v1/products/{product_id}")
async def get_product(product_id: str):
    """Получение информации о товаре (префикс /api/v1)."""
    try:
        return _resolve_product(product_id)
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


@app.get("/products/ping")
async def products_ping():
    """Проверка доступности: приложение живое и каталог загружен. 200 = запрос дошёл до приложения."""
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "catalog_size": len(db.products_catalog)},
    )


@app.get("/products/{product_id}")
async def get_product_short(product_id: str):
    """Тот же контракт без префикса /api/v1 — для запросов вида .../products/1111."""
    try:
        return _resolve_product(product_id)
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


# T1.2 Wrong Method: POST к read-only endpoint возвращает 200 вместо 405
def _post_product_response(product_id: str):
    """POST /products/{id} — баг: 200 OK с флагом вместо 405 Method Not Allowed."""
    return JSONResponse(
        status_code=200,
        content={
            "productId": product_id,
            "message": "Use GET for product details",
            "_debug": {"flag": T1_FLAG_METHOD_CONFUSION},
        },
    )


@app.post("/products/{product_id}")
async def post_product_short(product_id: str):
    """T1.2: POST к read-only endpoint — баг: возвращает 200 с флагом вместо 405."""
    return _post_product_response(product_id)


@app.post("/api/v1/products/{product_id}")
async def post_product(product_id: str):
    """T1.2: POST к read-only endpoint (префикс /api/v1)."""
    return _post_product_response(product_id)


# T1.3–T1.5: POST /cart/items — баги: quantity 0/отсутствует, строка "5шт", Content-Type: text/plain
def _parse_quantity_from_string(val) -> tuple[int | None, bool]:
    """Парсит quantity: если строка вроде '5' или '5шт', возвращает (int, True) для флага 1.4."""
    if isinstance(val, int):
        return val, False
    if isinstance(val, str) and val.strip():
        s = val.strip()
        num = ""
        for c in s:
            if c.isdigit():
                num += c
            else:
                break
        if num:
            return int(num), True  # parsed from string
    return None, False


async def _handle_cart_items(request: Request) -> JSONResponse:
    """Общий обработчик POST /cart/items с багами T1.3 (quantity 0/нет), T1.4 (строка), T1.5 (Content-Type). Один флаг по приоритету: 1.5 > 1.3 > 1.4."""
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    is_text_plain = content_type == "text/plain"

    try:
        body = await request.json()
    except Exception:
        body = {}

    product_id = body.get("productId", "")
    quantity_raw = body.get("quantity")
    warnings = []
    parsed_quantity = None
    response_headers = {}
    quantity_used = 0

    # Validate: negative quantity should be rejected (before bug checks)
    if isinstance(quantity_raw, (int, float)) and quantity_raw < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")
    
    # Определяем quantity_used и какой флаг отдавать (один по приоритету)
    if "quantity" not in body or quantity_raw is None:
        quantity_used = 0
        flag_1_3 = True
        flag_1_4 = False
    elif quantity_raw == 0:
        quantity_used = 0
        flag_1_3 = True
        flag_1_4 = False
    else:
        parsed, from_string = _parse_quantity_from_string(quantity_raw)
        if from_string and parsed is not None:
            parsed_quantity = parsed
            quantity_used = parsed
            flag_1_3 = False
            flag_1_4 = True
        elif isinstance(quantity_raw, (int, float)):
            quantity_used = int(quantity_raw) if quantity_raw == int(quantity_raw) else int(quantity_raw)
            flag_1_3 = quantity_used == 0
            flag_1_4 = False
        else:
            quantity_used = 0
            flag_1_3 = True
            flag_1_4 = False

    # T2.1: Boundary Off By One - quantity=100 проходит валидацию (должно быть <= 99)
    # Проверяем только если quantity валидное число и не 0, не строка, не text/plain
    if not is_text_plain and isinstance(quantity_raw, (int, float)) and quantity_raw == 100:
        content = {
            "productId": product_id,
            "quantity": 100,
            "added": True,
            "flag": T2_FLAG_BOUNDARY_OFF_BY_ONE,
            "_debug": "Boundary off-by-one: quantity=100 accepted (should be <= 99)"
        }
        return JSONResponse(status_code=201, content=content, headers=response_headers)

    # Приоритет: T1.5 (Content-Type) > T1.3 (zero) > T1.4 (string parsed)
    if is_text_plain:
        response_headers["X-Content-Warning"] = T1_FLAG_CONTENT_TYPE_BYPASS
    elif flag_1_3:
        warnings.append(T1_FLAG_QUANTITY_ZERO)
    elif flag_1_4:
        warnings.append(T1_FLAG_STRING_QUANTITY)

    content = {
        "productId": product_id,
        "quantity": quantity_used,
        "added": True,
    }
    if warnings:
        content["warnings"] = warnings
    if parsed_quantity is not None:
        content["parsedQuantity"] = parsed_quantity
        content["parsedQuantityFlag"] = T1_FLAG_STRING_QUANTITY

    return JSONResponse(status_code=200, content=content, headers=response_headers)


@app.post("/cart/items")
async def post_cart_items_short(request: Request):
    """T1.3–T1.5: POST /cart/items без префикса /api/v1."""
    return await _handle_cart_items(request)


@app.post("/api/v1/cart/items")
async def post_cart_items(request: Request):
    """T1.3–T1.5: POST /cart/items с префиксом /api/v1."""
    return await _handle_cart_items(request)


# T1.6: POST /orders — баг: idempotency key игнорируется, второй запрос создаёт новый заказ и отдаёт флаг
async def _handle_orders(request: Request) -> JSONResponse:
    """POST /orders: тело cartId; заголовок X-Idempotency-Key. Баг: ключ не используется, при повторном запросе — новый orderId и _debug.flag."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    cart_id = body.get("cartId", "")
    idem_key = request.headers.get("X-Idempotency-Key", "").strip()

    order_id = f"ord-{secrets.token_hex(6)}"
    count = db.idempotency_request_count.get(idem_key, 0) + 1
    db.idempotency_request_count[idem_key] = count

    content = {
        "orderId": order_id,
        "cartId": cart_id,
        "status": "CREATED",
    }
    if count >= 2 and idem_key:
        content["_debug"] = {"flag": T1_FLAG_IDEMPOTENCY_IGNORED}

    return JSONResponse(status_code=200, content=content)


@app.post("/orders")
async def post_orders_short(request: Request):
    """T1.6: POST /orders без префикса /api/v1."""
    return await _handle_orders(request)


@app.post("/api/v1/orders")
async def post_orders(request: Request):
    """T1.6: POST /orders с префиксом /api/v1."""
    return await _handle_orders(request)


@app.get("/api/v1/logistics/slots")
async def get_logistics_slots(
    date_from: date = Query(...),
    date_to: date = Query(...),
    city: str = Query(...)
):
    """Получение доступных слотов для курьера"""
    slots = []
    current = date_from
    
    while current <= date_to:
        if not ExternalServices.is_weekend(current):
            # БАГ: Не проверяем праздники!
            day_slots = [
                TimeSlot.MORNING_9_12,
                TimeSlot.DAY_12_15,
                TimeSlot.AFTERNOON_15_18
            ]
            
            # Вечерний слот только для больших городов
            if not ExternalServices.is_small_city(city):
                day_slots.append(TimeSlot.EVENING_18_22)
            
            slots.append({
                "date": current.isoformat(),
                "isHoliday": ExternalServices.is_holiday(current),  # Показываем, но не блокируем!
                "slots": [s.value for s in day_slots]
            })
        
        current += timedelta(days=1)
    
    return {"slots": slots}


@app.get("/api/v1/customers/{customer_id}/returns/stats")
async def get_customer_return_stats(customer_id: str):
    """Статистика возвратов клиента"""
    completed = db.customer_returns_count.get(customer_id, 0)
    cancelled = db.customer_cancelled_count.get(customer_id, 0)
    
    return {
        "customerId": customer_id,
        "completedReturns": completed,
        "cancelledReturns": cancelled,
        "totalAttempts": completed + cancelled,
        "fraudRisk": "HIGH" if completed >= 3 else "LOW",
        # Обратите внимание: fraudRisk учитывает только completed!
        "note": "Fraud score is based on completed returns only"
    }


@app.post("/api/v1/fraud/validate-iin")
async def validate_iin(iin: str = Body(..., embed=True)):
    """Валидация ИИН"""
    result = await ExternalServices.validate_iin(iin)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# FLAG VERIFICATION (для платформы)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/flags/verify")
async def verify_flag(
    flag: str = Body(..., embed=True),
    x_platform_secret: str = Header(None)
):
    """
    Верификация флага (для платформы)
    
    Требует секретный заголовок X-Platform-Secret
    """
    expected_secret = os.getenv("PLATFORM_SECRET", "dev-secret")
    
    if x_platform_secret != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid platform secret")
    
    all_flags = flag_registry.get_all_flags()
    
    for key, value in all_flags.items():
        if flag == value:
            flag_info = flag_registry.get_flag_info(key)
            return {
                "valid": True,
                "flag": value,
                "bug_key": key,
                "info": flag_info
            }
    
    return {
        "valid": False,
        "flag": flag,
        "message": "Flag not recognized"
    }


@app.get("/api/v1/flags/list")
async def list_flags(x_platform_secret: str = Header(None)):
    """
    Список всех флагов (только для платформы)
    """
    expected_secret = os.getenv("PLATFORM_SECRET", "dev-secret")
    
    if x_platform_secret != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid platform secret")
    
    return {
        "mission": settings.MISSION_ID,
        "total_flags": 12,
        "flags": [
            {
                "key": key,
                "flag": flag_registry.get_flag(key),
                "info": flag_registry.get_flag_info(key)
            }
            for key in flag_registry.flags
        ]
    }


# ═══════════════════════════════════════════════════════════════════════════════
# TEST DATA SEEDING
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/test/seed-data")
async def seed_test_data(scenario: str = Body("default", embed=True)):
    """
    Создание тестовых данных для различных сценариев
    """
    if scenario == "vip_after_purchase":
        # Для FLAG-001
        db.customer_type_at_order["order-test-001"] = CustomerType.REGULAR
        return {"message": "Seeded VIP after purchase scenario", "orderId": "order-test-001"}
    
    elif scenario == "high_return_count":
        # Для FLAG-007
        db.customer_cancelled_count["customer-fraud-test"] = 5
        return {"message": "Seeded high cancelled count", "customerId": "customer-fraud-test"}
    
    elif scenario == "loyalty_overflow":
        # Для FLAG-012
        db.loyalty_balances["customer-overflow-test"] = 2_100_000_000
        return {"message": "Seeded near-overflow loyalty balance", "customerId": "customer-overflow-test"}
    
    return {"message": "Unknown scenario", "available": ["vip_after_purchase", "high_return_count", "loyalty_overflow"]}


@app.delete("/api/v1/test/reset")
async def reset_test_data():
    """Сброс тестовых данных"""
    db.returns.clear()
    db.customer_returns_count.clear()
    db.customer_cancelled_count.clear()
    db._seed_data()
    return {"message": "Test data reset successfully"}


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8080)),
        reload=os.getenv("ENV", "dev") == "dev"
    )
