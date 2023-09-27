from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias, TypeVar

from lxml import html

from .http import HTTPClient
from .series import Series
from .user import User
from .work import Work


if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self
else:
    Self: TypeAlias = Any

BE = TypeVar("BE", bound=BaseException)

__all__ = ("Client",)


class Client:
    def __init__(self) -> None:
        self._http = HTTPClient()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, ext_type: type[BE] | None, exc_val: BE | None, exc_tb: TracebackType | None) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http.close()

    async def get_work(self, work_id: int, *, load: bool = False) -> Work:
        text = await self._http.get_work(work_id, load=load)
        element = html.fromstring(text)
        payload = {"_id": work_id}
        return Work(self._http, payload=payload, element=element)

    async def get_series(self, series_id: int) -> Series:
        text = await self._http.get_series(series_id)
        element = html.fromstring(text)
        payload = {"_id": series_id}
        return Series(self._http, payload=payload, element=element)

    async def get_user(self, username: str, *, load: bool = False) -> User:
        text = await self._http.get_user(username)
        element = html.fromstring(text)
        payload = {"username": username}
        return User(self._http, payload=payload, element=element)
