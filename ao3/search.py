from __future__ import annotations

import re
from abc import abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Generic, Literal, Tuple, TypeVar

import attrs
from lxml import html

from ._selectors import SEARCH_SELECTOR
from .abc import Page
from .enums import ArchiveWarningId, CategoryId, Language, RatingId
from .errors import UnloadedError
from .object import Object
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
    "WorkSearch",
    "PeopleSearch",
    "BookmarkSearch",
    "TagSearch",
)

TAG_SECTIONS = re.compile(r"(?P<type>.*): (?P<name>.*)\u200E\((?P<count>\d+)\)")


@attrs.define
class TagInfo:
    """Basic information about a tag.

    Attributes
    ----------
    type: :class:`str`
        The type of tag, e.g. "Character", "Relationship", "FreeForm", etc.
    name: :class:`str`
        The name of the tag.
    count: :class:`int`
        The number of works that bear this tag.
    canonical: :class:`bool`, optional
        Whether the tag is canonical.
    """

    type: str
    name: str
    count: int
    canonical: bool = False


@attrs.define
class SearchOptions:
    """The base dataclass for AO3 search options.

    Attributes
    ----------
    page: :class:`int`, optional
        The page of the seach results to get. By default 1.
    """

    page: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Serialize the dataclass into a query mapping that AO3 will understand.

        Returns
        -------
        dict[:class:`str`, Any]
            A mapping of the search options with potentially slight modifications.
        """

        return attrs.asdict(self)


@attrs.define
class WorkSearchOptions(SearchOptions):
    """A collection of options to use for searching works on AO3.

    Attributes
    ----------
    any_field: :class:`str`, optional
        Searches all the fields associated with a work in the AO3 database, including summary, notes and tags, but not
        the full work text. By default the empty string.
    title: :class:`str`, optional
        Text in the titles of works. By default the empty string.
    author: :class:`str`, optional
        Text in the names of authors of works. By default the empty string.
    revised_at: :class:`str`, optional
        By default the empty string.
    complete: :class:`bool` | None, optional
        Whether to filter by completion status and which type. True is only completed, False is only not completed. By
        default None, which gets both.
    crossover: :class:`bool` | None, optional
        Whether to filter by completion status and which type. True is only crossovers, False is only non-crossovers.
        By default None.
    single_chapter: :class:`bool`, optional
        Whether all results should be single chapters or "oneshots". By default False.
    word_count: :class:`Constraint` | None, optional
        A word count range with an optional minimum and maximum. See :class:`Constraint` for more info on how to
        construct that. By default None.
    language_id: :class:`Language` | None, optional
        What language to filter by. By default None.
    fandom_names: Sequence[:class:`str`], optional
        What fandoms to filter by. By default an empty list.
    rating_ids: :class:`RatingId` | None, optional
        What rating to filter by. By default None.
    archive_warning_ids: Sequence[:class:`ArchiveWarningId`], optional
        A list of archive warnings to filter by. By default an empty list.
    category_ids: Sequence[:class:`CategoryId`], optional
        A list of categories to filter by. By default an empty list.
    character_names: Sequence[:class:`str`], optional
        A list of character tags to filter by. By default an empty list.
    relationship_names: Sequence[:class:`str`], optional
        A list of relationship tags to filter by. By default an empty list.
    freeform_names: Sequence[:class:`str`], optional
        A list of freeform tags to filter by. By default an empty list.
    hits: :class:`Constraint` | None, optional
        A word count range with an optional minimum and maximum. See :class:`Constraint` for more info on how to
        construct that. By default None.
    kudos_count: :class:`Constraint` | None, optional
        A word count range with an optional minimum and maximum. See :class:`Constraint` for more info on how to
        construct that. By default None.
    comments_count: :class:`Constraint` | None, optional
        A word count range with an optional minimum and maximum. See :class:`Constraint` for more info on how to
        construct that. By default None.
    bookmarks_count: :class:`Constraint` | None, optional
        A word count range with an optional minimum and maximum. See :class:`Constraint` for more info on how to
        construct that. By default None.
    excluded_tag_names: Sequence[:class:`str`], optional
        A list of tags to exclude from the search results. By default an empty list.
    sort_column: :class:`str`, optional
        What filter option to sort by. By default "_score", which means "Best Match".
    sort_direction: Literal["asc", "desc"], optional
        What direction to sort by. By default "desc".
    """

    any_field: str = ""
    title: str = ""
    author: str = ""
    revised_at: str = ""
    complete: bool | None = None
    crossover: bool | None = None
    single_chapter: bool = False
    word_count: Constraint | None = None
    language_id: Language | None = None
    fandom_names: Sequence[str] = attrs.field(factory=list)
    rating_ids: RatingId | None = None
    archive_warning_ids: Sequence[ArchiveWarningId] = attrs.field(factory=list)
    category_ids: Sequence[CategoryId] = attrs.field(factory=list)
    character_names: Sequence[str] = attrs.field(factory=list)
    relationship_names: Sequence[str] = attrs.field(factory=list)
    freeform_names: Sequence[str] = attrs.field(factory=list)
    hits: Constraint | None = None
    kudos_count: Constraint | None = None
    comments_count: Constraint | None = None
    bookmarks_count: Constraint | None = None
    excluded_tag_names: Sequence[str] = attrs.field(factory=list)
    sort_column: str = "_score"
    sort_direction: Literal["asc", "desc"] = "desc"

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            word_count=self.word_count.string if self.word_count else "",
            language_id=self.language_id.name.lower() if self.language_id else "",
            fandom_names=",".join(self.fandom_names),
            rating_ids=self.rating_ids.value if self.rating_ids else "",
            archive_warning_ids=[id.value for id in self.archive_warning_ids],
            category_ids=[id.value for id in self.category_ids],
            character_names=",".join(self.character_names),
            relationship_names=",".join(self.relationship_names),
            freeform_names=",".join(self.freeform_names),
            hits=self.hits.string if self.hits else "",
            kudos_count=self.kudos_count.string if self.kudos_count else "",
            comments_count=self.comments_count.string if self.comments_count else "",
            bookmarks_count=self.bookmarks_count.string if self.bookmarks_count else "",
        )

        if self.complete is None:
            result.pop("complete")
        else:
            result["complete"] = "T" if self.complete else "F"

        if self.crossover is None:
            result.pop("crossover")
        else:
            result["crossover"] = "T" if self.crossover else "F"

        return result


@attrs.define
class PeopleSearchOptions(SearchOptions):
    """A collection of options to use for searching people on AO3.

    Attributes
    ----------
    any_field: :class:`str`, optional
        Searches all the fields associated with a person in the AO3 database. By default the empty string.
    names: Sequence[:class:`str`], optional
        What usernames to filter by. By default an empty list.
    fandoms: Sequence[:class:`str`], optional
        What fandoms to filter by, i.e. only pulling users that have written in these fandoms. By default an empty list.
    """

    any_field: str = ""
    names: Sequence[str] = attrs.field(factory=list)
    fandoms: Sequence[str] = attrs.field(factory=list)

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(names=",".join(self.names), fandoms=",".join(self.fandoms))
        return result


@attrs.define
class BookmarkSearchOptions(SearchOptions):
    """A collection of options to use for searching bookmarks on AO3.

    Attributes
    ----------
    any_field: :class:`str`, optional
        Searches all the fields associated with a work that has been bookmarked in the AO3 database. By default the
        empty string.
    work_tags: Sequence[:class:`str`], optional
        What tags to filter by that are on the actual bookmarked work. By default an empty list.
    type: Literal["Work", "Series", "External Work"] | None , optional
        What type of bookmarked work to filter by. By default None.
    language_id: :class:`Language` | None, optional
        What language to filter by. By default None.
    work_updated: :class:`str`, optional
        A range of time within which the bookmarked work was last updated. By default the empty string.
    any_bookmark_field: :class:`str`, optional
        Searches all the fields associated with a bookmark in the AO3 database, including notes and tags. By default
        the empty string.
    bookmark_tags: Sequence[:class:`str`], optional
        A list of bookmark tags to filter by. These are tags not present on the bookmarked work itself. By default an
        empty list.
    bookmarker: :class:`str`, optional
        Text in the names of the bookmarkers to filter by. By default the empty string.
    notes: :class:`str`, optional
        Terms in the notes of the bookmarks to filter by. By default the empty string.
    recommended: :class:`bool`, optional
        Whether to limit the search to bookmarks that have been recommended. By default False.
    with_notes: :class:`bool`, optional
        Whether to limit the search to bookmarks that have notes. By default False.
    sort_column: Literal["created_at", "bookmarkable_date"] | None, optional
        What filter option to sort by. By default "_score", which means "Best Match".
    """

    any_field: str = ""
    work_tags: Sequence[str] = attrs.field(factory=list)
    type: Literal["Work", "Series", "External Work"] | None = None
    language_id: Language | None = None
    work_updated: str = ""
    any_bookmark_field: str = ""
    bookmark_tags: Sequence[str] = attrs.field(factory=list)
    bookmarker: str = ""
    notes: str = ""
    recommended: bool = False
    with_notes: bool = False
    bookmark_date: str = ""
    sort_column: Literal["created_at", "bookmarkable_date"] | None = None

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result.update(
            work_tags=",".join(self.work_tags),
            language_id=self.language_id.name.lower() if self.language_id else "",
            bookmark_tags=",".join(self.bookmark_tags),
        )
        return result


@attrs.define
class TagSearchOptions(SearchOptions):
    """A collection of options to use for searching people on AO3.

    Attributes
    ----------
    any_field: :class:`str`, optional
        Searches all the fields associated with a person in the AO3 database. By default the empty string.
    names: :class:`str`, optional
        What text in usernames to filter by. By default the empty string.
    fandoms: Sequence[:class:`str`], optional
        What fandoms to filter by, i.e. only pulling tags that are specific to these fandoms. By default an empty list.
    type: Literal["Fandom", "Character", "Relationship", "Freeform"] | None, optional
        What type of high-level tag to filter by. By default None.
    wranging_status: :class:`bool` | None, optional
        Whether to limit tags by a particular wrangling status. True is canonical, False is non-canonical, and None is
        all. By default None.
    sort_direction: Literal["asc", "desc"], optional
        What direction to sort by. By default "desc".
    """

    name: str = ""
    fandoms: Sequence[str] = attrs.field(factory=list)
    type: Literal["Fandom", "Character", "Relationship", "Freeform"] | None = None
    wranging_status: bool | None = None
    sort_column: Literal["name", "created_at"] = "name"
    sort_direction: Literal["asc", "desc"] = "asc"

    def to_dict(self) -> dict[str, Any]:
        result = super().to_dict()
        result["fandoms"] = ",".join(self.fandoms)
        if self.wranging_status is None:
            result.pop("wranging_status")
        else:
            result["wranging_status"] = "T" if self.wranging_status else "F"
        return result


class Search(Page, Generic[SP, R]):
    """The base class for AO3 search results."""

    __slots__ = (
        "_id",
        "_http",
        "_element",
        "_authenticity_token",
        "_search_options",
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
            return __value.search_options == self.search_options
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.search_options)

    def __repr__(self) -> str:
        fields = ((field.name, field.default) for field in attrs.fields(type(self.search_options)))
        resolved = (
            f"{name}={val!r}"
            for name, default in fields
            if (val := getattr(self.search_options, name)) is not None and (val != default)
        )
        return f"{type(self).__name__}({' '.join(resolved)})"

    @property
    def id(self) -> int:
        """:class:`int`: The ID of the model. By default 0 for searches."""

        return self._id

    @property
    def search_options(self) -> SP:
        """SP: The dataclass of search options that led to these search results."""

        return self._search_options

    @property
    @abstractmethod
    def full_total(self) -> int:
        """:class:`int`: The total number of results for this search, not just what's on the current page."""
        # TODO: Consider caching result in subclass implementations.

        raise NotImplementedError

    @cached_slot_property("_cs_results")
    def results(self) -> tuple[R, ...]:
        """The parsed search results. Calculated once than cached.

        Returns
        -------
        tuple[R, ...]
            A tuple of parsed search results.

        Raises
        ------
        UnloadedError
            The item's HTML hasn't been loaded and can't be parsed.
        """

        if self.raw_element is None:
            raise UnloadedError
        return self._get_results()

    @abstractmethod
    def _get_results(self) -> tuple[R, ...]:
        # Internal function that actually parses the page for results.

        raise NotImplementedError


class WorkSearch(Search[WorkSearchOptions, "Work"]):
    """A page of AO3 work search results."""

    @property
    def full_total(self) -> int:
        if self.raw_element is None:
            raise UnloadedError
        try:
            return int(str(self.raw_element.cssselect("h3")[1].text).partition(" Found")[0])
        except (IndexError, ValueError):
            return 0

    def _get_results(self) -> tuple[Work, ...]:
        from .work import Work

        assert self.raw_element is not None  # Should raise an error before this point if not.
        return tuple(
            Work._from_banner(self._http, el, self.authenticity_token)
            for el in SEARCH_SELECTOR["work"](self.raw_element)
        )

    async def reload(self) -> None:
        text = await self._http.search_works(**self.search_options.to_dict())
        self._element = html.fromstring(text)
        del self._cs_results


class PeopleSearch(Search[PeopleSearchOptions, Object]):
    """A page of AO3 people search results."""

    @property
    def full_total(self) -> int:
        if self.raw_element is None:
            raise UnloadedError
        try:
            el = self.raw_element.cssselect("div.people-search.region p strong")[0]
            return int(str(el.text).partition(" Found")[0])
        except (IndexError, ValueError):
            return 0

    def _get_results(self) -> tuple[Object, ...]:
        from .user import User

        assert self.raw_element is not None  # Should raise an error before this point if not.
        return tuple(
            Object(name=str(el.cssselect("h4.heading > a")[0].text_content()), type=User)
            for el in SEARCH_SELECTOR["people"](self.raw_element)
        )

    async def reload(self) -> None:
        text = await self._http.search_people(**self.search_options.to_dict())
        self._element = html.fromstring(text)
        del self._cs_results


class BookmarkSearch(Search[BookmarkSearchOptions, Tuple[Object, "Work"]]):
    """A page of AO3 bookmark search results."""

    @property
    def full_total(self) -> int:
        if self.raw_element is None:
            raise UnloadedError
        try:
            return int(str(self.raw_element.cssselect("h3")[1].text).partition(" Found")[0])
        except (IndexError, ValueError):
            return 0

    def _get_results(self) -> tuple[tuple[Object, Work], ...]:
        from .user import User
        from .work import Work

        assert self.raw_element is not None  # Should raise an error before this point if not.
        return tuple(
            (
                Object(name=str(el.cssselect("h4.heading > a")[0].text_content()), type=User),
                Work._from_banner(self._http, el, self.authenticity_token),
            )
            for el in SEARCH_SELECTOR["bookmark"](self.raw_element)
        )

    async def reload(self) -> None:
        text = await self._http.search_bookmarks(**self.search_options.to_dict())
        self._element = html.fromstring(text)
        del self._cs_results


class TagSearch(Search[TagSearchOptions, TagInfo]):
    """A page of AO3 tag search results."""

    @property
    def full_total(self) -> int:
        if self.raw_element is None:
            raise UnloadedError
        try:
            return int(str(self.raw_element.cssselect("h3")[1].text).partition(" Found")[0])
        except (IndexError, ValueError):
            return 0

    def _get_results(self) -> tuple[TagInfo, ...]:
        assert self.raw_element is not None  # Should raise an error before this point if not.

        return tuple(
            TagInfo(result["type"], result["name"], int(result["count"]), len(el.cssselect("span.canonical")) > 0)
            for el in SEARCH_SELECTOR["tag"](self.raw_element)
            if (result := TAG_SECTIONS.search(str(el.text_content())))
        )

    async def reload(self) -> None:
        text = await self._http.search_tags(**self.search_options.to_dict())
        self._element = html.fromstring(text)
        del self._cs_results
