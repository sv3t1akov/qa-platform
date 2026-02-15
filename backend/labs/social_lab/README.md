# Social Media T1 Lab

Лабораторная работа T1 уровня для домена Social Media. 4 миссии, 17 флагов.

**Base URL:** https://qa-lab-social.fly.dev

## Миссии

1. **User Profile API** — валидация обязательных полей, типов, ограничений, mass assignment
2. **Posts API** — minLength, enum, maxItems, HTTP DELETE code
3. **Comments API** — referential integrity, HTTP POST code, integer overflow, strict parsing
4. **Feed & Social Graph API** — authentication, query params, business rules

## Локальный запуск

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

## Деплой на Fly.io

```bash
fly deploy
```
