# QA Training Platform - Frontend

🎯 Postman-style интерфейс для обучения API-тестированию.

![QA Platform](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![Tailwind](https://img.shields.io/badge/Tailwind-3.3-38B2AC?logo=tailwindcss)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite)

## 🚀 Quick Start

### Локальная разработка

```bash
# Установка зависимостей
npm install

# Запуск dev-сервера
npm run dev

# Открыть http://localhost:3000
```

### Production Build

```bash
# Сборка для продакшена
npm run build

# Preview production build
npm run preview
```

## 🌐 Deployment на Fly.io

```bash
# 1. Установка Fly CLI
curl -L https://fly.io/install.sh | sh

# 2. Авторизация
fly auth login

# 3. Создание приложения (первый раз)
fly launch --name qa-training-platform

# 4. Деплой
fly deploy

# 5. Проверка статуса
fly status
fly logs
```

## 📁 Структура проекта

```
qa-platform-frontend/
├── src/
│   ├── components/      # Переиспользуемые компоненты
│   │   └── Layout.jsx   # Основной layout с сайдбаром
│   ├── pages/           # Страницы приложения
│   │   ├── Dashboard.jsx    # Обзор с миссиями и статистикой
│   │   ├── Lab.jsx          # Домены → Миссии → Детали лабы
│   │   └── Flags.jsx        # Регистрация и просмотр флагов
│   ├── services/        # API и сервисы
│   │   └── api.js       # API клиент с поддержкой demo mode
│   ├── mocks/           # Mock данные для demo mode
│   │   └── data.js      # Домены, миссии, флаги, статистика
│   ├── App.jsx          # Корневой компонент с роутингом
│   ├── main.jsx         # Entry point
│   └── index.css        # Глобальные стили + Tailwind
├── public/              # Статические файлы
├── Dockerfile           # Docker образ для продакшена
├── nginx.conf           # Nginx конфигурация
├── fly.toml             # Fly.io конфигурация
├── tailwind.config.js   # Tailwind конфигурация
├── vite.config.js       # Vite конфигурация
└── package.json
```

## 🎨 Возможности

### Dashboard
- Обзор всех миссий из всех доменов
- Фильтрация по уровню (T1, T2, T3) и статусу
- Статистика пользователя
- Лента последней активности

### API Lab (Домены → Миссии)
- **Домены:** Fintech, E-Commerce, Booking, Marketplace, Healthcare, Social Media
- **Прогрессия:** T2 открывается после 80% флагов T1
- **Страница миссии:**
  - Описание задания
  - Теоретический блок с направлением к решению
  - API Endpoint для тестирования  
  - Кнопка запуска лабы
  - Подсказки

### Flags
- Поле регистрации найденных флагов
- Мгновенная валидация (верный/неверный)
- Отображение заработанных баллов
- История найденных флагов с фильтрацией по домену

## ⚙️ Конфигурация

### Environment Variables

| Переменная | Описание | Default |
|------------|----------|---------|
| `VITE_API_URL` | URL бэкенда | `""` (demo mode) |
| `VITE_DEMO_MODE` | Включить demo mode | `true` |

### Подключение к реальному бэкенду

```bash
# .env
VITE_API_URL=https://qa-platform-backend.fly.dev
VITE_DEMO_MODE=false
```

## 🎯 Demo Mode

По умолчанию приложение работает в demo mode с mock данными. Это позволяет:
- Тестировать UI без бэкенда
- Демонстрировать функционал
- Разрабатывать независимо от API

В demo mode:
- Отображаются тестовые миссии
- API Lab симулирует ответы с флагами
- Верификация флагов работает локально

## 🛠 Разработка

### Добавление новой страницы

1. Создайте компонент в `src/pages/`
2. Добавьте роут в `src/App.jsx`
3. Добавьте ссылку в `src/components/Layout.jsx`

### Добавление новых mock данных

Отредактируйте `src/mocks/data.js`:

```javascript
export const mockMissions = [
  {
    id: 'new-mission',
    title: 'New Mission',
    // ...
  }
];
```

## 📝 License

MIT
