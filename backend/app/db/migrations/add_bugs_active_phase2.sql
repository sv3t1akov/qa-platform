-- Phase 2: add active column to bugs (preserve user_found_flags history)
-- Run after schema and seed_bugs have been applied.

ALTER TABLE bugs ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT true NOT NULL;

-- Mark dropped T2 and T3 bugs as inactive (do not delete; user_found_flags preserved)
UPDATE bugs SET active = false WHERE id IN (
  -- T2: injection + duplicates (19)
  'ecom-t2-price-boundary-PRICE_NEGATIVE_FILTER',
  'ecom-t2-price-boundary-PRICE_MAX_INT_OVERFLOW',
  'ecom-t2-price-boundary-PRICE_CURRENCY_MISMATCH',
  'ecom-t2-quantity-limits-QTY_ZERO_ADD',
  'ecom-t2-quantity-limits-QTY_EXCEED_STOCK',
  'ecom-t2-pagination-abuse-PAGE_NEGATIVE',
  'ecom-t2-pagination-abuse-SORT_INJECTION',
  'ecom-t2-pagination-abuse-OFFSET_OVERFLOW',
  'ecom-t2-date-validation-DATE_FUTURE_ORDER',
  'ecom-t2-date-validation-DATE_LEAP_YEAR',
  'ecom-t2-string-length-STRING_WHITESPACE_ONLY',
  'ecom-t2-string-length-STRING_SQL_IN_NAME',
  'ecom-t2-string-length-STRING_UNICODE_ESCAPE',
  'ecom-t2-discount-calc-DISCOUNT_OVER_100',
  'ecom-t2-discount-calc-DISCOUNT_NEGATIVE_PRICE',
  'ecom-t2-discount-calc-DISCOUNT_LOYALTY_OVERFLOW',
  'ecom-t2-search-filter-SEARCH_EMPTY_QUERY',
  'ecom-t2-search-filter-SEARCH_SPECIAL_CHARS',
  'ecom-t2-search-filter-SEARCH_NOSQL_INJECTION',
  -- T3: negatives + trim to 17 total (28)
  'ecom-t3-cart-state-CART_NEGATIVE_TOTAL',
  'ecom-t3-order-state-STATE_REVERSE_DELIVERED',
  'ecom-t3-order-state-STATE_CANCELLED_RESURRECT',
  'ecom-t3-order-state-STATE_EXPIRED_PAY',
  'ecom-t3-order-state-STATE_DOUBLE_TRANSITION',
  'ecom-t3-order-state-STATE_INVALID_INITIAL',
  'ecom-t3-return-flow-RETURN_REOPEN_REJECTED',
  'ecom-t3-return-flow-RETURN_DOUBLE_REFUND',
  'ecom-t3-return-flow-RETURN_EXCEED_TOTAL',
  'ecom-t3-return-flow-RETURN_FOOD_ACCEPTED',
  'ecom-t3-inventory-STOCK_NEGATIVE_ADJUST',
  'ecom-t3-inventory-STOCK_RESERVE_EXCEED',
  'ecom-t3-inventory-STOCK_PHANTOM_AVAILABLE',
  'ecom-t3-inventory-STOCK_OVERSELL_RACE',
  'ecom-t3-discount-DISCOUNT_VOLUME_THRESHOLD_ABUSE',
  'ecom-t3-discount-DISCOUNT_FLASH_SALE_PERSIST',
  'ecom-t3-discount-DISCOUNT_EXCEED_50_CAP',
  'ecom-t3-discount-DISCOUNT_EXPIRED_PROMO',
  'ecom-t3-discount-DISCOUNT_NEGATIVE_TOTAL',
  'ecom-t3-loyalty-LOYALTY_RETURN_KEEP_POINTS',
  'ecom-t3-loyalty-LOYALTY_EARN_SPEND_SAME',
  'ecom-t3-loyalty-LOYALTY_EXCEED_50_PERCENT',
  'ecom-t3-loyalty-LOYALTY_NEGATIVE_BALANCE',
  'ecom-t3-payment-PAYMENT_IDEMPOTENCY_FAIL',
  'ecom-t3-payment-PAYMENT_PARTIAL_EXCEED',
  'ecom-t3-payment-PAYMENT_CANCEL_AFTER_CONFIRM',
  'ecom-t3-payment-PAYMENT_COD_LIMIT',
  'ecom-t3-payment-PAYMENT_NEGATIVE_AMOUNT'
);

-- Обновить счётчики багов в миссиях (Phase2: 20 T2, 17 T3)
UPDATE missions SET bugs = 1 WHERE id = 'ecom-t2-001';
UPDATE missions SET bugs = 3 WHERE id = 'ecom-t2-price-boundary';
UPDATE missions SET bugs = 3 WHERE id = 'ecom-t2-quantity-limits';
UPDATE missions SET bugs = 3 WHERE id = 'ecom-t2-pagination-abuse';
UPDATE missions SET bugs = 4 WHERE id = 'ecom-t2-date-validation';
UPDATE missions SET bugs = 3 WHERE id = 'ecom-t2-string-length';
UPDATE missions SET bugs = 3 WHERE id = 'ecom-t2-discount-calc';
UPDATE missions SET bugs = 2 WHERE id = 'ecom-t2-search-filter';

UPDATE missions SET bugs = 1 WHERE id = 'ecom-t3-001';
UPDATE missions SET bugs = 4 WHERE id = 'ecom-t3-cart-state';
UPDATE missions SET bugs = 2 WHERE id = 'ecom-t3-order-state';
UPDATE missions SET bugs = 2 WHERE id = 'ecom-t3-return-flow';
UPDATE missions SET bugs = 3 WHERE id = 'ecom-t3-inventory';
UPDATE missions SET bugs = 2 WHERE id = 'ecom-t3-discount';
UPDATE missions SET bugs = 2 WHERE id = 'ecom-t3-loyalty';
UPDATE missions SET bugs = 2 WHERE id = 'ecom-t3-payment';
