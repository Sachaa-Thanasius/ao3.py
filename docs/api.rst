.. currentmodule:: ao3

API Reference
=============
This is the API reference for ao3.py.

Here are the relevant models and functions that allow interaction with AO3.


Client
------
.. autoclass:: Client
    :members:


Models
------

Work
~~~~
.. autoclass:: Work()
    :members:

Series
~~~~~~
.. autoclass:: Series()
    :members:

User
~~~~
.. autoclass:: User()
    :members:

Object
~~~~~~
.. autoclass:: Object
    :members:


Search
------

.. autoclass:: Search
    :members:

Work Search
~~~~~~~~~~~
.. autoclass:: WorkSearch
    :members:

.. autoclass:: WorkSearchOptions
    :members:

People Search
~~~~~~~~~~~~~
.. autoclass:: PeopleSearch
    :members:

.. autoclass:: PeopleSearchOptions
    :members:

Bookmark Search
~~~~~~~~~~~~~~~
.. autoclass:: BookmarkSearch
    :members:

.. autoclass:: BookmarkSearchOptions
    :members:

Tag Search
~~~~~~~~~~
.. autoclass:: TagSearch
    :members:

.. autoclass:: TagSearchOptions
    :members:


ABCs and Mixins
---------------

.. autoclass:: ao3.abc.Page
    :members:

.. autoclass:: ao3.abc.KudoableMixin
    :members:

.. autoclass:: ao3.abc.BookmarkableMixin
    :members:

.. autoclass:: ao3.abc.SubscribableMixin
    :members:

.. autoclass:: ao3.abc.CommentableMixin
    :members:

.. autoclass:: ao3.abc.CollectableMixin
    :members:


Enumerations
------------

.. autoclass:: RatingId
    :members:

.. autoclass:: ArchiveWarningId
    :members:

.. autoclass:: CategoryId
    :members:

.. autoclass:: Language
    :members:

.. autoclass:: FandomKey
    :members:


Utilities
---------

.. autoclass:: ao3.utils.Constraint

.. autofunction:: ao3.utils.get_id_from_url


Exceptions
----------

.. autoexception:: AO3Exception

.. autoexception:: HTTPException

.. autoexception:: LoginFailure

.. autoexception:: UnloadedError

.. autoexception:: AuthError

.. autoexception:: PseudError

.. autoexception:: KudoError

.. autoexception:: BookmarkError

.. autoexception:: SubscribeError

.. autoexception:: CollectError

.. autoexception:: InvalidURLError

.. autoexception:: DuplicateCommentError

.. autoexception:: DownloadError
