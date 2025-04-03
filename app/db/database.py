import os
import sys
import sqlite3
from datetime import datetime, date
from typing import Optional, List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import Config

class Database:
    """Database interface supporting both PostgreSQL and SQLite fallback."""
    def __init__(self):
        self.is_sqlite = False
        self.conn = None
        
        database_url = getattr(Config, 'DATABASE_URL', os.environ.get('DATABASE_URL', 'sqlite:///data_storage/trading.db'))
        
        if database_url.startswith('sqlite:///'):
            self._init_sqlite(database_url)
        else:
            try:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                self.conn = psycopg2.connect(database_url)
                self.is_sqlite = False
            except Exception as e:
                print(f"PostgreSQL connection failed: {e}")
                print("Falling back to SQLite database...")
                self._init_sqlite('sqlite:///data_storage/trading.db')
                
        self.create_tables()

    def _init_sqlite(self, database_url: str):
        self.is_sqlite = True
        db_path = database_url.replace('sqlite:///', '')
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def _execute(self, query: str, params: tuple = ()):
        """Execute query with parameters adapted to engine."""
        cursor = self.conn.cursor()
        if self.is_sqlite:
            adapted_query = query.replace('%s', '?')
            cursor.execute(adapted_query, params)
        else:
            cursor.execute(query, params)
        return cursor

    def create_tables(self):
        try:
            cur = self.conn.cursor()
            if self.is_sqlite:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS trading_signals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        signal_type TEXT NOT NULL,
                        strategy TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        timestamp TEXT NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS screened_stocks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL UNIQUE,
                        company_name TEXT,
                        current_price REAL NOT NULL,
                        average_volume INTEGER NOT NULL,
                        last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS trading_decisions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        decision TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        agent_name TEXT NOT NULL DEFAULT 'supervisor',
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS audit_trail (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        decision_type TEXT NOT NULL,
                        action TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        rationale TEXT NOT NULL,
                        compliance_status TEXT,
                        risk_level TEXT,
                        position_size TEXT,
                        blocked_trades TEXT
                    )
                """)
            else:
                cur.execute("""
                    CREATE SEQUENCE IF NOT EXISTS trading_signals_id_seq;
                    CREATE SEQUENCE IF NOT EXISTS trading_decisions_id_seq;
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS trading_signals (
                        id INTEGER PRIMARY KEY DEFAULT nextval('trading_signals_id_seq'),
                        symbol VARCHAR(10) NOT NULL,
                        signal_type VARCHAR(10) NOT NULL,
                        strategy VARCHAR(50) NOT NULL,
                        confidence FLOAT NOT NULL,
                        timestamp TIMESTAMP NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS screened_stocks (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(10) NOT NULL UNIQUE,
                        company_name VARCHAR(100),
                        current_price DECIMAL(10, 2) NOT NULL,
                        average_volume BIGINT NOT NULL,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS trading_decisions (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(10) NOT NULL,
                        decision TEXT NOT NULL,
                        confidence FLOAT NOT NULL,
                        agent_name VARCHAR(50) NOT NULL DEFAULT 'supervisor',
                        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS audit_trail (
                        id SERIAL PRIMARY KEY,
                        symbol VARCHAR(10) NOT NULL,
                        timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        decision_type VARCHAR(50) NOT NULL,
                        action VARCHAR(50) NOT NULL,
                        confidence FLOAT NOT NULL,
                        rationale TEXT NOT NULL,
                        compliance_status VARCHAR(50),
                        risk_level VARCHAR(20),
                        position_size VARCHAR(50),
                        blocked_trades TEXT
                    )
                """)
            self.conn.commit()
            cur.close()
        except Exception as e:
            self.conn.rollback()
            print(f"Error creating tables: {str(e)}")
            raise

    def add_signal(self, symbol: str, signal_type: str, strategy: str, confidence: float):
        ts = datetime.now().isoformat() if self.is_sqlite else datetime.now()
        cur = self._execute("""
            INSERT INTO trading_signals (symbol, signal_type, strategy, confidence, timestamp)
            VALUES (%s, %s, %s, %s, %s)
        """, (symbol, signal_type, strategy, confidence, ts))
        self.conn.commit()
        cur.close()

    def upsert_screened_stock(self, symbol: str, company_name: str, current_price: float, average_volume: int):
        ts = datetime.now().isoformat() if self.is_sqlite else datetime.now()
        if self.is_sqlite:
            cur = self._execute("""
                INSERT INTO screened_stocks (symbol, company_name, current_price, average_volume, last_updated)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE SET
                    company_name = excluded.company_name,
                    current_price = excluded.current_price,
                    average_volume = excluded.average_volume,
                    last_updated = excluded.last_updated
            """, (symbol, company_name, current_price, average_volume, ts))
        else:
            cur = self._execute("""
                INSERT INTO screened_stocks (symbol, company_name, current_price, average_volume, last_updated)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    current_price = EXCLUDED.current_price,
                    average_volume = EXCLUDED.average_volume,
                    last_updated = EXCLUDED.last_updated
            """, (symbol, company_name, current_price, average_volume, ts))
        self.conn.commit()
        cur.close()

    def get_screened_stocks(self) -> List[Dict[str, Any]]:
        cur = self._execute("SELECT * FROM screened_stocks ORDER BY symbol ASC")
        rows = [dict(row) for row in cur.fetchall()]
        cur.close()
        return rows

    def clear_old_screened_stocks(self, hours: int = 24):
        if self.is_sqlite:
            cur = self._execute("DELETE FROM screened_stocks WHERE datetime(last_updated) < datetime('now', '-%s hours')", (hours,))
        else:
            cur = self._execute("DELETE FROM screened_stocks WHERE last_updated < NOW() - INTERVAL '%s hours'", (hours,))
        self.conn.commit()
        cur.close()

    def save_trading_decision(self, symbol: str, decision: str, confidence: float, agent_name: str = 'supervisor'):
        """Save a new trading decision for a stock"""
        try:
            ts = datetime.now().isoformat() if self.is_sqlite else datetime.now()
            cur = self._execute("""
                INSERT INTO trading_decisions (symbol, decision, confidence, agent_name, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (symbol, decision, confidence, agent_name, ts))
            self.conn.commit()
            cur.close()
        except Exception as e:
            print(f"Database error in save_trading_decision: {str(e)}")
            raise

    def get_latest_trading_decisions(self, symbol: str, limit: int = 2) -> List[Dict[str, Any]]:
        """Get the latest trading decisions for a stock"""
        cur = self._execute("""
            SELECT decision, confidence, agent_name, created_at
            FROM trading_decisions
            WHERE symbol = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (symbol, limit))
        rows = [dict(row) for row in cur.fetchall()]
        cur.close()
        return rows

    def get_all_agent_decisions(self, symbol: str) -> List[Dict[str, Any]]:
        """Get the latest decision from each agent for a stock"""
        cur = self._execute("""
            WITH RankedDecisions AS (
                SELECT 
                    symbol,
                    decision,
                    confidence,
                    agent_name,
                    created_at,
                    ROW_NUMBER() OVER (PARTITION BY agent_name ORDER BY created_at DESC) as rn
                FROM trading_decisions
                WHERE symbol = %s
            )
            SELECT symbol, decision, confidence, agent_name, created_at
            FROM RankedDecisions
            WHERE rn = 1
            ORDER BY agent_name;
        """, (symbol,))
        rows = [dict(row) for row in cur.fetchall()]
        cur.close()
        return rows

    def save_audit_entry(self, symbol: str, decision_type: str, action: str, confidence: float,
                         rationale: str, compliance_status: Optional[str] = None,
                         risk_level: Optional[str] = None, position_size: Optional[str] = None,
                         blocked_trades: Optional[str] = None):
        """Save an audit entry to the database"""
        try:
            ts = datetime.now().isoformat() if self.is_sqlite else datetime.now()
            cur = self._execute("""
                INSERT INTO audit_trail 
                (symbol, timestamp, decision_type, action, confidence, rationale, compliance_status, risk_level, position_size, blocked_trades)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (symbol, ts, decision_type, action, confidence, rationale, compliance_status, risk_level, position_size, blocked_trades))
            self.conn.commit()
            cur.close()
        except Exception as e:
            print(f"Database error in save_audit_entry: {str(e)}")
            raise

    def get_audit_trail(self, symbol: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve audit trail entries from database"""
        if symbol:
            cur = self._execute("""
                SELECT * FROM audit_trail
                WHERE symbol = %s
                ORDER BY timestamp DESC
                LIMIT %s
            """, (symbol, limit))
        else:
            cur = self._execute("""
                SELECT * FROM audit_trail
                ORDER BY timestamp DESC
                LIMIT %s
            """, (limit,))
        rows = [dict(row) for row in cur.fetchall()]
        cur.close()
        return rows

    def get_trading_decisions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all trading decisions from database"""
        if symbol:
            cur = self._execute("""
                SELECT * FROM trading_decisions
                WHERE symbol = %s
                ORDER BY created_at DESC
            """, (symbol,))
        else:
            cur = self._execute("SELECT * FROM trading_decisions ORDER BY created_at DESC")
        rows = [dict(row) for row in cur.fetchall()]
        cur.close()
        return rows

    def get_decisions_summary(self) -> Dict[str, Any]:
        """Summary metrics across all trading decisions"""
        all_decisions = self.get_trading_decisions()
        by_agent = {}
        by_symbol = {}
        for d in all_decisions:
            agent = d.get('agent_name', 'unknown')
            sym = d.get('symbol', 'unknown')
            by_agent[agent] = by_agent.get(agent, 0) + 1
            by_symbol[sym] = by_symbol.get(sym, 0) + 1
        return {
            "total_decisions": len(all_decisions),
            "by_agent": by_agent,
            "by_symbol": by_symbol,
            "recent_decisions": all_decisions[:10]
        }
