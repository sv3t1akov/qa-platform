-- Начальные данные для QA Platform

-- Домены
INSERT INTO domains (id, name, icon, description, sort_order) VALUES
('fintech', 'Fintech', '💳', 'Банковские API, платежи, кошельки', 1),
('ecommerce', 'E-Commerce', '🛒', 'Интернет-магазины, корзины, заказы', 2),
('booking', 'Booking', '🏨', 'Бронирование отелей, билетов, услуг', 3),
('marketplace', 'Marketplace', '🏪', 'Маркетплейсы, продавцы, товары', 4),
('healthcare', 'Healthcare', '🏥', 'Медицинские системы, записи, рецепты', 5),
('social', 'Social Media', '📱', 'Социальные сети, посты, профили', 6)
ON CONFLICT (id) DO NOTHING;

-- Миссии E-Commerce (из main.py)
-- Используем переменную для base_url
-- ВАЖНО: Если DO блок не выполнился, используйте seed_missions.sql отдельно
DO $$
DECLARE
    ecom_lab_url VARCHAR := 'https://qa-lab-ecom-return-refund.fly.dev';
BEGIN
    -- Используем $$ для экранирования многострочных строк
    -- T1: Mission 1.1 "Призрачный товар" (Ghost Product)
    INSERT INTO missions (
        id, domain_id, tier, title, description, difficulty, estimated_time, 
        points, bugs, endpoint, base_url, theory_title, theory_content, hints, task_description, request_body_example, sort_order
    ) VALUES (
        'ecom-t1-001', 'ecommerce', 'T1', 'Призрачный товар (Ghost Product)',
        'Проверка корректных HTTP status codes для отсутствующих ресурсов.',
        'Beginner', '15 мин', 50, 2,
        '/products/{id}', ecom_lab_url,
        'Призрачный товар — HTTP Status Codes',
        'Почему возникает ошибка

HTTP-статус коды — это стандартизированный способ сообщить клиенту о результате запроса. Однако разработчики часто:

— Используют generic-обработчики: один обработчик для всех случаев возвращает 200 OK, даже когда ресурс не найден
— Путают «пустой результат» с «отсутствием ресурса»: запрос выполнился успешно (нашли 0 записей), но это не означает, что ресурс существует
— Копируют код без адаптации: шаблонный код из другого endpoint''а, где 200 был уместен

Почему это допускается

Фактор — Описание:
Спешка в разработке — «Работает — не трогай», статус-код кажется мелочью
Отсутствие спецификации — Нет чёткого контракта API, каждый разработчик решает по-своему
Недостаток тестирования — Тесты проверяют happy path, но не edge cases
Frontend компенсирует — Клиентское приложение само проверяет пустое тело

Влияние на продукт

— Клиентские приложения: неправильная обработка ошибок, кэширование «пустых» ответов как валидных, сломанная логика retry
— SEO и индексация: поисковики индексируют несуществующие страницы, дубликаты контента
— Мониторинг: невозможно отличить ошибки от успеха, ложные метрики
— Интеграции: партнёры получают некорректные данные, цепочка ошибок в микросервисах

Отраслевая статистика

По данным исследований API-качества, 23% публичных API возвращают некорректные HTTP-статусы для отсутствующих ресурсов. Это приводит к увеличению времени отладки интеграций на 40%.',
        ARRAY[
            'Вспомни, какой статус-код должен возвращаться для несуществующего ресурса',
            'Подумай о граничных и нестандартных значениях идентификатора (вне ожидаемого диапазона)',
            'Скрытые баги: система может некорректно обрабатывать граничные случаи для id — найдите флаги и зарегистрируйте на странице Flags.'
        ],
        'Интернет-магазин электроники запустил новый каталог товаров. Клиенты жалуются, что при попытке открыть несуществующий товар система ведёт себя странно. Проверьте корректность обработки запросов к несуществующим ресурсам.

Ожидаемое поведение: несуществующий товар → 404 Not Found. Для id от 1 до 1000 API возвращает соответствующий товар из каталога. Для id вне допустимого диапазона — корректная ошибка без раскрытия внутренних данных.',
        NULL,
        1
    ) ON CONFLICT (id) DO NOTHING;

    -- T1: Mission 1.2 "Метод не тот" (Wrong Method)
    INSERT INTO missions (
        id, domain_id, tier, title, description, difficulty, estimated_time,
        points, bugs, endpoint, base_url, theory_title, theory_content, hints, task_description, request_body_example, sort_order
    ) VALUES (
        'ecom-t1-002', 'ecommerce', 'T1', 'Метод не тот (Wrong Method)',
        'Проверка допустимых HTTP методов для endpoints.',
        'Beginner', '15 мин', 50, 1,
        '/products/{id}', ecom_lab_url,
        'Метод не тот — HTTP Methods Validation',
        'Почему возникает ошибка

REST API предполагает семантическое использование HTTP-методов (GET для чтения, POST для создания и т.д.). Ошибки возникают когда: роутинг настроен слишком широко, framework по умолчанию принимает всё, middleware пропускает проверку метода, legacy-клиенты использовали POST для всего.

Почему это допускается

Разработчики рассуждают: «Какая разница, каким методом пришёл запрос?» Это игнорирует семантику кэширования (GET кэшируется, POST — нет), безопасность (CSRF по-разному), идемпотентность, логирование и аудит.

Влияние на продукт

Кэширование: CDN не кэширует POST. CSRF-уязвимости. Непредсказуемость. OpenAPI не соответствует реальности. Невозможно понять, что делал пользователь.',
        ARRAY[
            'Вспомни, какие HTTP-методы допустимы для read-only ресурсов и как сервер сообщает о недопустимом методе',
            'Подумай, как API должен реагировать на «не тот» метод к тому же пути',
            'Скрытый баг: API может принять неожиданный метод и вернуть 200 с флагом — найдите и зарегистрируйте флаг на странице Flags.'
        ],
        'Разработчики утверждают, что API строго следует REST-конвенциям. Проверьте, правильно ли обрабатываются некорректные HTTP-методы.

Ожидаемое поведение: POST к read-only endpoint → 405 Method Not Allowed.',
        '{"any": "data"}',
        2
    ) ON CONFLICT (id) DO NOTHING;

    -- T1: Mission 1.3 "Пустая корзина" (Empty Cart)
    INSERT INTO missions (
        id, domain_id, tier, title, description, difficulty, estimated_time,
        points, bugs, endpoint, base_url, theory_title, theory_content, hints, task_description, request_body_example, sort_order
    ) VALUES (
        'ecom-t1-003', 'ecommerce', 'T1', 'Пустая корзина (Empty Cart)',
        'Проверка обязательных полей (required fields validation).',
        'Beginner', '15 мин', 50, 1,
        '/cart/items', ecom_lab_url,
        'Пустая корзина — Required Fields Validation',
        'Почему возникает ошибка

Валидация обязательных полей часто пропускается из-за спешки, отсутствия спецификации, или неполного тестирования.',
        ARRAY[
            'Вспомни, как проверяются обязательные поля и минимальные значения в API',
            'Подумай о разнице между отсутствующим полем и нулевым значением',
            'Скрытый баг: API может принять невалидное или отсутствующее значение и вернуть 201 с флагом — найдите и зарегистрируйте на странице Flags.'
        ],
        'Функция добавления товара в корзину должна валидировать все обязательные поля. Проверьте, что система корректно отклоняет запросы с отсутствующими или недопустимыми данными.

Ожидаемое поведение: запрос с отсутствующими обязательными полями или недопустимыми значениями → 400 Bad Request.',
        '{"productId": "123", "quantity": 1}',
        3
    ) ON CONFLICT (id) DO NOTHING;

    -- T1: Mission 1.4 "Типы данных" (Data Types)
    INSERT INTO missions (
        id, domain_id, tier, title, description, difficulty, estimated_time,
        points, bugs, endpoint, base_url, theory_title, theory_content, hints, task_description, request_body_example, sort_order
    ) VALUES (
        'ecom-t1-004', 'ecommerce', 'T1', 'Типы данных (Data Types)',
        'Type coercion и строгая валидация типов.',
        'Beginner', '15 мин', 50, 1,
        '/cart/items', ecom_lab_url,
        'Типы данных — Type Coercion',
        'Почему возникает ошибка

Слабая типизация и автоматическое преобразование типов могут привести к неожиданному поведению.',
        ARRAY[
            'Вспомни, как контракт API задаёт типы полей (integer, string) и что происходит при несоответствии',
            'Подумай о неявном преобразовании типов в разных языках и фреймворках',
            'Скрытый баг: API может принять значение неверного типа и вернуть успешный ответ — найдите и зарегистрируйте на странице Flags.'
        ],
        'В endpoint добавления в корзину (POST /cart/items) поле quantity по контракту должно быть целым числом (integer). Партнёры иногда отправляют данные в неверном формате. Ожидается строгая валидация типов.

Ожидаемое поведение: запрос с некорректным типом для обязательных полей → 400 Bad Request. Корректный запрос с ожидаемыми типами → 201 Created.',
        '{"productId": "123", "quantity": 5}',
        4
    ) ON CONFLICT (id) DO NOTHING;

    -- T1: Mission 1.5 "Content-Type игнорируется" (Content-Type Bypass)
    INSERT INTO missions (
        id, domain_id, tier, title, description, difficulty, estimated_time,
        points, bugs, endpoint, base_url, theory_title, theory_content, hints, task_description, request_body_example, sort_order
    ) VALUES (
        'ecom-t1-005', 'ecommerce', 'T1', 'Content-Type игнорируется (Content-Type Bypass)',
        'Валидация Content-Type заголовка.',
        'Beginner', '15 мин', 50, 1,
        '/cart/items', ecom_lab_url,
        'Content-Type игнорируется — Content-Type Validation',
        'Почему возникает ошибка

Проверка Content-Type часто пропускается, что может привести к проблемам безопасности и обработки данных.',
        ARRAY[
            'Вспомни, зачем клиент отправляет заголовок Content-Type и как сервер должен на него реагировать',
            'Подумай, что происходит, если заголовок не совпадает с форматом тела',
            'Скрытый баг: API может игнорировать Content-Type и вернуть 200 с флагом — найдите и зарегистрируйте на странице Flags.'
        ],
        'REST API должен проверять заголовок Content-Type и отклонять запросы с неподдерживаемыми форматами.

Ожидаемое поведение: JSON с Content-Type: text/plain → 415 Unsupported Media Type.',
        '{"productId": "123", "quantity": 1}',
        5
    ) ON CONFLICT (id) DO NOTHING;

    -- T1: Mission 1.6 "Дублирование заказа" (Duplicate Order)
    INSERT INTO missions (
        id, domain_id, tier, title, description, difficulty, estimated_time,
        points, bugs, endpoint, base_url, theory_title, theory_content, hints, task_description, request_body_example, sort_order
    ) VALUES (
        'ecom-t1-006', 'ecommerce', 'T1', 'Дублирование заказа (Duplicate Order)',
        'Идемпотентность операций.',
        'Beginner', '20 мин', 50, 1,
        '/orders', ecom_lab_url,
        'Дублирование заказа — Idempotency',
        'Почему возникает ошибка

Идемпотентность операций часто игнорируется, что может привести к дублированию данных.',
        ARRAY[
            'Вспомни, зачем нужна идемпотентность при создании заказов и как её обычно реализуют',
            'Подумай, что должно происходить при повторной отправке того же запроса',
            'Скрытый баг: API может игнорировать ключ идемпотентности и создавать дубликаты — найдите флаг и зарегистрируйте на странице Flags.'
        ],
        'При создании заказа API должен корректно обрабатывать повторную отправку идентичного запроса.

Ожидаемое поведение: повторный POST с тем же X-Idempotency-Key → 200 OK с существующим заказом (тот же orderId).',
        '{"cartId": "cart-001"}',
        6
    ) ON CONFLICT (id) DO NOTHING;

    -- T2: Mission 2.1 "Граница количества" (Quantity Boundary)
    INSERT INTO missions (
        id, domain_id, tier, title, description, difficulty, estimated_time,
        points, bugs, endpoint, base_url, theory_title, theory_content, hints, task_description, request_body_example, sort_order
    ) VALUES (
        'ecom-t2-001', 'ecommerce', 'T2', 'Граница количества (Quantity Boundary)',
        'Граничные значения: quantity от 1 до 99. Off-by-one в валидации.',
        'Intermediate', '20 мин', 60, 1,
        '/cart/items', ecom_lab_url,
        'Граница количества — Boundary Values',
        'Почему возникает ошибка

Граничные значения часто проверяются некорректно из-за ошибок off-by-one.',
        ARRAY[
            'Вспомни про тестирование граничных значений: что проверять на границах объявленного диапазона',
            'Подумай об ошибках off-by-one в условиях валидации',
            'Скрытый баг: API может принять значение за границей диапазона и вернуть 201 с флагом — найдите и зарегистрируйте на странице Flags.'
        ],
        'В корзине действует правило: в одной позиции можно заказать от 1 до 99 единиц товара. Запросы с quantity вне этого диапазона должны отклоняться.

Ожидаемое поведение: значения в допустимом диапазоне принимаются (201 Created). Значения вне диапазона → 400 Bad Request.',
        '{"productId": "123", "quantity": 5}',
        7
    ) ON CONFLICT (id) DO NOTHING;

    -- T3: Mission 3.1 "Машина состояний заказа" (Order State Machine)
    INSERT INTO missions (
        id, domain_id, tier, title, description, difficulty, estimated_time,
        points, bugs, endpoint, base_url, theory_title, theory_content, hints, task_description, request_body_example, sort_order
    ) VALUES (
        'ecom-t3-001', 'ecommerce', 'T3', 'Машина состояний заказа (Order State Machine)',
        'Заказ в статусе DELIVERED нельзя отменить. Проверка допустимых переходов.',
        'Intermediate', '30 мин', 80, 1,
        '/orders/{id}/cancel', ecom_lab_url,
        'Машина состояний заказа — State Machine',
        'Почему возникает ошибка

Машины состояний часто реализуются некорректно, что позволяет недопустимые переходы состояний.',
        ARRAY[
            'Вспомни про машины состояний: какие переходы допустимы после доставки заказа',
            'Подумай, как API должен реагировать на попытку изменить состояние уже доставленного заказа',
            'Скрытый баг: API может разрешить недопустимый переход и вернуть флаг — найдите и зарегистрируйте на странице Flags.'
        ],
        'Заказ проходит через состояния: CREATED → PAID → PROCESSING → SHIPPED → DELIVERED. Проверьте корректность переходов между состояниями.

Ожидаемое поведение: доставленный заказ (DELIVERED) нельзя отменить.',
        NULL,
        8
    ) ON CONFLICT (id) DO NOTHING;

    -- T4: Mission 4.1 "Чужой заказ" (IDOR)
    INSERT INTO missions (
        id, domain_id, tier, title, description, difficulty, estimated_time,
        points, bugs, endpoint, base_url, theory_title, theory_content, hints, task_description, request_body_example, sort_order
    ) VALUES (
        'ecom-t4-001', 'ecommerce', 'T4', 'Чужой заказ (Other''s Order — IDOR)',
        'Пользователь должен видеть только свои заказы. Проверка изоляции данных.',
        'Hard', '35 мин', 100, 1,
        '/orders/{id}', ecom_lab_url,
        'Чужой заказ — IDOR Vulnerability',
        'Почему возникает ошибка

IDOR (Insecure Direct Object Reference) возникает когда система не проверяет права доступа к объектам.',
        ARRAY[
            'Вспомни про проверку владельца ресурса: кто должен видеть данные заказа',
            'Подумай, как API различает «свой» и «чужой» ресурс при доступе по id',
            'Скрытый баг: API может вернуть данные чужого ресурса — найдите флаг и зарегистрируйте на странице Flags.'
        ],
        'Пользователь должен видеть только свои заказы. Проверьте изоляцию данных между пользователями.

Ожидаемое поведение: пользователь видит только свои заказы.',
        NULL,
        9
    ) ON CONFLICT (id) DO NOTHING;

    -- T5: Mission 5.1 "Промокод-брутфорс" (Promo Bruteforce)
    INSERT INTO missions (
        id, domain_id, tier, title, description, difficulty, estimated_time,
        points, bugs, endpoint, base_url, theory_title, theory_content, hints, task_description, request_body_example, sort_order
    ) VALUES (
        'ecom-t5-001', 'ecommerce', 'T5', 'Промокод-брутфорс (Promo Bruteforce)',
        'Промокоды формата XXXX-XXXX. Проверка защиты от перебора.',
        'Expert', '45 мин', 120, 1,
        '/checkout/promo', ecom_lab_url,
        'Промокод-брутфорс — Rate Limiting',
        'Почему возникает ошибка

Отсутствие rate limiting позволяет перебрать промокоды методом brute force.',
        ARRAY[
            'Вспомни про защиту от перебора: что должно ограничивать количество попыток проверки кода',
            'Подумай, как сервер реагирует на массовые запросы к одному endpoint',
            'Скрытый баг: отсутствие ограничения позволяет перебирать коды — найдите флаг и зарегистрируйте на странице Flags.'
        ],
        'Промокоды имеют формат XXXX-XXXX. Проверьте защиту от перебора.

Ожидаемое поведение: защита от brute-force атак на промокоды.',
        '{"code": "TEST-0001"}',
        10
    ) ON CONFLICT (id) DO NOTHING;
END $$;

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
('ecom-t5-001-bug1', 'ecom-t5-001', 'Promo Bruteforce Allowed', 'Нет rate limit на промокоды', 'FLAG{PROMO_BRUTEFORCE_ALLOWED}', 120, 'Hard', 1)
ON CONFLICT (id) DO NOTHING;
