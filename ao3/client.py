from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any, TypeAlias, TypeVar

from lxml import html

from .errors import LoginFailure
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
    """Represents a client that interacts with AO3's frontend."""

    def __init__(self) -> None:
        self._http = HTTPClient()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, ext_type: type[BE] | None, exc_val: BE | None, exc_tb: TracebackType | None) -> None:
        await self.close()

    @property
    def user(self) -> User | None:
        if state := self._http.state:
            return state.client_user
        return None

    async def close(self) -> None:
        await self._http.close()

    async def login(self, username: str | None = None, password: str | None = None) -> None:
        """Logs into AO3 with the specified credentials.

        Parameters
        ----------
        username : :class:`str` | None, optional
            The AO3 account username. By default None.
        password : :class:`str` | None, optional
            The AO3 account password. By default None.

        Raises
        ------
        LoginError
            Logging into your AO3 account failed, either due to wrong credentials or some other reason.
        """

        if username and password:
            login_token, text = await self._http.login(username, password)
            element = html.fromstring(text)
            payload = {"username": username}
            self._http.state = AuthState(login_token or "", User(self._http, payload=payload, element=element))
            return
        msg = "Please provide both a username and a password."
        raise LoginFailure(msg)

    async def get_work(self, work_id: int) -> Work:
        """Returns a work with the given ID.

        Parameters
        ----------
        work_id : :class:`int`
            The ID to search for.

        Returns
        -------
        :class:`Work`
            The found work.

        Raises
        ------
        HTTPException
            The id could not be used to find a valid work.
        """

        text = await self._http.get_work(work_id)
        element = html.fromstring(text)
        payload = {"_id": work_id}
        return Work(self._http, payload=payload, element=element)

    async def get_series(self, series_id: int) -> Series:
        """Returns a series with the given ID.

        Parameters
        ----------
        series_id : :class:`int`
            The ID to search for.

        Returns
        -------
        :class:`Series`
            The found series.

        Raises
        ------
        HTTPException
            The id could not be used to find a valid series.
        """

        text = await self._http.get_series(series_id)
        element = html.fromstring(text)
        payload = {"_id": series_id}
        return Series(self._http, payload=payload, element=element)

    async def get_user(self, username: str) -> User:
        """Returns a user with the given username.

        Parameters
        ----------
        username : :class:`str`
            The username to search for.

        Returns
        -------
        :class:`User`
            The found user.

        Raises
        ------
        HTTPException
            The username could not be used to find a valid user.
        """

        text = await self._http.get_user(username)
        element = html.fromstring(text)
        payload = {"username": username}
        return User(self._http, payload=payload, element=element)

    async def search_works(self, options: WorkSearchOptions) -> WorkSearch:
        """Search for works based in the given options.

        Parameters
        ----------
        options : :class:`WorkSearchOptions`
            The options with which to narrow the search. See :class:`WorkSearchOptions` for more information.

        Returns
        -------
        :class:`WorkSearch`
            A search result object.
        """

        text = await self._http.search_works(**options.to_dict())
        element = html.fromstring(text)
        payload = {"_search_options": options}
        return WorkSearch(self._http, payload=payload, element=element)

    async def work_search_pages(
        self,
        options: WorkSearchOptions,
        start: int = 1,
        stop: int = 2,
        step: int = 1,
    ) -> AsyncIterator[WorkSearch]:
        """Returns an asynchronous iterator for work search results based on the given options through multiple pages of
        results. It stops at the first empty results page.

        Parameters
        ----------
        options : :class:`WorkSearchOptions`
            The options with which to narrow the search. See :class:`WorkSearchOptions` for more information.
        start : :class:`int`, optional
            The starting page. By default 1.
        stop : :class:`int`, optional
            The stoping page, which won't be included in the final result. By default 2.
        step : :class:`int`, optional
            The step size through which to iterate through the pages. By default 1.

        Yields
        ------
        :class:`WorkSearch`
            The search result object holding the results for a particular page.
        """

        for page_num in range(start, stop, step):
            options.page = page_num
            page_results = await self.search_works(options)
            if len(page_results.results) == 0:
                raise StopAsyncIteration
            yield page_results

    async def search_people(
        self,
        page: int = 1,
        any_field: str = "",
        names: list[str] | None = None,
        fandoms: list[str] | None = None,
    ) -> PeopleSearch:
        """Search for people based in the given options.

        Parameters
        ----------
        page : :class:`int`, optional
            The page number of the results to get. By default 1.
        any_field : :class:`str`, optional
            Text which can apply to any of the below fields. By default the empty string.
        names : list[:class:`str`] | None, optional
            The names of the people to search. By default None.
        fandoms : list[:class:`str`] | None, optional
            The names of the fandoms within which to search. By default None.

        Returns
        -------
        :class:`PeopleSearch`
            A search result object.
        """

        name_str = ",".join(names) if names else ""
        fandom_str = ",".join(fandoms) if fandoms else ""
        text = await self._http.search_people(page, any_field, name_str, fandom_str)
        element = html.fromstring(text)
        payload = {"_search_options": PeopleSearchOptions(page, any_field, name_str, fandom_str)}
        return PeopleSearch(self._http, payload=payload, element=element)

    async def people_search_pages(
        self,
        any_field: str = "",
        names: list[str] | None = None,
        fandoms: list[str] | None = None,
        start: int = 1,
        stop: int = 2,
        step: int = 1,
    ) -> AsyncIterator[PeopleSearch]:
        """Returns an asynchronous iterator for people search results based on the given options through multiple pages
        of results. It stops at the first empty results page.

        Parameters
        ----------
        any_field : :class:`str`, optional
            Text which can apply to any of the below fields. By default the empty string.
        names : list[:class:`str`] | None, optional
            The names of the people to search. By default None.
        fandoms : list[:class:`str`] | None, optional
            The names of the fandoms within which to search. By default None.
        start : :class:`int`, optional
            The starting page. By default 1.
        stop : :class:`int`, optional
            The stoping page, which won't be included in the final result. By default 2.
        step : :class:`int`, optional
            The step size through which to iterate through the pages. By default 1.

        Yields
        ------
        :class:`PeopleSearch`
            The search result object holding the results for a particular page.
        """

        for page_num in range(start, stop, step):
            page_results = await self.search_people(page_num, any_field, names, fandoms)
            if len(page_results.results) == 0:
                raise StopAsyncIteration
            yield page_results

    async def search_bookmarks(self, options: BookmarkSearchOptions) -> BookmarkSearch:
        """Search for bookmarks based in the given options.

        Parameters
        ----------
        options : :class:`BookmarkSearchOptions`
            The options with which to narrow the search. See :class:`BookmarkSearchOptions` for more information.

        Returns
        -------
        :class:`BookmarkSearch`
            A search result object.
        """

        text = await self._http.search_bookmarks(**options.to_dict())
        element = html.fromstring(text)
        payload = {"_search_options": options}
        return BookmarkSearch(self._http, payload=payload, element=element)

    async def bookmark_search_pages(
        self,
        options: BookmarkSearchOptions,
        start: int = 1,
        stop: int = 2,
        step: int = 1,
    ) -> AsyncIterator[BookmarkSearch]:
        """Returns an asynchronous iterator for bookmark search results based on the given options through multiple
        pages of results. It stops at the first empty results page.

        Parameters
        ----------
        options : :class:`BookmarkSearchOptions`
            The options with which to narrow the search. See :class:`BookmarkSearchOptions` for more information.
        start : :class:`int`, optional
            The starting page. By default 1.
        stop : :class:`int`, optional
            The stoping page, which won't be included in the final result. By default 2.
        step : :class:`int`, optional
            The step size through which to iterate through the pages. By default 1.

        Yields
        ------
        :class:`BookmarkSearch`
            The search result object holding the results for a particular page.
        """

        for page_num in range(start, stop, step):
            options.page = page_num
            page_results = await self.search_bookmarks(options)
            if len(page_results.results) == 0:
                raise StopAsyncIteration
            yield page_results

    async def search_tags(self, options: TagSearchOptions) -> TagSearch:
        """Search for tags based in the given options.

        Parameters
        ----------
        options : :class:`TagSearchOptions`
            The options with which to narrow the search. See :class:`TagSearchOptions` for more information.

        Returns
        -------
        :class:`TagSearch`
            A search result object.
        """

        text = await self._http.search_people(**options.to_dict())
        element = html.fromstring(text)
        payload = {"_search_options": options}
        return TagSearch(self._http, payload=payload, element=element)

    async def tag_search_pages(
        self,
        options: TagSearchOptions,
        start: int = 1,
        stop: int = 2,
        step: int = 1,
    ) -> AsyncIterator[TagSearch]:
        """Returns an asynchronous iterator for tag search results based on the given options through multiple pages of
        results. It stops at the first empty results page.

        Parameters
        ----------
        options : :class:`TagSearchOptions`
            The options with which to narrow the search. See :class:`TagSearchOptions` for more information.
        start : :class:`int`, optional
            The starting page. By default 1.
        stop : :class:`int`, optional
            The stoping page, which won't be included in the final result. By default 2.
        step : :class:`int`, optional
            The step size through which to iterate through the pages. By default 1.

        Yields
        ------
        :class:`TagSearch`
            The search result object holding the results for a particular page.
        """

        for page_num in range(start, stop, step):
            options.page = page_num
            page_results = await self.search_tags(options)
            if len(page_results.results) == 0:
                raise StopAsyncIteration
            yield page_results
