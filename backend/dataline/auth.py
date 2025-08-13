import binascii
import logging
import secrets
from base64 import b64decode
from typing import Optional, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param
from pydantic import BaseModel

from dataline.repositories.base import AsyncSession, get_session
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED
from jose import jwt
from uuid import UUID
from dataline.config import config
from dataline.models.user.enums import UserRoles
from dataline.repositories.user import UserRepository

logger = logging.getLogger(__name__)

class UserInfo(BaseModel):
    name: Optional[str] = None
    id: Optional[UUID] =None
    role: Optional[UserRoles] = None
    is_single_user: Optional[bool] = False


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
            user_info = UserInfo(role=payload.get('role'), id=payload.get('user_id'), name=payload.get('name'), is_single_user= payload.get('is_single_user'))
            return user_info

        except Exception as e:
            logger.error("Error while Processing Authorization Token: {}".format(e))
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid Token")



security = HTTPBearerCustomized() if config.has_auth else None

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


    def is_admin(self) -> bool:
        return self.user_info.role == UserRoles.ADMIN or not config.has_auth

    async def get_user_info(self) -> UserInfo | None:
        if (self.user_info.is_single_user and not self.user_info.id) or not config.has_auth:
            return await self.user_repo.get_one_by_role(self.session, UserRoles.ADMIN.value)
        return self.user_info

    async def get_user_id(self) -> UUID:
        user = await self.get_user_info()
        return user.id if user else None


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