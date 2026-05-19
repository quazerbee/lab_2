from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Email пользователя для регистрации",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Пароль пользователя. Должен содержать от 8 до 128 символов.",
        examples=["StrongPassword123"],
    )


class LoginRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Email пользователя для входа",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Пароль пользователя",
        examples=["StrongPassword123"],
    )


class AuthResponse(BaseModel):
    message: str = Field(
        ...,
        description="Сообщение о результате операции",
        examples=["User logged in successfully"],
    )
    user: UserResponse = Field(
        ...,
        description="Данные авторизованного пользователя без чувствительной информации",
    )


class MessageResponse(BaseModel):
    message: str = Field(
        ...,
        description="Сообщение о результате операции",
        examples=["Operation completed successfully"],
    )


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Email пользователя, для которого нужно сгенерировать токен сброса пароля",
        examples=["user@example.com"],
    )


class ForgotPasswordResponse(BaseModel):
    message: str = Field(
        ...,
        description="Сообщение о результате запроса на сброс пароля",
        examples=["Password reset token generated successfully"],
    )
    reset_token: str = Field(
        ...,
        description="Токен для сброса пароля. В учебном проекте возвращается в ответе, в реальных приложениях обычно отправляется по email.",
        examples=["reset-token-example"],
    )


class ResetPasswordRequest(BaseModel):
    token: str = Field(
        ...,
        description="Токен сброса пароля",
        examples=["reset-token-example"],
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Новый пароль пользователя. Должен содержать от 8 до 128 символов.",
        examples=["NewStrongPassword123"],
    )