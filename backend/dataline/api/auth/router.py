import base64
from fastapi.params import Depends
from google.oauth2 import id_token
from google.auth.transport import requests
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Response, Body, HTTPException
from logging import getLogger
from jose import jwt
from pydantic import BaseModel

from dataline.config import config
from dataline.models.user.enums import UserRoles
from dataline.repositories.base import AsyncSession, get_session
from dataline.auth import validate_credentials
from dataline.repositories.user import UserCreate, UserRepository
from dataline.services.user import UserService
from dataline.utils.posthog import posthog_capture

logger = getLogger()

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"description": "Incorrect username or password"}},
)


class GoogleCredentials(BaseModel):
    credential:str

@router.post("/login")
async def login(
    username: Annotated[str, Body()],
    password: Annotated[str, Body()],
    response: Response,
    background_tasks: BackgroundTasks,
    session:Annotated[AsyncSession, Depends(get_session)],
    user_repo:Annotated[UserRepository, Depends(UserRepository)]
) -> Response:
    background_tasks.add_task(posthog_capture, "user_logged_in")

    validate_credentials(username, password)
    response.status_code = 200
    user = await user_repo.get_one_by_role(session, UserRoles.ADMIN.value)
    if not user:
        app_token_data = {"role": UserRoles.ADMIN.value, "name": UserRoles.ADMIN.value, "is_single_user": True}
    else:
        app_token_data = {"role": UserRoles.ADMIN.value, "name": UserRoles.ADMIN.value, "is_single_user": False, "user_id": str(user.id)}
    app_token = jwt.encode(app_token_data, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
    response.set_cookie(key="Authorization", value=f"Bearer {app_token}", httponly=True)
    return response


@router.post("/logout")
async def logout(response: Response) -> Response:
    response.status_code = 200
    response.delete_cookie(key="Authorization", secure=True, httponly=True)
    return response


@router.head("/login")
async def login_head() -> Response:
    return Response(status_code=200)

@router.post("/google")
async def google_login(token:GoogleCredentials, response: Response, session:Annotated[AsyncSession, Depends(get_session)], user_repo:Annotated[UserService, Depends(UserService)])-> Response:
    try:
        user = id_token.verify_oauth2_token(token.credential, requests.Request(), config.GOOGLE_CLIENT_ID)
        domain = user.get('email','').split('@')[-1]
        if config.ALLOWED_EMAIL_ORIGINS and domain not in config.ALLOWED_EMAIL_ORIGINS:
            raise HTTPException(status_code=401, detail="Domain is not whitelisted")

        newuser = UserCreate(name=user.get('name'), avatar_url = user.get('picture', ''), email = user.get('email'))
        created_user = await user_repo.create_user(session, newuser)
        app_token_data = {"role": created_user.role, "name": created_user.name, "user_id": str(created_user.id), "is_single_user": False}
        app_token = jwt.encode(app_token_data, config.JWT_SECRET, algorithm=config.JWT_ALGORITHM)
        response.set_cookie(key="Authorization", value=f"Bearer {app_token}", httponly=True)
    except ValueError as e:
        logger.exception("Invalid Google Token: {}".format(e))
        raise HTTPException(status_code=401, detail="Invalid Google Token")

    response.status_code = 200
    return response
