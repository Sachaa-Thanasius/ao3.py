from __future__ import annotations

import asyncio
import logging
import sys
from collections.abc import Coroutine
from typing import Any, Literal, TypeAlias, TypeVar, overload
from urllib.parse import quote as uriquote

import aiohttp

from . import __version__
from .enums import Language, RatingId
from .errors import AuthError, HTTPException
from .utils import Constraint, extract_login_auth_token


T = TypeVar("T")
Coro: TypeAlias = Coroutine[Any, Any, T]
HTTPVerb: TypeAlias = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]

LOGGER = logging.getLogger(__name__)

__all__ = ("AO3_BASE", "HTTPClient")

AO3_BASE = "https://archiveofourown.org"


class Route:
    """A helper class for instantiating an HTTP request to AO3.

    Parameters
    ----------
    verb : :class:`str`
        The HTTP request to make, e.g. ``"GET"``.
    path : :class:`str`
        The prepended path to the API endpoint you want to hit, e.g. ``"/user/{user_id}/profile"``.
    **parameters : Any
        Special keyword arguments that will be substituted into the corresponding spot in the `path` where the key is
        present, e.g. if your parameters are ``user_id=1234`` and your path is ``"user/{user_id}/profile"``, the path
        will become ``"user/1234/profile"``.
    """

    __slots__ = ("verb", "path", "url")

    def __init__(self, verb: HTTPVerb, path: str, **parameters: Any) -> None:
        self.verb = verb
        self.path = path
        url = AO3_BASE + path
        if parameters:
            url = url.format_map({k: uriquote(v) if isinstance(v, str) else v for k, v in parameters.items()})
        self.url = url


class AuthState:
    __slots__ = ("login_token",)

    def __init__(self) -> None:
        self.login_token: str | None = None


class HTTPClient:
    """A small HTTP client that sends requests to AO3."""

    __slots__ = ("_session", "state", "user_agent")

    def __init__(self, *, _session: aiohttp.ClientSession | None = None) -> None:
        self._session = _session
        self.state = AuthState()
        user_agent = "bot: ao3.py (https://github.com/Sachaa-Thanasius/ao3.py {0} Python/{1[0]}.{1[1]} aiohttp/{2}"
        self.user_agent = user_agent.format(__version__, sys.version_info, aiohttp.__version__)

    @property
    def is_logged_in(self) -> bool:
        return self.state.login_token is not None

    def _start_session(self) -> None:
        if (not self._session) or self._session.closed:
            self._session = aiohttp.ClientSession()

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    @overload
    async def _request(self, route: Route, return_type: Literal["text"] = ..., **kwargs: Any) -> str:
        ...

    @overload
    async def _request(self, route: Route, return_type: Literal["raw"] = ..., **kwargs: Any) -> aiohttp.ClientResponse:
        ...

    async def _request(
        self,
        route: Route,
        return_type: Literal["text", "raw"] = "text",
        **kwargs: Any,
    ) -> str | aiohttp.ClientResponse:
        self._start_session()
        assert self._session

        headers = kwargs.pop("headers", {})
        if self.state.login_token is not None and ("authenticity_token" not in headers):
            if kwargs["data"] and "x-csrf-token" in kwargs["data"]:
                headers["authenticity_token"] = kwargs["data"]["x-csrf-token"]
            else:
                headers["authenticity_token"] = self.state.login_token
        headers["User-Agent"] = self.user_agent
        kwargs["headers"] = headers

        LOGGER.debug("Current request headers: %s", headers)
        LOGGER.debug("Current request url: %s", route.url)

        response: aiohttp.ClientResponse | None = None
        for tries in range(5):
            try:
                async with self._session.request(route.verb, route.url, **kwargs) as response:
                    retry = response.headers.get("retry-after", None)
                    LOGGER.debug("retry is: %s", retry)
                    if retry is not None:
                        retry = int(retry)

                    if 200 <= response.status < 300 or response.status == 302:
                        if return_type == "text":
                            return await response.text()
                        return response

                    if response.status == 429:
                        assert retry is not None
                        delta = retry + 1
                        LOGGER.warning("A ratelimit has been hit, sleeping for: %d", delta)
                        await asyncio.sleep(delta)
                        continue

                    if response.status in {500, 502, 503, 504}:
                        sleep_ = 1 + tries * 2
                        LOGGER.warning("Hit an API error, trying again in: %d", sleep_)
                        await asyncio.sleep(sleep_)
                        continue

                    LOGGER.exception("Unhandled HTTP error occured: %s -> %s", response.status, response)
                    raise HTTPException(response, "Unhandled HTTP error occured")
            except (aiohttp.ServerDisconnectedError, aiohttp.ServerTimeoutError):
                LOGGER.exception("Network error occured")
                await asyncio.sleep(5)

        if response is not None:
            raise HTTPException(response=response)

        msg = "Unreachable code in HTTP handling."
        raise RuntimeError(msg)

    async def _stream(self, route: Route, **kwargs: Any) -> aiohttp.StreamReader:
        self._start_session()
        assert self._session

        headers = kwargs.pop("headers", {})
        if self.state.login_token is not None and ("authenticity_token" not in headers):
            if kwargs["data"] and "x-csrf-token" in kwargs["data"]:
                headers["authenticity_token"] = kwargs["data"]["x-csrf-token"]
            else:
                headers["authenticity_token"] = self.state.login_token
        headers["User-Agent"] = self.user_agent
        kwargs["headers"] = headers

        LOGGER.debug("Current request headers: %s", headers)
        LOGGER.debug("Current request url: %s", route.url)

        try:
            async with self._session.request(route.verb, route.url, **kwargs) as response:
                return response.content
        except (aiohttp.ServerDisconnectedError, aiohttp.ServerTimeoutError):
            LOGGER.exception("Network error occured")
            await asyncio.sleep(5)

        msg = "Unreachable code in HTTP handling."
        raise RuntimeError(msg)

    async def login(self, username: str, password: str) -> None:
        route = Route("GET", "/users/login")
        text = await self._request(route)
        token = extract_login_auth_token(text)

        route = Route("POST", "/users/login")
        payload = {"user[login]": username, "user[password]": password, "authenticity_token": token}
        text = await self._request(route, params=payload, allow_redirects=False)
        self.state.login_token = extract_login_auth_token(text)

    async def logout(self) -> None:
        route = Route("POST", "/users/logout")
        data = {"_method": "delete"}
        await self._request(route, data=data)

    def get_languages(self) -> Coro[str]:
        route = Route("GET", "/languages")
        return self._request(route)

    def get_fandoms(self, fandom_key: str) -> Coro[str]:
        route = Route("GET", "/media/{key}/fandoms", key=fandom_key)
        return self._request(route)

    def get_user(self, username: str) -> Coro[str]:
        # Just go straight to the profile, I guess?
        route = Route("GET", "/users/{username}/profile", username=username)
        return self._request(route)

    def get_user_profile(self, username: str) -> Coro[str]:
        route = Route("GET", "/users/{username}/profile", username=username)
        return self._request(route)

    def get_user_works(self, username: str, page: int = 1) -> Coro[str]:
        route = Route("GET", "/users/{username}/works", username=username)
        payload = {"page": page}
        return self._request(route, params=payload)

    def get_user_bookmarks(self, username: str, page: int = 1) -> Coro[str]:
        route = Route("GET", "/users/{username}/bookmarks", username=username)
        payload = {"page": page}
        return self._request(route, params=payload)

    def get_user_subscriptions(self, username: str, page: int = 1) -> Coro[str]:
        route = Route("GET", "/users/{username}/subscriptions", username=username)
        payload = {"page": page}
        return self._request(route, params=payload)

    def get_user_history(
        self,
        username: str,
        page: int = 1,
        marked_later: bool = False,
    ) -> Coro[str]:
        route = Route("GET", "/users/{username}/readings", username=username)
        payload: dict[str, Any] = {"page": page}
        if marked_later:
            payload["show"] = "to-read"
        return self._request(route, params=payload)

    def get_user_work_statistics(self, username: str, year: int | Literal["All Years"]) -> Coro[str]:
        route = Route("GET", "/users/{username}/stats", username=username)
        payload = {"year": year}
        return self._request(route, params=payload)

    def get_work(self, work_id: int, *, load: bool = False) -> Coro[str]:
        route = Route("GET", "/works/{id}", id=work_id)
        payload = {"view_adult": "true"}
        if load:
            payload["view_full_work"] = "true"
        return self._request(route, params=payload)

    def get_work_download_stream(
        self,
        work_id: int,
        work_title: str,
        filetype: Literal["AZW3", "EPUB", "MOBI", "PDF", "HTML"],
    ) -> Coro[aiohttp.StreamReader]:
        filename = f"{work_title}.{filetype.lower()}"
        route = Route("GET", "/downloads/{id}/{filename}}", id=work_id, filename=filename)
        return self._stream(route)

    def get_series(self, series_id: int) -> Coro[str]:
        route = Route("GET", "/series/{id}", id=series_id)
        return self._request(route)

    def get_chapter(
        self,
        chapter_id: int,
        show_comments: bool = False,
        comment_page: int = 1,
    ) -> Coro[str]:
        route = Route("GET", "/chapters/{id}", id=chapter_id)
        payload: dict[str, Any] = {"view_adult": "true"}
        if show_comments:
            payload.update({"show_comments": "true", "comment_page": comment_page})
        return self._request(route, params=payload)

    def search_works(
        self,
        any_field: str = "",
        page: int = 1,
        title: str = "",
        author: str = "",
        revised_at: str = "",
        single_chapter: bool = False,
        word_count: Constraint | None = None,
        language_id: Language | None = None,
        fandom_names: str = "",
        character_names: str = "",
        relationship_names: str = "",
        freeform_names: str = "",
        rating_ids: RatingId | None = None,
        hits: Constraint | None = None,
        kudos_count: Constraint | None = None,
        crossover: Literal["T", "F"] | None = None,
        bookmarks_count: Constraint | None = None,
        excluded_tag_names: str = "",
        comments_count: Constraint | None = None,
        complete: Literal["T", "F"] | None = None,
        sort_column: str = "_score",
        sort_direction: Literal["asc", "desc"] = "desc",
    ) -> Coro[str]:
        route = Route("GET", "/works/search")
        payload = {
            "work_search[query]": any_field,
            "page": page,
            "work_search[title]": title,
            "work_search[creators]": author,
            "work_search[revised_at]": revised_at,
            "work_search[complete]": complete if complete is not None else "",
            "work_search[crossover]": crossover if crossover is not None else "",
            "work_search[single_chapter]": int(single_chapter),
            "work_search[word_count]": word_count.string() if word_count is not None else "",
            "work_search[language_id]": str(language_id) if language_id is not None else "",
            "work_search[fandom_names]": fandom_names,
            "work_search[rating_ids]": str(rating_ids) if rating_ids is not None else "",
            "work_search[character_names]": character_names,
            "work_search[relationship_names]": relationship_names,
            "work_search[freeform_names]": freeform_names,
            "work_search[hits]": hits.string() if hits is not None else "",
            "work_search[kudos_count]": kudos_count.string() if kudos_count is not None else "",
            "work_search[comments_count]": comments_count.string() if comments_count is not None else "",
            "work_search[bookmarks_count]": bookmarks_count.string() if bookmarks_count is not None else "",
            "work_search[sort_column]": sort_column,
            "work_search[sort_direction]": sort_direction,
        }
        if excluded_tag_names:
            payload["work_search[excluded_tag_names]"] = excluded_tag_names

        return self._request(route, params=payload)

    def search_people(self, any_field: str = "", name: str = "", fandom: str = "") -> Coro[str]:
        route = Route("GET", "/people/search")
        payload = {
            "people_search[query]": any_field,
            "people_search[name]": name,
            "people_search[fandom]": fandom,
        }
        return self._request(route, params=payload)

    def search_bookmarks(
        self,
        any_field: str = "",
        work_tags: str = "",
        type_: Literal["Work", "Series", "External Work"] | None = None,
        language_id: Language | None = None,
        work_updated: str = "",
        any_bookmark_field: str = "",
        bookmark_tags: str = "",
        bookmarker: str = "",
        recommended: bool = False,
        with_notes: bool = False,
        bookmark_date: str = "",
        sort_column: Literal["created_at", "bookmarkable_date"] | None = None,
    ) -> Coro[str]:
        route = Route("GET", "/bookmarks/search")
        payload = {
            "bookmark_search[bookmarkable_query]": any_field,
            "bookmark_search[other_tag_names]": work_tags,
            "bookmark_search[bookmarkable_type]": type_ if type_ is not None else "",
            "bookmark_search[language_id]": str(language_id) if language_id is not None else "",
            "bookmark_search[bookmarkable_date]": work_updated,
            "bookmark_search[bookmark_query]": any_bookmark_field,
            "bookmark_search[other_bookmark_tag_names]": bookmark_tags,
            "bookmark_search[bookmarker]": bookmarker,
            "bookmark_search[rec]": int(recommended),
            "bookmark_search[with_notes]": int(with_notes),
            "bookmark_search[date]": bookmark_date,
            "bookmark_search[sort_column]": sort_column if sort_column is not None else "",
        }
        return self._request(route, params=payload)

    def search_tags(
        self,
        name: str = "",
        fandoms: str = "",
        type_: Literal["Fandom", "Character", "Relationship", "Freeform"] | None = None,
        wranging_status: Literal["T", "F"] | None = None,
        sort_column: Literal["name", "created_at"] = "name",
        sort_direction: Literal["asc", "desc"] = "asc",
    ) -> Coro[str]:
        route = Route("GET", "/tags/search")
        payload = {
            "tag_search[name]": name,
            "tag_search[fandoms]": fandoms,
            "tag_search[type]": type_ if type_ is not None else "",
            "tag_search[canonical]": wranging_status if wranging_status is not None else "",
            "tag_search[sort_column]": sort_column,
            "tag_search[sort_direction]": sort_direction,
        }
        return self._request(route, params=payload)

    def get_comment(self, comment_id: str) -> Coro[str]:
        route = Route("GET", "/comments/{id}", id=comment_id)
        return self._request(route)

    def post_comment(
        self,
        ao3_object_id: int,
        comment_text: str,
        *,
        token: str | None = None,
        full_work: bool = False,
        reply_comment_id: int | None = None,
        email: str | None = None,
        name: str | None = None,
        pseud: str | None = None,
    ) -> Coro[str]:
        # TODO: Implement properly. Currently a stub. Needs authenticity token.
        route = Route("POST", "/comments.js")
        token = token or self.state.login_token
        if not token:
            raise AuthError

        # Assemble headers
        headers = {
            "X-NewRelic-ID": "VQcCWV9RGwIJVFFRAw==",
            "X-CSRF-Token": token,
            "X-Requested-With": "XMLHttpRequest",
        }

        # Assemble payload
        data: dict[str, Any] = {}

        temp_key = "work_id" if full_work else "chapter_id"
        data[temp_key] = ao3_object_id
        if reply_comment_id:
            data["comment_id"] = reply_comment_id

        if self.state.login_token is not None:
            pass

        return self._request(route, headers=headers, data=data)

    def delete_comment(self, comment_id: int) -> Coro[str]:
        # TODO: Implement properly. Currently a stub. Needs authenticity token.
        route = Route("POST", "/comments/{id}", id=comment_id)
        return self._request(route)

    def give_kudos(self, authenticity_token: str, kudoable_id: int, kudoable_type: str) -> Coro[aiohttp.ClientResponse]:
        route = Route("POST", "/kudos.js")
        headers = {
            "X-CSRF-Token": authenticity_token,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"https://archiveofourown.org/works/{kudoable_id}",
        }
        data = {
            "authenticity_token": authenticity_token,
            "kudo[commentable_id]": kudoable_id,
            "kudo[commentable_type]": kudoable_type,
        }
        return self._request(route, return_type="raw", headers=headers, data=data)

    def bookmark(
        self,
        authenticity_token: str,
        bookmarkable_path: str,
        notes: str = "",
        tags: list[str] | None = None,
        collections: list[str] | None = None,
        private: bool = False,
        recommend: bool = False,
        pseud_id: str = "",
    ) -> Coro[aiohttp.ClientResponse]:
        # TODO: Double-check implementation.
        route = Route("POST", "{bookmarkable_path}/bookmarks", bookmarkable_path=bookmarkable_path)

        if tags is None:
            tags = []
        if collections is None:
            collections = []

        data = {
            "authenticity_token": authenticity_token,
            "bookmark[pseud_id]": pseud_id,
            "bookmark[tag_string]": ",".join(tags),
            "bookmark[collection_names]": ",".join(collections),
            "bookmark[private]": int(private),
            "bookmark[rec]": int(recommend),
        }
        if notes:
            data["bookmark[bookmarker_notes]"] = notes
        return self._request(route, return_type="raw", data=data, allow_redirects=False)

    def delete_bookmark(self, authenticity_token: str, bookmark_id: int) -> Coro[aiohttp.ClientResponse]:
        # TODO: Double-check implementation.
        route = Route("POST", "bookmarks/{bookmark_id}", bookmark_id=bookmark_id)
        data = {"authenticity_token": authenticity_token, "_method": "delete"}
        return self._request(route, return_type="raw", data=data)

    def subscribe(
        self,
        authenticity_token: str,
        username: str,
        subable_id: int,
        subable_type: str,
    ) -> Coro[aiohttp.ClientResponse]:
        # FIXME: Get username from client user object?
        route = Route("POST", "/users/{username}/subscriptions", username=username)
        data = {
            "authenticity_token": authenticity_token,
            "subscription[subscribable_id]": subable_id,
            "subscription[subscribable_type]": subable_type,
        }
        return self._request(route, return_type="raw", data=data)

    def unsubscribe(
        self,
        authenticity_token: str,
        username: str,
        subable_id: int,
        subable_type: str,
        subscription_id: int,
    ) -> Coro[aiohttp.ClientResponse]:
        # FIXME: Get username from client user object?
        route = Route("POST", "/users/{username}/subscriptions/{sub_id}", username=username, sub_id=subscription_id)
        data = {
            "authenticity_token": authenticity_token,
            "subscription[subscribable_id]": subable_id,
            "subscription[subscribable_type]": subable_type,
            "_method": "delete",
        }
        return self._request(route, return_type="raw", data=data)

    def collect(self) -> Coro[aiohttp.ClientResponse]:
        # TODO: Implement properly. Currently a stub. Needs authenticity token.
        ...
