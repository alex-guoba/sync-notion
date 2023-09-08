"""
同步github trending到notion
"""
import logging
import time
import requests
from pyquery import PyQuery as pq
from github import Github
from github import Auth

from notion_client import Client

from config import CONFIG

class TrendItem:
    """trend item"""
    def __init__(self, title: str, url: str, desc: str) -> None:
        self.title = title
        self.url = url
        self.desc = desc
        self.watchers_count = 0
        self.forks_count = 0
        self.stargazers_count = 0

    def _repo_path(self) -> str:
        items = self.url.split('/')[-2:]
        return '/'.join(items)

    def fullfill_repo_info(self, git_token):
        "fullfill basic info from repo"
        if not self.url:
            return
        auth = None
        if git_token:
            auth = Auth.Token(git_token)
        git = Github(auth=auth)

        try:
            repo = git.get_repo(self._repo_path())
        # pylint: disable-next=broad-except
        except Exception as _e:
            logging.error("get repo %s error: %s", self._repo_path() , _e)
            return

        self.watchers_count = repo.watchers_count
        self.forks_count = repo.forks_count
        self.stargazers_count = repo.stargazers_count

def query_page(client: Client, database_id: str, title: str) -> bool:
    """检查是否已经插入过 如果已经插入了就忽略"""
    time.sleep(0.3)

    response = client.databases.query(
        database_id=database_id,
        filter={
            "property": "Title",
            "rich_text": {
                "equals": title
            }
        })
    if len(response["results"]):
        return True
    return False


def insert_page(client: Client, database_id: str, language: str, trend: TrendItem) -> None | str:
    '''插入page'''
    parent = {
        "database_id": database_id,
        "type": "database_id"
    }
    properties = {
        "Title": {"title": [{"type": "text", "text": {"content": trend.title}}]},
        "Language": {"select": {"name": language}},
        "URL": {"url": trend.url},
        "Desc": {"rich_text": [{"type": "text", "text": {"content": trend.desc}}]},
        "WatchersCount": {"number": trend.watchers_count},
        "ForksCount": {"number": trend.forks_count},
        "StargazersCount": {"number": trend.stargazers_count},
    }
    response = client.pages.create(parent=parent, properties=properties)
    return response["id"]

def _scrape(language: str) -> list[TrendItem]:
    headers = {
        # pylint: disable=line-too-long
        'User-Agent'		: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
        'Accept'			: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding'	: 'gzip,deflate,sdch',
        'Accept-Language'	: 'zh-CN,zh;q=0.8'
    }
    result = []

    url = f'https://github.com/trending/{language}'.format(language=language)
    req = requests.get(url, headers=headers)
    if req.status_code != 200:
        logging.error("git trending error. %d", req.status_code)
        return

    content = pq(req.content)
    items = content('div.Box article.Box-row')

    # codecs to solve the problem utf-8 codec like chinese
    # with codecs.open(filename, "a", "utf-8") as f:
    #     # f.write('\n#### {language}\n'.format(language=language))

    for item in items:
        i = pq(item)
        title = i(".lh-condensed a").text()
        description = i("p.col-9").text()
        url = "https://github.com" + i(".lh-condensed a").attr("href")

        result.append(TrendItem(title, url, description))

    return result

# pylint: disable=line-too-long
def _sync(client: Client, database_id: str, language: str, trends: list[TrendItem], git_token: str) -> None:
    for trend in trends:
        time.sleep(0.3) # avoid rate limit for notion API
        if query_page(client, database_id, trend.title):
            continue
        # insert to db
        logging.info(trend)

        if git_token:
            trend.fullfill_repo_info(git_token)

        insert_page(client, database_id, language, trend)


def sync_trending(notion_token, database_id, git_token=None):
    """同步github trending到notion"""
    client = Client(
        auth=notion_token,
        log_level=logging.ERROR
    )

    languages = list(map(lambda x: x.strip(), CONFIG.get("trending.language", "languages").split(",")))
    for language in languages:
        if not language:
            continue

        logging.info("sync %s", language)

        trends = _scrape(language)
        if not trends:
            logging.error("language [%s] error", language)
            continue

        _sync(client, database_id, language, trends, git_token)
