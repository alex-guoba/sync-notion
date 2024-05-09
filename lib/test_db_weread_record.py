"""unit test for PageBlockList"""
import unittest
# from datetime import datetime, timedelta

from lib.db_weread_record import DBWeReadRecord
from lib.page_block_list import PageBlockList
# from lib.db_weread_record import DBWeReadRecord # 替换your_module_name为实际的模块名

class TestPageBlockList(unittest.TestCase):
    """test PageBlockList"""

    def setUp(self):
        # 创建一个临时的数据库用于测试
        self.db_name = ":memory:"
        # self.db_name = "./var/tutorial.db"
        self.store = DBWeReadRecord(self.db_name)
        self.store.create_table()

    def tearDown(self):
        # 测试结束后关闭数据库连接
        del self.store

    def test_empty(self):
        """test append tail block"""
        book_id = "book_1"
        bookmark_id = 1
        block_id = "block_id_1"
        self.store.insert(book_id, bookmark_id, block_id)

        blocks = []
        page_block_list = PageBlockList(self.store, book_id, blocks)
        
        appended_block = page_block_list.found_chapter_position(bookmark_id)
        self.assertEqual(appended_block, None)
        
    def test_append_tail(self):
        """test append tail block"""
        book_id = "book_1"
        bookmark_id = 1
        block_id = "block_id_1"
        self.store.insert(book_id, bookmark_id, block_id)

        blocks = [
            {
                'id': block_id,
                'type': 'heading_1',
            }
        ]
        page_block_list = PageBlockList(self.store, book_id, blocks)
        
        appended_block = page_block_list.found_chapter_position(bookmark_id + 1)
        self.assertEqual(appended_block, block_id)


    def test_append_header(self):
        """test append tail block"""
        book_id = "book_2"
        bookmark_id = 2
        block_id = "block_id_2"
        self.store.insert(book_id, bookmark_id, block_id)

        blocks = [
            {
                'id': 'toc_id',
                'type': 'table_of_contents'
            },
            {
                'id': block_id,
                'type': 'heading_3',
            }
        ]
        page_block_list = PageBlockList(self.store, book_id, blocks)

        appended_block = page_block_list.found_chapter_position(bookmark_id - 1)
        self.assertEqual(appended_block, 'toc_id')

    def test_insert_mid(self):
        """test append tail block"""
        book_id = "book_1"

        self.store.insert(book_id, 3, 'block_3')
        self.store.insert(book_id, 5, 'block_5')
        self.store.insert(book_id, 7, 'block_7')

        blocks = [
            {
                'id': 'toc_id',
                'type': 'table_of_contents'
            },
            {
                'id': 'block_3',
                'type': 'heading_3',
            },
            {
                'id': 'block_5',
                'type': 'heading_5',
            },
            {
                'id': 'block_7',
                'type': 'heading_7',
            },
        ]
        page_block_list = PageBlockList(self.store, book_id, blocks)

        appended_block = page_block_list.found_chapter_position(4)
        self.assertEqual(appended_block, 'block_3')
