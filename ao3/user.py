from __future__ import annotations

import datetime
import re
from typing import TYPE_CHECKING, Any

from lxml import html

from ._selectors import USER_SELECTORS
from .abc import Page, SubscribableMixin
from .errors import UnloadedError
from .utils import cached_slot_property


if TYPE_CHECKING:
    from .http import HTTPClient


__all__ = ("User",)

NUM_MATCH = re.compile(r".*\((?P<id>\d*)\)")


class User(Page, SubscribableMixin):
    __slots__ = (
        "username",
        "_id",
        "_http",
        "_element",
        "_authenticity_token",
        "_cs_sub_id",
        "_cs_avatar_url",
        "_cs_pseuds",
        "_cs_date_joined",
        "_cs_nworks",
        "_cs_nseries",
        "_cs_nbookmarks",
        "_cs_ncollections",
        "_cs_ngifts",
    )
    username: str

    def __init__(
        self,
        http: HTTPClient,
        *,
        payload: dict[str, Any] | None = None,
        element: html.HtmlElement | None = None,
    ) -> None:
        self._http = http
        if payload:
            for attr, val in payload.items():
                setattr(self, attr, val)
        self._element = element

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, self.__class__):
            return __value.username == self.username
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.__class__.__name__, self.username))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(username={self.username!r} id={self.id!r})"

    @cached_slot_property("_id")
    def id(self) -> int:
        if self.raw_element is None:
            raise UnloadedError
        try:
            return int(str(USER_SELECTORS["profile_info"](self.raw_element)[2].text))
        except (IndexError, ValueError):
            return 0

    @property
    def subable_type(self) -> str:
        return "User"

    @cached_slot_property("_cs_sub_id")
    def sub_id(self) -> int | None:
        if self.raw_element is None or not self._http.state:
            return None
        try:
            sub_el = USER_SELECTORS["sub_id"](self.raw_element)[0]
            return int(text.split("/")[-1]) if (text := sub_el.get("action", None)) else None
        except (IndexError, ValueError):
            return None

    @property
    def url(self) -> str:
        return f"https://archiveofourown.org/users/{self.username}"

    @cached_slot_property("_cs_avatar_url")
    def avatar_url(self) -> str:
        if self.raw_element is None:
            raise UnloadedError
        try:
            return str(USER_SELECTORS["avatar"](self.raw_element)[0].get("src", None))
        except (IndexError, ValueError):
            return ""

    @cached_slot_property("_cs_pseuds")
    def pseuds(self) -> tuple[str, ...]:
        if self.raw_element is None:
            raise UnloadedError
        return tuple(str(el.text) for el in USER_SELECTORS["pseuds"](self.raw_element))

    @cached_slot_property("_cs_date_joined")
    def date_joined(self) -> datetime.datetime | None:
        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(USER_SELECTORS["profile_info"](self.raw_element)[1].text)
            return datetime.datetime.strptime(text, "%Y-%m-%d").astimezone()
        except (IndexError, ValueError):
            return None

    @cached_slot_property("_cs_bio")
    def bio(self) -> str:
        if self.raw_element is None:
            raise UnloadedError
        try:
            return str(USER_SELECTORS["bio"](self.raw_element)[0].text_content())
        except (IndexError, ValueError):
            return ""

    @cached_slot_property("_cs_nworks")
    def nworks(self) -> int:
        if self.raw_element is None:
            raise UnloadedError
        try:
            el_text = str(USER_SELECTORS["nworks"](self.raw_element)[0].text_content())
            num_match = NUM_MATCH.search(el_text)
            return int(num_match[1]) if num_match else 0
        except (IndexError, ValueError):
            return 0

    @cached_slot_property("_cs_nseries")
    def nseries(self) -> int:
        if self.raw_element is None:
            raise UnloadedError
        try:
            el_text = str(USER_SELECTORS["nseries"](self.raw_element)[0].text_content())
            num_match = NUM_MATCH.search(el_text)
            return int(num_match[1]) if num_match else 0
        except (IndexError, ValueError):
            return 0

    @cached_slot_property("_cs_nbookmarks")
    def nbookmarks(self) -> int:
        if self.raw_element is None:
            raise UnloadedError
        try:
            el_text = str(USER_SELECTORS["nbookmarks"](self.raw_element)[0].text_content())
            num_match = NUM_MATCH.search(el_text)
            return int(num_match[1]) if num_match else 0
        except (IndexError, ValueError):
            return 0

    @cached_slot_property("_cs_ncollections")
    def ncollections(self) -> int:
        if self.raw_element is None:
            raise UnloadedError
        try:
            el_text = str(USER_SELECTORS["ncollections"](self.raw_element)[0].text_content())
            num_match = NUM_MATCH.search(el_text)
            return int(num_match[1]) if num_match else 0
        except (IndexError, ValueError):
            return 0

    @cached_slot_property("_cs_ngifts")
    def ngifts(self) -> int:
        if self.raw_element is None:
            raise UnloadedError
        try:
            el_text = str(USER_SELECTORS["ngifts"](self.raw_element)[0].text_content())
            num_match = NUM_MATCH.search(el_text)
            return int(num_match[1]) if num_match else 0
        except (IndexError, ValueError):
            return 0

    async def reload(self) -> None:
        text = await self._http.get_user(self.username)
        self._element = html.fromstring(text)

        # Reset relevant cached properties.
        slots = set(self.__slots__).difference(("username", "_id", "_http", "_element"))
        for attr in slots:
            delattr(self, attr)
