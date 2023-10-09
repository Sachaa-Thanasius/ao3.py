from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, runtime_checkable

from .errors import (
    AO3_AUTH_ERROR_URL,
    AuthError,
    BookmarkError,
    CollectError,
    HTTPException,
    KudoError,
    PseudError,
    SubscribeError,
    UnloadedError,
)
from .utils import CachedSlotProperty, cached_slot_property, extract_csrf_token, extract_pseud_id


if TYPE_CHECKING:
    from lxml import html
    from typing_extensions import Self

    from .http import HTTPClient
else:
    Self: TypeAlias = Any

__all__ = (
    "Page",
    "KudoableMixin",
    "BookmarkableMixin",
    "SubscribableMixin",
    "CommentableMixin",
    "CollectableMixin",
)


@runtime_checkable
class Page(Protocol):
    """An protocol/ABC that details the common members and operations of AO3 items.

    Attributes
    ----------
    id: :class:`int`
        The item's ID. Unique for all items within their categories, excluding search-related ones that default to 0.
    """

    __slots__ = ()

    id: property | CachedSlotProperty[Self, int]
    _http: HTTPClient
    _element: html.HtmlElement | None
    _authenticity_token: str | None

    @property
    def raw_element(self) -> html.HtmlElement | None:
        """:class:`html.HtmlElement` | None: A representation of the raw HTML for this item's corresponding AO3
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
        """:class:`str`: The type of this item in respect to AO3's kudo mechanism."""

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

        auth_token = getattr(self._http.state, "login_token", self.authenticity_token)

        if auth_token is None:
            raise AuthError

        try:
            await self._http.give_kudos(auth_token, self.id, self.kudoable_type)
        except HTTPException as err:
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
        if self.raw_element is None or not self._http.state:
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
        """Adds a bookmark corresponding to this item for the current logged-in user.

        Be careful — you can bookmark the same work multiple times.

        Parameters
        ----------
        notes: :class:`str`, optional
            The notes to add to this bookmark. By default "".
        tags: list[:class:`str`] | None, optional
            The tags to add to this bookmark. By default None.
        collections: list[:class:`str`] | None, optional
            The collections to add this bookmark to. By default None.
        private: :class:`bool`, optional
            Whether to make this bookmark private. By default False.
        recommend: :class:`bool`, optional
            Whether to recommend this bookmark. By default False.
        as_pseud: :class:`str` | None, optional
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

        auth_token = getattr(self._http.state, "login_token", self.authenticity_token)

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
        except HTTPException as err:
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

        auth_token = getattr(self._http.state, "login_token", self.authenticity_token)

        if auth_token is None:
            raise AuthError
        if self.bookmark_id is None:
            msg = "This item has not been bookmarked yet."
            raise BookmarkError(msg)

        try:
            await self._http.delete_bookmark(auth_token, self.bookmark_id)
        except HTTPException as err:
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
        """:class:`str`: The type of this item in respect to AO3's subscription mechanism."""

        raise NotImplementedError

    async def subscribe(self) -> None:
        """Subscribes the current logged-in user to this item.

        Be careful — you can subscribe to the same work multiple times.

        Raises
        ------
        AuthError
            Invalid authenticity token was used (might be expired or not logged in).
        SubscribeError
            Something went wrong in the subscription process.
        """

        auth_token = getattr(self._http.state, "login_token", self.authenticity_token)

        if auth_token is None:
            raise AuthError
        if self.sub_id is not None:
            msg = "This item has already been subscribed to."
            raise SubscribeError(msg)

        assert self._http.state  # Not sure if this is accurate.
        client_username = self._http.state.client_user.username
        try:
            data = await self._http.subscribe(auth_token, client_username, self.id, self.subable_type)
        except HTTPException as err:
            raise SubscribeError from err
        else:
            self._cs_sub_id = data.get("item_id", None)

    async def unsubscribe(self) -> None:
        """Removes a subscription corresponding to this item.

        Raises
        ------
        AuthError
            Invalid authenticity token was used (might be expired or not logged in).
        SubscribeError
            Something went wrong in the subscription process.
        """

        auth_token = getattr(self._http.state, "login_token", self.authenticity_token)

        if auth_token is None:
            raise AuthError
        if self.sub_id is None:
            msg = "This item has not been subscribed to yet."
            raise SubscribeError(msg)

        assert self._http.state  # Not sure if this is accurate.
        client_username = self._http.state.client_user.username
        try:
            await self._http.unsubscribe(auth_token, client_username, self.id, self.subable_type, self.sub_id)
        except HTTPException as err:
            raise SubscribeError from err
        else:
            self._cs_sub_id = None


class CommentableMixin:
    # Includes works (?)
    async def comment(self) -> None:
        ...

    async def delete_comment(self) -> None:
        ...


class CollectableMixin:
    """A mixin that adds collection-related members and functionality to AO3 items that can be collected.

    The following implement this mixin:

    - :class:`ao3.Work`

    This mixin must also implement :class:`ao3.abc.Page`.
    """

    __slots__ = ()

    id: property | CachedSlotProperty[Self, int]
    _http: HTTPClient
    authenticity_token: CachedSlotProperty[Self, str | None]
    url: property | str

    async def collect(self, collections: list[str]) -> None:
        """Invite and/or collect this item to a list of collections.

        Raises
        ------
        AuthError
            Invalid authenticity token was used (might be expired or not logged in).
        CollectError
            Something went wrong in the collection process.
        """

        auth_token = getattr(self._http.state, "login_token", self.authenticity_token)

        if auth_token is None:
            raise AuthError

        try:
            path = self.url.partition(".org")[-1]
            resp, text = await self._http.collect(auth_token, path, ",".join(collections))
        except HTTPException as err:
            raise CollectError from err
        else:
            # TODO: Investigate if there's a better way to handle this.
            # Since AO3 doesn't return negative response codes for this, apparently, we need to manually parse the page
            # to determine success or failure.
            if resp.status == 302 and resp.headers["Location"] == AO3_AUTH_ERROR_URL:
                raise AuthError
            if resp.status == 200:
                element = html.fromstring(text)
                notice_el, error_el = element.cssselect("div.notice"), element.cssselect("div.error")
                if len(notice_el) == 0 and len(error_el) == 0:
                    raise CollectError

                if len(error_el) > 0:
                    errors = [str(el.text_content()) for el in error_el[0].cssselect("ul")]

                    if len(errors) > 0:
                        msg = f"We couldn't add your submission to the following collection(s): {', '.join(errors)}"
                        raise CollectError(msg)

                    raise CollectError
