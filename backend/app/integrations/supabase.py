from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class SupabaseConfig:
    project_url: str | None
    anon_key: str | None
    service_role_key: str | None

    @property
    def is_configured(self) -> bool:
        return bool(self.project_url and self.anon_key and self.service_role_key)


def get_supabase_config() -> SupabaseConfig:
    return SupabaseConfig(
        project_url=settings.supabase_project_url,
        anon_key=settings.supabase_anon_key,
        service_role_key=settings.supabase_service_role_key,
    )
