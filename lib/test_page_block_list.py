"""unit test for DBWeReadRecord"""
import unittest
from datetime import datetime, timedelta

from lib.db_weread_record import DBWeReadRecord
# from lib.db_weread_record import DBWeReadRecord # 替换your_module_name为实际的模块名

class TestDBReadRecord(unittest.TestCase):
    """unit test for DBWeReadRecord"""

    def setUp(self):
        # 创建一个临时的数据库用于测试
        self.db_name = ":memory:"
        # self.db_name = "./var/tutorial.db"
        self.db_reader = DBWeReadRecord(self.db_name)

    def tearDown(self):
        # 测试结束后关闭数据库连接
        del self.db_reader

    def test_insert_and_query(self):
        """test insert and query"""
        # 测试插入和查询数据
        book_id = '12345'
        bookmark_id = 'chapter1'
        block_id = 'b55c9c91-384d-452b-81db-d1ef79372b75'

        expected_op_time = datetime.now()
        
        # 插入数据
        inserted_id = self.db_reader.insert(book_id, bookmark_id, block_id)
        self.assertTrue(inserted_id >= 0)

        # 查询数据
        results = self.db_reader.query(book_id, bookmark_id)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result['book_id'], book_id)
        self.assertEqual(result['bookmark_id'], bookmark_id)
        self.assertEqual(result['block_id'], block_id)
        # 检查op_time在合理范围内
        self.assertLessEqual(result['op_time'], expected_op_time + timedelta(seconds=10))
        self.assertGreaterEqual(result['op_time'], expected_op_time - timedelta(seconds=10))

    def test_insert_duplicate_and_query(self):
        """test insert duplicate and query"""
        # 测试插入重复数据并查询
        book_id = '987652'
        bookmark_id = 'chapter3'
        block_id = 'b55c9c91-384d-452b-81db-d1ef79379999'

        # 第一次插入
        inserted_id_1 = self.db_reader.insert(book_id, bookmark_id, block_id)
        self.assertTrue(inserted_id_1 >= 0)

        # 尝试第二次插入相同的数据，应不插入新数据
        inserted_id_2 = self.db_reader.insert(book_id, bookmark_id, block_id)
        self.assertEqual(inserted_id_1, inserted_id_2)

        # 查询数据，应该只有一条记录
        results = self.db_reader.query(book_id, bookmark_id)
        self.assertEqual(len(results), 1)

if __name__ == '__main__':
    unittest.main()
