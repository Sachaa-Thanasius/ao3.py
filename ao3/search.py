from __future__ import annotations

import dataclasses
import re
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar

from lxml import html

from ._selectors import SEARCH_SELECTOR
from .abc import Object, Page
from .enums import Language, RatingId
from .errors import UnloadedError
from .utils import Constraint, cached_slot_property


if TYPE_CHECKING:
    from .http import HTTPClient
    from .work import Work

R = TypeVar("R")
SP = TypeVar("SP", bound="SearchParams")

__all__ = (
    "WorkSearchParams",
    "PeopleSearchParams",
    "BookmarkSearchParams",
    "TagSearchParams",
    "Search",
)

TAG_SECTIONS = re.compile(r"(?P<type>.*): (?P<name>.*)\u200E\((?P<count>\d+)\)")


@dataclasses.dataclass(slots=True)
class TagResult:
    type: str
    name: str
    count: int


@dataclasses.dataclass(slots=True)
class SearchParams:
    page: int = 1

    def astuple(self) -> tuple[Any, ...]:
        return dataclasses.astuple(self)

    def asdict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(slots=True)
class WorkSearchParams(SearchParams):
    any_field: str = ""
    title: str = ""
    author: str = ""
    revised_at: str = ""
    single_chapter: bool = False
    word_count: Constraint | None = None
    language_id: Language | None = None
    fandom_names: str = ""
    character_names: str = ""
    relationship_names: str = ""
    freeform_names: str = ""
    rating_ids: RatingId | None = None
    hits: Constraint | None = None
    kudos_count: Constraint | None = None
    crossover: Literal["T", "F"] | None = None
    bookmarks_count: Constraint | None = None
    excluded_tag_names: str = ""
    comments_count: Constraint | None = None
    complete: Literal["T", "F"] | None = None
    sort_column: str = "_score"
    sort_direction: Literal["asc", "desc"] = "desc"


@dataclasses.dataclass(slots=True)
class PeopleSearchParams(SearchParams):
    any_field: str = ""
    names: str = ""
    fandoms: str = ""


@dataclasses.dataclass(slots=True)
class BookmarkSearchParams(SearchParams):
    any_field: str = ""
    work_tags: str = ""
    type_: Literal["Work", "Series", "External Work"] | None = None
    language_id: Language | None = None
    work_updated: str = ""
    any_bookmark_field: str = ""
    bookmark_tags: str = ""
    bookmarker: str = ""
    recommended: bool = False
    with_notes: bool = False
    bookmark_date: str = ""
    sort_column: Literal["created_at", "bookmarkable_date"] | None = None


@dataclasses.dataclass(slots=True)
class TagSearchParams(SearchParams):
    name: str = ""
    fandoms: str = ""
    type_: Literal["Fandom", "Character", "Relationship", "Freeform"] | None = None
    wranging_status: Literal["T", "F"] | None = None
    sort_column: Literal["name", "created_at"] = "name"
    sort_direction: Literal["asc", "desc"] = "asc"


class Search(Page, Generic[SP, R]):
    __slots__ = (
        "_id",
        "_http",
        "_element",
        "_authenticity_token",
        "_search_params",
        "_cs_results",
    )

    def __init__(
        self,
        http: HTTPClient,
        *,
        payload: dict[str, Any] | None = None,
        element: html.HtmlElement | None = None,
    ) -> None:
        self._id = 0
        self._http = http
        if payload:
            for attr, val in payload.items():
                setattr(self, attr, val)
        self._element = element

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, self.__class__):
            return __value.search_params == self.search_params
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.search_params)

    def __repr__(self) -> str:
        attrs = ((field.name, field.default) for field in dataclasses.fields(self.search_params))
        resolved = (
            f"{attr}={val!r}"
            for attr, default in attrs
            if (val := getattr(self.search_params, attr)) is not None and (val != default)
        )
        return f"<{type(self).__name__}({' '.join(resolved)})>"

    @property
    def id(self) -> int:
        return self._id

    @property
    def search_params(self) -> SP:
        return self._search_params

    @cached_slot_property("_cs_results")
    def results(self) -> tuple[R, ...]:
        if self.raw_element is None:
            raise UnloadedError
        return self._get_results()

    @abstractmethod
    def _get_results(self) -> tuple[R, ...]:
        raise NotImplementedError


class WorkSearch(Search[WorkSearchParams, "Work"]):
    def _get_results(self) -> tuple[Work, ...]:
        from .work import Work

        assert self.raw_element is not None
        return tuple(
            Work._from_banner(self._http, el, self.authenticity_token)
            for el in SEARCH_SELECTOR["work"](self.raw_element)
        )

    async def reload(self) -> None:
        text = await self._http.search_works(*self.search_params.astuple())
        self._element = html.fromstring(text)
        del self._cs_results


class PeopleSearch(Search[PeopleSearchParams, Object]):
    def _get_results(self) -> tuple[Object, ...]:
        from .user import User

        assert self.raw_element is not None
        return tuple(
            Object(name=str(el.cssselect("h4.heading > a")[0].text_content()), type=User)
            for el in SEARCH_SELECTOR["people"](self.raw_element)
        )

    async def reload(self) -> None:
        text = await self._http.search_people(**self.search_params.asdict())
        self._element = html.fromstring(text)
        del self._cs_results


class BookmarkSearch(Search[BookmarkSearchParams, tuple[Object, "Work"]]):
    def _get_results(self) -> tuple[tuple[Object, Work], ...]:
        from .user import User
        from .work import Work

        assert self.raw_element is not None
        return tuple(
            (
                Object(name=str(el.cssselect("h4.heading > a")[0].text_content()), type=User),
                Work._from_banner(self._http, el, self.authenticity_token),
            )
            for el in SEARCH_SELECTOR["bookmark"](self.raw_element)
        )

    async def reload(self) -> None:
        text = await self._http.search_bookmarks(**self.search_params.asdict())
        self._element = html.fromstring(text)
        del self._cs_results


class TagSearch(Search[TagSearchParams, TagResult]):
    def _get_results(self) -> tuple[TagResult, ...]:
        assert self.raw_element is not None

        return tuple(
            TagResult(result["type"], result["name"], int(result["count"]))
            for el in SEARCH_SELECTOR["tag"](self.raw_element)
            if (result := TAG_SECTIONS.search(str(el.text_content())))
        )

    async def reload(self) -> None:
        text = await self._http.search_tags(**self.search_params.asdict())
        self._element = html.fromstring(text)
        del self._cs_results
