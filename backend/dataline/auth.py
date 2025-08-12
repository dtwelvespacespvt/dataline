import binascii
import logging
import secrets
from base64 import b64decode
from typing import Optional, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel, EmailStr

from dataline.models.user.model import UserModel
from dataline.repositories.base import AsyncSession, get_session
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED
from jose import jwt
from uuid import UUID
from dataline.config import config
from dataline.models.user.enums import UserRoles
from dataline.repositories.user import UserRepository
from enum import Enum

logger = logging.getLogger(__name__)

class UserInfo(BaseModel):
    name: Optional[str] = None
    id: Optional[UUID] =None
    email: Optional[EmailStr] = None
    role: Optional[UserRoles] = None

class AuthType(Enum):
    GOOGLE = 'GOOGLE'
    BASIC = 'BASIC'
    NONE = 'NONE'


class HTTPBasicCustomized(HTTPBasic):
    # Override __call__ method to not send www-authenticate header back
    async def __call__(self, request: Request) -> Optional[HTTPBasicCredentials]:  # type: ignore
        authorization = request.cookies.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "basic":
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                )
            else:
                return None
        invalid_user_credentials_exc = HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
        try:
            data = b64decode(param).decode("ascii")
        except (ValueError, UnicodeDecodeError, binascii.Error):
            raise invalid_user_credentials_exc  # noqa: B904
        username, separator, password = data.partition(":")
        if not separator:
            raise invalid_user_credentials_exc
        return HTTPBasicCredentials(username=username, password=password)

class HTTPBearerCustomized(SecurityBase):

    async def __call__(self, request: Request, user_repo:Annotated[UserRepository, Depends(UserRepository)], session:Annotated[AsyncSession, Depends(get_session)]) -> UserInfo:
        token = request.cookies.get('Authorization')
        scheme, param = get_authorization_scheme_param(token)
        if not token:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Token not found")

        try:
            payload = jwt.decode(param, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
            user = await user_repo.get_by_uuid(session, UUID(payload.get('user_id')))
            user_info = UserInfo(email=user.email,role=user.role, id=user.id, name=user.name)
            return user_info

        except Exception as e:
            logger.error("Error while Processing Authorization Token: {}".format(e))
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid Token")



security = HTTPBearerCustomized() if config.AUTH_TYPE ==AuthType.GOOGLE.value else HTTPBasicCustomized() if config.AUTH_TYPE == AuthType.BASIC.value else None

def validate_credentials(username: str, password: str) -> bool:
    correct_username = secrets.compare_digest(username, str(config.auth_username))
    correct_password = secrets.compare_digest(password, str(config.auth_password))
    if not (correct_username and correct_password):
        # Do not send www-authenticate header back
        # as we do not want the browser to show a popup
        # FE will handle authentication
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return True

def validate_jwt_credentials(credentials:str) -> True:
    try:
        jwt.decode(credentials,config.JWT_SECRET,algorithms=[config.JWT_ALGORITHM])
        return True
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token",
        )


class AuthManager:

    def __init__(self, user_info=Depends(security), user_repo:UserRepository = Depends(UserRepository), session:AsyncSession=Depends(get_session)):
        self.user_info = user_info
        self.user_repo = user_repo
        self.session = session

    def __call__(self):
        return self.get_user_info()

    @classmethod
    def is_single_user_mode(cls) -> bool:
        return config.AUTH_TYPE != AuthType.GOOGLE.value

    def is_admin(self) -> bool:
        if self.is_single_user_mode():
            return True
        return self.user_info.role == UserRoles.ADMIN

    async def get_user_info(self) -> UserInfo | UserModel:
        if self.is_single_user_mode():
            return await self.user_repo.get_one_or_none(self.session)
        return self.user_info

    async def get_user_id(self) -> UUID:
        user = await self.get_user_info()
        return user.id


def get_auth_manager(
    user_info: UserInfo = Depends(security),
    user_repo: UserRepository = Depends(UserRepository),
    session: AsyncSession = Depends(get_session)
) -> AuthManager:
    return AuthManager(user_info, user_repo, session)

async def admin_required(auth_manager:Annotated[AuthManager, Depends(get_auth_manager)]):
    if auth_manager.is_admin():
        return True
    raise HTTPException(
        status_code=HTTP_401_UNAUTHORIZED,
        detail="Missing Permissions",
    )