"""
sysnc  memos to notion database.
"""
import logging
import time
import requests

from notion_client import Client

from config import CONFIG

class MemosItem:
    """
    memos item, format:
        "id": 3,
        "rowStatus": "NORMAL",
        "creatorId": 101,
        "createdTs": 1696766005,
        "updatedTs": 1696766005,
        "displayTs": 1696766005,
        "content": "**[Slash](https://github.com/boojack/slash)**:",
        "visibility": "PUBLIC",
        "pinned": true,
        "parent": null,
        "creatorName": "Derobot",
        "creatorUsername": "memos-demo",
        "resourceList": [
            {
            "id": 1,
            "creatorId": 101,
            "createdTs": 1696925000,
            "updatedTs": 1696925000,
            "filename": "00002.jpg",
            "externalLink": "",
            "type": "image/jpeg",
            "size": 77321
            }
        ],
        "relationList": []
    """
    def __init__(self, data) -> None:
        self.id: str = str(data.get('id'))
        self.row_status: str = data.get('rowStatus')
        self.creator_id: int = data.get('creatorId')
        self.created_ts: int  = data.get('createdTs')
        # self.updated_ts = data.get('updatedTs')
        self.content: str = str(data.get('content'))
        self.visibility: str = str(data.get('visibility'))
        self.pinned: str = str(data.get('pinned'))
        self.parent: str = str(data.get('parent')) # convert to string
        self.creator_name: str = str(data.get('creatorName'))
        self.creator_username: str = str(data.get('creatorUsername'))
        # self.creatorUsername = data.get('creatorUsername')


def query_page(client: Client, database_id: str, id: int) -> bool:
    """检查是否已经插入过 如果已经插入了就忽略"""
    time.sleep(0.3)

    response = client.databases.query(
        database_id=database_id,
        filter={
            "property": "ID",
            "rich_text": {
                "equals": str(id)
            }
        })
    if len(response["results"]):
        return True
    return False


def insert_page(client: Client, database_id: str, memos: MemosItem) -> None | str:
    '''插入page'''
    parent = {
        "database_id": database_id,
        "type": "database_id"
    }

    # pylint: disable=line-too-long
    properties = {
        "ID": {"title": [{"type": "text", "text": {"content": memos.id}}]},
        "RowStatus": {"rich_text": [{"type": "text", "text": {"content": memos.row_status}}]},
        "CreatorID": {"number": memos.creator_id},
        "CreatedTs": {"number": memos.created_ts},
        "Content": {"rich_text": [{"type": "text", "text": {"content": memos.content}}]},
        "Visibility": {"select": {"name": memos.visibility}},
        "Pinned": {"select": {"name": memos.pinned}},
        "Parent": {"rich_text": [{"type": "text", "text": {"content": memos.parent}}]},
        "CreatorName": {"rich_text": [{"type": "text", "text": {"content": memos.creator_name}}]},
        "CreatorUsername": {"rich_text": [{"type": "text", "text": {"content": memos.creator_username}}]},
    }
    response = client.pages.create(parent=parent, properties=properties)
    return response["id"]

# pylint: disable=line-too-long
def _memos_list(offset: int, limit: int, host: str, create_user: str, memos_token: str) -> list[MemosItem]:
    headers = {
        # pylint: disable=line-too-long
        'User-Agent'		: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:11.0) Gecko/20100101 Firefox/11.0',
        'Accept'			: 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding'	: 'gzip,deflate,sdch',
        'Accept-Language'	: 'zh-CN,zh;q=0.8'
    }
    result = []

    url = f'{host}/api/v1/memo?'.format(host=host)
    params = {
        'limit': limit,
        'offset': offset,
        'creatorUsername': create_user,
    }
    # PRIVATE memos could only be retrieved by cookie
    cookies = {
        'memos.access-token': memos_token,
    }
    rsp = requests.get(url, headers=headers, params=params, cookies=cookies, timeout=30)
    if rsp.status_code != 200:
        logging.error("memos error. %d, %s", rsp.status_code, rsp.json())
        return result

    data = rsp.json()
    if not data:
        return result

    for item in data:
        result.append(MemosItem(item))

    return result


# pylint: disable=line-too-long
def _sync(client: Client, database_id: str, memos_token: str) -> None:
    limit = 10
    count = 0

    host = CONFIG.get('memos.opts', 'MemosHost')
    create_user = CONFIG.get('memos.opts', 'MemosUserName')
    if not create_user or not host:
        logging.error("`MemosHost` `MemosUserName` not setted in configuration file.")
        return

    while True:
        time.sleep(0.3) # avoid rate limit for notion API

        memos_list = _memos_list(count*limit, limit, host, create_user, memos_token)
        if not memos_list:
            break

        logging.info("%d memos to sync", len(memos_list))

        for memo in memos_list:
            if query_page(client, database_id, memo.id):
                continue

            # insert to db
            insert_page(client, database_id, memo)

        count += 1
        if len(memos_list) != limit:
            break

def sync_memos(notion_token, database_id, memos_token):
    """sync memos to notion"""
    client = Client(
        auth=notion_token,
        log_level=logging.ERROR)

    _sync(client, database_id, memos_token)
