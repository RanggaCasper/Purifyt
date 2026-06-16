from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AppSetting


class AppSettingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, key: str) -> Optional[str]:
        result = await self.db.execute(select(AppSetting).where(AppSetting.key == key))
        setting = result.scalar_one_or_none()
        return setting.value if setting else None

    async def get_many(self, keys: list[str]) -> dict[str, Optional[str]]:
        if not keys:
            return {}
        result = await self.db.execute(select(AppSetting).where(AppSetting.key.in_(keys)))
        rows = {setting.key: setting.value for setting in result.scalars().all()}
        return {key: rows.get(key) for key in keys}

    async def set_many(self, values: dict[str, Optional[str]]) -> dict[str, Optional[str]]:
        current = await self.get_many(list(values.keys()))
        for key, value in values.items():
            if key in current and current[key] is not None:
                result = await self.db.execute(select(AppSetting).where(AppSetting.key == key))
                setting = result.scalar_one()
                setting.value = value
            else:
                self.db.add(AppSetting(key=key, value=value))
        await self.db.flush()
        return await self.get_many(list(values.keys()))
