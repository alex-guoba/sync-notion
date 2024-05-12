"""sync reading log to calendar database"""

from datetime import datetime
from notion_client import Client
from api.notion import BlockHelper


def query_filter(book_id: str, date: str):
    """query filter for calendar database"""
    return {
        "and": [
            {
                "property": "BookId",
                "rich_text": {
                    "equals": book_id,
                },
            },
            {
                "property": "ReadDate",
                "date": {
                    "equals": datetime.fromtimestamp(date).strftime("%Y-%m-%d"),
                },
            },
        ]
    }


def sync_to_calener(client: Client, calendar_db: str, read_detail: object):
    """sync reading log to calendar database"""
    if not client or not read_detail:
        return
    rdetail = read_detail.get("readDetail")
    book_info = read_detail.get("bookInfo")

    if not rdetail or not book_info:
        return

    # from latest to oldest
    records = sorted(
        rdetail.get("data", []), key=lambda x: x.get("readDate") or 0, reverse=True
    )

    # No batch-updating API exist😢
    book_id = book_info.get("bookId")
    for record in records:
        date = record.get("readDate")
        read_time = record.get("readTime", 0)

        response = client.databases.query(
            database_id=calendar_db,
            filter=query_filter(book_id, date),
        )
        if len(response["results"]) > 0:
            result = response["results"][0]
            _old = result.get("properties", {}).get("ReadTime", {}).get("number", 0)
            if _old < read_time:
                properties = {"ReadTime": BlockHelper.number(read_time)}
                client.pages.update(page_id=result["id"], properties=properties)

            # 每日更新，仅更新最近一次即可
            break

        properties = {
            "Name": BlockHelper.title(book_info.get("title", "")),
            "BookId": BlockHelper.rich_text(book_id),            
            "ReadDate": {"date": {"start": datetime.fromtimestamp(date).strftime("%Y-%m-%d")}}, # Discard timezone
            "ReadTime": BlockHelper.number(read_time),
        }
        client.pages.create(
            parent={"database_id": calendar_db, "type": "database_id"},
            properties=properties,
        )

