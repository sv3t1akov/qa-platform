-- Social T1 Missions
-- Based on SOCIAL_T1_INTERNAL_FLAGS.md and SOCIAL_T1_STUDENT_THEORY.md
-- Execute this file BEFORE seed_social_t1_bugs.sql
-- Plain INSERTs (no DO block) for compatibility with all PostgreSQL drivers

INSERT INTO missions (
    id, domain_id, tier, title, description, difficulty, estimated_time,
    points, bugs, endpoint, base_url, theory_title, theory_content, hints, task_description, request_body_example, sort_order
) VALUES (
    'social-t1-user-profile', 'social', 'T1', 'User Profile API',
    'Вы тестируете User Profile API социальной сети SocialHub. Исследуйте создание, просмотр и редактирование профилей пользователей.',
    'Beginner', '25 мин', 300, 4,
    '/api/v1/users/me', 'https://qa-lab-social.fly.dev',
    'User Profile API — Валидация входных данных',
    'Валидация входных данных — первая линия обороны любого API. Типичные ошибки: обязательные поля не проверяются на сервере, типы данных не валидируются строго, ограничения длины не применяются, защищённые поля могут приниматься от клиента. Реальные случаи: GitHub 2012 — Mass Assignment в Rails, MongoDB Injection.',
    ARRAY[
        'Какие поля документация помечает как обязательные?',
        'Какие ограничения указаны для каждого поля?',
        'Есть ли поля, которые возвращаются в ответе, но не должны изменяться пользователем?'
    ],
    'Исследуйте API управления профилями и найдите скрытые дефекты. Эндпоинты: POST /api/v1/users, GET /api/v1/users/me, PUT /api/v1/users/me. Сравните реальное поведение API с документацией.',
    '{"displayName": "John", "bio": "Hello world", "website": "https://example.com"}',
    1
) ON CONFLICT (id) DO UPDATE SET
    theory_title = EXCLUDED.theory_title,
    theory_content = EXCLUDED.theory_content,
    hints = EXCLUDED.hints,
    task_description = EXCLUDED.task_description,
    title = EXCLUDED.title,
    description = EXCLUDED.description;

INSERT INTO missions (
    id, domain_id, tier, title, description, difficulty, estimated_time,
    points, bugs, endpoint, base_url, theory_title, theory_content, hints, task_description, request_body_example, sort_order
) VALUES (
    'social-t1-posts', 'social', 'T1', 'Posts API',
    'API управления постами с текстом и медиа-контентом. Исследуйте создание постов с различными комбинациями параметров.',
    'Beginner', '25 мин', 300, 4,
    '/api/v1/posts', 'https://qa-lab-social.fly.dev',
    'Posts API — Enum-поля и массивы',
    'Enum — тип с фиксированным набором допустимых значений. Массивы часто имеют ограничения на размер. Типичные проблемы: enum не валидируется, ограничения массивов не проверяются, строковые ограничения игнорируются. HTTP-семантика: для операций удаления и создания существуют стандартные коды ответа.',
    ARRAY[
        'Какие поля имеют фиксированный набор допустимых значений?',
        'Есть ли поля-массивы с ограничениями на размер?',
        'Какие минимальные и максимальные длины указаны для текстовых полей?'
    ],
    'Найдите дефекты в API управления постами. Эндпоинты: POST /api/v1/posts, DELETE /api/v1/posts/{id}. Проверьте соответствие поведения документации и REST-конвенциям.',
    '{"content": "My post", "visibility": "public", "mediaUrls": ["https://cdn.example.com/1.jpg"]}',
    2
) ON CONFLICT (id) DO UPDATE SET
    theory_title = EXCLUDED.theory_title,
    theory_content = EXCLUDED.theory_content,
    hints = EXCLUDED.hints,
    task_description = EXCLUDED.task_description,
    title = EXCLUDED.title,
    description = EXCLUDED.description;

INSERT INTO missions (
    id, domain_id, tier, title, description, difficulty, estimated_time,
    points, bugs, endpoint, base_url, theory_title, theory_content, hints, task_description, request_body_example, sort_order
) VALUES (
    'social-t1-comments', 'social', 'T1', 'Comments API',
    'API комментариев к постам. Исследуйте создание комментариев, связь с постами и корректность HTTP-ответов.',
    'Beginner', '25 мин', 300, 4,
    '/api/v1/posts/{postId}/comments', 'https://qa-lab-social.fly.dev',
    'Comments API — Связи между сущностями и HTTP-контракт',
    'Ссылочная целостность: дочерние сущности ссылаются на родительские. Что если родитель не существует? HTTP-коды передают результат операции — клиенты полагаются на них. Идентификаторы — тоже входные данные. Strict vs Loose parsing: как API обрабатывает недокументированные поля?',
    ARRAY[
        'Как API обрабатывает ссылки на несуществующие ресурсы?',
        'Соответствуют ли HTTP-коды ответов ожиданиям REST?',
        'Принимает ли API недокументированные поля?',
        'Как обрабатываются различные форматы ID?'
    ],
    'Исследуйте API комментариев. Эндпоинты: POST /api/v1/posts/{postId}/comments, GET /api/v1/comments/{id}. Проверьте связи между сущностями, HTTP-коды и обработку полей запроса.',
    '{"content": "Great post!"}',
    3
) ON CONFLICT (id) DO UPDATE SET
    theory_title = EXCLUDED.theory_title,
    theory_content = EXCLUDED.theory_content,
    hints = EXCLUDED.hints,
    task_description = EXCLUDED.task_description,
    title = EXCLUDED.title,
    description = EXCLUDED.description;

INSERT INTO missions (
    id, domain_id, tier, title, description, difficulty, estimated_time,
    points, bugs, endpoint, base_url, theory_title, theory_content, hints, task_description, request_body_example, sort_order
) VALUES (
    'social-t1-feed-social', 'social', 'T1', 'Feed & Social Graph API',
    'API ленты новостей и подписок. Исследуйте аутентификацию, параметры запросов и бизнес-правила подписок.',
    'Beginner', '30 мин', 400, 5,
    '/api/v1/feed', 'https://qa-lab-social.fly.dev',
    'Feed & Social Graph — Аутентификация, Query Parameters и бизнес-правила',
    'Защищённые эндпоинты должны проверять аутентификацию. Query параметры — входные данные, требующие валидации. Бизнес-правила задают логические ограничения предметной области. Связи между сущностями могут требовать проверки уникальности. Реальные случаи: Parler 2021, Peloton 2021.',
    ARRAY[
        'Требуется ли аутентификация для всех защищённых эндпоинтов?',
        'Валидируются ли параметры запроса?',
        'Какие бизнес-правила должны соблюдаться?',
        'Как система обрабатывает повторные действия?'
    ],
    'Исследуйте Feed и Social Graph API. Эндпоинты: GET /api/v1/feed, POST /api/v1/users/{userId}/follow. Проверьте аутентификацию, валидацию параметров и бизнес-правила.',
    NULL,
    4
) ON CONFLICT (id) DO UPDATE SET
    theory_title = EXCLUDED.theory_title,
    theory_content = EXCLUDED.theory_content,
    hints = EXCLUDED.hints,
    task_description = EXCLUDED.task_description,
    title = EXCLUDED.title,
    description = EXCLUDED.description;
