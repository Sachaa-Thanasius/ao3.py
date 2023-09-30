from __future__ import annotations

import re
from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, fields
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar

from lxml import html

from ._selectors import SEARCH_SELECTOR
from .abc import Object, Page
from .enums import ArchiveWarningId, CategoryId, Language, RatingId
from .errors import UnloadedError
from .utils import Constraint, cached_slot_property


if TYPE_CHECKING:
    from .http import HTTPClient
    from .work import Work

R = TypeVar("R")
SP = TypeVar("SP", bound="SearchOptions")

__all__ = (
    "WorkSearchOptions",
    "PeopleSearchOptions",
    "BookmarkSearchOptions",
    "TagSearchOptions",
    "Search",
)

TAG_SECTIONS = re.compile(r"(?P<type>.*): (?P<name>.*)\u200E\((?P<count>\d+)\)")


@dataclass(slots=True)
class TagResult:
    type: str
    name: str
    count: int


@dataclass(slots=True)
class SearchOptions:
    page: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class WorkSearchOptions(SearchOptions):
    any_field: str = ""
    title: str = ""
    author: str = ""
    revised_at: str = ""
    complete: Literal["T", "F"] | None = None
    crossover: Literal["T", "F"] | None = None
    single_chapter: bool = False
    word_count: Constraint | None = None
    language_id: Language | None = None
    fandom_names: Sequence[str] = field(default_factory=list)
    rating_ids: RatingId | None = None
    archive_warning_ids: Sequence[ArchiveWarningId] = field(default_factory=list)
    category_ids: Sequence[CategoryId] = field(default_factory=list)
    character_names: Sequence[str] = field(default_factory=list)
    relationship_names: Sequence[str] = field(default_factory=list)
    freeform_names: Sequence[str] = field(default_factory=list)
    hits: Constraint | None = None
    kudos_count: Constraint | None = None
    comments_count: Constraint | None = None
    bookmarks_count: Constraint | None = None
    excluded_tag_names: Sequence[str] = field(default_factory=list)
    sort_column: str = "_score"
    sort_direction: Literal["asc", "desc"] = "desc"

    def to_dict(self) -> dict[str, Any]:
        result = super(WorkSearchOptions, self).to_dict()  # noqa: UP008 # Necessary for dataclass with slots.
        result.update(
            word_count=self.word_count.string() if self.word_count else "",
            language_id=self.language_id.name.lower() if self.language_id else "",
            fandom_names=",".join(self.fandom_names),
            rating_ids=self.rating_ids.value if self.rating_ids else "",
            archive_warning_ids=[id.value for id in self.archive_warning_ids],
            category_ids=[id.value for id in self.category_ids],
            character_names=",".join(self.character_names),
            relationship_names=",".join(self.relationship_names),
            freeform_names=",".join(self.freeform_names),
            hits=self.hits.string() if self.hits else "",
            kudos_count=self.kudos_count.string() if self.kudos_count else "",
            comments_count=self.comments_count.string() if self.comments_count else "",
            bookmarks_count=self.bookmarks_count.string() if self.bookmarks_count else "",
        )
        return result


@dataclass(slots=True)
class PeopleSearchOptions(SearchOptions):
    any_field: str = ""
    names: Sequence[str] = field(default_factory=list)
    fandoms: Sequence[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = super(PeopleSearchOptions, self).to_dict()  # noqa: UP008 # Necessary for dataclass with slots.
        result.update(names=",".join(self.names), fandoms=",".join(self.fandoms))
        return result


@dataclass(slots=True)
class BookmarkSearchOptions(SearchOptions):
    any_field: str = ""
    work_tags: Sequence[str] = field(default_factory=list)
    type_: Literal["Work", "Series", "External Work"] | None = None
    language_id: Language | None = None
    work_updated: str = ""
    any_bookmark_field: str = ""
    bookmark_tags: Sequence[str] = field(default_factory=list)
    bookmarker: str = ""
    notes: str = ""
    recommended: bool = False
    with_notes: bool = False
    bookmark_date: str = ""
    sort_column: Literal["created_at", "bookmarkable_date"] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = super(BookmarkSearchOptions, self).to_dict()  # noqa: UP008 # Necessary for dataclass with slots.
        result.update(
            work_tags=",".join(self.work_tags),
            language_id=self.language_id.name.lower() if self.language_id else "",
            bookmark_tags=",".join(self.bookmark_tags),
        )
        return result


@dataclass(slots=True)
class TagSearchOptions(SearchOptions):
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
        attrs = ((attr.name, attr.default) for attr in fields(self.search_params))
        resolved = (
            f"{attr}={val!r}"
            for attr, default in attrs
            if (val := getattr(self.search_params, attr)) is not None and (val != default)
        )
        return f"{type(self).__name__}({' '.join(resolved)})"

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


class WorkSearch(Search[WorkSearchOptions, "Work"]):
    def _get_results(self) -> tuple[Work, ...]:
        from .work import Work

        assert self.raw_element is not None
        return tuple(
            Work._from_banner(self._http, el, self.authenticity_token)
            for el in SEARCH_SELECTOR["work"](self.raw_element)
        )

    async def reload(self) -> None:
        text = await self._http.search_works(**self.search_params.to_dict())
        self._element = html.fromstring(text)
        del self._cs_results


class PeopleSearch(Search[PeopleSearchOptions, Object]):
    def _get_results(self) -> tuple[Object, ...]:
        from .user import User

        assert self.raw_element is not None
        return tuple(
            Object(name=str(el.cssselect("h4.heading > a")[0].text_content()), type=User)
            for el in SEARCH_SELECTOR["people"](self.raw_element)
        )

    async def reload(self) -> None:
        text = await self._http.search_people(**self.search_params.to_dict())
        self._element = html.fromstring(text)
        del self._cs_results


class BookmarkSearch(Search[BookmarkSearchOptions, tuple[Object, "Work"]]):
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
        text = await self._http.search_bookmarks(**self.search_params.to_dict())
        self._element = html.fromstring(text)
        del self._cs_results


class TagSearch(Search[TagSearchOptions, TagResult]):
    def _get_results(self) -> tuple[TagResult, ...]:
        assert self.raw_element is not None

        return tuple(
            TagResult(result["type"], result["name"], int(result["count"]))
            for el in SEARCH_SELECTOR["tag"](self.raw_element)
            if (result := TAG_SECTIONS.search(str(el.text_content())))
        )

    async def reload(self) -> None:
        text = await self._http.search_tags(**self.search_params.to_dict())
        self._element = html.fromstring(text)
        del self._cs_results
