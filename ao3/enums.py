from __future__ import annotations

from enum import Enum


__all__ = (
    "ArchiveWarningId",
    "CategoryId",
    "FandomKey",
    "Language",
    "RatingId",
)


class RatingId(Enum):
    NOT_RATED = 9
    GENERAL_AUDIENCES = 10
    TEEN_AND_UP = 11
    MATURE = 12
    EXPLICIT = 13


class ArchiveWarningId(Enum):
    NOT_WARNED = 14
    VIOLENCE = 17
    MAJOR_DEATH = 18
    NO_WARNINGS = 16
    NONCON = 19
    UNDERAGE = 20


class CategoryId(Enum):
    FF = 116
    FM = 22
    GEN = 21
    MM = 23
    MULTI = 2246
    OTHER = 24


class Language(Enum):
    SO = "Soomaali"
    AFR = "Afrikaans"
    AR = "العربية"
    EGY = "𓂋𓏺𓈖 𓆎𓅓𓏏𓊖"
    ARC = "ܐܪܡܝܐ | ארמיא"
    HY = "հայերեն"
    AST = "asturianu"
    ID = "Bahasa Indonesia"
    MS = "Bahasa Malaysia"
    BG = "Български"
    BN = "বাংলা"
    JV = "Basa Jawa"
    BA = "Башҡорт теле"
    BE = "беларуская"
    BR = "Brezhoneg"
    CA = "Català"
    CS = "Čeština"
    CY = "Cymraeg"
    DA = "Dansk"
    DE = "Deutsch"
    ET = "eesti keel"
    EL = "Ελληνικά"
    EN = "English"
    ES = "Español"
    EO = "Esperanto"
    EU = "Euskara"
    FA = "فارسی"
    FR = "Français"
    GA = "Gaeilge"
    GD = "Gàidhlig"
    GL = "Galego"
    KO = "한국어"
    HI = "हिन्दी"
    HR = "Hrvatski"
    IA = "Interlingua"
    ZU = "isiZulu"
    IS = "Íslenska"
    IT = "Italiano"
    HE = "עברית"
    SW = "Kiswahili"
    HT = "kreyòl ayisyen"
    KU = "Kurdî | کوردی"
    LV = "Latviešu valoda"
    LB = "Lëtzebuergesch"
    LT = "Lietuvių kalba"
    LA = "Lingua latina"
    HU = "Magyar"
    MK = "македонски"
    ML = "മലയാളം"
    MT = "Malti"
    MR = "मराठी"
    MY = "မြန်မာဘာသာ"
    NL = "Nederlands"
    JA = "日本語"
    NO = "Norsk"
    CE = "Нохчийн мотт"
    PS = "پښتو"
    PL = "Polski"
    PA = "ਪੰਜਾਬੀ"
    RO = "Română"
    RU = "Русский"
    SQ = "Shqip"
    SI = "සිංහල"
    SK = "Slovenčina"
    SR = "Српски"
    FI = "Suomi"
    SV = "Svenska"
    TA = "தமிழ்"
    TH = "ไทย"
    VI = "Tiếng Việt"
    TR = "Türkçe"
    UK = "Українська"
    YI = "יידיש"
    ZH = "中文-普通话 國語"
    UNKNOWN = "Unknown"

    @classmethod
    def _missing_(cls, value: object) -> Language:
        try:
            value = str(value).casefold()
            for member in cls:
                if member.value.casefold() == value:
                    return member
        except ValueError:
            return cls.UNKNOWN
        else:
            return cls.UNKNOWN


class FandomKey(Enum):
    ANIME = "Anime *a* Manga"
    BOOK = "Books *a* Literature"
    CARTOON = "Cartoons *a* Comics *a* Graphic Novels"
    CELEBRITIES = "Celebrities *a* Real People"
    MUSIC = "Music *a* Bands"
    OTHER = "Other Media"
    THEATER = "Theater"
    TV_SHOW = "TV Shows"
    VIDEOGAME = "Video Games"
    UNCATEGORIZED = "Uncategorized Fandoms"
