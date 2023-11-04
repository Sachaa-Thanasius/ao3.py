from __future__ import annotations

import asyncio
import logging
from time import perf_counter
from typing import TYPE_CHECKING, TypeVar

import ao3


if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self
else:
    TracebackType = Self = object

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


async def get_work_test(client: ao3.Client) -> None:
    url = "https://archiveofourown.org/works/48637876"

    log.info("----------WORK OBJECT TESTING----------")

    work_id = ao3.utils.get_id_from_url(url)
    assert work_id

    with catchtime() as work_time:
        work = await client.get_work(work_id)

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


async def get_series_test(client: ao3.Client) -> None:
    url = "https://archiveofourown.org/series/1664050"

    log.info("----------SERIES OBJECT TESTING----------")

    series_id = ao3.utils.get_id_from_url(url)
    assert series_id

    with catchtime() as series_time:
        series = await client.get_series(series_id)

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

    for work in works:
        log.info("Work Stats: %s", work.stats)
        log.info("Work Chapters: %s", work.nchapters)

    log.info("works:\n%s\n%s", series_works_time.time, works)

    with catchtime() as series_works_time:
        works = list(series.works_list)

    log.info("\nSecond time - works:\n%s\n%s", series_works_time.time, works)

    log.info("--------------------------------------------------")


async def get_user_test(client: ao3.Client) -> None:
    username = "Quordle"

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


async def get_search_test(client: ao3.Client) -> None:
    log.info("----------SEARCH TESTING----------")

    # Create work search parameters
    search_params = ao3.WorkSearchOptions(author="deniigiq")
    with catchtime() as search_time:
        search = await client.search_works(search_params)

    log.info("Select: %r", search)
    log.info("load time: %s", search_time.time)
    log.info("1st page (%s):\n%s\n", len(search.results), "\n".join(f"{result!r}" for result in search.results))

    search_params.page = 2
    search = await client.search_works(search_params)
    log.info("2nd page (%s):\n%s\n", len(search.results), "\n".join(f"{result!r}" for result in search.results))

    # Test work search generator
    async for page_search in client.work_search_pages(search_params, stop=5):
        log.info(
            "Page %s:\n%s\n",
            page_search.search_options.page,
            "\n".join(f"{work!r}" for work in page_search.results),
        )
    log.info("--------------------------------------------------")


async def run_tests() -> None:
    async with ao3.Client() as client:
        await get_work_test(client)
        await get_series_test(client)
        await get_user_test(client)
        await get_search_test(client)

    await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(run_tests())
