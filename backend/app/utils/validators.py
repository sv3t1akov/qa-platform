"""
Валидация данных для авторизации
"""
import re


def validate_password(password: str) -> tuple[bool, str]:
    """
    Валидация пароля.
    Returns: (is_valid, error_message)
    
    Примечание: Используется Argon2 для хеширования паролей, который не имеет
    ограничений по длине (в отличие от bcrypt с лимитом 72 байта).
    """
    if len(password) < 6:
        return False, "Пароль должен содержать минимум 6 символов"
    
    # Максимальная длина для безопасности (можно увеличить при необходимости)
    # Пароли длиннее 72 байт будут предварительно хешироваться через SHA-256
    if len(password) > 1000:
        return False, "Пароль слишком длинный (максимум 1000 символов)"
    
    if not re.search(r'\d', password):
        return False, "Пароль должен содержать хотя бы одну цифру"
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
        return False, "Пароль должен содержать хотя бы один спецсимвол"
    
    return True, ""


def validate_email(email: str) -> tuple[bool, str]:
    """Валидация email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Некорректный формат email"
    return True, ""
