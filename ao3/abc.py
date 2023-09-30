from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, SupportsInt, TypeAlias, runtime_checkable

from .errors import AO3Exception, AuthError, BookmarkError, KudoError, PseudError, UnloadedError
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
    """An protocol/ABC that details the common members and operations of AO3 items.

    Attributes
    ----------
    id : :class:`int`
        The item's ID. Unique for all items, excluding search-related ones.
    """

    __slots__ = ()

    id: property | CachedSlotProperty[Self, int]
    _http: HTTPClient
    _element: html.HtmlElement | None
    _authenticity_token: str | None

    @property
    def raw_element(self) -> html.HtmlElement | None:
        """:class:`html.HtmlElement` | None : A representation of the raw HTML for this item's corresponding AO3
        webpage.

        If not provided, then this is ``None``.
        """

        return self._element

    @cached_slot_property("_authenticity_token")
    def authenticity_token(self) -> str | None:
        if self.raw_element is None:
            return None
        return extract_csrf_token(self.raw_element)

    @abstractmethod
    async def reload(self) -> None:
        """Reloads the item's corresponding webpage to update its members."""

        raise NotImplementedError


class KudoableMixin:
    """A mixin that adds kudo-giving members and functionality to AO3 items that can receive kudos.

    The following implement this mixin:

    - :class:`ao3.Work`

    This mixin must also implement :class:`ao3.abc.Page`.
    """

    __slots__ = ()

    id: property | CachedSlotProperty[Self, int]
    _http: HTTPClient
    authenticity_token: CachedSlotProperty[Self, str | None]

    @property
    def kudoable_type(self) -> str:
        """:class:`str` : The type of this item in respect to AO3's kudo mechanism."""

        raise NotImplementedError

    async def give_kudos(self) -> None:
        """Give this item a kudo. Currently limited to works.

        Fails if a valid auth token can't be found.

        Raises
        ------
        AuthError
            Invalid authenticity token was used (might be expired or not logged in).
        KudoError
            Something went wrong in the kudoing process.
        """

        try:
            auth_token = self._http.state.login_token
        except AttributeError:
            auth_token = self.authenticity_token

        if auth_token is None:
            raise AuthError

        try:
            await self._http.give_kudos(auth_token, self.id, self.kudoable_type)
        except Exception as err:
            raise KudoError from err


class BookmarkableMixin:
    """A mixin that adds bookmark-related members and functionality to AO3 items that can be bookmarked.

    The following implement this mixin:

    - :class:`ao3.Work`
    - :class:`ao3.Series`

    This mixin must also implement :class:`ao3.abc.Page`.
    """

    __slots__ = ()

    id: property | CachedSlotProperty[Self, int]
    _http: HTTPClient
    authenticity_token: CachedSlotProperty[Self, str | None]
    raw_element: property | html.HtmlElement
    url: property | str
    _cs_bookmark_id: int | None

    @cached_slot_property("_cs_bookmark_id")
    def bookmark_id(self) -> int | None:
        if self.raw_element is None or not self._http.state.login_token:
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
        as_pseud: str | None = None,
    ) -> None:
        """Adds a bookmark corresponding to the item. Be careful — you can bookmark the same work multiple times.

        Parameters
        ----------
        notes : :class:`str`, optional
            The notes to add to this bookmark. By default "".
        tags : list[:class:`str`] | None, optional
            The tags to add to this bookmark. By default None.
        collections : list[:class:`str`] | None, optional
            The collections to add this bookmark to. By default None.
        private : :class:`bool`, optional
            Whether to make this bookmark private. By default False.
        recommend : :class:`bool`, optional
            Whether to recommend this bookmark. By default False.
        as_pseud : :class:`str` | None, optional
            Which pseud to make this bookmark as. By default None, which means the default pseud will be used.

        Raises
        ------
        AuthError
            Invalid authenticity token was used (might be expired or not logged in).
        UnloadedError
            The item hasn't been loaded.
        BookmarkError
            Something went wrong in the bookmarking process.
        PseudError
            ID for specified or default pseud could not be found.
        """

        try:
            auth_token = self._http.state.login_token
        except AttributeError:
            auth_token = self.authenticity_token

        if auth_token is None:
            raise AuthError
        if self.raw_element is None:
            raise UnloadedError
        if self.bookmark_id is not None:
            msg = "This item has already been bookmarked."
            raise BookmarkError(msg)

        pseud_id = extract_pseud_id(self.raw_element, as_pseud if as_pseud else None)
        if pseud_id is None:
            raise PseudError(as_pseud)

        try:
            path = self.url.partition(".org")[-1]
            resp = await self._http.bookmark(auth_token, path, notes, tags, collections, private, recommend, pseud_id)
        except Exception as err:
            raise BookmarkError from err
        else:
            self._cs_bookmark_id = int(resp.url.parts[-1])

    async def delete_bookmark(self) -> None:
        """Removes a bookmark corresponding to this item.

        Raises
        ------
        AuthError
            Invalid authenticity token was used (might be expired or not logged in).
        BookmarkError
            Something went wrong in the bookmarking process.
        """

        try:
            auth_token = self._http.state.login_token
        except AttributeError:
            auth_token = self.authenticity_token

        if auth_token is None:
            raise AuthError
        if self.bookmark_id is None:
            msg = "This item has not been bookmarked yet."
            raise BookmarkError(msg)

        try:
            await self._http.delete_bookmark(auth_token, self.bookmark_id)
        except Exception as err:
            raise BookmarkError from err
        else:
            self._cs_bookmark_id = None


class SubscribableMixin:
    """A mixin that adds subscription-related members and functionality to AO3 items that can be subscribed to.

    The following implement this mixin:

    - :class:`ao3.Work`
    - :class:`ao3.Series`
    - :class:`ao3.User`

    This mixin must also implement :class:`ao3.abc.Page`.
    """

    __slots__ = ()

    id: property | CachedSlotProperty[Self, int]
    _http: HTTPClient
    authenticity_token: CachedSlotProperty[Self, str | None]
    sub_id: CachedSlotProperty[Self, int | None]

    @property
    def subable_type(self) -> str:
        """:class:`str` : The type of this item in respect to AO3's subscription mechanism."""

        raise NotImplementedError

    async def subscribe(self) -> None:
        try:
            auth_token = self._http.state.login_token
        except AttributeError:
            auth_token = self.authenticity_token

        # Account for already having bookmarked the thing.
        if auth_token is None or self.sub_id is not None:
            raise AO3Exception

        client_username = self._http.state.client_user.username
        response = await self._http.subscribe(auth_token, client_username, self.id, self.subable_type)
        self._cs_sub_id = (await response.json())["item_id"]

    async def unsubscribe(self) -> None:
        try:
            auth_token = self._http.state.login_token
        except AttributeError:
            auth_token = self.authenticity_token

        if auth_token is None or self.sub_id is None:
            raise AO3Exception

        client_username = self._http.state.client_user.username
        await self._http.unsubscribe(auth_token, client_username, self.id, self.subable_type, self.sub_id)
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
        id: SupportsIntCast | None = None,
        name: str | None = None,
        type: type[Page] | None = None,
    ) -> None:
        if id is None and name is None:
            msg = "At least one of id and name must be specified."
            raise ValueError(msg)

        if id is not None:
            try:
                id = int(id)
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

    def __repr__(self) -> str:
        attrs = ("id", "name", "type")
        resolved = (f"{attr}={val}" for attr in attrs if (val := getattr(self, attr)) is not None)
        return f"{type(self).__name__}({' '.join(resolved)})"
