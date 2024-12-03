"""
同步product hunt到notion
"""

import logging
import time
import requests
from pyquery import PyQuery as pq
from notion_client import Client

from config import CONFIG
from api.notion import BlockHelper


class ProductItem:
    """product item"""

    def __init__(
        self,
        name: str,
        desc: str,
        topics: list[str],
        comments: int,
        votes: int,
        url: str = "",
        cover: str = "",
    ) -> None:
        self.name = name
        self.desc = desc
        self.topics = topics
        self.comments = comments
        self.votes = votes
        self.cover = cover
        self.url = f"https://www.producthunt.com{url}"

    # def fullfill_repo_info(self, git_token):
    #     pass
    def __repr__(self) -> str:
        return f"""<ProductItem name={self.name} desc={self.desc} topics={self.topics} \
comments={self.comments} votes={self.votes} url={self.url} cover={self.cover}>"""


def query_page(client: Client, database_id: str, name: str) -> bool:
    """check page exist or not"""
    time.sleep(0.3)

    response = client.databases.query(
        database_id=database_id,
        filter={"property": "Name", "rich_text": {"equals": name}},
    )
    if len(response["results"]):
        return True
    return False


def _append_page(client: Client, database_id: str, prod: ProductItem) -> None | str:
    """插入page"""
    parent = {"database_id": database_id, "type": "database_id"}
    properties = {
        "Name": BlockHelper.title(prod.name),
        "Description": BlockHelper.rich_text(prod.desc),
        "Topics": BlockHelper.multi_select(prod.topics),
        "Comments": BlockHelper.number(prod.comments),
        "Votes": BlockHelper.number(prod.votes),
        "URL": BlockHelper.url(prod.url),
        "Cover": BlockHelper.files("Cover", prod.cover),
    }
    response = client.pages.create(
        parent=parent, icon=BlockHelper.icon(prod.cover), properties=properties
    )
    return response["id"]


def _scrape() -> list[ProductItem]:
    headers = {
        # pylint: disable=line-too-long
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip,deflate,sdch",
        "Accept-Language": "zh-CN,zh;q=0.8",
    }
    result = []

    url = "https://www.producthunt.com/all"
    req = requests.get(url, headers=headers, timeout=60)
    if req.status_code != 200:
        logging.error("access product hunt error. %d", req.status_code)
        return

    content = pq(req.content)
    items = content("main div.flex-col div.flex-col div[class^='styles_item']")
    if items.length == 0:
        items = content("main div.flex-col div.flex-col section")

    for item in items:
        logging.debug("parse product: %s", item)
        i = pq(item)
        url = i('a[href^="/posts/"]').eq(0).attr("href")

        mid = i("div.flex-col a")
        name = mid.eq(0).text()
        description = mid.eq(1).text()
        # name = i("div.flex-col a strong").text()
        # description = i("div.flex-col a").text()

        comments = i("div.flex-col div.flex-row div").eq(0).text()
        if not comments:
            comments = i("button div.flex-col").eq(0).text()

        votes = i('button[data-test="vote-button"]').text()

        cover = i('a[href^="/posts/"] img').eq(0).attr("src")
        if not cover:
            cover = i('a[href^="/posts/"] video').eq(0).attr("poster")

        _topics = i('div.flex-col div.flex-row a[href^="/topics/"]')
        topics = []
        for topic in _topics:
            topic = pq(topic).text()
            topics.append(topic)

        if name == "" or description == "" or len(topics) == 0:
            logging.error(
                "parse name or description error: %s-%s-%d",
                name,
                description,
                len(topics),
            )
            continue
        if not votes.isnumeric() or not comments.isnumeric():
            logging.error(
                "parse votes or comments error: %s-%s-%s", name, votes, comments
            )
            continue

        try:
            votes = int(votes)
            comments = int(comments)
        except ValueError:
            logging.error("parse votes or comments error")
            continue

        result.append(
            ProductItem(
                name, description, topics, votes, comments, url=url, cover=cover
            )
        )

    return result


def _filter_product(prod: ProductItem) -> bool:
    filters = {
        "MinVotes": "votes",
        "MinComments": "comments",
    }
    for k, v in filters.items():
        thresh_hold = CONFIG.getint("producthunt.filter", k)
        current = getattr(prod, v, 0)
        if thresh_hold > 0 and current < thresh_hold:
            return True
    return False


# pylint: disable=line-too-long
def _sync(
    client: Client,
    database_id: str,
    products: list[ProductItem],
) -> None:
    for prod in products:
        if _filter_product(prod):
            logging.info("filter product: %s", prod.name)
            continue

        time.sleep(0.3)  # avoid rate limit for notion API
        if query_page(client, database_id, prod.name):
            continue

        # insert to db
        logging.info(prod)

        _id = _append_page(client, database_id, prod)
        print(_id)


def sync_producthunt(notion_token, database_id):
    """sync product hunt to notion"""
    client = Client(auth=notion_token, log_level=logging.ERROR)

    products = _scrape()
    if not products:
        logging.error(
            "ph scape error",
        )
        return

    logging.info("ph scape total num [%s]", len(products))
    _sync(client, database_id, products)
