# ao3.py
[![License: MIT](https://img.shields.io/github/license/Sachaa-Thanasius/ao3.py.svg)](https://opensource.org/licenses/MIT)
[![Checked with pyright](https://img.shields.io/badge/pyright-checked-informational.svg)](https://github.com/microsoft/pyright/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![Documentation Status](https://readthedocs.org/projects/ao3py/badge/?version=latest)](https://ao3py.readthedocs.io/en/latest/?badge=latest)

An asynchronous scraper of Archive Of Our Own, made in Python.

## Features

- Uses Python's `async`/`await` syntax
- Fully type annotated


## Documentation

[Official Documentation](https://ao3py.readthedocs.io/en/latest)


# Installation

**ao3.py currently requires Python 3.8 or higher.**

To install the library, run one of the following commands:

```sh
# Linux/macOS
python3 -m pip install -U "ao3.py @ git+https://github.com/Sachaa-Thanasius/ao3.py@main"

# Windows
py -3 -m pip install -U "ao3.py @ git+https://github.com/Sachaa-Thanasius/ao3.py@main"
```


## Quick Example

```python
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
```

# To Do

- [ ] Properly implement and test user-based actions
    - [ ] Logging in
    - [ ] Giving kudos
    - [ ] (Un)bookmarking
    - [ ] (Un)subscribing
    - [ ] Adding/Deleting comments
    - [ ] (Un)collecting


## Motivation

Honestly, I just wanted a fully typed Python AO3 scraper that I could use in asynchronous contexts. That's it.


# Acknowledgements

Thank you to:

- other AO3 scrapers like Armindo Flores's `[ao3_api](https://github.com/ArmindoFlores/ao3_api),
- large projects like [discord.py](https://github.com/Rapptz/discord.py/) and [steam.py](https://github.com/Gobot1234/steam.py) for heavily inspiring the overall structure of this repo,
- and of course, aeroali, for everything.



