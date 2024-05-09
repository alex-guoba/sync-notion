""" sync wereading history to private notion database & pages 
author: alex-guoba
"""

import logging
import re
import time
from datetime import datetime
import hashlib
from collections import defaultdict

from lib.db_weread_record import DBWeReadRecord
from lib.page_block_list import PageBlockList
from treelib import Tree
from notion_client import Client

from api import weread
from api.notion import BlockHelper
from config import CONFIG

ROOT_NODE_ID = "#root"
BOOK_MARK_KEY = "#bookmarks"
NOTION_MAX_LEVEL = 3


class BlockItem:
    """Just for enveloping the child block"""

    def __init__(self, after=None, bookmark=None, block=None, child=None) -> None:
        """
        初始化方法，用于创建一个新的Block对象。
        Args:
            after (str, optional): 用于追加到该block之后时使用。
            bookmark (str, optional): 对应的bookmarkid，需要与bid一起写入db时使用
            block (str, optional): Block的内容
            child (list, optional): 子Block对象的列表，默认为None。
        Returns:
            None

        """
        self.after = after
        self.bookmark = bookmark
        self.block = block
        self.child = child
        self.bid = None

    def set_bid(self, bid):
        """set block id after appending to notion success"""
        self.bid = bid


def query_database(client, database_id, book_id):
    """查询原page信息，并返回pageinfo和pid"""
    time.sleep(0.3)
    response = client.databases.query(
        database_id=database_id,
        filter={"property": "BookId", "rich_text": {"equals": book_id}},
    )
    pageinfo = None
    pid = None
    for result in response["results"]:
        pageinfo = result
        pid = result["id"]
        break

    return pageinfo, pid


def inherit_properties(page):
    """
    从传入的 page 字典中提取 properties 字段，并返回一个新的字典，其中不包含类型为 'formula' 的属性。
    Args:
        page (dict): 包含页面信息的字典，其中包含名为 'properties' 的字段，该字段是一个字典，包含页面属性的键值对。
    Returns:
        dict: 一个新的字典，包含从原始 'properties' 字段中提取的、类型不为 'formula' 的页面属性键值对。
    """
    properties = {}
    if page:
        for k, v in page["properties"].items():
            if v.get("type") == "formula":
                continue
            properties[k] = v
    return properties


def create_or_update_page(
    client,
    database_id,
    pageinfo,
    pid,
    book_name="",
    book_id="",
    cover="",
    sort=0,
    author="",
    isbn="",
    rating=0,
    category="",
    note_count=0,
    read_info=None,
):
    """插入到notion"""
    parent = {"database_id": database_id, "type": "database_id"}

    properties = inherit_properties(pageinfo)

    properties.update(
        {
            "BookName": BlockHelper.title(book_name),
            "BookId": BlockHelper.rich_text(book_id),
            "ISBN": BlockHelper.rich_text(isbn),
            "URL": BlockHelper.url(
                f"https://weread.qq.com/web/reader/{calculate_book_str_id(book_id)}"
            ),
            "Author": BlockHelper.rich_text(author),
            "Sort": BlockHelper.number(sort),
            "Rating": BlockHelper.number(rating),
            "Cover": BlockHelper.files("Cover", cover),
            "NoteCount": BlockHelper.number(note_count),
            "Category": BlockHelper.rich_text(category),
        }
    )

    # print(page)

    if read_info:
        marked_status = read_info.get("markedStatus", 0)
        properties["Status"] = BlockHelper.select(
            "读完" if marked_status == 4 else "在读"
        )

        format_time = weread.str_reading_time(read_info.get("readingTime", 0))
        properties["ReadingTime"] = BlockHelper.rich_text(format_time)

        # 最近阅读
        detail = read_info.get("readDetail", {})
        if detail.get("lastReadingDate"):
            properties["lastReadingDate"] = BlockHelper.date(
                detail.get("lastReadingDate")
            )

        # 完成时间
        if read_info.get("finishedDate"):
            properties["FinishAt"] = BlockHelper.date(detail.get("finishedDate"))

    if pid is None:
        response = client.pages.create(
            parent=parent, icon=BlockHelper.icon(cover), properties=properties
        )
        return response["id"], True

    response = client.pages.update(
        page_id=pid, icon=BlockHelper.icon(cover), properties=properties
    )
    return pid, False


def list_page_blocks(client, pid):
    """query page blocks (children not included)"""
    response = client.blocks.children.list(block_id=pid)
    children = response["results"] if len(response.get("results")) > 0 else []
    while response.get("has_more"):
        response = client.blocks.children.list(
            block_id=pid, start_cursor=response["next_cursor"]
        )
        children += response["results"] if len(response.get("results")) > 0 else []
    # remove other fileds in blocks
    tailor = list(map(lambda x: {"id": x.get("id"), "type": x.get("type")}, children))
    return tailor


def append_children(client, pid, after, children):
    """append child block to page. Notion API limit 100 blocker per appending"""
    results = []
    print("appending ", len(children), " blocks after ", after)
    for i in range(0, len(children) // 100 + 1):
        time.sleep(0.3)
        subchild = children[i * 100 : (i + 1) * 100]
        response = None
        if after:
            response = client.blocks.children.append(
                block_id=pid, children=subchild, after=after
            )
        else:
            response = client.blocks.children.append(block_id=pid, children=subchild)
        # Notion will return all the blocks start from the appending block. So we need to filter the result.
        results.extend(response.get("results")[: len(subchild)])
    return results if len(results) == len(children) else []


def append_blocks(
    client, pid: str, appending: list[BlockItem], store: DBWeReadRecord, book_id: str
):
    """append child block to page by group"""
    batch = []
    block_id = None
    result = []
    for item in appending:
        if not batch:
            block_id = item.after
            batch.append(item.block)
            continue
        if block_id == item.after:
            batch.append(item.block)
            continue
        _result = append_children(client, pid, block_id, batch)
        result.extend(_result)

        block_id = item.after
        batch = [item.block]

    if len(batch) > 0:
        _result = append_children(client, pid, block_id, batch)
        result.extend(_result)

    for idx, item in enumerate(appending):
        bid = result[idx].get("id")
        item.set_bid(bid)
        if item.child:
            append_children(client, bid, None, item.child)

    # write to db
    for block in appending:
        if block.bookmark and block.bid:
            store.insert(book_id, block.bookmark, block.bid)


def get_db_latest_sort(client, database_id):
    """获取database中的最新更新时间"""
    db_filter = {"property": "Sort", "number": {"is_not_empty": True}}
    sorts = [
        {
            "property": "Sort",
            "direction": "descending",
        }
    ]
    response = client.databases.query(
        database_id=database_id, filter=db_filter, sorts=sorts, page_size=1
    )
    if len(response.get("results")) == 1:
        return response.get("results")[0].get("properties").get("Sort").get("number")
    return 0


def gen_chapter_tree(chapter_list):
    """生成章节树"""
    tree = Tree()
    root = tree.create_node(identifier=ROOT_NODE_ID)  # root node
    p = {}
    for chapter in chapter_list:
        level = chapter.get("level", 1)
        if level <= 0:
            level = 1
        elif level > NOTION_MAX_LEVEL:  # 目前仅支持header1-3
            level = NOTION_MAX_LEVEL

        parent = p.get(level - 1, root)  # 取最近一次更新节点
        chapter_uid = chapter.get("chapterUid")
        p[level] = tree.create_node(
            tag=chapter_uid, identifier=chapter_uid, parent=parent, data=chapter
        )
    return tree


def mount_bookmarks(chapter_tree, bookmark_list):
    """挂载划线、评论到对应的树节点"""
    d = defaultdict(list)
    for data in bookmark_list:
        uid = data.get("chapterUid", 1)
        d[uid].append(data)

    for key, value in d.items():
        node = chapter_tree.get_node(key)
        if not node:
            logging.error("chapter info not found [%s].", key)
            continue

        # mount bookmark list to chapter list
        node.data[BOOK_MARK_KEY] = value


def remove_empty_chapter(chapter_tree):
    """从底向上，删除章节树中的空节点"""
    max_depth = chapter_tree.depth()
    for d in range(max_depth, 0, -1):
        nodes = list(chapter_tree.filter_nodes(lambda x: chapter_tree.depth(x) == d))

        for n in nodes:
            if n.data.get(BOOK_MARK_KEY) is None and n.is_leaf():
                chapter_tree.remove_node(n.identifier)


def content_block(text: str, style: str, color: str, review_id: str) -> dict:
    """
    根据配置选择内容block形态
    """
    enable_emoj = CONFIG.getboolean("weread.format", "EnableEmoj")
    match CONFIG.get("weread.format", "ContentType"):
        case "callout":
            return BlockHelper.callout(
                text, style, color, review_id, enable_emoj=enable_emoj
            )

        case "list":
            return BlockHelper.bullet_list(
                text, style, color, review_id, enable_emoj=enable_emoj
            )

        case _:
            return BlockHelper.paragraph(
                text, style, color, review_id, enable_emoj=enable_emoj
            )


def made_page_blocks(
    store, blocks, bookID, chapters_list, bookmark_list
) -> list[BlockItem]:
    """generate page blocks to appending"""
    appending: list[BlockItem] = []

    page_block_list = PageBlockList(store, bookID, blocks)

    # 添加目录
    if not blocks:
        # child format: [after_blockid, bookmarkd_id, block_data]
        appending.append(BlockItem(block=BlockHelper.table_of_contents()))
        appending.append(BlockItem(block=BlockHelper.divider()))

    if len(chapters_list) > 0:
        chapter_tree = gen_chapter_tree(chapters_list)
        mount_bookmarks(chapter_tree, bookmark_list)
        remove_empty_chapter(chapter_tree)

        for n in chapter_tree.expand_tree(mode=Tree.DEPTH):
            if chapter_tree[n].is_root():
                continue

            data = chapter_tree[n].data
            chapter_uid = data.get("chapterUid")

            block_id = None
            _records = store.query(bookID, chapter_uid)
            if len(_records) > 0:
                block_id = _records[0]["block_id"]
            else:
                # find a suitable position to insert
                block_id = page_block_list.found_chapter_position(chapter_uid)
                appending.append(
                    BlockItem(
                        after=block_id,
                        bookmark=chapter_uid,
                        block=BlockHelper.heading(data.get("level"), data.get("title")),
                    )
                )

            for i in data.get(BOOK_MARK_KEY, []):
                bookmark_id = i.get("bookmarkId") or i.get("reviewId")
                _records = store.query(bookID, bookmark_id)
                if len(_records) > 0:
                    continue
                appending.append(
                    BlockItem(
                        after=block_id,
                        bookmark=bookmark_id,
                        block=content_block(
                            i.get("markText"),
                            i.get("style"),
                            i.get("colorStyle"),
                            i.get("reviewId"),
                        ),
                        child=(
                            [BlockHelper.quote(i.get("abstract"))]
                            if i.get("abstract")
                            else None
                        ),
                    )
                )
    else:
        # no chapter info
        for data in bookmark_list:
            bookmark_id = i.get("bookmarkId") or i.get("reviewId")
            _records = store.query(bookID, bookmark_id)
            if len(_records) > 0:
                continue
            appending.append(
                BlockItem(
                    bookmark=bookmark_id,
                    block=content_block(
                        i.get("markText"),
                        i.get("style"),
                        i.get("colorStyle"),
                        i.get("reviewId"),
                    ),
                    child=(
                        [BlockHelper.quote(i.get("abstract"))]
                        if i.get("abstract")
                        else None
                    ),
                )
            )

    return appending


def made_comment_blocks(
    store: DBWeReadRecord, book_id: str, summary: list
) -> list[BlockItem]:
    """generate extra stat blocks to appending"""
    appending: list[BlockItem] = []

    # 追加推荐评语
    if not summary:
        return appending

    bookmark_id = "_comment_"
    block_id = None
    _records = store.query(book_id, bookmark_id)
    if len(_records) == 0:
        appending.extend(
            (
                BlockItem(block=BlockHelper.divider()),
                BlockItem(block=BlockHelper.heading(1, "点评"), bookmark=bookmark_id),
            )
        )
    else:
        block_id = _records[0]["block_id"]

    for i in summary:
        # print("summary:", i)
        bookmark_id = i.get("review").get("reviewId")
        _records = store.query(book_id, bookmark_id)
        if len(_records) > 0:
            continue
        appending.append(
            BlockItem(
                after=block_id,
                bookmark=bookmark_id,
                block=content_block(
                    i.get("review").get("content"),
                    i.get("style"),
                    i.get("colorStyle"),
                    i.get("review").get("reviewId"),
                ),
            )
        )

    return appending


def made_readinfo_blocks(
    client: Client,
    store: DBWeReadRecord,
    book_id: str,
    rinfo: object,
    bookmark_count: int,
) -> list[BlockItem]:
    """generate extra stat blocks to appending"""
    appending: list[BlockItem] = []
    rdetail = rinfo.get("readDetail")

    if not rdetail:
        return appending
    if not CONFIG.getboolean("weread.format", "EnableReadingDetail"):
        return appending

    bookmark_id = "_stat_"
    block_id = None
    _records = store.query(book_id, bookmark_id)
    if len(_records) == 0:
        appending.extend(
            (
                BlockItem(block=BlockHelper.divider()),
                BlockItem(
                    block=BlockHelper.heading(1, "阅读明细"), bookmark=bookmark_id
                ),
            )
        )
    else:
        block_id = _records[0]["block_id"]

    # 总计
    bookmark_id = "_stat.total_"
    _records = store.query(book_id, bookmark_id)
    if len(_records):
        store.delete_bookmark(book_id, bookmark_id)
        client.blocks.delete(block_id=_records[0]["block_id"])

    longest_reading_time = weread.str_reading_time(rdetail.get("longestReadingTime", 0))
    longest_reading_date = datetime.fromtimestamp(
        rdetail.get("longestReadingDate")
    ).strftime("%Y/%m/%d")
    appending.append(
        BlockItem(
            after=block_id,
            bookmark=bookmark_id,
            block=BlockHelper.table(2, ["维度", "指标"], True),
            child=[
                BlockHelper.table_row(
                    ["累积阅读天数", str(rdetail.get("totalReadDay", 0)) + "天"]
                ),
                BlockHelper.table_row(
                    ["最长连续阅读天数", str(rdetail.get("continueReadDays", 0)) + "天"]
                ),
                BlockHelper.table_row(
                    ["单日阅读最久", f"{longest_reading_time} ({longest_reading_date})"]
                ),
                BlockHelper.table_row(["阅读笔记条数", str(bookmark_count) + "条"]),
            ],
        )
    )

    # 明细
    bookmark_id = "_stat.detail_"
    _records = store.query(book_id, bookmark_id)
    if len(_records):
        store.delete_bookmark(book_id, bookmark_id)
        client.blocks.delete(block_id=_records[0]["block_id"])
    item = BlockItem(
        after=block_id,
        bookmark=bookmark_id,
        block=BlockHelper.table(2, ["日期", "阅读时长"], True),
        child=[],
    )
    for daily in rdetail.get("data"):
        item.child.append(
            BlockHelper.table_row(
                [
                    datetime.fromtimestamp(daily.get("readDate")).strftime("%Y/%m/%d"),
                    weread.str_reading_time(daily.get("readTime", 0)),
                ]
            )
        )
    appending.append(item)

    return appending


def transform_id(book_id):
    """transform book id to hex string"""
    id_length = len(book_id)
    if re.match(r"^\d*$", book_id):
        ary = []
        for i in range(0, id_length, 9):
            ary.append(format(int(book_id[i : min(i + 9, id_length)]), "x"))
        return "3", ary

    result = ""
    for i in range(id_length):
        result += format(ord(book_id[i]), "x")
    return "4", [result]


def calculate_book_str_id(book_id):
    """calculate book id string"""
    md5 = hashlib.md5()
    md5.update(book_id.encode("utf-8"))
    digest = md5.hexdigest()
    result = digest[0:3]
    code, transformed_ids = transform_id(book_id)
    result += code + "2" + digest[-2:]

    for i in range(len(transformed_ids)):
        hex_length_str = format(len(transformed_ids[i]), "x")
        if len(hex_length_str) == 1:
            hex_length_str = "0" + hex_length_str

        result += hex_length_str + transformed_ids[i]

        if i < len(transformed_ids) - 1:
            result += "g"

    if len(result) < 20:
        result += digest[0 : 20 - len(result)]

    md5 = hashlib.md5()
    md5.update(result.encode("utf-8"))
    result += md5.hexdigest()[0:3]
    return result


def sync_read(weread_cookie, notion_token, database_id):
    """sync weread reading notes to notion"""
    client = Client(auth=notion_token, log_level=logging.ERROR)
    latest_sort = get_db_latest_sort(client, database_id)

    wreader = weread.WeReadAPI(weread_cookie)
    store = DBWeReadRecord("./var/sync_read.db")

    books = wreader.get_notebooklist()
    for _book in books:
        sort = _book["sort"]
        if sort <= latest_sort:  # 笔记无更新，跳过
            continue

        book_dict = _book.get("book")
        book_id = book_dict.get("bookId")

        logging.info("Start to synch book %s", book_id)

        chapters_list = wreader.get_chapter_list(book_id)
        bookmark_list = wreader.get_bookmark_list(book_id)
        summary, reviews = wreader.get_review_list(book_id)

        # converge bookmark and chapter review
        bookmark_list.extend(reviews)
        bookmark_list = sorted(
            bookmark_list,
            key=lambda x: (
                x.get("chapterUid", 1),
                (
                    0
                    if (x.get("range", "") == "" or x.get("range").split("-")[0] == "")
                    else int(x.get("range").split("-")[0])
                ),
            ),
        )

        isbn, rating, category = wreader.get_bookinfo(book_id)
        read_info = wreader.get_read_info(book_id)

        # delete before insert again
        pageinfo, pid = query_database(client, database_id, book_id)
        pid, created = create_or_update_page(
            client,
            database_id,
            pageinfo,
            pid,
            book_name=book_dict.get("title"),
            book_id=book_id,
            cover=book_dict.get("cover"),
            sort=sort,
            author=book_dict.get("author"),
            isbn=isbn,
            rating=rating,
            category=category,
            note_count=_book.get("noteCount"),
            read_info=read_info,
        )

        blocks = []
        if not created:
            blocks = list_page_blocks(client, pid)
        else:
            store.delete_book(book_id)

        appending = made_page_blocks(
            store,
            blocks,
            book_id,
            chapters_list,
            bookmark_list,
        )
        append_blocks(client, pid, appending, store, book_id)

        appending = made_comment_blocks(
            store,
            book_id,
            summary,
        )
        append_blocks(client, pid, appending, store, book_id)

        appending = made_readinfo_blocks(
            client, store, book_id, read_info, len(bookmark_list)
        )
        append_blocks(client, pid, appending, store, book_id)
