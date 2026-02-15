"""
API endpoints для авторизации
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import secrets
import logging

from app.db.session import get_db
from app.services.auth_service import AuthService
from app.services.google_oauth import GoogleOAuthService
from app.schemas.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest, TokenResponse,
    RefreshRequest,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest,
    VerifyEmailRequest, VerifyEmailResponse,
    ResendVerificationRequest, ResendVerificationResponse,
    UserResponse
)
from app.dependencies import get_current_user
from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()
auth_service = AuthService()
google_oauth = GoogleOAuthService()

# Хранилище state для OAuth (в production использовать Redis или БД)
oauth_states = {}


@router.post("/register", response_model=RegisterResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    # #region agent log
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Register endpoint called: email={request.email}, hasPassword={bool(request.password)}, hasDisplayName={bool(request.display_name)}")
    # #endregion
    try:
        # #region agent log
        logger.info("Before auth_service.register")
        # #endregion
        user = await auth_service.register(
            db, 
            request.email, 
            request.password, 
            request.display_name
        )
        # #region agent log
        logger.info(f"Register success: userId={user.id}")
        # #endregion
        return RegisterResponse(
            user_id=str(user.id), 
            email=user.email,
            message="Регистрация успешна"
        )
    except ValueError as e:
        # #region agent log
        logger.error(f"Register ValueError: {e}")
        # #endregion
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # #region agent log
        logger.exception(f"Register exception: {type(e).__name__}: {e}")
        # #endregion
        # Пробрасываем как HTTPException чтобы CORS заголовки были установлены
        raise HTTPException(status_code=500, detail=f"Ошибка при регистрации: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    user = await auth_service.authenticate(db, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    access_token = auth_service.create_access_token(str(user.id), user.role.value)
    refresh_token, refresh_hash = auth_service.create_refresh_token()
    await auth_service.create_session(
        db,
        str(user.id),
        refresh_token,
        user_agent=None,
        ip_address=None
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    # Отозвать сессию
    await auth_service.revoke_session(db, request.refresh_token)
    return {"message": "Вы вышли из системы"}


@router.post("/logout-all")
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Отозвать все сессии пользователя
    count = await auth_service.revoke_all_user_sessions(db, str(current_user.id))
    return {"message": f"Отозвано сессий: {count}"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    # Проверить refresh token в БД
    user = await auth_service.verify_refresh_token(db, request.refresh_token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный или истёкший refresh token"
        )
    
    # Создать новую пару токенов
    access_token = auth_service.create_access_token(str(user.id), user.role.value)
    new_refresh_token, _ = auth_service.create_refresh_token()
    
    # Отозвать старый refresh token и создать новый
    await auth_service.revoke_session(db, request.refresh_token)
    await auth_service.create_session(
        db,
        str(user.id),
        new_refresh_token
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    # Найти пользователя
    user = await auth_service.find_user_by_email(db, request.email)
    
    if user:
        # Сгенерировать reset_token
        token = await auth_service.set_reset_token(db, user)
        
        # TODO: Отправить email со ссылкой
        # В MVP можно просто логировать токен или использовать mock отправку
        if settings.DEBUG:
            print(f"Reset token for {user.email}: {token}")
            print(f"Reset URL: {settings.FRONTEND_URL}/reset-password?token={token}")
    
    # Всегда возвращать успех (безопасность)
    return ForgotPasswordResponse()


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    # Найти пользователя по reset_token
    user = await auth_service.reset_password(db, request.token, request.new_password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невалидный или истёкший токен сброса пароля"
        )
    
    return {"message": "Пароль успешно изменён"}


@router.get("/google")
async def google_login(request: Request):
    state = secrets.token_urlsafe(16)
    # Сохранить state в памяти (в production использовать Redis или БД)
    oauth_states[state] = True
    url = google_oauth.get_authorization_url(state)
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # Проверить state (в production проверять из Redis/БД)
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невалидный state параметр"
        )
    del oauth_states[state]
    
    try:
        # Обменять code на токены
        tokens = await google_oauth.exchange_code(code)
        
        # Получить информацию о пользователе
        user_info = await google_oauth.get_user_info(tokens["access_token"])
        
        # Найти или создать пользователя
        user = await auth_service.find_or_create_google_user(
            db,
            google_id=user_info["id"],
            email=user_info["email"],
            display_name=user_info.get("name"),
            avatar_url=user_info.get("picture")
        )
        
        # Создать JWT токены
        access_token = auth_service.create_access_token(str(user.id), user.role.value)
        refresh_token, _ = auth_service.create_refresh_token()
        
        await auth_service.create_session(
            db,
            str(user.id),
            refresh_token,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None
        )
        
        # Редирект на фронтенд с токенами
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка OAuth: {str(e)}"
        )


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    request: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db)
):
    """Верификация email по токену"""
    user = await auth_service.verify_email_token(db, request.token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невалидный или истёкший токен верификации"
        )
    
    return VerifyEmailResponse(message="Email успешно подтверждён")


@router.post("/resend-verification", response_model=ResendVerificationResponse)
async def resend_verification(
    request: ResendVerificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Повторная отправка письма с верификацией"""
    user = await auth_service.find_user_by_email(db, request.email)
    
    if not user:
        # Всегда возвращаем успех для безопасности
        return ResendVerificationResponse()
    
    if user.email_verified == 'true':
        return ResendVerificationResponse(message="Email уже подтверждён")
    
    # Генерируем новый токен
    token = await auth_service.set_verification_token(db, user)
    
    # TODO: Отправить email с токеном
    # В MVP можно просто логировать токен или использовать mock отправку
    if settings.DEBUG:
        print(f"Verification token for {user.email}: {token}")
        print(f"Verification URL: {settings.FRONTEND_URL}/verify-email?token={token}")
    
    return ResendVerificationResponse()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        role=current_user.role.value,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        email_verified=current_user.email_verified or 'false',
        created_at=current_user.created_at
    )
