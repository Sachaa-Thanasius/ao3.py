from __future__ import annotations

from typing import TYPE_CHECKING, SupportsInt, Union


if TYPE_CHECKING:
    from .abc import Page
else:
    Page = object

SupportsIntCast = Union[SupportsInt, str, bytes, bytearray]


__all__ = ("Object",)


class Object:
    """Represents a generic AO3 object.

    This serves as a standin for user items when the full data to form those items isn't available.

    Parameters
    ----------
    id: :class:`int` | None, optional
        The ID of the object. This or `name` must be provided. Defaults to None.
    name: :class:`str` | None, optional
        The name of the object. This or `id` must be provided. Defaults to None.
    type: type[:class:`Page`] | None, optional
        The type of the object, which can be any Page subclasses. Defaults to None, which is substituted with `Object`.

    Attributes
    ----------
    id: :class:`int` | None, optional
        The ID of the object. Defaults to None.
    name: :class:`str` | None, optional
        The name of the object. Defaults to None.
    type: type[:class:`ao3.abc.Page`] | type[:class:`Object`]
        The type of the object, which can be any Page subclasses. Defaults to `Object`.
    """

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
        attrs_ = ("id", "name", "type")
        resolved = (f"{attr}={val}" for attr in attrs_ if (val := getattr(self, attr)) is not None)
        return f"{type(self).__name__}({' '.join(resolved)})"
