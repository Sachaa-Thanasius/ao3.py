ao3.py
======

.. image:: https://img.shields.io/github/license/Sachaa-Thanasius/ao3.py.svg
    :target: LICENSE
    :alt: License: MIT

.. image:: https://img.shields.io/badge/pyright-checked-informational.svg
    :target: https://microsoft.github.io/pyright/
    :alt: Checked with pyright

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Ruff

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Code style: black

.. image:: https://readthedocs.org/projects/ao3py/badge/?version=latest
    :target: https://ao3py.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status


An asynchronous scraper of Archive Of Our Own, made in Python.

Features
--------

- Uses Python's ``async``/``await`` syntax
- Fully type annotated


Documentation
-------------

`Official Documentation <https://ao3py.readthedocs.io/en/latest>`_.


Installation
------------

**ao3.py currently requires Python 3.8 or higher.**

To install the development version, run one of the following commands:

.. code:: sh

    # Windows
    py -3.10 -m pip install -U "ao3.py @ git+https://github.com/Sachaa-Thanasius/ao3.py@main"

    # Linux
    python3.10 -m pip install -U "ao3.py @ git+https://github.com/Sachaa-Thanasius/ao3.py@main"


Quick Example
-------------

.. code-block:: py

    import asyncio
    import ao3

    async def main():
        test_url = "https://archiveofourown.org/works/48637876"

        async with ao3.Client() as client:
            work_id = ao3.utils.get_id_from_url(test_url)
            work = await client.get_work(work_id)
            print(work)
            print(work.stats)

    asyncio.run(main)


To Do
-----

* ☐ Properly implement and test user-based actions
    * ☐ Logging in
    * ☐ Giving kudos
    * ☐ (Un)bookmarking
    * ☐ (Un)subscribing
    * ☐ Adding/Deleting comments
    * ☐ (Un)collecting


Motivation
----------

Honestly, I just wanted a fully typed Python AO3 scraper that I could use in asynchronous contexts. That's it.


Acknowledgements
----------------

Thank you to:

- other AO3 scrapers like Armindo Flores's `ao3_api <https://github.com/ArmindoFlores/ao3_api>`_,
- large projects like `discord.py <https://github.com/Rapptz/discord.py/>`_ and `steam.py <https://github.com/Gobot1234/steam.py>`_ for heavily inspiring the overall structure of this repo,
- and of course, aeroali, for everything.



