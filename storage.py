#!/usr/bin/env python3
"""
Storage - 對話歷史存儲

支援 SQLite + FTS5 全文搜尋
"""

import sqlite3
import json
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class Message:
    """訊息"""
    id: Optional[int] = None
    role: str = ""  # user, assistant, system
    content: str = ""
    timestamp: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class Conversation:
    """對話"""
    id: Optional[int] = None
    title: str = ""
    created_at: str = ""
    updated_at: str = ""
    messages: List[Message] = field(default_factory=list)


class Storage:
    """存儲管理器"""
    
    def __init__(self, db_path: str = "data/conversations.db"):
        """
        初始化
        
        Args:
            db_path: 資料庫路徑
        """
        self.db_path = db_path
        self._ensure_dir()
        self._init_db()
    
    def _ensure_dir(self):
        """確保目錄存在"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _init_db(self):
        """初始化資料庫"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 對話表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # 訊息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        
        # FTS5 全文搜尋
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                content,
                content='messages',
                content_rowid='id'
            )
        """)
        
        # 觸發器：自動同步 FTS
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
                INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
            END
        """)
        
        conn.commit()
        conn.close()
    
    def create_conversation(self, title: str = "新對話") -> int:
        """
        建立新對話
        
        Args:
            title: 對話標題
            
        Returns:
            對話 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute(
            "INSERT INTO conversations (title, created_at, updated_at) VALUES (?, ?, ?)",
            (title, now, now)
        )
        
        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return conversation_id
    
    def add_message(self, conversation_id: int, role: str, content: str, 
                   metadata: Dict = None) -> int:
        """
        添加訊息
        
        Args:
            conversation_id: 對話 ID
            role: 角色 (user/assistant/system)
            content: 內容
            metadata: 額外數據
            
        Returns:
            訊息 ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        metadata_json = json.dumps(metadata) if metadata else "{}"
        
        cursor.execute(
            """INSERT INTO messages (conversation_id, role, content, timestamp, metadata) 
               VALUES (?, ?, ?, ?, ?)""",
            (conversation_id, role, content, now, metadata_json)
        )
        
        message_id = cursor.lastrowid
        
        # 更新對話時間
        cursor.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id)
        )
        
        conn.commit()
        conn.close()
        
        return message_id
    
    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """
        獲取對話
        
        Args:
            conversation_id: 對話 ID
            
        Returns:
            Conversation 或 None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        conversation = Conversation(
            id=row["id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
        
        # 獲取訊息
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp",
            (conversation_id,)
        )
        
        for msg_row in cursor.fetchall():
            message = Message(
                id=msg_row["id"],
                role=msg_row["role"],
                content=msg_row["content"],
                timestamp=msg_row["timestamp"],
                metadata=json.loads(msg_row["metadata"] or "{}")
            )
            conversation.messages.append(message)
        
        conn.close()
        return conversation
    
    def list_conversations(self, limit: int = 50) -> List[Conversation]:
        """
        列出對話
        
        Args:
            limit: 數量限制
            
        Returns:
            對話列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )
        
        conversations = []
        for row in cursor.fetchall():
            conversations.append(Conversation(
                id=row["id"],
                title=row["title"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            ))
        
        conn.close()
        return conversations
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        全文搜尋
        
        Args:
            query: 搜尋關鍵詞
            limit: 結果數量
            
        Returns:
            搜尋結果
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.*, c.title as conversation_title
            FROM messages m
            JOIN conversations c ON m.conversation_id = c.id
            JOIN messages_fts fts ON m.id = fts.rowid
            WHERE messages_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "message_id": row["id"],
                "conversation_id": row["conversation_id"],
                "conversation_title": row["conversation_title"],
                "role": row["role"],
                "content": row["content"],
                "timestamp": row["timestamp"]
            })
        
        conn.close()
        return results
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """
        刪除對話
        
        Args:
            conversation_id: 對話 ID
            
        Returns:
            是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "DELETE FROM messages WHERE conversation_id = ?",
            (conversation_id,)
        )
        cursor.execute(
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return success
    
    def export_conversation(self, conversation_id: int, format: str = "json") -> str:
        """
        匯出對話
        
        Args:
            conversation_id: 對話 ID
            format: 格式 (json/markdown)
            
        Returns:
            匯出內容
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return ""
        
        if format == "json":
            return json.dumps(asdict(conversation), indent=2, ensure_ascii=False)
        
        # Markdown 格式
        lines = [f"# {conversation.title}\n"]
        lines.append(f"建立時間: {conversation.created_at}\n")
        lines.append(f"更新時間: {conversation.updated_at}\n")
        lines.append("\n---\n")
        
        for msg in conversation.messages:
            lines.append(f"**{msg.role}** ({msg.timestamp})\n")
            lines.append(f"{msg.content}\n")
            lines.append("\n")
        
        return "\n".join(lines)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    storage = Storage()
    
    # 測試
    print("=== Create Conversation ===")
    conv_id = storage.create_conversation("測試對話")
    print(f"Created: {conv_id}")
    
    print("\n=== Add Messages ===")
    storage.add_message(conv_id, "user", "你好！")
    storage.add_message(conv_id, "assistant", "你好！有什麼可以幫你？")
    print("Messages added")
    
    print("\n=== Get Conversation ===")
    conv = storage.get_conversation(conv_id)
    print(f"Title: {conv.title}")
    print(f"Messages: {len(conv.messages)}")
    
    print("\n=== Search ===")
    results = storage.search("你好")
    print(f"Found: {len(results)} results")
    
    print("\n=== Export ===")
    print(storage.export_conversation(conv_id, "markdown"))
