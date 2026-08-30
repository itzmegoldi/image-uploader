from pydantic import BaseModel, Field, field_validator


class UploadImageFields(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value: str) -> str:
        return value.strip()


class UploadImageFile(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str
    content: bytes

    @property
    def size(self) -> int:
        return len(self.content)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: bytes) -> bytes:
        if not value:
            raise ValueError("Image cannot be empty")

        # Example: 10 MB maximum
        max_size = 10 * 1024 * 1024

        if len(value) > max_size:
            raise ValueError("Image size cannot exceed 10 MB")

        return value


class ListImagesRequest(BaseModel):
    user_id: str = Field(
        min_length=1,
        max_length=100,
    )

    page_size: int = Field(
        default=10,
        ge=1,
        le=100,
    )

    next_token: str | None = None


class GetImageUrlRequest(BaseModel):
    user_id: str = Field(
        min_length=1,
        max_length=100,
    )
    image_id: str = Field(
        min_length=1,
        max_length=100,
    )
