import fire
import logging

from sync_read import sync_read
from sync_trending import sync_trending

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    fire.Fire({
      'sync_read': sync_read,
      'sync_trending': sync_trending,
  })
