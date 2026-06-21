"""
Order Database
SQLite database for tracking synced orders
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Tuple, Dict, Optional

logger = logging.getLogger(__name__)


class OrderDatabase:
    """SQLite database for tracking orders"""
    
    def __init__(self, db_path: str = 'orders.db'):
        """Initialize database"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create orders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ecwid_id INTEGER UNIQUE NOT NULL,
                    shiprocket_id INTEGER,
                    status TEXT NOT NULL DEFAULT 'pending',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create sync logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_type TEXT NOT NULL,
                    total_orders INTEGER,
                    successful INTEGER,
                    failed INTEGER,
                    skipped INTEGER,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    duration_seconds INTEGER,
                    error_details TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"✓ Database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    def save_order(
        self,
        ecwid_id: int,
        shiprocket_id: Optional[int] = None,
        status: str = 'success',
        error_message: Optional[str] = None
    ):
        """Save or update order record"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO orders
                (ecwid_id, shiprocket_id, status, error_message, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (ecwid_id, shiprocket_id, status, error_message))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save order: {str(e)}")
            raise
    
    def order_exists(self, ecwid_id: int) -> bool:
        """Check if order has been processed"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM orders WHERE ecwid_id = ?', (ecwid_id,))
            result = cursor.fetchone()
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Database query failed: {str(e)}")
            return False
    
    def update_order_status(
        self,
        ecwid_id: int,
        shiprocket_id: Optional[int] = None,
        status: str = 'success',
        error_message: Optional[str] = None
    ):
        """Update order status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE orders
                SET shiprocket_id = ?, status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP
                WHERE ecwid_id = ?
            ''', (shiprocket_id, status, error_message, ecwid_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update order: {str(e)}")
            raise
    
    def get_failed_orders(self) -> List[Tuple[int, int]]:
        """Get list of failed orders"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT id, ecwid_id FROM orders WHERE status = ?',
                ('failed',)
            )
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get failed orders: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get sync statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM orders')
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'success'")
            success = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'failed'")
            failed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
            pending = cursor.fetchone()[0]
            
            cursor.execute("SELECT MAX(updated_at) FROM orders")
            last_sync = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total': total,
                'success': success,
                'failed': failed,
                'pending': pending,
                'last_sync': last_sync
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            return {'total': 0, 'success': 0, 'failed': 0, 'pending': 0, 'last_sync': None}
    
    def get_sync_history(self, limit: int = 50) -> List[Dict]:
        """Get sync history"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM sync_logs
                ORDER BY started_at DESC
                LIMIT ?
            ''', (limit,))
            
            results = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get sync history: {str(e)}")
            return []
