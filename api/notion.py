"""
封装notion相关操作
"""

from datetime import datetime

from notion_client import AsyncClient


# class NotionAPI:
#     """暂未启用"""

#     def __init__(self, token):
#         self.token = token

#     def dumy(self):
#         """pass"""
#         pass


class BlockHelper:
    """生成notion格式的工具函数"""

    headings = {
        1: "heading_1",
        2: "heading_2",
        3: "heading_3",
    }

    table_contents = {
        "type": "table_of_contents",
        "table_of_contents": {"color": "default"},
    }

    color_styles = {
        1: "red",
        2: "purple",
        3: "blue",
        4: "green",
        5: "yellow",
    }

    def __init__(self):
        pass

    @classmethod
    def table_of_contents(cls):
        """获取目录"""
        return cls.table_contents

    @classmethod
    def heading(cls, level, content):
        """取heading格式""" ""
        heading_type = cls.headings.get(level, "heading_3")
        return {
            "type": heading_type,
            heading_type: {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": content,
                        },
                    }
                ],
                "color": "default",
                "is_toggleable": False,
            },
        }

    @classmethod
    def table(
        cls,
        table_width: int,
        cells: list,
        has_column_header: bool = False,
        has_row_header: bool = False,
    ):
        """table""" ""
        # heading_type = cls.headings.get(level, "heading_3")
        table = {
            "type": "table",
            "table": {
                "table_width": table_width,
                "has_column_header": has_column_header,
                "has_row_header": has_row_header,
            },
        }
        table["table"]["children"] = [cls.table_row(cells)]

        return table

    @classmethod
    def table_row(cls, content_list: list):
        """table row, see https://developers.notion.com/reference/block#table-rows .
        When creating a table block via the Append block children endpoint, the table
        must have at least one table_row whose cells array has the same length as the table_width.
        """
        table_row = {
            "type": "table_row",
            "table_row": {
                "cells": [],
            },
        }
        for content in content_list:
            item = [
                {
                    "type": "text",
                    "text": {
                        "content": str(content),
                    },
                }
            ]
            table_row["table_row"]["cells"].append(item)
        return table_row

    @classmethod
    def quote(cls, content):
        """取引用格式"""
        return {
            "type": "quote",
            "quote": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": content},
                    }
                ],
                "color": "default",
            },
        }

    @classmethod
    def divider(cls):
        """ "divier"""
        return {"type": "divider", "divider": {}}

    @classmethod
    def emoj_style(cls, style, review_id):
        """根据不同的划线样式设置不同的emoji 直线type=0 背景颜色是1 波浪线是2"""
        emoji = "🌟"
        if style == 0:
            emoji = "💡"
        elif style == 1:
            emoji = "⭐"
        # 如果reviewId不是空说明是笔记
        if review_id is not None:
            emoji = "✍️"
        return emoji

    @classmethod
    def callout(cls, content, style, color, review_id, enable_emoj=False):
        """取callout格式"""
        emoji = ""
        if enable_emoj:
            emoji = cls.emoj_style(style, review_id)
        return {
            "type": "callout",
            "callout": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": content,
                        },
                    }
                ],
                "icon": {"emoji": emoji},
                "color": cls.color_styles.get(color, "default"),
            },
        }

    @classmethod
    def paragraph(cls, content, style, color, review_id, enable_emoj=False):
        """取text格式"""
        emoji = ""
        if enable_emoj:
            emoji = cls.emoj_style(style, review_id)
        return {
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": emoji + content,
                        },
                    }
                ],
                "color": cls.color_styles.get(color, "default"),
            },
        }

    @classmethod
    def bullet_list(cls, content, style, color, review_id, enable_emoj=False):
        """取callout格式"""
        emoji = ""
        if enable_emoj:
            emoji = cls.emoj_style(style, review_id)
        return {
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": emoji + content,
                        },
                    }
                ],
                "color": cls.color_styles.get(color, "default"),
            },
        }

    @classmethod
    def rich_text(cls, content):
        "generate rich text"
        return {"rich_text": [{"type": "text", "text": {"content": content}}]}

    @classmethod
    def title(cls, content):
        "generate title block"
        return {"title": [{"type": "text", "text": {"content": content}}]}

    @classmethod
    def url(cls, remoteurl):
        "generate url block"
        return {"url": remoteurl}

    @classmethod
    def number(cls, num):
        "generate number block"
        return {"number": num}

    @classmethod
    def files(cls, name, url):
        "generate external file & media block"
        return {"files": [{"type": "external", "name": name, "external": {"url": url}}]}

    @classmethod
    def select(cls, option):
        "generate select block"
        return {"select": {"name": option}}

    @classmethod
    def multi_select(cls, selected_options: list[any]):
        "generate multi-select block"
        return {"multi_select": [{"name": option} for option in selected_options]}

    @classmethod
    def date(cls, d):
        "generate date block"
        return {
            "date": {
                "start": datetime.fromtimestamp(d).strftime("%Y-%m-%d %H:%M:%S"),
                "time_zone": "Asia/Shanghai",
            }
        }

    @classmethod
    def icon(cls, img):
        """generate icon block"""
        return {"type": "external", "external": {"url": img}}


async def get_datasource_id(client: AsyncClient, database_id: str) -> str:
    """获取data source"""
    db = await client.databases.retrieve(database_id=database_id)
    data_sources = db.get("data_sources", [])
    if not data_sources:
        return ""
    return data_sources[0]["id"]
