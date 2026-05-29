"""认证 API — 登录 + 注册 + 个人资料"""
from datetime import timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
)
from app.core.config import get_settings
from app.core.response import ApiResponse, ok
from app.models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)


class UserPayload(BaseModel):
    """前端 User 类型对齐：types/index.ts"""

    id: str
    name: str
    email: str
    department_id: str
    department_name: str = ""
    role: str
    avatar: Optional[str] = None


class LoginPayload(BaseModel):
    token: str
    user: UserPayload


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    display_name: str = Field(..., min_length=1, max_length=64)
    department_id: str = Field(..., min_length=1, max_length=36)
    role: str = Field(default="member", pattern="^(admin|dept_head|member)$")
    email: str = Field(default="", max_length=128)


def _user_to_payload(user: User) -> UserPayload:
    return UserPayload(
        id=user.id,
        name=user.display_name,
        email=user.email or "",
        department_id=user.department_id,
        department_name=user.department_id,  # MVP：dept_name 暂时同 id，后续接 departments 表
        role=user.role,
    )


@router.post("/login", response_model=ApiResponse[LoginPayload])
async def login(request: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    """用户登录，返回 JWT token 和用户信息"""
    result = await db.execute(select(User).where(User.username == request.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已停用",
        )

    access_token = create_access_token(
        data={"sub": user.id, "role": user.role, "dept": user.department_id},
        expires_delta=timedelta(minutes=get_settings().jwt_expire_minutes),
    )

    return ok(LoginPayload(token=access_token, user=_user_to_payload(user)), message="登录成功")


@router.post("/register", response_model=ApiResponse[LoginPayload], status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    """注册新用户（开发环境方便测试）"""
    result = await db.execute(select(User).where(User.username == request.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="用户名已存在",
        )

    user = User(
        username=request.username,
        hashed_password=get_password_hash(request.password),
        display_name=request.display_name,
        department_id=request.department_id,
        role=request.role,
        email=request.email or None,
    )
    db.add(user)
    await db.flush()

    access_token = create_access_token(
        data={"sub": user.id, "role": user.role, "dept": user.department_id},
    )

    return ok(LoginPayload(token=access_token, user=_user_to_payload(user)), message="注册成功")


@router.get("/profile", response_model=ApiResponse[UserPayload])
async def get_profile(current_user: Annotated[User, Depends(get_current_user)]):
    """获取当前用户信息"""
    return ok(_user_to_payload(current_user))


@router.post("/logout", response_model=ApiResponse[dict])
async def logout(current_user: Annotated[User, Depends(get_current_user)]):
    """登出（MVP：客户端清 token 即可；V2 可加 token 黑名单）"""
    return ok({"logged_out": True}, message="已退出登录")
