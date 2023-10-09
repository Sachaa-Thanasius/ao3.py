from aiohttp import ClientResponse


__all__ = (
    "AO3Exception",
    "HTTPException",
    "LoginFailure",
    "UnloadedError",
    "AuthError",
    "PseudError",
    "KudoError",
    "BookmarkError",
    "SubscribeError",
    "CollectError",
    "InvalidURLError",
    "DuplicateCommentError",
    "DownloadError",
)


AO3_AUTH_ERROR_URL = "https://archiveofourown.org/auth_error"


class AO3Exception(Exception):
    """Base exception for AO3."""


class HTTPException(AO3Exception):
    """Exception that's raised when something goes wrong during an HTTP request.

    Parameters
    ----------
    response: :class:`aiohttp.ClientResponse`
        The HTTP response that caused this error.
    message: :class:`str`
        The given message accompanying this error to be added to the error display.

    Attributes
    ----------
    response: :class:`aiohttp.ClientResponse`
        The HTTP response that caused this error.
    status: :class:`int`
        The HTTP status or code of the response.
    text: :class:`str`
        The message accompanying this error that will be part of the error display.
    """

    def __init__(self, response: ClientResponse, message: str | None = None) -> None:
        self.response = response
        self.status = response.status
        self.text = message or ""

        new_message = f"{response.status} {response.reason or ''}"  # type: ignore[reportUnknownMemberType]
        if self.text:
            new_message += f": {self.text}"

        super().__init__(new_message)


class LoginFailure(AO3Exception):
    """Exception that's raised when an attempt to log in to AO3 fails."""


class UnloadedError(AO3Exception):
    """Exception that's raised when the content of an AO3 object hasn't been loaded, but accessing it was attempted."""

    def __init__(self, message: str | None = None) -> None:
        message = message or "._element for this object was never loaded, and thus has nothing to pull from."
        super().__init__(message)


class AuthError(AO3Exception):
    """Exception that's raised when the authentication token for the AO3 session is invalid."""

    def __init__(self, message: str | None = None) -> None:
        message = message or (
            "Valid authenticity token for this model can't be found. If you're sure you don't need to be logged in to "
            "perform this action, try again after reloading the model."
        )
        super().__init__(message)


class PseudError(AO3Exception):
    """Exception that's raised when a pseud's ID couldn't be found."""

    def __init__(self, pseud: str | None = None) -> None:
        actual_pseud = f'pseud "{pseud}"' if pseud else "your default pseud"
        message = f"The ID for {actual_pseud} could not be found."
        super().__init__(message)


class KudoError(AO3Exception):
    """Exception that's raised when attempting to give a kudo fails."""

    def __init__(self, message: str | None = None) -> None:
        message = message or "Unknown error coccured while attempting to give kudos to this item."
        super().__init__(message)


class BookmarkError(AO3Exception):
    """Exception that's raised when attempting to create or access a bookmark fails."""

    def __init__(self, message: str | None = None) -> None:
        message = message or "Unknown error coccured while attempting to bookmark this item."
        super().__init__(message)


class SubscribeError(AO3Exception):
    """Exception that's raised when attempting to create or access a subscription fails."""

    def __init__(self, message: str | None = None) -> None:
        message = message or "Unknown error coccured while attempting to subscribe to this item."
        super().__init__(message)


class CollectError(AO3Exception):
    """Exception that's raised when attempting to invite a work to a collection fails."""

    def __init__(self, message: str | None = None) -> None:
        message = message or "Unknown error coccured while attempting to collect this item."
        super().__init__(message)


class InvalidURLError(AO3Exception):
    """Exception that's raised when an invalid AO3 url was passed in."""


class DownloadError(AO3Exception):
    """Exception that's raised when downloading an AO3 work fails."""


class DuplicateCommentError(AO3Exception):
    """Exception that's raised when attempting to post a comment that already exists."""
