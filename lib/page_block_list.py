"""Orgnize the page blocks in a Notion page"""

def safe_cast(val, to_type, default=None):
    """
    尝试将输入值 `val` 转换为指定类型 `to_type`，如果转换失败则返回默认值 `default`。
    """
    try:
        return to_type(val)
    except (ValueError, TypeError):
        return default

class PageBlockList(object):
    """Implements the PageBlockList class."""

    def __init__(self, store, book_id, blocks):
        """Constructor for the PageBlockList class.
        list item format:
        {
            'type': 'paragraph / heading / list / image ....',
            'id': '$block_id',
        }
        """
        self.book_id = book_id
        self.blocks = []
        for block in blocks:
            bookmark_id = None
            _result = store.query_by_block(book_id, block['id'])
            if _result:
                bookmark_id = _result[0]['bookmark_id']
            self.blocks.append({
                'type': block['type'],
                'id': block['id'],
                'bookmark_id': bookmark_id,
            })

    def found_chapter_position(self, chapter_uid: int) -> str | None:
        """Find the position of a chapter in the list.
        return true if found, false if not found
        """
        chapter, block_id, block_idx = -1, None, -1
        for idx, block in enumerate(self.blocks):
            if block['bookmark_id'] is not None and block['type'].startswith('heading_'):
                _cuid = safe_cast(block['bookmark_id'], int, 0)
                if _cuid < chapter_uid and _cuid > chapter: # find the biggest one in [0, chapter_uid]
                    chapter = _cuid
                    block_id = block['id']
                    block_idx = idx

        # push to the first block if not found
        if not block_id:
            return self.blocks[0]['id'] if len(self.blocks) > 0 else None
        
        # iterate to the end of chapter
        while block_idx < len(self.blocks) - 1:
            block = self.blocks[block_idx + 1]
            if block['type'].startswith('heading_'):
                return block_id
            block_idx += 1
            block_id = block['id']
        return block_id