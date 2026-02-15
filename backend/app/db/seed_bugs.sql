-- Начальные данные: Баги (флаги) для миссий
-- Выполнить этот файл ПОСЛЕ seed_missions.sql

-- Баги (флаги) для миссий
-- ВАЖНО: Все флаги должны быть в ВЕРХНЕМ регистре, так как система валидации приводит их к UPPER()
INSERT INTO bugs (id, mission_id, title, description, flag, points, difficulty, sort_order) VALUES
('ecom-t1-001-bug1', 'ecom-t1-001', 'IDOR Negative ID', 'Отрицательный ID возвращает внутренние данные', 'FLAG{IDOR_NEGATIVE_ID_A1B2C3}', 50, 'Easy', 1),
('ecom-t1-001-bug2', 'ecom-t1-001', 'Integer Overflow', 'ID > MAX_INT вызывает переполнение', 'FLAG{INTEGER_OVERFLOW_D4E5F6}', 50, 'Easy', 2),
('ecom-t1-002-bug1', 'ecom-t1-002', 'Wrong Method Allowed', 'POST к read-only endpoint возвращает 200', 'FLAG{METHOD_CONFUSION_ALLOWED}', 50, 'Easy', 1),
('ecom-t1-003-bug1', 'ecom-t1-003', 'Quantity Zero Accepted', 'quantity=0 или отсутствует принимается', 'FLAG{QUANTITY_ZERO_ACCEPTED}', 50, 'Easy', 1),
('ecom-t1-004-bug1', 'ecom-t1-004', 'String Quantity Parsed', 'Строка типа "5шт" парсится как число', 'FLAG{STRING_QUANTITY_PARSED}', 50, 'Easy', 1),
('ecom-t1-005-bug1', 'ecom-t1-005', 'Content-Type Bypass', 'JSON с Content-Type: text/plain принимается', 'FLAG{CONTENT_TYPE_BYPASS}', 50, 'Easy', 1),
('ecom-t1-006-bug1', 'ecom-t1-006', 'Idempotency Ignored', 'Повторный POST с тем же ключом создаёт новый заказ', 'FLAG{IDEMPOTENCY_IGNORED}', 50, 'Easy', 1),
('ecom-t2-001-bug1', 'ecom-t2-001', 'Boundary Off By One', 'quantity=100 проходит', 'FLAG{BOUNDARY_OFF_BY_ONE}', 60, 'Medium', 1),
('ecom-t3-001-bug1', 'ecom-t3-001', 'Delivered Order Cancelled', 'Отмена доставленного заказа', 'FLAG{DELIVERED_ORDER_CANCELLED}', 80, 'Medium', 1),
('ecom-t4-001-bug1', 'ecom-t4-001', 'Order IDOR Exposed', 'Доступ к чужому заказу', 'FLAG{ORDER_IDOR_EXPOSED}', 100, 'Hard', 1),
('ecom-t5-001-bug1', 'ecom-t5-001', 'Promo Bruteforce Allowed', 'Нет rate limit на промокоды', 'FLAG{PROMO_BRUTEFORCE_ALLOWED}', 120, 'Hard', 1),

-- T2 E-Commerce (38 bugs)
('ecom-t2-price-boundary-PRICE_ZERO_FILTER', 'ecom-t2-price-boundary', 'Price Zero Filter', 'GET minPrice=0 maxPrice=0 returns 500', 'FLAG{PRICE_ZERO_FILTER_A1B2C3D4}', 25, 'Medium', 1),
('ecom-t2-price-boundary-PRICE_NEGATIVE_FILTER', 'ecom-t2-price-boundary', 'Price Negative Filter', 'minPrice=-1000 returns all products', 'FLAG{PRICE_NEGATIVE_FILTER_B2C3D4E5}', 30, 'Hard', 2),
('ecom-t2-price-boundary-PRICE_MAX_INT_OVERFLOW', 'ecom-t2-price-boundary', 'Price Max Int Overflow', 'PUT price 9999999999999 causes overflow', 'FLAG{PRICE_MAX_INT_OVERFLOW_C3D4E5F6}', 35, 'Hard', 3),
('ecom-t2-price-boundary-PRICE_FLOAT_PRECISION', 'ecom-t2-price-boundary', 'Price Float Precision', 'cart/items price 99.999 not rounded', 'FLAG{PRICE_FLOAT_PRECISION_D4E5F6G7}', 20, 'Medium', 4),
('ecom-t2-price-boundary-PRICE_CURRENCY_MISMATCH', 'ecom-t2-price-boundary', 'Price Currency Mismatch', 'Different currency summed without conversion', 'FLAG{PRICE_CURRENCY_MISMATCH_E5F6G7H8}', 25, 'Hard', 5),
('ecom-t2-price-boundary-PRICE_DECIMAL_SEPARATOR', 'ecom-t2-price-boundary', 'Price Decimal Separator', 'price "99,99" drops fraction', 'FLAG{PRICE_DECIMAL_SEPARATOR_F6G7H8I9}', 15, 'Easy', 6),
('ecom-t2-quantity-limits-QTY_ZERO_ADD', 'ecom-t2-quantity-limits', 'Qty Zero Add', 'POST cart/items quantity=0 accepted', 'FLAG{QTY_ZERO_ADD_G7H8I9J0}', 25, 'Medium', 1),
('ecom-t2-quantity-limits-QTY_EXCEED_STOCK', 'ecom-t2-quantity-limits', 'Qty Exceed Stock', 'quantity exceeds stock accepted', 'FLAG{QTY_EXCEED_STOCK_H8I9J0K1}', 35, 'Hard', 2),
('ecom-t2-quantity-limits-QTY_MAX_CART_BYPASS', 'ecom-t2-quantity-limits', 'Qty Max Cart Bypass', 'Cart limit 100 bypassed by multiple POST', 'FLAG{QTY_MAX_CART_BYPASS_I9J0K1L2}', 30, 'Hard', 3),
('ecom-t2-quantity-limits-QTY_UPDATE_NEGATIVE', 'ecom-t2-quantity-limits', 'Qty Update Negative', 'PUT cart/items quantity=-5 accepted', 'FLAG{QTY_UPDATE_NEGATIVE_J0K1L2M3}', 25, 'Medium', 4),
('ecom-t2-quantity-limits-QTY_FLOAT_ACCEPTED', 'ecom-t2-quantity-limits', 'Qty Float Accepted', 'quantity 2.7 accepted', 'FLAG{QTY_FLOAT_ACCEPTED_K1L2M3N4}', 25, 'Easy', 5),
('ecom-t2-pagination-abuse-PAGE_NEGATIVE', 'ecom-t2-pagination-abuse', 'Page Negative', 'GET products?page=-1 returns 500', 'FLAG{PAGE_NEGATIVE_L2M3N4O5}', 20, 'Medium', 1),
('ecom-t2-pagination-abuse-PAGE_ZERO', 'ecom-t2-pagination-abuse', 'Page Zero', 'page=0 returns empty off-by-one', 'FLAG{PAGE_ZERO_M3N4O5P6}', 15, 'Easy', 2),
('ecom-t2-pagination-abuse-LIMIT_EXCESSIVE', 'ecom-t2-pagination-abuse', 'Limit Excessive', 'limit=10000 returns 10000 records', 'FLAG{LIMIT_EXCESSIVE_N4O5P6Q7}', 35, 'Hard', 3),
('ecom-t2-pagination-abuse-SORT_INJECTION', 'ecom-t2-pagination-abuse', 'Sort Injection', 'sort=price;DROP TABLE-- SQL injection', 'FLAG{SORT_INJECTION_O5P6Q7R8}', 40, 'Hard', 4),
('ecom-t2-pagination-abuse-SORT_INTERNAL_FIELD', 'ecom-t2-pagination-abuse', 'Sort Internal Field', 'sort=internalCost accepted', 'FLAG{SORT_INTERNAL_FIELD_P6Q7R8S9}', 30, 'Hard', 5),
('ecom-t2-pagination-abuse-OFFSET_OVERFLOW', 'ecom-t2-pagination-abuse', 'Offset Overflow', 'page=99999999 returns 500', 'FLAG{OFFSET_OVERFLOW_Q7R8S9T0}', 20, 'Medium', 6),
('ecom-t2-date-validation-DATE_FUTURE_ORDER', 'ecom-t2-date-validation', 'Date Future Order', 'deliveryDate 2030-12-31 accepted', 'FLAG{DATE_FUTURE_ORDER_R8S9T0U1}', 30, 'Hard', 1),
('ecom-t2-date-validation-DATE_PAST_PROMO', 'ecom-t2-date-validation', 'Date Past Promo', 'promo endDate 2020-01-01 accepted', 'FLAG{DATE_PAST_PROMO_S9T0U1V2}', 25, 'Medium', 2),
('ecom-t2-date-validation-DATE_INVALID_FORMAT', 'ecom-t2-date-validation', 'Date Invalid Format', 'from=31-12-2025 filter ignored', 'FLAG{DATE_INVALID_FORMAT_T0U1V2W3}', 25, 'Medium', 3),
('ecom-t2-date-validation-DATE_TIMEZONE_ABUSE', 'ecom-t2-date-validation', 'Date Timezone Abuse', 'returnDate +14:00 bypasses 14-day limit', 'FLAG{DATE_TIMEZONE_ABUSE_U1V2W3X4}', 35, 'Hard', 4),
('ecom-t2-date-validation-DATE_LEAP_YEAR', 'ecom-t2-date-validation', 'Date Leap Year', 'deliveryDate 2025-02-29 accepted', 'FLAG{DATE_LEAP_YEAR_V2W3X4Y5}', 30, 'Easy', 5),
('ecom-t2-string-length-STRING_OVERLENGTH_NAME', 'ecom-t2-string-length', 'String Overlength Name', 'name 10000 chars truncated', 'FLAG{STRING_OVERLENGTH_NAME_W3X4Y5Z6}', 25, 'Medium', 1),
('ecom-t2-string-length-STRING_EMPTY_REQUIRED', 'ecom-t2-string-length', 'String Empty Required', 'PUT products name="" accepted', 'FLAG{STRING_EMPTY_REQUIRED_X4Y5Z6A7}', 30, 'Hard', 2),
('ecom-t2-string-length-STRING_UNICODE_ESCAPE', 'ecom-t2-string-length', 'String Unicode Escape', 'name with null byte accepted', 'FLAG{STRING_UNICODE_ESCAPE_Y5Z6A7B8}', 25, 'Medium', 3),
('ecom-t2-string-length-STRING_WHITESPACE_ONLY', 'ecom-t2-string-length', 'String Whitespace Only', 'profile name "   " accepted', 'FLAG{STRING_WHITESPACE_ONLY_Z6A7B8C9}', 20, 'Easy', 4),
('ecom-t2-string-length-STRING_SQL_IN_NAME', 'ecom-t2-string-length', 'String SQL In Name', 'name with SQL injection', 'FLAG{STRING_SQL_IN_NAME_A7B8C9D0}', 35, 'Hard', 5),
('ecom-t2-discount-calc-DISCOUNT_OVER_100', 'ecom-t2-discount-calc', 'Discount Over 100', 'Total discount >100% negative total', 'FLAG{DISCOUNT_OVER_100_B8C9D0E1}', 40, 'Hard', 1),
('ecom-t2-discount-calc-DISCOUNT_STACK_BYPASS', 'ecom-t2-discount-calc', 'Discount Stack Bypass', 'Two promos without limit', 'FLAG{DISCOUNT_STACK_BYPASS_C9D0E1F2}', 35, 'Hard', 2),
('ecom-t2-discount-calc-DISCOUNT_EXPIRED_CODE', 'ecom-t2-discount-calc', 'Discount Expired Code', 'EXPIRED2024 applied', 'FLAG{DISCOUNT_EXPIRED_CODE_D0E1F2G3}', 25, 'Medium', 3),
('ecom-t2-discount-calc-DISCOUNT_ROUNDING_ABUSE', 'ecom-t2-discount-calc', 'Discount Rounding Abuse', '0.01 items 50% round to 0', 'FLAG{DISCOUNT_ROUNDING_ABUSE_E1F2G3H4}', 30, 'Hard', 4),
('ecom-t2-discount-calc-DISCOUNT_NEGATIVE_PRICE', 'ecom-t2-discount-calc', 'Discount Negative Price', 'cart/items price -10 accepted', 'FLAG{DISCOUNT_NEGATIVE_PRICE_F2G3H4I5}', 20, 'Medium', 5),
('ecom-t2-discount-calc-DISCOUNT_LOYALTY_OVERFLOW', 'ecom-t2-discount-calc', 'Discount Loyalty Overflow', 'loyaltyPoints 999999999 without check', 'FLAG{DISCOUNT_LOYALTY_OVERFLOW_G3H4I5J6}', 20, 'Hard', 6),
('ecom-t2-search-filter-SEARCH_EMPTY_QUERY', 'ecom-t2-search-filter', 'Search Empty Query', 'search?q= returns 500', 'FLAG{SEARCH_EMPTY_QUERY_H4I5J6K7}', 15, 'Easy', 1),
('ecom-t2-search-filter-SEARCH_SPECIAL_CHARS', 'ecom-t2-search-filter', 'Search Special Chars', 'q with %00%0A%0D returns 500', 'FLAG{SEARCH_SPECIAL_CHARS_I5J6K7L8}', 25, 'Medium', 2),
('ecom-t2-search-filter-FILTER_NONEXISTENT_CATEGORY', 'ecom-t2-search-filter', 'Filter Nonexistent Category', 'category=999999 returns all', 'FLAG{FILTER_NONEXISTENT_CATEGORY_J6K7L8M9}', 30, 'Medium', 3),
('ecom-t2-search-filter-FILTER_BOOLEAN_STRING', 'ecom-t2-search-filter', 'Filter Boolean String', 'inStock=yes filter ignored', 'FLAG{FILTER_BOOLEAN_STRING_K7L8M9N0}', 20, 'Easy', 4),
('ecom-t2-search-filter-SEARCH_NOSQL_INJECTION', 'ecom-t2-search-filter', 'Search NoSQL Injection', 'q={$ne:null} returns all', 'FLAG{SEARCH_NOSQL_INJECTION_L8M9N0O1}', 60, 'Hard', 5),

-- T3 E-Commerce (45 bugs)
-- 4.1 Cart State Manipulation (5 bugs)
('ecom-t3-cart-state-CART_STALE_TOTAL', 'ecom-t3-cart-state', 'Cart Stale Total', 'Multi-step: Cart total cached, not updated after item removal', 'FLAG{CART_STALE_TOTAL_X1Y2Z3A4}', 45, 'Hard', 1),
('ecom-t3-cart-state-CART_PROMO_PERSIST', 'ecom-t3-cart-state', 'Cart Promo Persist', 'Multi-step: Promo code persists after removing eligible items', 'FLAG{CART_PROMO_PERSIST_B2C3D4E5}', 40, 'Hard', 2),
('ecom-t3-cart-state-CART_QUANTITY_CACHE', 'ecom-t3-cart-state', 'Cart Quantity Cache', 'Multi-step: Quantity updated without stock validation', 'FLAG{CART_QUANTITY_CACHE_C3D4E5F6}', 35, 'Hard', 3),
('ecom-t3-cart-state-CART_PRICE_FREEZE', 'ecom-t3-cart-state', 'Cart Price Freeze', 'Multi-step: Frozen price used instead of current catalog price', 'FLAG{CART_PRICE_FREEZE_D4E5F6G7}', 45, 'Hard', 4),
('ecom-t3-cart-state-CART_NEGATIVE_TOTAL', 'ecom-t3-cart-state', 'Cart Negative Total', 'Discount exceeds cart total, negative total allowed', 'FLAG{CART_NEGATIVE_TOTAL_E5F6G7H8}', 30, 'Medium', 5),

-- 4.2 Order State Machine (7 bugs)
('ecom-t3-order-state-STATE_SKIP_PROCESSING', 'ecom-t3-order-state', 'State Skip Processing', 'Skip PROCESSING state, go directly to SHIPPED', 'FLAG{STATE_SKIP_PROCESSING_F6G7H8I9}', 40, 'Hard', 1),
('ecom-t3-order-state-STATE_REVERSE_DELIVERED', 'ecom-t3-order-state', 'State Reverse Delivered', 'Reverse from DELIVERED to previous states', 'FLAG{STATE_REVERSE_DELIVERED_G7H8I9J0}', 40, 'Hard', 2),
('ecom-t3-order-state-STATE_CANCEL_SHIPPED', 'ecom-t3-order-state', 'State Cancel Shipped', 'Cancel shipped order', 'FLAG{STATE_CANCEL_SHIPPED_H8I9J0K1}', 35, 'Hard', 3),
('ecom-t3-order-state-STATE_CANCELLED_RESURRECT', 'ecom-t3-order-state', 'State Cancelled Resurrect', 'Multi-step: Pay cancelled order', 'FLAG{STATE_CANCELLED_RESURRECT_I9J0K1L2}', 40, 'Hard', 4),
('ecom-t3-order-state-STATE_EXPIRED_PAY', 'ecom-t3-order-state', 'State Expired Pay', 'Multi-step: Pay expired order', 'FLAG{STATE_EXPIRED_PAY_J0K1L2M3}', 35, 'Hard', 5),
('ecom-t3-order-state-STATE_DOUBLE_TRANSITION', 'ecom-t3-order-state', 'State Double Transition', 'Allow same state transition twice', 'FLAG{STATE_DOUBLE_TRANSITION_K1L2M3N4}', 25, 'Medium', 6),
('ecom-t3-order-state-STATE_INVALID_INITIAL', 'ecom-t3-order-state', 'State Invalid Initial', 'Invalid initial state transition', 'FLAG{STATE_INVALID_INITIAL_L2M3N4O5}', 15, 'Easy', 7),

-- 4.3 Return & Refund Flow (6 bugs)
('ecom-t3-return-flow-RETURN_PARTIAL_THEN_FULL', 'ecom-t3-return-flow', 'Return Partial Then Full', 'Multi-step: Full return after partial refund exceeds order total', 'FLAG{RETURN_PARTIAL_THEN_FULL_M3N4O5P6}', 45, 'Hard', 1),
('ecom-t3-return-flow-RETURN_REFUND_BEFORE_RECEIVE', 'ecom-t3-return-flow', 'Return Refund Before Receive', 'Multi-step: Refund before item received at warehouse', 'FLAG{RETURN_REFUND_BEFORE_RECEIVE_N4O5P6Q7}', 40, 'Hard', 2),
('ecom-t3-return-flow-RETURN_REOPEN_REJECTED', 'ecom-t3-return-flow', 'Return Reopen Rejected', 'Multi-step: Reopen rejected return', 'FLAG{RETURN_REOPEN_REJECTED_O5P6Q7R8}', 30, 'Medium', 3),
('ecom-t3-return-flow-RETURN_DOUBLE_REFUND', 'ecom-t3-return-flow', 'Return Double Refund', 'Refund same return twice', 'FLAG{RETURN_DOUBLE_REFUND_P6Q7R8S9}', 40, 'Hard', 4),
('ecom-t3-return-flow-RETURN_EXCEED_TOTAL', 'ecom-t3-return-flow', 'Return Exceed Total', 'Return amount exceeds order total', 'FLAG{RETURN_EXCEED_TOTAL_Q7R8S9T0}', 30, 'Hard', 5),
('ecom-t3-return-flow-RETURN_FOOD_ACCEPTED', 'ecom-t3-return-flow', 'Return Food Accepted', 'Food item return accepted', 'FLAG{RETURN_FOOD_ACCEPTED_R8S9T0U1}', 20, 'Medium', 6),

-- 4.4 Inventory & Stock Logic (7 bugs)
('ecom-t3-inventory-STOCK_RESERVE_EXPIRE_CHECKOUT', 'ecom-t3-inventory', 'Stock Reserve Expire Checkout', 'Multi-step: Checkout with expired reservation when stock sold out', 'FLAG{STOCK_RESERVE_EXPIRE_CHECKOUT_S9T0U1V2}', 45, 'Hard', 1),
('ecom-t3-inventory-STOCK_CANCEL_NO_RESTORE', 'ecom-t3-inventory', 'Stock Cancel No Restore', 'Multi-step: Stock not restored after order cancellation', 'FLAG{STOCK_CANCEL_NO_RESTORE_T0U1V2W3}', 35, 'Hard', 2),
('ecom-t3-inventory-STOCK_RETURN_DOUBLE_RESTORE', 'ecom-t3-inventory', 'Stock Return Double Restore', 'Multi-step: Stock restored twice on return', 'FLAG{STOCK_RETURN_DOUBLE_RESTORE_U1V2W3X4}', 35, 'Hard', 3),
('ecom-t3-inventory-STOCK_OVERSELL_RACE', 'ecom-t3-inventory', 'Stock Oversell Race', 'Race condition allows overselling', 'FLAG{STOCK_OVERSELL_RACE_V2W3X4Y5}', 40, 'Hard', 4),
('ecom-t3-inventory-STOCK_NEGATIVE_ADJUST', 'ecom-t3-inventory', 'Stock Negative Adjust', 'Stock adjustment allows negative values', 'FLAG{STOCK_NEGATIVE_ADJUST_W3X4Y5Z6}', 25, 'Medium', 5),
('ecom-t3-inventory-STOCK_RESERVE_EXCEED', 'ecom-t3-inventory', 'Stock Reserve Exceed', 'Reserve more stock than available', 'FLAG{STOCK_RESERVE_EXCEED_X4Y5Z6A7}', 20, 'Medium', 6),
('ecom-t3-inventory-STOCK_PHANTOM_AVAILABLE', 'ecom-t3-inventory', 'Stock Phantom Available', 'Show available stock that is actually reserved', 'FLAG{STOCK_PHANTOM_AVAILABLE_Y5Z6A7B8}', 15, 'Easy', 7),

-- 4.5 Discount & Pricing Logic (7 bugs)
('ecom-t3-discount-DISCOUNT_REMOVE_KEEP_PERCENT', 'ecom-t3-discount', 'Discount Remove Keep Percent', 'Multi-step: Volume discount persists after removing qualifying items', 'FLAG{DISCOUNT_REMOVE_KEEP_PERCENT_Z6A7B8C9}', 45, 'Hard', 1),
('ecom-t3-discount-DISCOUNT_VOLUME_THRESHOLD_ABUSE', 'ecom-t3-discount', 'Discount Volume Threshold Abuse', 'Multi-step: Add expensive item for threshold, remove after discount applied', 'FLAG{DISCOUNT_VOLUME_THRESHOLD_ABUSE_A7B8C9D0}', 40, 'Hard', 2),
('ecom-t3-discount-DISCOUNT_FLASH_SALE_PERSIST', 'ecom-t3-discount', 'Discount Flash Sale Persist', 'Multi-step: Flash sale discount persists after sale ended', 'FLAG{DISCOUNT_FLASH_SALE_PERSIST_B8C9D0E1}', 35, 'Hard', 3),
('ecom-t3-discount-DISCOUNT_STACK_FORBIDDEN', 'ecom-t3-discount', 'Discount Stack Forbidden', 'Stack forbidden discount types (PROMO + LOYALTY)', 'FLAG{DISCOUNT_STACK_FORBIDDEN_C9D0E1F2}', 40, 'Hard', 4),
('ecom-t3-discount-DISCOUNT_EXCEED_50_CAP', 'ecom-t3-discount', 'Discount Exceed 50 Cap', 'Total discount exceeds 50% cap', 'FLAG{DISCOUNT_EXCEED_50_CAP_D0E1F2G3}', 25, 'Hard', 5),
('ecom-t3-discount-DISCOUNT_EXPIRED_PROMO', 'ecom-t3-discount', 'Discount Expired Promo', 'Apply expired promo code', 'FLAG{DISCOUNT_EXPIRED_PROMO_E1F2G3H4}', 20, 'Medium', 6),
('ecom-t3-discount-DISCOUNT_NEGATIVE_TOTAL', 'ecom-t3-discount', 'Discount Negative Total', 'Discount results in negative total', 'FLAG{DISCOUNT_NEGATIVE_TOTAL_F2G3H4I5}', 15, 'Easy', 7),

-- 4.6 Loyalty Program Abuse (6 bugs)
('ecom-t3-loyalty-LOYALTY_CANCEL_KEEP_POINTS', 'ecom-t3-loyalty', 'Loyalty Cancel Keep Points', 'Multi-step: Points not reverted after order cancellation', 'FLAG{LOYALTY_CANCEL_KEEP_POINTS_G3H4I5J6}', 45, 'Hard', 1),
('ecom-t3-loyalty-LOYALTY_RETURN_KEEP_POINTS', 'ecom-t3-loyalty', 'Loyalty Return Keep Points', 'Multi-step: Points not reverted after return', 'FLAG{LOYALTY_RETURN_KEEP_POINTS_H4I5J6K7}', 40, 'Hard', 2),
('ecom-t3-loyalty-LOYALTY_EARN_SPEND_SAME', 'ecom-t3-loyalty', 'Loyalty Earn Spend Same', 'Earn and spend points in same order', 'FLAG{LOYALTY_EARN_SPEND_SAME_I5J6K7L8}', 30, 'Hard', 3),
('ecom-t3-loyalty-LOYALTY_DOUBLE_REDEEM', 'ecom-t3-loyalty', 'Loyalty Double Redeem', 'Redeem same points twice', 'FLAG{LOYALTY_DOUBLE_REDEEM_J6K7L8M9}', 35, 'Hard', 4),
('ecom-t3-loyalty-LOYALTY_EXCEED_50_PERCENT', 'ecom-t3-loyalty', 'Loyalty Exceed 50 Percent', 'Points discount exceeds 50% of order total', 'FLAG{LOYALTY_EXCEED_50_PERCENT_K7L8M9N0}', 20, 'Medium', 5),
('ecom-t3-loyalty-LOYALTY_NEGATIVE_BALANCE', 'ecom-t3-loyalty', 'Loyalty Negative Balance', 'Redeem more points than available, negative balance', 'FLAG{LOYALTY_NEGATIVE_BALANCE_L8M9N0O1}', 20, 'Medium', 6),

-- 4.7 Payment & Checkout Flow (7 bugs)
('ecom-t3-payment-PAYMENT_CART_MODIFIED_AFTER_INIT', 'ecom-t3-payment', 'Payment Cart Modified After Init', 'Multi-step: Cart modified between payment initiation and confirmation', 'FLAG{PAYMENT_CART_MODIFIED_AFTER_INIT_M9N0O1P2}', 45, 'Hard', 1),
('ecom-t3-payment-PAYMENT_DOUBLE_CHARGE', 'ecom-t3-payment', 'Payment Double Charge', 'Charge same payment twice', 'FLAG{PAYMENT_DOUBLE_CHARGE_N0O1P2Q3}', 40, 'Hard', 2),
('ecom-t3-payment-PAYMENT_IDEMPOTENCY_FAIL', 'ecom-t3-payment', 'Payment Idempotency Fail', 'Same idempotency key creates multiple payments', 'FLAG{PAYMENT_IDEMPOTENCY_FAIL_O1P2Q3R4}', 30, 'Hard', 3),
('ecom-t3-payment-PAYMENT_PARTIAL_EXCEED', 'ecom-t3-payment', 'Payment Partial Exceed', 'Partial payment exceeds order total', 'FLAG{PAYMENT_PARTIAL_EXCEED_P2Q3R4S5}', 25, 'Hard', 4),
('ecom-t3-payment-PAYMENT_CANCEL_AFTER_CONFIRM', 'ecom-t3-payment', 'Payment Cancel After Confirm', 'Cancel payment after confirmation', 'FLAG{PAYMENT_CANCEL_AFTER_CONFIRM_Q3R4S5T6}', 20, 'Medium', 5),
('ecom-t3-payment-PAYMENT_COD_LIMIT', 'ecom-t3-payment', 'Payment COD Limit', 'Cash on Delivery exceeds limit', 'FLAG{PAYMENT_COD_LIMIT_R4S5T6U7}', 20, 'Medium', 6),
('ecom-t3-payment-PAYMENT_NEGATIVE_AMOUNT', 'ecom-t3-payment', 'Payment Negative Amount', 'Payment with negative amount accepted', 'FLAG{PAYMENT_NEGATIVE_AMOUNT_S5T6U7V8}', 15, 'Easy', 7)
ON CONFLICT (id) DO NOTHING;
