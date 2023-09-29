"""
ao3.utils
-------------------

Utility functions and classes for the ao3 package.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Generic, NamedTuple, TypeVar, overload

from lxml import html

from .errors import AO3Exception


T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)

__all__ = (
    "get_id_from_url",
    "Constraint",
)

AO3_STORY_REGEX = re.compile(r"(?:https://|)(?:www\.|)archiveofourown\.org/(?:works|series)/(?P<ao3_id>\d+)")
ICON_URL_USER_ID_REGEX = re.compile(r".*/(\d+)/")


def get_id_from_url(url: str, *, will_raise: bool = False) -> int | None:
    """Get the work/series ID from an AO3 website url.

    Parameters
    ----------
    url : :class:`str`
        The AO3 url. Could be for a series or a work.
    will_raise : :class:`bool`, default=False
        Whether to raise an exception if an id is not found in the given string. Defaults to false.

    Returns
    -------
    :class:`int` | None
        The work/series ID or None if not found.
    """

    result = AO3_STORY_REGEX.search(url)
    if will_raise and not result:
        raise AO3Exception
    return int(result.group("ao3_id")) if result else None


def parse_max_pages_num(element: html.HtmlElement) -> int:
    default_page_num = 1
    try:
        num_gen = (int(li.text_content().strip()) for li in element.cssselect("ol[title=pagination] li"))
        return max(num_gen)
    except AttributeError:
        return default_page_num


def extract_login_auth_token(text: str | html.HtmlElement) -> str | None:
    element = html.fromstring(text) if isinstance(text, str) else text
    try:
        return element.cssselect("input[name=authenticity_token]")[0].get("value", None)
    except IndexError:
        return None


def extract_csrf_token(text: str | html.HtmlElement) -> str | None:
    element = html.fromstring(text) if isinstance(text, str) else text
    try:
        return element.cssselect("meta[name=csrf-token]")[0].get("content", None)
    except IndexError:
        return None


def extract_pseud_id(element: html.HtmlElement, specified_pseud: str | None = None) -> str | None:
    pseuds = element.cssselect('input[name$="[pseud_id]"]')
    if len(pseuds) > 0:
        return pseuds[0].get("value")

    pseuds = element.cssselect('select[name$="[pseud_id]"]')
    if len(pseuds) > 0:
        return next(
            (
                option.get("value")
                for option in pseuds[0].cssselect("option")
                if bool(
                    (str(option.text_content()) == specified_pseud) if specified_pseud else option.get("selected"),
                )
            ),
            None,
        )

    return None


def int_or_none(data: str) -> int | None:
    try:
        return int(data.replace(",", ""))
    except ValueError:
        return None


def cssselect_one(element: html.HtmlElement, expr: str) -> html.HtmlElement | None:
    try:
        return element.cssselect(expr)[0]
    except IndexError:
        return None


class Constraint(NamedTuple):
    """A representation for a constraint on integer amounts via a range.

    Attributes
    ----------
    min_val : :class:`int`, default=0
        The lower end of the constraint. Defaults to 0.
    max_val : :class:`int` | None, optional
        The upper bound of the constraint. Optional.
    """

    min_val: int = 0
    max_val: int | None = None

    def string(self) -> str:
        """Stringify the constraint in a way that AO3 can understand."""

        if self.min_val == 0 and self.max_val is None:
            return ""
        if self.min_val == 0:
            return f"<{self.max_val}"
        if self.max_val is None:
            return f">{self.min_val}"
        if self.min_val == self.max_val:
            return str(self.min_val)

        return f"{self.min_val}-{self.max_val}"


class CachedSlotProperty(Generic[T, T_co]):
    """Source: https://github.com/Rapptz/discord.py/blob/master/discord/utils.py#L208"""

    def __init__(self, name: str, function: Callable[[T], T_co]) -> None:
        self.name = name
        self.function = function
        self.__doc__ = function.__doc__

    @overload
    def __get__(self, instance: None, owner: type[T]) -> CachedSlotProperty[T, T_co]:
        ...

    @overload
    def __get__(self, instance: T, owner: type[T]) -> T_co:
        ...

    def __get__(self, instance: T | None, owner: type[T]) -> T_co | CachedSlotProperty[T, T_co]:
        if instance is None:
            return self

        try:
            return getattr(instance, self.name)
        except AttributeError:
            value = self.function(instance)
            setattr(instance, self.name, value)
            return value


def cached_slot_property(name: str) -> Callable[[Callable[[T], T_co]], CachedSlotProperty[T, T_co]]:
    def decorator(func: Callable[[T], T_co]) -> CachedSlotProperty[T, T_co]:
        return CachedSlotProperty(name, func)

    return decorator
