"""
AO3 Scraper/Wrapper
-------------------

A basic scraper/wrapper for the Archive Of Our Own website.
"""

__title__ = "ao3"
__author__ = "Thanos"
__license__ = "MIT"
__version__ = "2023.9.23"

from . import utils as utils
from .abc import *
from .client import *
from .enums import *
from .errors import *
from .http import *
from .search import *
from .series import *
from .user import *
from .work import *
