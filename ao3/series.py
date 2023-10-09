from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from lxml import html

from ._selectors import SERIES_SELECTORS
from .abc import BookmarkableMixin, Object, Page, SubscribableMixin
from .errors import UnloadedError
from .user import User
from .utils import cached_slot_property, int_or_none


if TYPE_CHECKING:
    from .http import HTTPClient
    from .work import Work

__all__ = ("Series",)


class Series(Page, BookmarkableMixin, SubscribableMixin):
    """A series on AO3.

    This implements the following:

    - :class:`Page`
    - :class:`BookmarkableMixin`
    - :class:`SubscribableMixin`
    """

    __slots__ = (
        "_id",
        "_http",
        "_element",
        "_authenticity_token",
        "_cs_bookmark_id",
        "_cs_sub_id",
        "_cs_name",
        "_cs_creators",
        "_cs_date_begun",
        "_cs_date_updated",
        "_cs_description",
        "_cs_notes",
        "_cs_nwords",
        "_cs_nworks",
        "_cs_is_complete",
        "_cs_nbookmarks",
        "_cs_works_list",
    )

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
            return __value.id == self.id
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self.__class__.__name__, self.id))

    def __repr__(self) -> str:
        return f"{type(self).__name__}(name={self.name!r} id={self.id!r})"

    @property
    def id(self) -> int:
        """:class:`int`: The series's ID."""

        return self._id

    @property
    def subable_type(self) -> str:
        return "Series"

    @cached_slot_property("_cs_sub_id")
    def sub_id(self) -> int | None:
        if self.raw_element is None or not self._http.state:
            return None
        try:
            sub_el = SERIES_SELECTORS["sub_btn"](self.raw_element)[0]
            return int(text.split("/")[-1]) if (text := sub_el.get("action", None)) else None
        except (IndexError, ValueError):
            return None

    @property
    def url(self) -> str:
        """:class:`str`: The series's base URL."""

        return f"https://archiveofourown.org/series/{self.id}"

    @cached_slot_property("_cs_name")
    def name(self) -> str:
        """:class:`str`: The series name."""

        if self.raw_element is None:
            raise UnloadedError
        try:
            return str(SERIES_SELECTORS["name"](self.raw_element)[0].text).strip()
        except (IndexError, ValueError):
            return ""

    @cached_slot_property("_cs_creators")
    def creators(self) -> tuple[Object, ...]:
        """tuple[:class:`Object`, ...]The series's creators, minimized as :class:`ao3.Object`s."""

        if self.raw_element is None:
            raise UnloadedError
        return tuple(
            Object(name=el.get("href", "").split("/")[1], type=User)
            for el in SERIES_SELECTORS["creators"](self.raw_element)
        )

    @cached_slot_property("_cs_date_begun")
    def date_begun(self) -> datetime.datetime | None:
        """:class:`datetime.datetime` | None: The date the series began.

        Might be None, which means unknown.
        """

        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(SERIES_SELECTORS["dates"](self.raw_element)[1].text)
            return datetime.datetime.strptime(text or "", "%Y-%m-%d").astimezone()
        except (IndexError, ValueError):
            return None

    @cached_slot_property("_cs_date_updated")
    def date_updated(self) -> datetime.datetime | None:
        """:class:`datetime.datetime` | None: The date the series was last updated.

        Might be None, which means unknown.
        """

        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(SERIES_SELECTORS["dates"](self.raw_element)[2].text)
            return datetime.datetime.strptime(text or "", "%Y-%m-%d").astimezone()
        except (IndexError, ValueError):
            return None

    @cached_slot_property("_cs_description")
    def description(self) -> str:
        """:class:`str`: The series's description."""

        if self.raw_element is None:
            return ""
        try:
            return str(SERIES_SELECTORS["descr"](self.raw_element)[0].text_content())
        except (IndexError, ValueError):
            return ""

    @cached_slot_property("_cs_notes")
    def notes(self) -> str:
        """:class:`str`: Any notes the creators have written for the series."""

        if self.raw_element is None:
            return ""
        try:
            return str(SERIES_SELECTORS["descr"](self.raw_element)[1].text_content())
        except (IndexError, ValueError):
            return ""

    @cached_slot_property("_cs_nwords")
    def nwords(self) -> int:
        """:class:`int`: The total number of words in the series so far."""

        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(SERIES_SELECTORS["stats"](self.raw_element)[0].text_content())
            return num if (num := int_or_none(text)) else 0
        except (IndexError, ValueError):
            return 0

    @cached_slot_property("_cs_nworks")
    def nworks(self) -> int:
        """:class:`int`: The number of works in the series so far."""

        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(SERIES_SELECTORS["stats"](self.raw_element)[1].text_content())
            return num if (num := int_or_none(text)) else 0
        except (IndexError, ValueError):
            return 0

    @cached_slot_property("_cs_nworks")
    def is_complete(self) -> bool:
        """:class:`bool`: Whether the series is complete. Defaults to False if unknown."""

        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(SERIES_SELECTORS["stats"](self.raw_element)[2].text_content())
        except (IndexError, ValueError):
            return False
        else:
            return text == "No"

    @cached_slot_property("_cs_nbookmarks")
    def nbookmarks(self) -> int:
        """:class:`int`: The number of bookmarks on this series."""
        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(SERIES_SELECTORS["stats"](self.raw_element)[3].text_content())
            return result if (result := int_or_none(text)) else 0
        except (IndexError, ValueError):
            return 0

    @property
    def stats(self) -> tuple[int, int, bool, int]:
        """tuple[:class:`int', :class:`int', :class:`bool', :class:`int']: A tuple with the most common series stats.

        This includes the number of words, number of works, completion status, and number of bookmarks.
        """

        return (self.nwords, self.nworks, self.is_complete, self.nbookmarks)

    @cached_slot_property("_cs_works_list")
    def works_list(self) -> tuple[Work, ...]:
        """tuple[:class:`Work`, ...]: A tuple of works that make up this series.

        This may take time to load, but will be cached for later references.
        """

        from .work import Work  # To avoid an import cycle.

        if self.raw_element is None:
            raise UnloadedError
        return tuple(
            Work._from_banner(self._http, el, self.authenticity_token)
            for el in SERIES_SELECTORS["works"](self.raw_element)
        )

    async def reload(self) -> None:
        text = await self._http.get_series(self.id)
        self._element = html.fromstring(text)

        # Reset cached properties.
        slots = set(self.__slots__).difference(("_id", "_http", "_element"))
        for attr in slots:
            delattr(self, attr)
