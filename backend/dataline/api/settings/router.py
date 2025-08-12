import base64
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, BackgroundTasks

from dataline.auth import admin_required
from dataline.models.user.schema import AvatarOut, UserOut, UserUpdateIn, UserUpdateAdmin
from dataline.old_models import SuccessResponse
from dataline.repositories.base import AsyncSession, get_session
from dataline.services.settings import SettingsService
from dataline.services.user import UserService
from dataline.utils.posthog import posthog_capture

router = APIRouter(prefix="/settings", tags=["settings"])


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    settings_service: SettingsService = Depends(SettingsService),
    session: AsyncSession = Depends(get_session),
) -> SuccessResponse[AvatarOut]:
    background_tasks.add_task(posthog_capture, "avatar_uploaded")

    media = await settings_service.upload_avatar(session, file)
    blob_base64 = base64.b64encode(media.blob).decode("utf-8")
    return SuccessResponse(data=AvatarOut(blob=blob_base64))


@router.get("/avatar")
async def get_avatar(
    settings_service: SettingsService = Depends(SettingsService), session: AsyncSession = Depends(get_session)
) -> SuccessResponse[AvatarOut]:
    media = await settings_service.get_avatar_by_url(session)
    if media is None:
        raise HTTPException(status_code=404, detail="No user avatar found")

    blob_base64 = base64.b64encode(media.blob).decode("utf-8")
    return SuccessResponse(data=AvatarOut(blob=blob_base64))


@router.patch("/info")
async def update_info(
    data: UserUpdateIn,
    settings_service: SettingsService = Depends(SettingsService),
    session: AsyncSession = Depends(get_session)
) -> SuccessResponse[UserOut]:
    user_info = await settings_service.update_user_info(session, data)
    return SuccessResponse(data=user_info)

@router.get("/info")
async def get_info(
    settings_service: SettingsService = Depends(SettingsService), session: AsyncSession = Depends(get_session)) -> SuccessResponse[UserOut]:
    user_info = await settings_service.get_user_info(session)
    return SuccessResponse(data=user_info)

@router.patch('/users')
async def update_users(users: list[UserUpdateAdmin], session: AsyncSession = Depends(get_session), setting_service: SettingsService = Depends(SettingsService), _:None = Depends(admin_required))->SuccessResponse[list[UserOut]]:
    return SuccessResponse(data=await setting_service.update_users(session, users))

@router.get('/users')
async def get_all_users(session: Annotated[AsyncSession, Depends(get_session)],
                        user_service: Annotated[UserService, Depends(UserService)], _:None = Depends(admin_required)) -> list[UserOut]:
    return await user_service.get_all_users(session)