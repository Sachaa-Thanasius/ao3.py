"""
ao3.errors
-------------------

Custom exceptions for the ao3 package.
"""

import aiohttp


__all__ = (
    "AO3Exception",
    "HTTPException",
    "UnloadedError",
    "LoginError",
    "UnexpectedResponseError",
    "InvalidIdError",
    "DownloadError",
    "AuthError",
    "DuplicateCommentError",
    "PseudError",
    "BookmarkError",
    "CollectError",
)


class AO3Exception(Exception):
    """Base exception for AO3."""

    def __init__(self, message: str | None = None, *args: object) -> None:
        self.message = message
        super().__init__(*args)


class HTTPException(AO3Exception):
    """Exception that's raised when something goes wrong during an HTTP request."""

    def __init__(self, response: aiohttp.ClientResponse, message: str | None = None) -> None:
        self.response = response
        self.status = response.status
        self.text = message or ""

        new_message = f"{response.status} {response.reason or ''}"  # type: ignore
        if self.text:
            new_message += f": {self.text}"

        super().__init__(new_message)


class UnloadedError(AO3Exception):
    """Exception that's raised when the content of an AO3 object hasn't been loaded, but accessing it was attempted."""

    def __init__(self, message: str | None = None, *args: object) -> None:
        message = message or "._element for this object was never loaded, and thus has nothing to pull from."
        super().__init__(message, *args)


class LoginError(AO3Exception):
    """Exception that's raised when an attempt to log in to AO3 fails."""


class UnexpectedResponseError(AO3Exception):
    """Exception that's raised when something 'unexpected' happens. Used liberally."""


class InvalidIdError(AO3Exception):
    """Exception that's raised when an invalid AO3 object ID was passed in."""


class DownloadError(AO3Exception):
    """Exception that's raised when downloading an AO3 work fails."""


class AuthError(AO3Exception):
    """Exception that's raised when the authentication token for the AO3 session is invalid."""


class DuplicateCommentError(AO3Exception):
    """Exception that's raised when attempting to post a comment that already exists."""


class PseudError(AO3Exception):
    """Exception that's raised when a pseud's ID couldn't be found."""


class BookmarkError(AO3Exception):
    """Exception that's raised when attempting to create or access a bookmark fails."""


class CollectError(AO3Exception):
    """Exception that's raised when attempting to invite a work to a collection fails."""
