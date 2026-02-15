// Mock data for demo mode
// Structured by domains and tiers

export const domains = [
  {
    id: 'fintech',
    name: 'Fintech',
    icon: '💳',
    description: 'Банковские API, платежи, кошельки',
    color: 'from-emerald-500 to-teal-600',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30',
    textColor: 'text-emerald-400',
    totalMissions: 6,
    completedMissions: 1,
  },
  {
    id: 'ecommerce',
    name: 'E-Commerce',
    icon: '🛒',
    description: 'Интернет-магазины, корзины, заказы',
    color: 'from-blue-500 to-indigo-600',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    textColor: 'text-blue-400',
    totalMissions: 3,
    completedMissions: 0,
  },
  {
    id: 'booking',
    name: 'Booking',
    icon: '🏨',
    description: 'Бронирование отелей, билетов, услуг',
    color: 'from-purple-500 to-violet-600',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
    textColor: 'text-purple-400',
    totalMissions: 2,
    completedMissions: 0,
  },
  {
    id: 'marketplace',
    name: 'Marketplace',
    icon: '🏪',
    description: 'Маркетплейсы, продавцы, товары',
    color: 'from-orange-500 to-amber-600',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/30',
    textColor: 'text-orange-400',
    totalMissions: 1,
    completedMissions: 0,
  },
  {
    id: 'healthcare',
    name: 'Healthcare',
    icon: '🏥',
    description: 'Медицинские системы, записи, рецепты',
    color: 'from-red-500 to-rose-600',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    textColor: 'text-red-400',
    totalMissions: 1,
    completedMissions: 0,
  },
  {
    id: 'social',
    name: 'Social Media',
    icon: '📱',
    description: 'Социальные сети, посты, профили',
    color: 'from-pink-500 to-fuchsia-600',
    bgColor: 'bg-pink-500/10',
    borderColor: 'border-pink-500/30',
    textColor: 'text-pink-400',
    totalMissions: 1,
    completedMissions: 0,
  },
];

// Landing page: 6 techniques (for main page intro block)
export const landingTechniques = [
  { id: 'boundary', title: 'Boundary Testing', description: 'Проверка граничных значений: min/max, overflow, пустые и невалидные данные.' },
  { id: 'idor', title: 'IDOR Hunting', description: 'Поиск небезопасных прямых ссылок на объекты: доступ к чужим ресурсам по ID.' },
  { id: 'fuzzing', title: 'Input Fuzzing', description: 'Массовая подстановка нестандартных входных данных для выявления сбоев и утечек.' },
  { id: 'state', title: 'State Manipulation', description: 'Нарушение ожидаемого порядка состояний: переходы в обход бизнес-правил.' },
  { id: 'race', title: 'Race Conditions', description: 'Параллельные запросы для проверки гонок и неконсистентного состояния.' },
  { id: 'auth', title: 'Auth Bypass', description: 'Обход аутентификации и авторизации: токены, заголовки, роли.' },
];

// Landing page: T1–T5 tiers (focus + unlock condition)
export const landingTiers = [
  { tier: 'T1', focus: 'HTTP контракты, базовая валидация', unlock: 'Доступен сразу' },
  { tier: 'T2', focus: 'Граничные значения, форматы данных', unlock: '80% багов в T1' },
  { tier: 'T3', focus: 'Бизнес-логика, состояния', unlock: '80% багов в T2' },
  { tier: 'T4', focus: 'Авторизация, async-операции', unlock: '80% багов в T3' },
  { tier: 'T5', focus: 'Security, race conditions', unlock: '80% багов в T4' },
];

// Landing page: illustrative flag examples only (not from missions)
export const landingFlagExamples = [
  'QA_FLAG{demo_format_abc}',
  'QA_FLAG{example_xyz}',
  'QA_FLAG{sample_illustration}',
];

export const missionsByDomain = {
  fintech: {
    T1: [
      {
        id: 'fin-t1-wallet-basic',
        title: 'Wallet API - Basic',
        description: 'Базовое тестирование API электронного кошелька. Научитесь находить типичные ошибки валидации.',
        difficulty: 'Beginner',
        estimatedTime: '30 min',
        points: 100,
        bugs: 3,
        foundBugs: 2,
        status: 'in_progress',
        endpoint: '/api/v1/wallets/{wallet_id}/transfer',
        baseUrl: 'https://qa-lab-fin-t1-wallet.fly.dev',
        theory: {
          title: 'Негативное тестирование',
          content: `При тестировании финансовых API важно проверять не только позитивные сценарии, но и граничные случаи. 

Обратите внимание на:
• Как система обрабатывает нестандартные значения в полях суммы?
• Что происходит при передаче данных неожиданного типа?
• Проверяется ли знак числа перед выполнением операции?

Финансовые системы особенно чувствительны к ошибкам в валидации числовых значений.`,
        },
        hints: [
          'Подумайте о математических операциях с отрицательными числами',
          'Проверьте границы допустимых значений',
        ],
      },
      {
        id: 'fin-t1-wallet-boundaries',
        title: 'Wallet API - Boundaries',
        description: 'Тестирование граничных значений. Найдите баги в обработке экстремальных данных.',
        difficulty: 'Beginner',
        estimatedTime: '45 min',
        points: 150,
        bugs: 4,
        foundBugs: 4,
        status: 'completed',
        endpoint: '/api/v1/wallets/{wallet_id}/deposit',
        baseUrl: 'https://qa-lab-fin-t1-boundaries.fly.dev',
        theory: {
          title: 'Граничное тестирование',
          content: `Граничные значения — это значения на границе допустимых диапазонов. Именно здесь чаще всего скрываются баги.

Типичные границы для финансовых систем:
• Минимальная и максимальная сумма транзакции
• Лимиты баланса
• Количество знаков после запятой
• Максимальное значение для типа данных

Попробуйте значения: 0, -1, MAX_INT, очень длинные числа.`,
        },
        hints: [
          'Что будет если сумма равна нулю?',
          'Проверьте очень большие числа',
        ],
      },
      {
        id: 'fin-t1-auth-tokens',
        title: 'Auth Tokens Validation',
        description: 'Тестирование механизмов аутентификации и валидации токенов.',
        difficulty: 'Beginner',
        estimatedTime: '40 min',
        points: 120,
        bugs: 3,
        foundBugs: 0,
        status: 'available',
        endpoint: '/api/v1/auth/verify',
        baseUrl: 'https://qa-lab-fin-t1-auth.fly.dev',
        theory: {
          title: 'Тестирование аутентификации',
          content: `Аутентификация — критически важный компонент любого API. Ошибки здесь могут привести к серьёзным уязвимостям.

На что обратить внимание:
• Как система реагирует на невалидные токены?
• Что происходит при отсутствии заголовка авторизации?
• Проверяется ли формат токена перед валидацией?

Попробуйте различные вариации заголовка Authorization.`,
        },
        hints: [
          'Проверьте разные форматы токенов',
          'Что если токен пустой?',
        ],
      },
    ],
    T2: [
      {
        id: 'fin-t2-credit-pipeline',
        title: 'Credit Pipeline API',
        description: 'Тестирование процесса кредитной заявки. Сложные бизнес-процессы и state machine.',
        difficulty: 'Intermediate',
        estimatedTime: '1 hour',
        points: 250,
        bugs: 5,
        foundBugs: 0,
        status: 'available',
        endpoint: '/api/v1/applications',
        baseUrl: 'https://qa-lab-fin-t2-credit.fly.dev',
        theory: {
          title: 'Тестирование State Machine',
          content: `Кредитные заявки проходят через несколько состояний: draft → submitted → review → approved/rejected.

Ключевые аспекты тестирования:
• Можно ли перейти в состояние, минуя промежуточные?
• Что происходит при повторной отправке заявки?
• Как система обрабатывает параллельные изменения?

Попробуйте нарушить ожидаемый порядок переходов между состояниями.`,
        },
        hints: [
          'Проверьте переходы между статусами',
          'Можно ли изменить уже одобренную заявку?',
        ],
      },
      {
        id: 'fin-t2-payment-gateway',
        title: 'Payment Gateway',
        description: 'Интеграционное тестирование платежного шлюза с внешними системами.',
        difficulty: 'Intermediate',
        estimatedTime: '1.5 hours',
        points: 300,
        bugs: 6,
        foundBugs: 0,
        status: 'available',
        endpoint: '/api/v1/payments',
        baseUrl: 'https://qa-lab-fin-t2-payments.fly.dev',
        theory: {
          title: 'Идемпотентность платежей',
          content: `Платежные системы должны быть идемпотентными — повторный запрос не должен создавать дублирующую транзакцию.

Важные проверки:
• Используется ли idempotency key?
• Что происходит при таймауте и повторном запросе?
• Как обрабатываются race conditions?

Попробуйте отправить один и тот же платеж несколько раз.`,
        },
        hints: [
          'Проверьте обработку дубликатов',
          'Что если сеть прервётся во время платежа?',
        ],
      },
    ],
    T3: [
      {
        id: 'fin-t3-fraud-detection',
        title: 'Fraud Detection System',
        description: 'Продвинутое тестирование системы антифрода. Race conditions и timing attacks.',
        difficulty: 'Advanced',
        estimatedTime: '2 hours',
        points: 500,
        bugs: 8,
        foundBugs: 0,
        status: 'locked',
        requiredProgress: 80,
        endpoint: '/api/v1/transactions/analyze',
        baseUrl: 'https://qa-lab-fin-t3-fraud.fly.dev',
        theory: {
          title: 'Race Conditions в финансах',
          content: `Race conditions — это ситуации, когда результат зависит от порядка выполнения параллельных операций.

В финансовых системах это критично:
• Двойное списание при параллельных запросах
• Обход лимитов при одновременных транзакциях
• Некорректный баланс при конкурентном доступе

Попробуйте отправить несколько запросов одновременно.`,
        },
        hints: [
          'Используйте параллельные запросы',
          'Проверьте timing между операциями',
        ],
      },
    ],
  },
  ecommerce: {
    T1: [
      {
        id: 'ecom-t1-cart-basic',
        title: 'Shopping Cart API',
        description: 'Базовое тестирование корзины покупок. Добавление, удаление, обновление товаров.',
        difficulty: 'Beginner',
        estimatedTime: '35 min',
        points: 100,
        bugs: 3,
        foundBugs: 0,
        status: 'available',
        endpoint: '/api/v1/cart/items',
        baseUrl: 'https://qa-lab-ecom-t1-cart.fly.dev',
        theory: {
          title: 'Тестирование корзины',
          content: `Корзина покупок — центральный элемент любого e-commerce приложения.

Типичные проблемы:
• Отрицательное количество товаров
• Добавление несуществующих товаров
• Превышение доступного количества на складе

Проверьте все CRUD операции с товарами в корзине.`,
        },
        hints: [
          'Что если добавить -1 товар?',
          'Проверьте лимиты количества',
        ],
      },
      {
        id: 'ecom-t1-product-search',
        title: 'Product Search API',
        description: 'Тестирование поиска и фильтрации товаров.',
        difficulty: 'Beginner',
        estimatedTime: '30 min',
        points: 90,
        bugs: 3,
        foundBugs: 0,
        status: 'available',
        endpoint: '/api/v1/products/search',
        baseUrl: 'https://qa-lab-ecom-t1-search.fly.dev',
        theory: {
          title: 'Injection в поисковых запросах',
          content: `Поисковые поля часто уязвимы для различных инъекций.

Что проверять:
• SQL injection в параметрах поиска
• NoSQL injection 
• Специальные символы и escape-последовательности

Попробуйте специальные символы в поисковом запросе.`,
        },
        hints: [
          'Проверьте специальные символы',
          'Попробуйте SQL-подобные конструкции',
        ],
      },
    ],
    T2: [
      {
        id: 'ecom-t2-checkout',
        title: 'Checkout Process',
        description: 'Тестирование процесса оформления заказа с промокодами и скидками.',
        difficulty: 'Intermediate',
        estimatedTime: '1 hour',
        points: 220,
        bugs: 5,
        foundBugs: 0,
        status: 'locked',
        requiredProgress: 80,
        endpoint: '/api/v1/checkout',
        baseUrl: 'https://qa-lab-ecom-t2-checkout.fly.dev',
        theory: {
          title: 'Манипуляции с ценами',
          content: `Checkout — критическая точка для бизнеса. Здесь деньги переходят от клиента к магазину.

Уязвимости:
• Изменение цены на клиенте
• Многократное применение промокодов
• Race condition при применении скидок`,
        },
        hints: [
          'Можно ли применить промокод дважды?',
          'Проверьте порядок расчёта скидок',
        ],
      },
    ],
    T3: [],
  },
  booking: {
    T1: [
      {
        id: 'book-t1-room-availability',
        title: 'Room Availability API',
        description: 'Проверка доступности номеров и базовое бронирование.',
        difficulty: 'Beginner',
        estimatedTime: '35 min',
        points: 100,
        bugs: 3,
        foundBugs: 0,
        status: 'available',
        endpoint: '/api/v1/rooms/availability',
        baseUrl: 'https://qa-lab-book-t1-rooms.fly.dev',
        theory: {
          title: 'Тестирование дат',
          content: `Системы бронирования сильно зависят от корректной работы с датами и бизнес-правилами доступности.

Направления для исследования:
• Валидация периода (формат, порядок дат, длительность)
• Граничные и редкие календарные случаи (конец месяца, високосные годы)
• Согласованность правил доступности при разных комбинациях параметров`,
        },
        hints: [
          'Подумайте о порядке дат и минимальной длительности периода',
          'Какие граничные календарные случаи стоит учитывать?',
        ],
      },
    ],
    T2: [
      {
        id: 'book-t2-overbooking',
        title: 'Overbooking Prevention',
        description: 'Тестирование защиты от овербукинга при параллельных бронированиях.',
        difficulty: 'Intermediate',
        estimatedTime: '1.5 hours',
        points: 280,
        bugs: 4,
        foundBugs: 0,
        status: 'locked',
        requiredProgress: 80,
        endpoint: '/api/v1/bookings',
        baseUrl: 'https://qa-lab-book-t2-overbook.fly.dev',
        theory: {
          title: 'Параллельные бронирования',
          content: `Овербукинг — классическая проблема систем бронирования.

Направления для исследования:
• Конкурентные сценарии и согласованность данных
• Повторные запросы и идемпотентность операций
• Конфликты при изменении/отмене и повторном создании`,
        },
        hints: [
          'Что произойдёт, если действия выполняются почти одновременно?',
          'Есть ли защита от повторной отправки одного и того же запроса?',
        ],
      },
    ],
    T3: [],
  },
  marketplace: {
    T1: [
      {
        id: 'mp-t1-seller-products',
        title: 'Seller Products API',
        description: 'Управление товарами продавца. CRUD операции и валидация.',
        difficulty: 'Beginner',
        estimatedTime: '40 min',
        points: 110,
        bugs: 4,
        foundBugs: 0,
        status: 'available',
        endpoint: '/api/v1/sellers/{seller_id}/products',
        baseUrl: 'https://qa-lab-mp-t1-seller.fly.dev',
        theory: {
          title: 'Авторизация на уровне объектов',
          content: `В маркетплейсах критически важно, чтобы продавцы могли управлять только своими товарами.

Проверьте:
• Можно ли изменить чужой товар?
• Доступ к товарам другого продавца
• Изменение seller_id в запросе`,
        },
        hints: [
          'Попробуйте ID другого продавца',
          'Проверьте права доступа к чужим товарам',
        ],
      },
    ],
    T2: [],
    T3: [],
  },
  healthcare: {
    T1: [
      {
        id: 'hc-t1-appointments',
        title: 'Appointments API',
        description: 'Запись к врачу. Проверка слотов и конфликтов расписания.',
        difficulty: 'Beginner',
        estimatedTime: '35 min',
        points: 100,
        bugs: 3,
        foundBugs: 0,
        status: 'available',
        endpoint: '/api/v1/appointments',
        baseUrl: 'https://qa-lab-hc-t1-appt.fly.dev',
        theory: {
          title: 'Медицинские данные',
          content: `Медицинские системы имеют строгие требования к безопасности и приватности.

Критические проверки:
• Доступ к чужим записям
• Утечка персональных данных в ответах
• Корректность временных слотов`,
        },
        hints: [
          'Проверьте доступ к чужим appointment',
          'Какие данные возвращаются в ответе?',
        ],
      },
    ],
    T2: [],
    T3: [],
  },
  social: {
    T1: [
      {
        id: 'soc-t1-posts',
        title: 'Posts API',
        description: 'Создание и управление постами. Проверка прав доступа.',
        difficulty: 'Beginner',
        estimatedTime: '30 min',
        points: 90,
        bugs: 3,
        foundBugs: 0,
        status: 'available',
        endpoint: '/api/v1/posts',
        baseUrl: 'https://qa-lab-soc-t1-posts.fly.dev',
        theory: {
          title: 'Контроль доступа к контенту',
          content: `Социальные сети должны строго контролировать, кто может видеть и редактировать контент.

Проверьте:
• Редактирование чужих постов
• Доступ к приватным постам
• Удаление чужого контента`,
        },
        hints: [
          'Попробуйте изменить чужой пост',
          'Проверьте приватность',
        ],
      },
    ],
    T2: [],
    T3: [],
  },
};

// Helper to calculate tier unlock status (optional 3rd arg: missionsByDomain override for API data)
export function getTierProgress(domainId, tier, missionsByDomainOverride) {
  const source = missionsByDomainOverride ?? missionsByDomain;
  const domain = source[domainId];
  if (!domain) return { unlocked: false, progress: 0 };
  
  const tierData = domain[tier];
  
  // Если данные из API (с полями unlocked и progress)
  if (tierData && typeof tierData === 'object' && 'unlocked' in tierData && 'progress' in tierData) {
    const tierMissions = tierData.missions || [];
    const totalBugs = tierMissions.reduce((sum, m) => sum + (m.bugs || 0), 0);
    const foundBugs = tierMissions.reduce((sum, m) => sum + (m.foundBugs ?? 0), 0);
    return {
      unlocked: tierData.unlocked,
      progress: tierData.progress,
      totalBugs,
      foundBugs,
    };
  }
  
  // Старый формат (моки) - массив миссий напрямую
  const tierMissions = Array.isArray(tierData) ? tierData : (tierData?.missions || []);
  if (tierMissions.length === 0) return { unlocked: false, progress: 0, empty: true };
  
  const totalBugs = tierMissions.reduce((sum, m) => sum + (m.bugs || 0), 0);
  const foundBugs = tierMissions.reduce((sum, m) => sum + (m.foundBugs ?? 0), 0);
  const progress = totalBugs > 0 ? Math.round((foundBugs / totalBugs) * 100) : 0;
  
  return { unlocked: true, progress, totalBugs, foundBugs };
}

export function isTierUnlocked(domainId, tier, missionsByDomainOverride) {
  // T1 всегда разблокирован для всех студентов
  if (tier === 'T1') return true;
  
  const source = missionsByDomainOverride ?? missionsByDomain;
  const domain = source[domainId];
  if (!domain) return false;
  
  const tierData = domain[tier];
  
  // Если данные из API (с полем unlocked)
  if (tierData && typeof tierData === 'object' && 'unlocked' in tierData) {
    return tierData.unlocked;
  }
  
  // Старый формат (моки) - вычисляем на основе предыдущего тира
  const prevTier = `T${parseInt(tier.slice(1)) - 1}`;
  const prevProgress = getTierProgress(domainId, prevTier, missionsByDomainOverride);
  
  return prevProgress.progress >= 80;
}

// User stats
export const mockUserStats = {
  totalPoints: 270,
  rank: {
    id: 'tester',
    nameRu: 'Тестировщик',
    nameEn: 'Tester',
    color: '#3B82F6'
  },
  nextRank: {
    id: 'bug_hunter',
    nameRu: 'Охотник за багами',
    nameEn: 'Bug Hunter',
    minPoints: 350
  },
  rankProgress: 44,
  pointsToNextRank: 80,
  completedMissions: 1,
  foundBugs: 6,
  totalBugs: 45,
  badges: [
    { id: 'first-bug', name: 'First Bug', icon: '🐛', description: 'Найден первый баг' },
    { id: 'quick-learner', name: 'Quick Learner', icon: '⚡', description: 'Завершена первая миссия' },
    { id: 'fintech-starter', name: 'Fintech Starter', icon: '💳', description: 'Начат путь в Fintech' },
  ],
};

// Found flags history
export const mockFoundFlags = [
  {
    id: 'flag-001',
    missionId: 'fin-t1-wallet-basic',
    missionTitle: 'Wallet API - Basic',
    domain: 'fintech',
    bugTitle: 'Negative Transfer Amount',
    flag: 'QA_FLAG{negative_balance_a1b2c3}',
    points: 30,
    foundAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    difficulty: 'Easy',
  },
  {
    id: 'flag-002',
    missionId: 'fin-t1-wallet-basic',
    missionTitle: 'Wallet API - Basic',
    domain: 'fintech',
    bugTitle: 'Missing Content-Type Validation',
    flag: 'QA_FLAG{content_type_bypass_d4e5f6}',
    points: 30,
    foundAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    difficulty: 'Easy',
  },
  {
    id: 'flag-003',
    missionId: 'fin-t1-wallet-boundaries',
    missionTitle: 'Wallet API - Boundaries',
    domain: 'fintech',
    bugTitle: 'Integer Overflow',
    flag: 'QA_FLAG{overflow_g7h8i9}',
    points: 40,
    foundAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    difficulty: 'Medium',
  },
  {
    id: 'flag-004',
    missionId: 'fin-t1-wallet-boundaries',
    missionTitle: 'Wallet API - Boundaries',
    domain: 'fintech',
    bugTitle: 'Zero Amount Bypass',
    flag: 'QA_FLAG{zero_bypass_j0k1l2}',
    points: 30,
    foundAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    difficulty: 'Easy',
  },
  {
    id: 'flag-005',
    missionId: 'fin-t1-wallet-boundaries',
    missionTitle: 'Wallet API - Boundaries',
    domain: 'fintech',
    bugTitle: 'Decimal Precision Error',
    flag: 'QA_FLAG{decimal_m3n4o5}',
    points: 35,
    foundAt: new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString(),
    difficulty: 'Medium',
  },
  {
    id: 'flag-006',
    missionId: 'fin-t1-wallet-boundaries',
    missionTitle: 'Wallet API - Boundaries',
    domain: 'fintech',
    bugTitle: 'Currency Mismatch',
    flag: 'QA_FLAG{currency_p6q7r8}',
    points: 45,
    foundAt: new Date(Date.now() - 26 * 60 * 60 * 1000).toISOString(),
    difficulty: 'Medium',
  },
];

// Simulates flag verification
export const verifyFlag = async (flag) => {
  await new Promise(r => setTimeout(r, 500));
  
  // Check if flag matches expected pattern
  const flagPattern = /^QA_FLAG\{[\w_]+\}$/;
  if (!flagPattern.test(flag)) {
    return {
      valid: false,
      message: 'Неверный формат флага. Ожидается: QA_FLAG{...}',
      points: 0,
    };
  }
  
  // Check against known flags (in demo mode)
  const knownFlag = mockFoundFlags.find(f => f.flag === flag);
  if (knownFlag) {
    return {
      valid: true,
      message: 'Флаг уже был зарегистрирован ранее',
      points: 0,
      alreadyFound: true,
    };
  }
  
  // Simulate finding a new flag (in demo)
  if (flag.includes('demo') || flag.includes('test')) {
    const points = 30 + Math.floor(Math.random() * 20);
    return {
      valid: true,
      message: `🎉 Отлично! Вы нашли новый баг!`,
      points: points,
      newFlag: true,
      bugTitle: 'Demo Bug Found',
    };
  }
  
  return {
    valid: false,
    message: 'Флаг не найден в системе. Проверьте правильность ввода.',
    points: 0,
  };
};
