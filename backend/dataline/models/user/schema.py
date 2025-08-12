import logging
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_serializer, EmailStr

from dataline.models.user.enums import UserRoles
from dataline.repositories.user import UserConfig
from uuid import UUID

logger = logging.getLogger(__name__)


class UserUpdateIn(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=250)
    openai_api_key: Optional[SecretStr] = Field(None, min_length=4)
    openai_base_url: str | None = Field(None, min_length=4)
    langsmith_api_key: Optional[SecretStr] = Field(None, min_length=4)
    preferred_openai_model: Optional[str] = None
    sentry_enabled: Optional[bool] = None
    analytics_enabled: Optional[bool] = None

    @field_serializer("openai_api_key")
    def dump_openai_api_key(self, v: SecretStr) -> str:
        return v.get_secret_value()

    @field_serializer("langsmith_api_key")
    def dump_langsmith_api_key(self, v: SecretStr | None) -> str | None:
        return v.get_secret_value() if v else None

class UserUpdateAdmin(BaseModel):
    id: UUID
    name: Optional[str] = Field(None, min_length=1, max_length=250)
    sentry_enabled: Optional[bool] = None
    analytics_enabled: Optional[bool] = None
    role: Optional[str] = UserRoles.USER.value
    config: Optional[UserConfig] = None



class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[UUID] = None
    name: Optional[str] = None
    openai_api_key: Optional[SecretStr] = None
    openai_base_url: str | None = None
    langsmith_api_key: Optional[SecretStr] = None
    preferred_openai_model: Optional[str] = None
    sentry_enabled: bool
    analytics_enabled: Optional[bool] = None
    config: Optional[UserConfig] = None
    role: Optional[UserRoles] = None
    email: Optional[EmailStr] = None



class UserWithKeys(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None

    openai_api_key: SecretStr
    openai_base_url: str | None = None
    langsmith_api_key: SecretStr | None = None
    preferred_openai_model: str
    sentry_enabled: bool
    analytics_enabled: Optional[bool] = None


class AvatarOut(BaseModel):
    blob: str
