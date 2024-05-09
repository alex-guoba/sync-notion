"""
封装存储相关操作
"""

import sqlite3
import datetime


class DBWeReadRecord(object):
    """存储微信读书同步记录"""

    TabName = "weread_sync_record"
    SqlCreate = f"""create table if not exists {TabName}
    (book_id VARCHAR(255), bookmark_id varchar(255), block_id VARCHAR(255),
    op_time TIMESTAMP, resv VARCHAR(255),
    PRIMARY KEY (book_id, bookmark_id, block_id))"""

    def __init__(self, db_name):
        """
        :param db_name: 数据库名称
        """
        self.connection = sqlite3.connect(
            db_name, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        self.connection.row_factory = sqlite3.Row  # use dictionary to return row
        self.create_table()

    def __del__(self):
        """
        析构函数
        :return:
        """
        print("closing db connection")
        self.connection.close()

    def create_table(self):
        """
        创建表
        :return:
        """
        cursor = self.connection.cursor()
        cursor.execute(self.SqlCreate)

    def insert(self, book_id, bookmark_id, block_id):
        """
        插入数据
        :param book_id: 书籍ID
        :param bookmark_id: 书签ID/章节ID
        :param block_id: 章节ID
        :param op_time: 操作时间
        :return: 插入后的主键值
        """
        now = datetime.datetime.now()

        sql = f"insert or ignore into {self.TabName}(book_id, bookmark_id, block_id, op_time)\
              values (?, ?, ?, ?)"
        cursor = self.connection.cursor()
        cursor.execute(sql, (book_id, bookmark_id, block_id, now))
        self.connection.commit()
        return cursor.lastrowid

    def query(self, book_id, bookmark_id):
        """
        查询是否已经写如果
        :return: 查询后的主键值
        """
        sql = f"select book_id, bookmark_id, block_id, op_time \
            from {self.TabName} where book_id=? and bookmark_id=?"
        cursor = self.connection.cursor()
        cursor.execute(sql, (book_id, bookmark_id))
        return cursor.fetchall()

    def query_by_block(self, book_id, block_id):
        """
        查询是否已经写如果
        :return: 查询后的主键值
        """
        sql = f"select book_id, bookmark_id, block_id, op_time \
            from {self.TabName} where book_id=? and block_id=?"
        cursor = self.connection.cursor()
        cursor.execute(sql, (book_id, block_id))
        return cursor.fetchall()

    def delete_book(self, book_id):
        """
        删除书籍记录
        :param book_id: 书籍ID
        :return:
        """
        sql = f"delete from {self.TabName} where book_id=?"
        cursor = self.connection.cursor()
        cursor.execute(sql, (book_id,))
        self.connection.commit()

    def delete_bookmark(self, book_id, bookmark_id):
        """
        删除book_id, bookmark_id记录
        :param book_id: 书籍ID
        :param bookmark_id: 书签ID/章节ID
        :return:
        """
        sql = f"delete from {self.TabName} where book_id=? and bookmark_id=?"
        cursor = self.connection.cursor()
        cursor.execute(sql, (book_id, bookmark_id))
        self.connection.commit()