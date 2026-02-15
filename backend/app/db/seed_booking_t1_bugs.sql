-- Booking T1 Bugs (Flags)
-- Based on BOOKING_T1_SPEC_v2.md
-- Execute this file AFTER seed_booking_t1_missions.sql
-- IMPORTANT: All flags must be in UPPERCASE, as the validation system converts them to UPPER()

INSERT INTO bugs (id, mission_id, title, description, flag, points, difficulty, sort_order, active) VALUES
-- Mission 1: Properties & Rooms API (3 flags)
('book-t1-properties-NEGATIVE_ID', 'book-t1-properties', 'Negative ID', 'Отрицательный ID обходит валидацию и возвращает тестовые данные', 'FLAG{NEGATIVE_ID_3f7a9c2d}', 100, 'Easy', 1, true),
('book-t1-properties-BOUNDARY_OVERFLOW', 'book-t1-properties', 'Boundary Overflow', 'Очень большие числа вызывают ошибку БД вместо валидации', 'FLAG{BOUNDARY_OVERFLOW_8b4e2f1a}', 100, 'Easy', 2, true),
('book-t1-properties-HIDDEN_FIELDS', 'book-t1-properties', 'Hidden Fields', 'Ответ содержит внутренние бизнес-данные (себестоимость, маржа)', 'FLAG{HIDDEN_FIELDS_9a1f5d3c}', 100, 'Easy', 3, true),

-- Mission 2: Availability API (4 flags)
('book-t1-availability-DATE_PAST', 'book-t1-availability', 'Date Past', 'Даты в прошлом принимаются без валидации', 'FLAG{DATE_PAST_4f8a2c6e}', 100, 'Easy', 1, true),
('book-t1-availability-DATE_REVERSED', 'book-t1-availability', 'Date Reversed', 'checkout раньше checkin не валидируется, отрицательный расчёт', 'FLAG{DATE_REVERSED_7d3b9a1f}', 100, 'Easy', 2, true),
('book-t1-availability-ZERO_DURATION', 'book-t1-availability', 'Zero Duration', 'Нулевая длительность (одинаковые даты) принимается', 'FLAG{ZERO_DURATION_1c5e9b3d}', 100, 'Easy', 3, true),
('book-t1-availability-CAPACITY_EXCEEDED', 'book-t1-availability', 'Capacity Exceeded', 'Количество гостей превышает вместимость номера, но принимается', 'FLAG{CAPACITY_EXCEEDED_9d1a5f7e}', 100, 'Easy', 4, true),

-- Mission 3: Bookings API (4 flags)
('book-t1-bookings-MISSING_REQUIRED', 'book-t1-bookings', 'Missing Required', 'Пустое обязательное поле (roomId) принимается', 'FLAG{MISSING_REQUIRED_5b1e3c9a}', 100, 'Easy', 1, true),
('book-t1-bookings-PRICE_OVERRIDE', 'book-t1-bookings', 'Price Override', 'Цена от клиента принимается вместо серверного расчёта', 'FLAG{PRICE_OVERRIDE_2f6a8d4e}', 100, 'Easy', 2, true),
('book-t1-bookings-WRONG_STATUS_CODE', 'book-t1-bookings', 'Wrong Status Code', 'Ошибка валидации возвращает 200 вместо 400', 'FLAG{WRONG_STATUS_CODE_6c2d8a4f}', 100, 'Easy', 3, true),
('book-t1-bookings-IDOR_ACCESS', 'book-t1-bookings', 'IDOR Access', 'Доступ к чужому бронированию без проверки прав', 'FLAG{IDOR_ACCESS_8c4e2a6f}', 100, 'Easy', 4, true),

-- Mission 4: Guest Profile API (2 flags)
('book-t1-guests-TYPE_COERCION', 'book-t1-guests', 'Type Coercion', 'Нестроковые значения неявно преобразуются в строки без валидации', 'FLAG{TYPE_COERCION_4a3c7e9b}', 100, 'Easy', 1, true),
('book-t1-guests-INVALID_FORMAT', 'book-t1-guests', 'Invalid Format', 'Невалидный формат email принимается без проверки', 'FLAG{INVALID_FORMAT_1b5e9c3f}', 100, 'Easy', 2, true)

ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    flag = EXCLUDED.flag,
    points = EXCLUDED.points,
    difficulty = EXCLUDED.difficulty,
    sort_order = EXCLUDED.sort_order,
    active = EXCLUDED.active;
