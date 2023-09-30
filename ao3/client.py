from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, TypeAlias, TypeVar

from lxml import html

from ao3.errors import LoginError

from .http import AuthState, HTTPClient
from .search import (
    BookmarkSearch,
    BookmarkSearchOptions,
    PeopleSearch,
    PeopleSearchOptions,
    TagSearch,
    TagSearchOptions,
    WorkSearch,
    WorkSearchOptions,
)
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

    async def login(self, username: str | None = None, password: str | None = None) -> None:
        if username and password:
            login_token, text = await self._http.login(username, password)
            element = html.fromstring(text)
            payload = {"username": username}
            self._http.state = AuthState(login_token or "", User(self._http, payload=payload, element=element))
        raise LoginError

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

    async def search_works(self, search_params: WorkSearchOptions) -> WorkSearch:
        text = await self._http.search_works(**search_params.to_dict())
        element = html.fromstring(text)
        payload = {"_search_params": search_params}
        return WorkSearch(self._http, payload=payload, element=element)

    async def generate_work_search_pages(
        self,
        search_params: WorkSearchOptions,
        start: int = 1,
        stop: int = 2,
        step: int = 1,
    ) -> AsyncGenerator[WorkSearch, None]:
        page_range_iter = iter(range(start, stop, step))
        for page_num in page_range_iter:
            search_params.page = page_num
            text = await self._http.search_works(**search_params.to_dict())
            element = html.fromstring(text)
            payload = {"_search_params": search_params}
            yield WorkSearch(self._http, payload=payload, element=element)

    async def search_people(
        self,
        page: int = 1,
        any_field: str = "",
        names: list[str] | None = None,
        fandoms: list[str] | None = None,
    ) -> PeopleSearch:
        name_str = ",".join(names) if names else ""
        fandom_str = ",".join(fandoms) if fandoms else ""
        text = await self._http.search_people(page, any_field, name_str, fandom_str)
        element = html.fromstring(text)
        payload = {"_search_params": PeopleSearchOptions(page, any_field, name_str, fandom_str)}
        return PeopleSearch(self._http, payload=payload, element=element)

    async def generate_people_search_pages(
        self,
        any_field: str = "",
        names: list[str] | None = None,
        fandoms: list[str] | None = None,
        start: int = 1,
        stop: int = 2,
        step: int = 1,
    ) -> AsyncGenerator[PeopleSearch, None]:
        page_range_iter = iter(range(start, stop, step))
        for page_num in page_range_iter:
            name_str = ",".join(names) if names else ""
            fandom_str = ",".join(fandoms) if fandoms else ""
            text = await self._http.search_people(page_num, any_field, name_str, fandom_str)
            element = html.fromstring(text)
            payload = {"_search_params": PeopleSearchOptions(page_num, any_field, name_str, fandom_str)}
            yield PeopleSearch(self._http, payload=payload, element=element)

    async def search_bookmarks(self, search_params: BookmarkSearchOptions) -> BookmarkSearch:
        text = await self._http.search_people(**search_params.to_dict())
        element = html.fromstring(text)
        payload = {"_search_params": search_params}
        return BookmarkSearch(self._http, payload=payload, element=element)

    async def generate_bookmark_search_pages(
        self,
        search_params: BookmarkSearchOptions,
        start: int = 1,
        stop: int = 2,
        step: int = 1,
    ) -> AsyncGenerator[BookmarkSearch, None]:
        page_range_iter = iter(range(start, stop, step))
        for page_num in page_range_iter:
            search_params.page = page_num
            text = await self._http.search_people(**search_params.to_dict())
            element = html.fromstring(text)
            payload = {"_search_params": search_params}
            yield BookmarkSearch(self._http, payload=payload, element=element)

    async def search_tags(self, search_params: TagSearchOptions) -> TagSearch:
        text = await self._http.search_people(**search_params.to_dict())
        element = html.fromstring(text)
        payload = {"_search_params": search_params}
        return TagSearch(self._http, payload=payload, element=element)

    async def generate_tag_search_pages(
        self,
        search_params: TagSearchOptions,
        start: int = 1,
        stop: int = 2,
        step: int = 1,
    ) -> AsyncGenerator[TagSearch, None]:
        page_range_iter = iter(range(start, stop, step))
        for page_num in page_range_iter:
            search_params.page = page_num
            text = await self._http.search_people(**search_params.to_dict())
            element = html.fromstring(text)
            payload = {"_search_params": search_params}
            yield TagSearch(self._http, payload=payload, element=element)
