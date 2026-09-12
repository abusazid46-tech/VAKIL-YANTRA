from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import httpx

from app.core.config import settings


class StorageError(RuntimeError):
    pass


@dataclass(frozen=True)
class StoredObject:
    bucket: str
    path: str
    size_bytes: int


class SupabaseStorageGateway:
    def __init__(self) -> None:
        if not settings.supabase_project_url or not settings.supabase_service_role_key:
            raise StorageError("Supabase storage is not configured")
        self.base_url = settings.supabase_project_url.rstrip("/")
        self.bucket = settings.supabase_storage_bucket
        self.headers = {
            "apikey": settings.supabase_service_role_key,
            "Authorization": f"Bearer {settings.supabase_service_role_key}",
        }

    def ensure_bucket(self) -> None:
        existing = httpx.get(
            f"{self.base_url}/storage/v1/bucket/{self.bucket}",
            headers=self.headers,
            timeout=20,
        )
        if existing.status_code == 200:
            return
        payload = {"id": self.bucket, "name": self.bucket, "public": False}
        response = httpx.post(
            f"{self.base_url}/storage/v1/bucket",
            headers={**self.headers, "Content-Type": "application/json"},
            json=payload,
            timeout=20,
        )
        if response.status_code in {200, 201, 409} or (
            response.status_code == 400 and "exist" in response.text.lower()
        ):
            return
        raise StorageError(f"Could not create storage bucket: {response.status_code}")

    def upload_bytes(self, path: str, content: bytes, content_type: str) -> StoredObject:
        self.ensure_bucket()
        encoded_path = quote(path, safe="/")
        response = httpx.post(
            f"{self.base_url}/storage/v1/object/{self.bucket}/{encoded_path}",
            headers={
                **self.headers,
                "Content-Type": content_type,
                "x-upsert": "false",
            },
            content=content,
            timeout=60,
        )
        if response.status_code not in {200, 201}:
            raise StorageError(f"Could not upload object: {response.status_code}")
        return StoredObject(bucket=self.bucket, path=path, size_bytes=len(content))

    def create_signed_download_url(self, path: str, expires_in_seconds: int = 600) -> str:
        encoded_path = quote(path, safe="/")
        response = httpx.post(
            f"{self.base_url}/storage/v1/object/sign/{self.bucket}/{encoded_path}",
            headers={**self.headers, "Content-Type": "application/json"},
            json={"expiresIn": expires_in_seconds},
            timeout=20,
        )
        if response.status_code != 200:
            raise StorageError(f"Could not sign object: {response.status_code}")
        data = response.json()
        signed_url = data.get("signedURL") or data.get("signedUrl")
        if not signed_url:
            raise StorageError("Supabase did not return a signed URL")
        if signed_url.startswith("http"):
            return signed_url
        return f"{self.base_url}/storage/v1{signed_url}"


def get_storage_gateway() -> SupabaseStorageGateway:
    return SupabaseStorageGateway()
