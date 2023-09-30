"""
AO3 Scraper
~~~~~~~~~~~

A basic scraper for the Archive Of Our Own website.
"""

__title__ = "ao3"
__author__ = "Thanos"
__license__ = "MIT"
__copyright__ = "Copyright 2023-present Sachaa-Thanasius"
__version__ = "0.1.0"

from . import abc as abc, utils as utils
from .client import *
from .enums import *
from .errors import *
from .search import *
from .series import *
from .user import *
from .work import *
