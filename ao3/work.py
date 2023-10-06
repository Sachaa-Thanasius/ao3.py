from __future__ import annotations

import datetime
from collections.abc import Iterator
from itertools import chain
from typing import TYPE_CHECKING, Any, TypeAlias

from lxml import html

from ._selectors import WORK_SELECTORS
from .abc import BookmarkableMixin, CollectableMixin, KudoableMixin, Object, Page, SubscribableMixin
from .enums import Language
from .errors import AO3Exception, UnloadedError
from .utils import cached_slot_property, get_id_from_url, int_or_none


if TYPE_CHECKING:
    from typing_extensions import Self

    from .http import HTTPClient
else:
    Self: TypeAlias = Any

__all__ = ("Work",)


class Work(Page, KudoableMixin, BookmarkableMixin, SubscribableMixin, CollectableMixin):
    __slots__ = (
        "_id",
        "_http",
        "_element",
        "_authenticity_token",
        "_cs_bookmark_id",
        "_cs_sub_id",
        "_cs_title",
        "_cs_authors",
        "_cs_restricted",
        "_cs_series",
        "_cs_summary",
        "_cs_rating",
        "_cs_warnings",
        "_cs_categories",
        "_cs_fandoms",
        "_cs_relationships",
        "_cs_characters",
        "_cs_freeforms",
        "_cs_language",
        "_cs_date_published",
        "_cs_date_updated",
        "_cs_nwords",
        "_cs_nchapters",
        "_cs_ncomments",
        "_cs_nkudos",
        "_cs_nbookmarks",
        "_cs_nhits",
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
        return f"{type(self).__name__}(title={self.title!r} id={self.id!r})"

    @property
    def id(self) -> int:
        return self._id

    @property
    def subable_type(self) -> str:
        return "Work"

    kudoable_type = subable_type

    @cached_slot_property("_cs_sub_id")
    def sub_id(self) -> int | None:
        if self.raw_element is None or not self._http.state:
            return None
        try:
            sub_el = WORK_SELECTORS["sub_id"](self.raw_element)[0]
            return int(text.split("/")[-1]) if (text := sub_el.get("action", None)) else None
        except (IndexError, ValueError):
            return None

    @property
    def url(self) -> str:
        return f"https://archiveofourown.org/works/{self.id}"

    @cached_slot_property("_cs_title")
    def title(self) -> str:
        if self.raw_element is None:
            raise UnloadedError
        try:
            return str(WORK_SELECTORS["title"](self.raw_element)[0].text_content()).strip()
        except (IndexError, ValueError):
            return ""

    @cached_slot_property("_cs_authors")
    def authors(self) -> tuple[Object, ...]:
        from .user import User  # Avoid circular import.

        # Consider implementing PartialUser and using it here.
        if self.raw_element is None:
            raise UnloadedError
        return tuple(
            Object(name=el.get("href", "").split("/")[1], type=User)
            for el in WORK_SELECTORS["authors"](self.raw_element)
        )

    @cached_slot_property("_cs_summary")
    def summary(self) -> str:
        if self.raw_element is None:
            raise UnloadedError
        try:
            return str(WORK_SELECTORS["summary"](self.raw_element)[0].text_content()).strip()
        except (IndexError, ValueError):
            return ""

    @cached_slot_property("_cs_series")
    def series(self) -> tuple[Object, ...]:
        from .series import Series  # Avoid circular import.

        # Consider implementing PartialSeries and using it here.
        if self.raw_element is None:
            raise UnloadedError
        return tuple(
            Object(id=int((a.get("href") or "0").rpartition("/")[-1]), type=Series)
            for a in WORK_SELECTORS["series"](self.raw_element)
        )

    @cached_slot_property("_cs_restricted")
    def is_restricted(self) -> bool:
        if self.raw_element is None:
            return False
        return len(WORK_SELECTORS["restricted"](self.raw_element)) > 0

    @cached_slot_property("_cs_rating")
    def rating(self) -> str:
        if self.raw_element is None:
            raise UnloadedError
        try:
            return str(WORK_SELECTORS["rating"](self.raw_element)[0].text_content()).strip()
        except (IndexError, ValueError):
            return ""

    @cached_slot_property("_cs_warnings")
    def warnings(self) -> tuple[str, ...]:
        if self.raw_element is None:
            raise UnloadedError
        return tuple(str(el.text_content()) for el in WORK_SELECTORS["warnings"](self.raw_element))

    @cached_slot_property("_cs_categories")
    def categories(self) -> tuple[str, ...]:
        if self.raw_element is None:
            raise UnloadedError
        return tuple(str(el.text_content()) for el in WORK_SELECTORS["categories"](self.raw_element))

    @cached_slot_property("_cs_fandoms")
    def fandoms(self) -> tuple[str, ...]:
        if self.raw_element is None:
            raise UnloadedError
        return tuple(str(el.text_content()) for el in WORK_SELECTORS["fandoms"](self.raw_element))

    @cached_slot_property("_cs_relationships")
    def relationships(self) -> tuple[str, ...]:
        if self.raw_element is None:
            raise UnloadedError
        return tuple(str(el.text_content()) for el in WORK_SELECTORS["relationships"](self.raw_element))

    @cached_slot_property("_cs_characters")
    def characters(self) -> tuple[str, ...]:
        if self.raw_element is None:
            raise UnloadedError
        return tuple(str(el.text_content()) for el in WORK_SELECTORS["characters"](self.raw_element))

    @cached_slot_property("_cs_freeforms")
    def freeforms(self) -> tuple[str, ...]:
        if self.raw_element is None:
            raise UnloadedError
        return tuple(str(el.text_content()) for el in WORK_SELECTORS["freeforms"](self.raw_element))

    def all_tags(self) -> Iterator[str]:
        return chain(self.warnings, self.relationships, self.characters, self.freeforms, self.categories)

    @cached_slot_property("_cs_language")
    def language(self) -> Language:
        if self.raw_element is None:
            return Language.UNKNOWN
        try:
            return Language(WORK_SELECTORS["language"](self.raw_element)[0].text)
        except (IndexError, ValueError):
            return Language.UNKNOWN

    @cached_slot_property("_cs_date_published")
    def date_published(self) -> datetime.datetime | None:
        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(WORK_SELECTORS["date_published"](self.raw_element)[0].text)
            return datetime.datetime.strptime(text or "", "%Y-%m-%d").astimezone()
        except (IndexError, ValueError):
            return None

    @cached_slot_property("_cs_date_updated")
    def date_updated(self) -> datetime.datetime | None:
        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(WORK_SELECTORS["date_updated"](self.raw_element)[0].text)
            return datetime.datetime.strptime(text or "", "%Y-%m-%d").astimezone()
        except (IndexError, ValueError):
            return None

    @cached_slot_property("_cs_nwords")
    def nwords(self) -> int | None:
        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(WORK_SELECTORS["nwords"](self.raw_element)[0].text)
            return result if (result := int_or_none(text)) else 0
        except (IndexError, ValueError):
            return 0

    @cached_slot_property("_cs_nchapters")
    def nchapters(self) -> tuple[int | None, int | None]:
        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(WORK_SELECTORS["nchapters"](self.raw_element)[0].text)
            current, _, expected = text.partition("/")
            return (int_or_none(current), int_or_none(expected))
        except (IndexError, ValueError):
            return (None, None)

    @property
    def is_complete(self) -> bool:
        current, expected = self.nchapters
        if isinstance(current, type(expected)):
            return current == expected
        return False

    @cached_slot_property("_cs_ncomments")
    def ncomments(self) -> int:
        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(WORK_SELECTORS["ncomments"](self.raw_element)[0].text)
            return result if (result := int_or_none(text)) else 0
        except (IndexError, ValueError):
            return 0

    @cached_slot_property("_cs_nkudos")
    def nkudos(self) -> int:
        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(WORK_SELECTORS["nkudos"](self.raw_element)[0].text)
            return result if (result := int_or_none(text)) else 0
        except (IndexError, ValueError):
            return 0

    @cached_slot_property("_cs_nbookmarks")
    def nbookmarks(self) -> int:
        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(WORK_SELECTORS["nbookmarks"](self.raw_element)[0].text_content())
            return result if (result := int_or_none(text)) else 0
        except (IndexError, ValueError):
            return 0

    @cached_slot_property("_cs_nhits")
    def nhits(self) -> int:
        if self.raw_element is None:
            raise UnloadedError
        try:
            text = str(WORK_SELECTORS["nhits"](self.raw_element)[0].text)
            return result if (result := int_or_none(text)) else 0
        except (IndexError, ValueError):
            return 0

    @property
    def stats(self) -> tuple[int, int, int, int]:
        return (self.ncomments, self.nkudos, self.nbookmarks, self.nhits)

    @classmethod
    def _from_banner(
        cls,
        http: HTTPClient,
        work_element: html.HtmlElement,
        authenticity_token: str | None = None,
    ) -> Self:
        # Avoid circular imports.
        from .series import Series
        from .user import User

        try:
            work_el = work_element.cssselect('a[href^="/works"]')[0]
            title = str(work_el.text_content())
            work_id = get_id_from_url("archiveofourown.org" + (work_el.get("href") or ""))
        except (IndexError, ValueError) as err:
            raise AO3Exception from err

        authors = [
            Object(name=el.get("href", "").split("/")[1], type=User)
            for el in work_element.cssselect('h4 a > [rel*="author"]')
        ]
        restricted = len(work_element.cssselect('img [title*="Restricted"]')) > 0
        series = [
            Object(id=int(href.rpartition("/")[-1]), type=Series)
            for el in work_element.cssselect(".series a")
            if (href := el.get("href"))
        ]
        summary = str(el[0].text_content()) if (el := work_element.cssselect(".userstuff.summary")) else None
        rating = str(el[0].text_content()) if (el := work_element.cssselect(".required-tags .rating")) else None
        warnings = [str(el.text_content()) for el in work_element.cssselect(".tags li.warnings")]

        try:
            categories = str(work_element.cssselect(".required-tags .category")[0].text_content()).split(",")
        except IndexError:
            categories = None

        fandoms = [str(el.text_content()) for el in work_element.cssselect("h5.fandoms a")]
        relationships = [str(el.text_content()) for el in work_element.cssselect(".tags li.relationships")]
        characters = [str(el.text_content()) for el in work_element.cssselect(".tags li.characters")]
        freeforms = [str(el.text_content()) for el in work_element.cssselect(".tags li.freeforms")]

        try:
            language = Language(str(work_element.cssselect(".stats dd.language")[0].text_content()))
        except IndexError:
            language = Language.UNKNOWN

        try:
            date = str(work_element.cssselect("p.datetime")[0].text_content())
            date_updated = datetime.datetime.strptime(date, "%d %b %Y").astimezone()
        except IndexError:
            date_updated = None

        try:
            words = int_or_none(str(work_element.cssselect(".stats dd.words")[0].text_content()))
        except IndexError:
            words = None

        chapters_el = work_element.cssselect(".stats dd.chapters")
        if len(el := chapters_el[0]):
            current, _, expected = str(el.text_content()).partition("/")
            chapters = (int_or_none(current), int_or_none(expected))
        else:
            chapters = (None, None)

        comments = int_or_none(str(el[0].text)) if (el := work_element.cssselect(".stats dd.comments")) else None
        kudos = int_or_none(str(el[0].text)) if (el := work_element.cssselect(".stats dd.kudos")) else None
        bookmarks = (
            int_or_none(str(el[0].text_content())) if (el := work_element.cssselect(".stats dd.bookmarks")) else None
        )
        hits = int_or_none(str(el[0].text)) if (el := work_element.cssselect(".stats dd.hits")) else None

        payload = {
            "_id": work_id,
            "_authenticity_token": authenticity_token,
            "_cs_title": title,
            "_cs_authors": authors,
            "_cs_restricted": restricted,
            "_cs_series": series,
            "_cs_summary": summary,
            "_cs_rating": rating,
            "_cs_warnings": warnings,
            "_cs_categories": categories,
            "_cs_fandoms": fandoms,
            "_cs_relationships": relationships,
            "_cs_characters": characters,
            "_cs_freeforms": freeforms,
            "_cs_language": language,
            "_cs_date_updated": date_updated,
            "_cs_nwords": words,
            "_cs_nchapters": chapters,
            "_cs_ncomments": comments,
            "_cs_nkudos": kudos,
            "_cs_nbookmarks": bookmarks,
            "_cs_nhits": hits,
        }
        return cls(http, payload=payload)

    async def reload(self) -> None:
        text = await self._http.get_work(self.id)
        self._element = html.fromstring(text)

        # Reset cached properties.
        slots = set(self.__slots__).difference(("_id", "_http", "_element"))
        for attr in slots:
            delattr(self, attr)
