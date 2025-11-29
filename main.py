"""
Entrance point of the program.
"""

import logging

import fire

from sync_read import sync_read
from sync_trending import sync_trending
from sync_producthunt import sync_producthunt

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    fire.Fire(
        {
            "sync_read": sync_read,
            "sync_trending": sync_trending,
            "sync_producthunt": sync_producthunt,
        }
    )
