import os
import time
import datetime
import traceback
from dotenv import load_dotenv, find_dotenv
from binance.client import Client

from database import DatabaseHandler
from market_data import MarketDataHandler
from strategy import AIStrategy
from execution import TradeExecutor
from ml_logic import MLPredictor
from researcher import ResearchAgent
from sentiment import SentimentSentinel
from technical_indicators import TechnicalIndicators

def log_pid(msg):
    print(msg, flush=True)

LOCK_FILE = "shared/bot.lock"

def acquire_lock():
    """Try to acquire a lock file atomically to prevent dual-execution."""
    my_pid = os.getpid()
    try:
        # 1. Check if file exists and process is alive
        if os.path.exists(LOCK_FILE):
            with open(LOCK_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    try:
                        old_pid = int(content)
                        if old_pid == my_pid:
                            return True # Already ours
                        
                        # Check if old process is still alive
                        os.kill(old_pid, 0)
                        log_pid(f"ABORT: Bot is already running (PID {old_pid}). Close the other process first.")
                        return False
                    except (ValueError, OSError):
                        # Process dead or invalid, we can proceed to try-create
                        log_pid("Stale or invalid lock file found. Overwriting...")
                        try:
                            os.remove(LOCK_FILE)
                        except:
                            pass

        # 2. Atomic creation of the lock file
        try:
            fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, 'w') as f:
                f.write(str(my_pid))
            log_pid("Lock acquired.")
            return True
        except FileExistsError:
            # Re-verify lock owner
            with open(LOCK_FILE, 'r') as f:
                content = f.read().strip()
                if content and int(content) != my_pid:
                    log_pid(f"ABORT: Lost lock race to PID {content}.")
                    return False
                return True
                
    except Exception as e:
        log_pid(f"Singleton lock error: {e}")
        return False # Be strict - if we can't determine lock status, don't start





# Load Env
load_dotenv(find_dotenv())

# --- CONFIGURATION ---
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
BRAIN_INTERVAL_SECONDS = int(os.getenv('BRAIN_INTERVAL_SECONDS', '12'))
CLEAN_RUN_ENABLED = os.getenv('CLEAN_RUN_ENABLED', 'true').lower() == 'true'
CLEAR_TRACKED_SYMBOLS_ON_CLEAN_RUN = os.getenv('CLEAR_TRACKED_SYMBOLS_ON_CLEAN_RUN', 'true').lower() == 'true'
MODEL_NAME = "llama3"

# --- GLOBALS ---
global_time_offset_ms = 0
original_time_time = time.time

def get_adjusted_time():
    return original_time_time() + (global_time_offset_ms / 1000.0)

def init_binance_client():
    global global_time_offset_ms
    if not BINANCE_API_KEY or not BINANCE_API_SECRET:
        print("Warning: Binance keys not found. Running in MOCK MODE.")
        return None

    try:
        temp_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=True)
        server_time = temp_client.get_server_time()
        local_time = int(original_time_time() * 1000)
        global_time_offset_ms = (server_time['serverTime'] - local_time) - 2000 # Subtract 2s buffer to avoid "ahead of server" errors
        log_pid(f"Time offset: {global_time_offset_ms}ms (including safety buffer)")
        
        time.time = get_adjusted_time # Monkey-patch
        return Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=True, requests_params={'timeout': 10})
    except Exception as e:
        log_pid(f"Error connecting to Binance: {e}")
        return None

def print_status_update(symbol, market_summary, wallet_info, ai_decision, ai_reasoning, ai_quantity, live_data, order_book, trade_executed_info, session_profit=0.0, session_profit_pct=0.0, trades_summary="", full_market_data=None, price_history=None, rule_citation=""):
    try:
        total_worth = wallet_info.get('total_usd', 0.0)
        log_pid("\n" + "="*80)
        log_pid(f"TRADING BOT STATUS - {symbol}")
        
        # --- PORTFOLIO PULSE (Phase 15) ---
        if full_market_data and price_history:
            log_pid("--- PORTFOLIO PULSE (Held Assets) ---")
            for s, data in full_market_data.items():
                curr_p = data.get('price', 0.0)
                prev_p = price_history.get(s)
                
                change_str = ""
                if prev_p and prev_p > 0:
                    chg_pct = (curr_p - prev_p) / prev_p * 100
                    trend_char = "↑" if chg_pct > 0 else "↓" if chg_pct < 0 else "→"
                    change_str = f" | {trend_char} {chg_pct:+.4f}% "
                
                # Check if we own this asset
                asset = s.replace('USDT', '')
                bal = 0.0
                for b in wallet_info.get('balances', []):
                    if b['asset'] == asset:
                        bal = float(b['free']) + float(b['locked'])
                        break
                
                if bal > 0 or s == symbol:
                    bal_str = f" | {bal:.6f} {asset}" if bal > 0 else ""
                    log_pid(f"  {s:<10}: ${curr_p:>12.4f}{bal_str}{change_str}")
            log_pid("-" * 40)

        log_pid(f"TOTAL PORTFOLIO WORTH: ${total_worth:.2f} | Session P/L: ${session_profit:.2f} ({session_profit_pct:.2f}%)")
        log_pid(wallet_info.get('text', ''))
        log_pid(f"{trades_summary}")
        log_pid(f"--- ORDER BOOK ---\n{order_book}\n")
        log_pid(f"{market_summary}")
        
        log_pid("\n" + "-"*80 + "\n--- AI ANALYSIS & DECISION ---")
        if rule_citation:
            log_pid(f"RULE APPLIED: {rule_citation}")
        log_pid(f"{ai_reasoning}")
        log_pid(f"\nFINAL DECISION: [{ai_decision}] | QUANTITY: {ai_quantity*100:.0f}%")
        if trade_executed_info:
             log_pid(f"TRADE EXECUTED: {trade_executed_info}")
        log_pid("-" * 80)
        
    except Exception as e:
        log_pid(f"Error printing status update: {e}")
        traceback.print_exc()

def main_loop():
    # 0. Startup Delay (to prevent tight race conditions in Docker)
    import random
    startup_delay = random.uniform(0.1, 2.0)
    time.sleep(startup_delay)
    
    if not acquire_lock():
        return
    
    # Additional safety check - verify no other instances are running
    import psutil
    import sys
    current_pid = os.getpid()
    current_process = psutil.Process(current_pid)
    current_name = current_process.name()
    
    # Check for other Python processes running the same script
    duplicate_instances = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] != current_pid and proc.info['name'] == current_name:
                cmdline = proc.info['cmdline']
                if cmdline and len(cmdline) > 1 and 'bot_logic/main.py' in cmdline[1]:
                    duplicate_instances.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    if duplicate_instances:
        log_pid(f"ABORT: Found {len(duplicate_instances)} duplicate bot instances running: {duplicate_instances}")
        log_pid("Only one instance should run at a time. Close the other processes first.")
        return
    
    log_pid("Starting Modular AI Trading Terminal...")

    # 1. Initialize DB
    try:
        db = DatabaseHandler()
        # 1.1 Secure Postgres Advisory Lock (Final line of defense)
        if not db.acquire_advisory_lock():
            log_pid("ABORT: Bot instance already holding database lock. Scaling conflict?")
            return
        log_pid("Database lock secured.")
    except Exception as e:
        log_pid(f"CRITICAL: Database connection failed. {e}")
        return

    # 2. Initialize Strategy (Ollama)
    ai = AIStrategy(MODEL_NAME)
    if not ai.ensure_model_available():
        log_pid("Aborting: AI Model not available.")
        return

    # 3. Clean Run Logic
    if CLEAN_RUN_ENABLED:
        if CLEAR_TRACKED_SYMBOLS_ON_CLEAN_RUN:
            # We also reset the DB tables now to ensure schema issues are cleared on clean runs
            db.reset_tables()
        else:
            db.clear_tracked_symbols()

    tracked_symbols = db.get_active_tracked_symbols()
    if not tracked_symbols:
        log_pid("No active symbols. Initializing from .env...")
        initial = os.getenv('SYMBOLS', 'BTCUSDT,ETHUSDT')
        for s in initial.split(','):
            db.add_tracked_symbol(s.strip())
        tracked_symbols = db.get_active_tracked_symbols()

    # 4. Initialize Binance & Sub-handlers
    client = init_binance_client()
    market = MarketDataHandler(client)
    executor = TradeExecutor(client, db=db)
    ml = MLPredictor()
    researcher = ResearchAgent(ai, db=db)
    sentinel = SentimentSentinel(ai)

    # 5. Start Permanent Background Research (New Phase 12 & 13)
    # This runs in a separate thread, does not block trading, and checks duplicates in Postgres.
    researcher.start_background_research(interval_seconds=1200) # Full cycle every 20 mins

    # Prepare Wallet for Clean Run (Liquidate and Reset to 200 USDT)
    if CLEAN_RUN_ENABLED:
        executor.prepare_real_wallet_for_clean_run(tracked_symbols)

    initial_worth = None
    thinking_registry = {} # { symbol: { 'cycles_left': int, 'buffer': [] } }
    cycle_count = 0
    price_history = {} # Phase 15: Store prices from previous heartbeat

    while True:
        try:
            cycle_count += 1
            # Research is now handled in the background thread (ResearchAgent.thread).
            # No more synchronous blockages in the trading loop.

            # Prune DB daily (simple check)
            # db.prune_database() # Optional, call strictly if needed

            current_tracked_symbols = db.get_active_tracked_symbols()
            # Filter to valid trading pairs (ending with USDT)
            current_tracked_symbols = [s for s in current_tracked_symbols if s.endswith('USDT')]
            if not current_tracked_symbols:
                log_pid("SYMBOL GUARDIAN: No active valid symbols left. Re-initializing from defaults...")
                initial = os.getenv('SYMBOLS', 'BTCUSDT,ETHUSDT')
                for s in initial.split(','):
                    db.add_tracked_symbol(s.strip().upper())
                current_tracked_symbols = db.get_active_tracked_symbols()

                if not current_tracked_symbols:
                    log_pid("No symbols found even after re-init. Sleeping...")
                    time.sleep(BRAIN_INTERVAL_SECONDS)
                    continue

            # Phase 15: Pre-fetch all live prices for the "Portfolio Pulse"
            current_cycle_market_data = { s: market.get_live_ticker(s) for s in current_tracked_symbols }

            wallet_info = executor.get_wallet_info(current_tracked_symbols)
            
            # Track Session Profit
            total_worth = wallet_info.get('total_usd', 0.0)
            if initial_worth is None: initial_worth = total_worth
            profit = total_worth - initial_worth
            profit_pct = (profit/initial_worth*100) if initial_worth else 0

            # A. Prepare Comprehensive Portfolio Data
            portfolio_summary = ""
            for s in current_tracked_symbols:
                summary, _ = market.get_multi_timeframe_analysis(s)
                portfolio_summary += f"\n{summary}\n"

            trades_summary = db.get_recent_trades_summary()

            # Trade Cycle
            for symbol in current_tracked_symbols:
                # B. Per-Symbol Real-time Data
                live_data = current_cycle_market_data.get(symbol, {"price": 0.0})
                order_book = market.get_order_book_snapshot(symbol)

                # B2. ML Confidence Score
                ml_score = 0.5
                df_ml = market.get_ml_features(symbol)
                if df_ml is not None:
                    # Auto-train if no model
                    if ml.model is None:
                        ml.train_on_data(df_ml)
                    ml_score = float(ml.predict_confidence(df_ml))

                # B2.1 Sentiment Score
                sentiment_score = float(sentinel.analyze_symbol_sentiment(symbol))

                # B3. Deep Thinking State Check
                symbol_thinking = thinking_registry.get(symbol)
                thought_buffer = symbol_thinking['buffer'] if symbol_thinking else []
                
                if symbol_thinking:
                    log_pid(f"SYMBOL {symbol} is currently THINKING... Cycle {len(thought_buffer)} of requested duration.")

                # Get symbol rules for minimum notional
                rules = executor._get_symbol_rules(symbol)
                min_notional = rules['min_notional'] if rules else 5.0

                # C. AI Analysis (Now with full portfolio context + ML Score + Thought Buffer + Sentiment + Min Notional)
                decision, reasoning, quantity, add_syms, remove_syms, kb_update, thinking_cycles, rule_citation = ai.ask_ai_opinion(
                    current_tracked_symbols, portfolio_summary, wallet_info, order_book, live_data, trades_summary, ml_score, thought_buffer, sentiment_score, min_notional
                )
                
                # C2. Handle Deep Thinking Cycle Logic
                if thinking_cycles > 0 and len(thought_buffer) < thinking_cycles:
                    # AI wants to think more. Store reasoning and skip execution.
                    if not symbol_thinking:
                        thinking_registry[symbol] = {'buffer': [reasoning]}
                    else:
                        thinking_registry[symbol]['buffer'].append(reasoning)
                    
                    log_pid(f"DEEP THINKING: {symbol} requested {thinking_cycles} cycles. Buffer updated.")
                    # Log as THINKING decision
                    db.log_decision(symbol, "THINKING", 0.0, reasoning, None, wallet_info, {"thought_buffer": thinking_registry[symbol]['buffer']}, trade_type='STRATEGIC')
                    continue # Skip to next symbol
                
                # If we were thinking and now we have a decision (cycles=0 or reached limit)
                if symbol_thinking:
                    log_pid(f"DEEP THINKING COMPLETE: {symbol} has reached its decision after {len(thought_buffer)} cycles.")
                    del thinking_registry[symbol]

                if kb_update:
                    ai.update_knowledge_base(kb_update)

                # D2. Dynamic Portfolio Rebalancing (Kelly Criterion)
                # If AI wants to BUY, we override/refine quantity based on ML Score (Statistical Probability)
                if decision == "BUY":
                    kelly_qty = float(executor.calculate_kelly_size(ml_score))
                    log_pid(f"KELLY OPTIMIZATION: ML Score {ml_score:.2f} -> Kelly Recommended Size: {kelly_qty*100:.1f}%")
                    # We take a blend or the AI's cap if it's more conservative
                    quantity = float(min(quantity, kelly_qty) if quantity > 0 else kelly_qty)
                    reasoning += f"\n[Kelly Optimization]: Adjusting size to {quantity*100:.1f}% based on statistical confidence."
                
                # D3. Profit-Taking & Snowball Strategy
                # Check if we have open positions and if we should take profits
                elif decision == "HOLD":
                    # Check for profit-taking opportunities even when AI says HOLD
                    asset = symbol.replace('USDT', '')
                    asset_balance = next((float(b['free']) for b in wallet_info.get('balances', []) if b['asset'] == asset), 0.0)
                    
                    if asset_balance > 0:
                        # Get entry price from recent trades
                        entry_price = db.get_last_entry_price(symbol)
                        current_price = live_data.get('price', 0.0)
                        if entry_price and current_price > entry_price:
                            profit_pct = (current_price - entry_price) / entry_price * 100
                            profit_usd = asset_balance * (current_price - entry_price)
                            
                            # SNOWBALL STRATEGY: Aggressive profit-taking for compounding
                            if profit_usd > 1.0:  # Take profits if > $1
                                decision = "SELL"
                                quantity = 0.4  # Sell 40% of position to lock in gains
                                reasoning = f"[SNOWBALL]: Securing ${profit_usd:.2f} profit ({profit_pct:.2f}%). Selling 40% to reinvest capital immediately."
                                rule_citation = "Auto-Learned 2026-01-05: SNOWBALL STRATEGY - Take profits aggressively and reinvest"
                                log_pid(f"SNOWBALL PROFIT-TAKING: {symbol} - ${profit_usd:.2f} profit detected. Preparing to reinvest.")
                            elif profit_pct > 1.5:  # Take profits if > 1.5%
                                decision = "SELL"
                                quantity = 0.25  # Sell 25% of position
                                reasoning = f"[SNOWBALL]: Securing {profit_pct:.2f}% profit. Selling 25% to compound capital faster."
                                rule_citation = "Auto-Learned 2026-01-05: SNOWBALL STRATEGY - Frequent small wins for compounding"
                                log_pid(f"SNOWBALL PROFIT-TAKING: {symbol} - {profit_pct:.2f}% profit detected. Compound cycle initiated.")

                # D. Execution
                full_reasoning = f"[Rule Citation]: {rule_citation}\n\n{reasoning}"
                trade_info = executor.execute_trade(symbol, decision, quantity)
                
                # D4. SMART SNOWBALL REINVESTMENT STRATEGY
                # If we just took profits, strategically redeploy the capital to the best opportunity
                if trade_info and trade_info['action'] == "SELL" and "SNOWBALL" in reasoning:
                    # Get updated wallet info after the sell
                    updated_wallet = executor.get_wallet_info(current_tracked_symbols)
                    usdt_balance = next((float(b['free']) for b in updated_wallet.get('balances', []) if b['asset'] == 'USDT'), 0.0)
                    
                    if usdt_balance > 10.0:  # Minimum for reinvestment
                        log_pid(f"SNOWBALL REINVESTMENT: ${usdt_balance:.2f} available. Analyzing best reinvestment opportunity...")
                        
                        # SMART REINVESTMENT: Find the best opportunity among all tracked symbols
                        best_opportunity = None
                        best_score = -float('inf')
                        
                        for test_symbol in current_tracked_symbols:
                            if test_symbol == symbol:  # Avoid immediately buying back the same asset we just sold
                                continue
                            
                            # Get current data for this symbol
                            test_live_data = current_cycle_market_data.get(test_symbol, {"price": 0.0})
                            test_price = test_live_data.get('price', 0.0)
                            if test_price <= 0:
                                continue
                            
                            # Get technical indicators for smart assessment
                            test_df = market.get_ml_features(test_symbol)
                            if test_df is None or len(test_df) < 20:
                                continue
                            
                            # Calculate key indicators for reinvestment decision
                            try:
                                rsi_14 = TechnicalIndicators.calculate_rsi(test_df, 14).iloc[-1]
                                ema_20 = TechnicalIndicators.calculate_ema(test_df, 20).iloc[-1]
                                current_price = test_price
                                
                                # Score the opportunity (higher = better)
                                score = 0
                                
                                # RSI-based scoring (lower RSI = better entry)
                                if rsi_14 < 30:  # Oversold = good buying opportunity
                                    score += 50
                                elif rsi_14 < 50:  # Neutral = reasonable
                                    score += 30
                                elif rsi_14 < 70:  # Overbought = cautious
                                    score += 10
                                
                                # Price vs EMA scoring (below EMA = better entry)
                                if current_price < ema_20 * 0.98:  # Below EMA = good
                                    score += 40
                                elif current_price < ema_20 * 1.02:  # Near EMA = reasonable
                                    score += 20
                                
                                # Volatility scoring (lower volatility = safer entry)
                                atr_14 = TechnicalIndicators.calculate_atr(test_df, 14).iloc[-1]
                                atr_pct = (atr_14 / current_price) * 100
                                if atr_pct < 2:  # Low volatility
                                    score += 30
                                elif atr_pct < 5:  # Medium volatility
                                    score += 15
                                
                                # Check if this is the best opportunity so far
                                if score > best_score:
                                    best_score = score
                                    best_opportunity = {
                                        'symbol': test_symbol,
                                        'price': current_price,
                                        'rsi': rsi_14,
                                        'ema_ratio': current_price / ema_20,
                                        'score': score,
                                        'atr_pct': atr_pct
                                    }
                            
                            except Exception as e:
                                log_pid(f"Error analyzing {test_symbol} for reinvestment: {e}")
                                continue
                        
                        # Decision based on best opportunity found
                        if best_opportunity and best_score > 30:  # Only reinvest if we find a good opportunity
                            best_symbol = best_opportunity['symbol']
                            log_pid(f"SNOWBALL SMART REINVESTMENT: Best opportunity found - {best_symbol} (Score: {best_score:.0f}, RSI: {best_opportunity['rsi']:.1f}, Price/EMA: {best_opportunity['ema_ratio']:.2f})")
                            
                            # Set up the reinvestment trade for the next cycle
                            decision = "BUY"
                            quantity = min(0.6, usdt_balance / (usdt_balance + 50))  # Conservative sizing for reinvestment
                            reasoning = f"[SMART SNOWBALL]: Reinvesting ${trade_info['usdt_amount']:.2f} profit in {best_symbol}. " \
                                        f"Opportunity score: {best_score:.0f} (RSI: {best_opportunity['rsi']:.1f}, " \
                                        f"Price/EMA: {best_opportunity['ema_ratio']:.2f}, ATR: {best_opportunity['atr_pct']:.1f}%)"
                            rule_citation = "Auto-Learned 2026-01-05: SNOWBALL STRATEGY - Reinvest strategically in best available opportunity"
                            
                            # Log this smart reinvestment decision
                            db.log_decision(best_symbol, "SMART_REINVEST", quantity, reasoning, None, updated_wallet,
                                          {"snowball_amount": trade_info['usdt_amount'], "opportunity_score": best_score},
                                          trade_type='SNOWBALL')
                            
                        else:
                            # No good opportunity found - keep capital in USDT for now
                            log_pid(f"SNOWBALL PATIENT MODE: No attractive reinvestment opportunities found (best score: {best_score:.0f}). Holding ${usdt_balance:.2f} for better entry points.")
                            reasoning = f"[SNOWBALL PATIENT]: Secured ${trade_info['usdt_amount']:.2f} profit. Waiting for better reinvestment opportunity (RSI<30 or price<EMA)."
                            rule_citation = "Auto-Learned 2026-01-05: SNOWBALL STRATEGY - Be patient, wait for value"
                            db.log_decision(symbol, "PATIENT_HOLD", 0.0, reasoning, None, updated_wallet,
                                          {"snowball_amount": trade_info['usdt_amount'], "waiting_for_value": True},
                                          trade_type='SNOWBALL')

                # E. Logging
                if trade_info:
                    # Update wallet if trade happened
                    wallet_info = executor.get_wallet_info(current_tracked_symbols)

                # Log decision first to ensure DB is up to date
                db.log_decision(symbol, decision, quantity, full_reasoning, trade_info, wallet_info, {"thought_buffer": thought_buffer, "rule_citation": rule_citation}, trade_type='STRATEGIC')

                # If a trade occurred, refresh the summary so it appears in the status immediately
                if trade_info:
                     trades_summary = db.get_recent_trades_summary()

                print_status_update(
                    symbol, portfolio_summary, wallet_info, decision, reasoning, quantity, live_data, order_book, trade_info, profit, profit_pct, trades_summary,
                    full_market_data=current_cycle_market_data, price_history=price_history, rule_citation=rule_citation
                )

                # E. Symbol Management
                for s in add_syms:
                    if not s or not isinstance(s, str) or not s.strip(): continue # Filter invalid
                    s = s.strip().upper()
                    # Normalize to trading pair if not already
                    if not s.endswith('USDT'):
                        s += 'USDT'

                    # CRITICAL: Prevent re-adding (and re-cleaning) symbols we are already tracking
                    if s in current_tracked_symbols:
                        continue

                    log_pid(f"AI RECOMMENDATION: ADD {s}")
                    trade_info_cleanup = executor.liquidate_symbol(s) # Zero it first
                    
                    if trade_info_cleanup:
                        # Log the liquidation for visibility
                        db.log_decision(s, "REMOVE", 1.0, f"Initial cleanup before adding {s} to tracking.", trade_info_cleanup, wallet_info, {}, trade_type='OPERATIONAL')
                        
                        liquidated_val = trade_info_cleanup['usdt_amount']
                        # User Request: If we have existing funds (e.g. 100 SOL), "clean" it by buying INDEPENDENT currency (USDC).
                        # This segregates it from Trading Capital (USDT) and Profit Savings (TUSD).
                        log_pid(f"Parking ${liquidated_val:.2f} of pre-existing {s} into USDC (Capital Exclusion).")
                        executor.park_asset(liquidated_val, target_asset='USDC')
                        # We do NOT adjust initial_worth. This money is ejected from the system.
                        
                    db.add_tracked_symbol(s)
                    current_tracked_symbols.append(s) # Update local list for immediate visibility
                    
                for s in remove_syms:
                    if not s or not isinstance(s, str) or not s.strip(): continue
                    s = s.strip().upper()
                    # Normalize to trading pair if not already
                    if not s.endswith('USDT'):
                        s += 'USDT'

                    log_pid(f"AI RECOMMENDATION: REMOVE {s}")
                    # Just exit position to USDT. Do NOT park it.
                    trade_info_remove = executor.liquidate_symbol(s)
                    if trade_info_remove:
                        db.log_decision(s, "REMOVE", 1.0, f"AI Recommendation: Remove {s} from tracking.", trade_info_remove, wallet_info, {})

                    db.remove_tracked_symbol(s)
                    if s in current_tracked_symbols: current_tracked_symbols.remove(s) # Update local list
                    
                # Update wallet info immediately to reflect new assets for next iteration/logging
                if add_syms or remove_syms:
                     wallet_info = executor.get_wallet_info(current_tracked_symbols)

            # End of cycle: Update price history for next heartbeat
            price_history = { s: d.get('price', 0.0) for s, d in current_cycle_market_data.items() }

        except Exception as e:
            log_pid(f"Main Loop Error: {e}")
            traceback.print_exc()

        time.sleep(BRAIN_INTERVAL_SECONDS)

if __name__ == "__main__":
    main_loop()