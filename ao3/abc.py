from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, SupportsInt, TypeAlias, runtime_checkable

from .errors import AO3Exception
from .utils import CachedSlotProperty, cached_slot_property, extract_csrf_token, extract_pseud_id


if TYPE_CHECKING:
    from lxml import html
    from typing_extensions import Self

    from .http import HTTPClient
else:
    Self: TypeAlias = Any

SupportsIntCast = SupportsInt | str | bytes | bytearray

__all__ = (
    "Page",
    "KudoableMixin",
    "BookmarkableMixin",
    "SubscribableMixin",
    "CommentableMixin",
    "CollectableMixin",
    "Object",
)


@runtime_checkable
class Page(Protocol):
    __slots__ = ()

    id: property | CachedSlotProperty[Self, int]  # noqa: A003
    _http: HTTPClient
    _element: html.HtmlElement | None
    _authenticity_token: str | None

    @property
    def raw_element(self) -> html.HtmlElement | None:
        return self._element

    @cached_slot_property("_authenticity_token")
    def authenticity_token(self) -> str | None:
        if self.raw_element is None:
            return None
        return extract_csrf_token(self.raw_element)

    @abstractmethod
    async def reload(self) -> None:
        raise NotImplementedError


class KudoableMixin:
    # Includes works.
    __slots__ = ()

    id: property | CachedSlotProperty[Self, int]  # noqa: A003
    _http: HTTPClient
    authenticity_token: CachedSlotProperty[Self, str | None]

    @property
    def kudoable_type(self) -> str:
        raise NotImplementedError

    async def give_kudos(self) -> None:
        auth_token = self._http.state.login_token or self.authenticity_token
        if auth_token is None:
            raise AO3Exception

        await self._http.give_kudos(auth_token, self.id, self.kudoable_type)


class BookmarkableMixin:
    # Includes series and works.
    __slots__ = ()

    id: property | CachedSlotProperty[Self, int]  # noqa: A003
    _http: HTTPClient
    authenticity_token: CachedSlotProperty[Self, str | None]
    raw_element: property | html.HtmlElement
    url: property | str
    _cs_bookmark_id: int | None

    @cached_slot_property("_cs_bookmark_id")
    def bookmark_id(self) -> int | None:
        if self.raw_element is None or (self._http.state.login_token is None):
            return None
        try:
            el = self.raw_element.cssselect('div#bookmark-form > form[action^="/bookmark"]')[0]
            return int(text.split("/")[-1]) if (text := el.get("action")) else None
        except (IndexError, ValueError):
            return None

    async def bookmark(
        self,
        notes: str = "",
        tags: list[str] | None = None,
        collections: list[str] | None = None,
        private: bool = False,
        recommend: bool = False,
        as_pseud: str = "",
    ) -> None:
        auth_token = self._http.state.login_token or self.authenticity_token

        # Account for already having bookmarked the thing.
        if auth_token is None or self.raw_element is None or self.bookmark_id is not None:
            raise AO3Exception

        pseud_id = extract_pseud_id(self.raw_element, as_pseud if as_pseud else None)
        if pseud_id is None:
            raise AO3Exception

        path = self.url.partition(".org")[-1]
        response = await self._http.bookmark(auth_token, path, notes, tags, collections, private, recommend, pseud_id)
        self._cs_bookmark_id = int(response.url.parts[-1])

    async def delete_bookmark(self) -> None:
        auth_token = self._http.state.login_token or self.authenticity_token
        if auth_token is None or self.bookmark_id is None:
            raise AO3Exception

        await self._http.delete_bookmark(auth_token, self.bookmark_id)
        self._cs_bookmark_id = None


class SubscribableMixin:
    # Includes series, works, and users.
    __slots__ = ()

    id: property | CachedSlotProperty[Self, int]  # noqa: A003
    _http: HTTPClient
    authenticity_token: CachedSlotProperty[Self, str | None]
    sub_id: CachedSlotProperty[Self, int | None]

    @property
    def subable_type(self) -> str:
        raise NotImplementedError

    async def subscribe(self) -> None:
        # FIXME: Get actual client username?
        auth_token = self._http.state.login_token or self.authenticity_token

        # Account for already having bookmarked the thing.
        if auth_token is None or self.sub_id is not None:
            raise AO3Exception

        response = await self._http.subscribe(auth_token, "name", self.id, self.subable_type)
        self._cs_sub_id = (await response.json())["item_id"]

    async def unsubscribe(self) -> None:
        # FIXME: Get actual client username?
        auth_token = self._http.state.login_token or self.authenticity_token
        if auth_token is None or self.sub_id is None:
            raise AO3Exception

        await self._http.unsubscribe(auth_token, "name", self.id, self.subable_type, self.sub_id)
        self._cs_sub_id = None


class CommentableMixin:
    # Includes works (?)
    async def comment(self) -> None:
        ...

    async def delete_comment(self) -> None:
        ...


class CollectableMixin:
    # Includes works and series (?)
    async def collect(self) -> None:
        ...


class Object:
    __slots__ = ("id", "name", "type")

    def __init__(
        self,
        *,
        id: SupportsIntCast | None = None,  # noqa: A002
        name: str | None = None,
        type: type[Page] | None = None,  # noqa: A002
    ) -> None:
        if id is None and name is None:
            msg = "At least one of id and name must be specified."
            raise ValueError(msg)

        if id is not None:
            try:
                id = int(id)  # noqa: A001
            except ValueError:
                msg = f"id parameter must be int-compatible, not {id.__class__}"
                raise ValueError(msg) from None

        self.id = id
        self.name = name
        self.type = type or self.__class__

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, self.type):
            return self.id == __value.id
        return NotImplemented

    def __hash__(self) -> int:
        return hash(tuple(attr for attr in (self.id, self.name, self.type) if attr is not None))
