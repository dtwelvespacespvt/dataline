import logging

from fastapi import Depends

from dataline.models.user.enums import UserRoles
from dataline.models.user.model import UserConfig, UserModel
from dataline.repositories.base import AsyncSession
from dataline.repositories.user import UserRepository, UserCreate


logger = logging.getLogger(__name__)


class UserService:
    user_repo: UserRepository


    def __init__(
        self,
        user_repo: UserRepository = Depends(UserRepository)
    ) -> None:
        self.user_repo = user_repo

    async def create_user(self, session:AsyncSession, user:UserCreate)-> UserModel:

        if existing_user:=await self.user_repo.get_by_email(session, user.email):
            return existing_user

        admin_user = await self.user_repo.get_one_by_role(session, UserRoles.ADMIN.value)

        if admin_user:
            user.openai_api_key = admin_user.openai_api_key
            user.langsmith_api_key = admin_user.langsmith_api_key
            user.analytics_enabled = admin_user.analytics_enabled
            user.preferred_openai_model = admin_user.preferred_openai_model

        user.config = UserConfig(connections=[])
        return await self.user_repo.create(session, user)

    async def get_all_users(self, session:AsyncSession):
        return await self.user_repo.list_all(session)
