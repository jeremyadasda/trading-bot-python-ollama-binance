import os
import time
import json
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager

def log_pid(msg):
    print(msg, flush=True)

class DatabaseHandler:
    def __init__(self, db_url=None):
        self.db_url = db_url or os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable is not set")

        # Initialize connection pool with retry logic for DNS resolution issues
        max_retries = 10
        retry_delay = 2  # seconds
        for attempt in range(max_retries):
            try:
                self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                    1, 20, dsn=self.db_url
                )
                break  # Success, exit retry loop
            except Exception as e:
                if attempt < max_retries - 1:
                    log_pid(f"Database connection attempt {attempt + 1} failed: {e}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise e  # Re-raise the last exception if all retries failed

        self.init_db()

    def acquire_advisory_lock(self, lock_id=123456789):
        """Uses a Postgres advisory lock with a dedicated connection to ensure singleton."""
        try:
            # We open a DEDICATED connection for the lock that stays alive with the object.
            # This prevents the pool from reclaiming it and potentially releasing the lock.
            self._lock_conn = psycopg2.connect(self.db_url)
            self._lock_conn.set_session(autocommit=True)
            cur = self._lock_conn.cursor()
            cur.execute("SELECT pg_try_advisory_lock(%s)", (lock_id,))
            acquired = cur.fetchone()[0]
            if not acquired:
                self._lock_conn.close()
                self._lock_conn = None
            return acquired
        except Exception as e:
            log_pid(f"Error acquiring advisory lock: {e}")
            return False

    def reset_tables(self):
        try:
            with self.get_cursor() as cur:
                # We KEEP decisions_log for long-term learning as requested by user.
                # Only reset the tracked_symbols to allow a fresh set of starting coins.
                cur.execute("DELETE FROM tracked_symbols")
            log_pid("Tracked symbols cleared for CLEAN RUN. History preserved.")
            self.init_db() # Ensure schema is correct
        except Exception as e:
            print(f"Error resetting tables: {e}")

    @contextmanager
    def get_cursor(self):
        conn = self.connection_pool.getconn()
        try:
            yield conn.cursor()
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.connection_pool.putconn(conn)

    def init_db(self):
        try:
            with self.get_cursor() as cur:
                # Decisions Log Table
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS decisions_log (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        symbol TEXT,
                        ai_decision TEXT,
                        ai_quantity_pct REAL,
                        ai_reasoning TEXT,
                        actual_action TEXT,
                        actual_quantity REAL,
                        actual_price REAL,
                        post_trade_usdt_balance REAL,
                        post_trade_asset_balance REAL,
                        post_trade_total_worth REAL,
                        context_snapshot TEXT,
                        trade_id TEXT, 
                        profit REAL,
                        trade_type TEXT DEFAULT 'STRATEGIC'
                    )
                ''')
                # Migration: Add trade_type if it doesn't exist
                cur.execute('''
                    DO $$ 
                    BEGIN 
                        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='decisions_log' AND column_name='trade_type') THEN
                            ALTER TABLE decisions_log ADD COLUMN trade_type TEXT DEFAULT 'STRATEGIC';
                        END IF;
                    END $$;
                ''')
                cur.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON decisions_log (timestamp)")

                cur.execute('''
                    CREATE TABLE IF NOT EXISTS tracked_symbols (
                        symbol TEXT PRIMARY KEY,
                        added_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'active'
                    )
                ''')

                # Research URL Tracking Table
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS researched_urls (
                        url TEXT PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'visited'
                    )
                ''')
            log_pid("PostgreSQL Database initialized successfully.")
        except Exception as e:
            log_pid(f"Error initializing database: {e}")
            raise

    def add_tracked_symbol(self, symbol):
        if not symbol or not symbol.strip():
            return
        try:
            with self.get_cursor() as cur:
                cur.execute('''
                    INSERT INTO tracked_symbols (symbol, status) 
                    VALUES (%s, 'active') 
                    ON CONFLICT (symbol) DO UPDATE SET status = 'active'
                ''', (symbol,))
            log_pid(f"Symbol {symbol} added/updated in tracked_symbols.")
        except Exception as e:
            print(f"Error adding tracked symbol: {e}")

    def remove_tracked_symbol(self, symbol):
        try:
            with self.get_cursor() as cur:
                cur.execute("UPDATE tracked_symbols SET status = 'inactive' WHERE symbol = %s", (symbol,))
            print(f"Symbol {symbol} marked as inactive.")
        except Exception as e:
            print(f"Error removing tracked symbol: {e}")

    def clear_tracked_symbols(self):
        try:
            with self.get_cursor() as cur:
                cur.execute("DELETE FROM tracked_symbols")
            print("Tracked symbols table cleared.")
        except Exception as e:
            print(f"Error clearing tracked symbols: {e}")

    def get_active_tracked_symbols(self):
        try:
            with self.get_cursor() as cur:
                cur.execute("SELECT symbol FROM tracked_symbols WHERE status = 'active'")
                rows = cur.fetchall()
                symbols = [row[0] for row in rows]
                return [s for s in symbols if s and s.strip()]
        except Exception as e:
            print(f"Error getting active tracked symbols: {e}")
            return []

    def log_decision(self, symbol, ai_decision, ai_quantity_pct, ai_reasoning, trade_info, wallet_info, context_snapshot, trade_type='STRATEGIC'):
        try:
            trade_info = trade_info or {}
            # Context is already a dict, dump it to json string if strictly needed.
            context_str = json.dumps(context_snapshot) if trade_info.get('action') in ["BUY", "SELL"] else None
            
            balances = wallet_info.get('balances', []) if wallet_info else []
            usdt_balance = next((float(b['free']) for b in balances if b['asset'] == 'USDT'), 0.0)
            asset = symbol.replace('USDT', '')
            asset_balance = next((float(b['free']) for b in balances if b['asset'] == asset), 0.0)
            total_usd = float(wallet_info.get('total_usd', 0.0)) if wallet_info else 0.0

            with self.get_cursor() as cur:
                cur.execute('''
                    INSERT INTO decisions_log (
                        symbol, ai_decision, ai_quantity_pct, ai_reasoning, 
                        actual_action, actual_quantity, actual_price, 
                        post_trade_usdt_balance, post_trade_asset_balance, post_trade_total_worth, 
                        context_snapshot, trade_id, trade_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    symbol, ai_decision, float(ai_quantity_pct), ai_reasoning,
                    trade_info.get('action', 'NONE'), float(trade_info.get('amount', 0.0)), float(trade_info.get('price', 0.0)),
                    float(usdt_balance), float(asset_balance), total_usd,
                    context_str, str(trade_info.get('orderId', '')), trade_type
                ))
                return cur.fetchone()[0]
        except Exception as e:
            print(f"Error logging decision: {e}")
            return None

    def get_recent_trades_summary(self, limit=5):
        try:
            with self.get_cursor() as cur:
                cur.execute('''
                    SELECT timestamp, actual_action, actual_quantity, actual_price, symbol 
                    FROM decisions_log 
                    WHERE actual_action IN ('BUY', 'SELL') 
                      AND trade_type = 'STRATEGIC'
                    ORDER BY timestamp DESC LIMIT %s
                ''', (limit,))
                trades = cur.fetchall()
                
                if not trades:
                    return "No recent trades found in database."

                summary = "--- RECENT TRADES (from DB) ---"
                for t in trades:
                    # t is a tuple: (timestamp, action, quantity, price, symbol)
                    ts_str = str(t[0]).split('.')[0] # Simple formatting
                    usd_val = t[2] * t[3]
                    summary += f"\n{ts_str} | {t[1]:<4} | {t[2]:.6f} {t[4].replace('USDT','')} @ ${t[3]:.2f} (Total: ${usd_val:.2f})"
                return summary
        except Exception as e:
            print(f"Error getting trades summary: {e}")
            return "Could not retrieve recent trades."

    def prune_database(self, max_rows=10000):
        # Postgres can handle more, but let's keep a loose limit if desired. 
        # Actually with Postgres we rarely need to prune by lines unless specific requirement.
        # I'll implement a basic cleanup if table gets massive, effectively retaining last N rows.
        try:
            with self.get_cursor() as cur:
                # Count rows roughly
                cur.execute("SELECT count(*) FROM decisions_log")
                count = cur.fetchone()[0]
                if count > max_rows:
                    print(f"Pruning database (Row count: {count})...")
                    cur.execute('''
                        DELETE FROM decisions_log 
                        WHERE id IN (
                            SELECT id FROM decisions_log 
                            ORDER BY id ASC 
                            LIMIT %s
                        )
                    ''', (count - max_rows,))
                    print("Database pruned.")
        except Exception as e:
            print(f"Error pruning database: {e}")

    def is_url_researched(self, url):
        """Check if a URL has already been processed."""
        try:
            with self.get_cursor() as cur:
                cur.execute("SELECT 1 FROM researched_urls WHERE url = %s", (url,))
                return cur.fetchone() is not None
        except Exception as e:
            log_pid(f"Error checking URL: {e}")
            return False

    def register_researched_url(self, url):
        """Mark a URL as visited."""
        try:
            with self.get_cursor() as cur:
                cur.execute("INSERT INTO researched_urls (url) VALUES (%s) ON CONFLICT (url) DO NOTHING", (url,))
        except Exception as e:
            log_pid(f"Error registering URL: {e}")
