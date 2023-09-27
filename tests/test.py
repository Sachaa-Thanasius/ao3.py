from __future__ import annotations

import asyncio
import logging
from time import perf_counter
from typing import TYPE_CHECKING, Any, TypeAlias, TypeVar

import ao3


if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self
else:
    Self: TypeAlias = Any

BE = TypeVar("BE", bound=BaseException)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class catchtime:
    """Utility context manager for timing execution of statements."""

    def __init__(self) -> None:
        self.time = 0.0
        self.readout = ""

    def __enter__(self) -> Self:
        self.time = perf_counter()
        return self

    def __exit__(self, exc_type: type[BE] | None, exc_value: BE | None, traceback: TracebackType | None) -> None:
        self.time = perf_counter() - self.time
        self.readout = f"Time: {self.time:.3f} seconds"


async def get_work_test(client: ao3.Client, url: str) -> None:
    log.info("----------WORK OBJECT TESTING----------")

    work_id = ao3.utils.id_from_url(url)
    assert work_id

    with catchtime() as work_time:
        work = await client.get_work(work_id)

    try:
        log.info("Work instance dict: %s", work.__dict__)
    except AttributeError:
        log.info("Work instance has no dict")
    log.info("load time: %s", work_time.time)
    log.info("repr: %r", work)
    log.info("url: %s", work.url)
    log.info("summary: %s", work.summary)

    with catchtime() as work_stats_time:
        stats = work.stats
        words = work.nwords

    log.info(
        "stats:\nstats time: %s\nbookmarks=%s comments=%s hits=%s kudos=%s words=%s",
        work_stats_time.time,
        *stats,
        words,
    )

    with catchtime() as tags_time:
        tags = list(work.all_tags())

    log.info("tags:\n%s\n%s", tags_time.time, tags)
    log.info("completed? %s", work.is_complete)
    log.info("--------------------------------------------------")


async def get_series_test(client: ao3.Client, url: str) -> None:
    log.info("----------SERIES OBJECT TESTING----------")

    series_id = ao3.utils.id_from_url(url)
    assert series_id

    with catchtime() as series_time:
        series = await client.get_series(series_id)

    try:
        log.info("Series instance dict: %s", series.__dict__)
    except AttributeError:
        log.info("Series instance has no dict")
    log.info("load time: %s", series_time.time)
    log.info("repr: %r", series)
    log.info("url: %s", series.url)
    log.info("description: %s", series.description)

    with catchtime() as series_stats_time:
        stats = series.stats

    log.info(
        "stats:\nstats time: %s\nwords=%s works=%s complete=%s bookmarks=%s",
        series_stats_time.time,
        *stats,
    )

    with catchtime() as series_works_time:
        works = list(series.works_list)

    log.info("works:\n%s\n%s", series_works_time.time, works)

    with catchtime() as series_works_time:
        works = list(series.works_list)

    log.info("\nSecond time - works:\n%s\n%s", series_works_time.time, works)

    log.info("--------------------------------------------------")


async def get_user_test(client: ao3.Client, username: str) -> None:
    log.info("----------USER OBJECT TESTING----------")

    with catchtime() as user_time:
        user = await client.get_user(username)

    log.info("load time: %s", user_time.time)
    log.info("repr: %r", user)
    log.info("user id: %s", user.id)
    log.info("url: %s", user.url)
    log.info("avatar url: %s", user.avatar_url)
    log.info(
        "stats: works=%s series=%s bookmarks=%s collections=%s gifts=%s",
        user.nworks,
        user.nseries,
        user.nbookmarks,
        user.ncollections,
        user.ngifts,
    )
    log.info("--------------------------------------------------")


async def main() -> None:
    test_work_url = "https://archiveofourown.org/works/48637876"
    test_series_url = "https://archiveofourown.org/series/1902145"
    test_username = "Quordle"

    async with ao3.Client() as client:
        await get_work_test(client, test_work_url)
        await get_series_test(client, test_series_url)
        await get_user_test(client, test_username)

    await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(main())
