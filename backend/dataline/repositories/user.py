from typing import Optional, Type, List

from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy import select

from dataline.models.user.enums import UserRoles
from dataline.models.user.model import UserModel
from dataline.repositories.base import AsyncSession, BaseRepository, NotFoundError

class UserConfig(BaseModel):
    connections: List[str]

class UserCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    name: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_base_url: str | None = None
    langsmith_api_key: Optional[str] = None
    preferred_openai_model: Optional[str] = None
    sentry_enabled: Optional[bool] = True
    analytics_enabled: Optional[bool] = True
    avatar_url: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = UserRoles.USER.value
    config: Optional[UserConfig] = None


class UserUpdate(UserCreate):
    sentry_enabled: Optional[bool] = None
    analytics_enabled: Optional[bool] = None


class UserRepository(BaseRepository[UserModel, UserCreate, UserUpdate]):
    @property
    def model(self) -> Type[UserModel]:
        return UserModel

    async def get_one_or_none(self, session: AsyncSession) -> Optional[UserModel]:
        query = select(self.model)
        try:
            return  await self.first(session, query=query)
        except NotFoundError:
            return None

    async def get_by_email(self, session:AsyncSession, email:str) -> Optional[UserModel]:
        query = select(self.model).where(self.model.email==email)
        try:
            return await self.first(session, query=query)
        except NotFoundError:
            return None

    async def get_one_by_role(self, session:AsyncSession, role:UserRoles):
        query = select(self.model).where(self.model.role==role).limit(1)
        try:
            return await self.first(session, query)
        except NotFoundError:
            return None

