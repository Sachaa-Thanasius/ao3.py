from functools import partial

from lxml import cssselect


__all__ = (
    "WORK_SELECTORS",
    "SERIES_SELECTORS",
    "USER_SELECTORS",
)

CSSSelector = partial(cssselect.CSSSelector, translator="html")


# fmt: off
# Selectors for a work's front page.
WORK_SELECTORS = {
    "sub_id":           CSSSelector("ul.work.navigation.actions li.subscribe form"),
    "title":            CSSSelector("h2.title"),
    "authors":          CSSSelector('div.preface.group a[rel*="author"]'),
    "summary":          CSSSelector("div.summary > blockquote.userstuff"),
    "series":           CSSSelector("dl.work.meta.group dd.series span.position a"),
    "restricted":       CSSSelector('img [title*="Restricted"]'),
    "rating":           CSSSelector("dl.work.meta.group dd.fandom.tags li"),
    "warnings":         CSSSelector("dl.work.meta.group dd.warning.tags li"),
    "categories":       CSSSelector("dl.work.meta.group dd.category.tags li"),
    "fandoms":          CSSSelector("dl.work.meta.group dd.fandom.tags li"),
    "relationships":    CSSSelector("dl.work.meta.group dd.relationship.tags li"),
    "characters":       CSSSelector("dl.work.meta.group dd.character.tags li"),
    "freeforms":        CSSSelector("dl.work.meta.group dd.freeform.tags li"),
    "language":         CSSSelector("dl.work.meta.group dd.language"),
    "date_published":   CSSSelector("dl.work.meta.group dl.stats > dd.published"),
    "date_updated":     CSSSelector("dl.work.meta.group dl.stats > dd.updated"),
    "nwords":           CSSSelector("dl.work.meta.group dl.stats > dd.words"),
    "nchapters":        CSSSelector("dl.work.meta.group dl.stats > dd.chapters"),
    "ncomments":        CSSSelector("dl.work.meta.group dl.stats > dd.comments"),
    "nkudos":           CSSSelector("dl.work.meta.group dl.stats > dd.kudos"),
    "nbookmarks":       CSSSelector("dl.work.meta.group dl.stats > dd.bookmarks"),
    "nhits":            CSSSelector("dl.work.meta.group dl.stats > dd.hits"),
}


# Selectors for a work stub on a series/user/search/etc. page.
SEARCH_SELECTOR = {
    "work":             CSSSelector("li.work.blurb.group"),
    "people":           CSSSelector("li.user.blurb.group"),
    "bookmark":         CSSSelector("li.bookmark.blurb.group"),
    "tag":              CSSSelector("ol.tag.index.group > li"),
}


# Selectors for a series page.
SERIES_SELECTORS = {
    "sub_btn":          CSSSelector('form[data-create-value="Subscribe"]'),
    "name":             CSSSelector("div#main > h2.heading"),
    "creators":         CSSSelector('dl.series.meta.group > dd > a[rel="author"]'),
    "dates":            CSSSelector("dl.series.meta.group > dd"),
    "descr":            CSSSelector("dl.series.meta.group > dd > blockquote.userstuff"),
    "stats":            CSSSelector("dl.series.meta.group > dd.stats > dl.stats > dd"),
    "works":            CSSSelector("ul.series.work.index.group > li"),
}


# Selectors for a user's profile page.
USER_SELECTORS = {
    "profile_info":     CSSSelector("dl.meta dd"),
    "sub_id":           CSSSelector("div.primary.header.module form[action]"),
    "avatar":           CSSSelector("img.icon"),
    "pseuds":           CSSSelector("dl.meta > dd.pseuds > a"),
    "bio":              CSSSelector("div.bio.module > blockquote.userstuff"),
    "nworks":           CSSSelector('ul.navigation.actions > li > a[href$="works"]'),
    "nseries":          CSSSelector('ul.navigation.actions > li > a[href$="series"]'),
    "nbookmarks":       CSSSelector('ul.navigation.actions > li > a[href$="bookmarks"]'),
    "ncollections":     CSSSelector('ul.navigation.actions > li > a[href$="collections"]'),
    "ngifts":           CSSSelector('ul.navigation.actions > li > a[href$="gifts"]'),
}
# fmt: on
