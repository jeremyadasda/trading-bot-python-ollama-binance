import os
import json
import requests
import datetime
import traceback

def log_pid(msg):
    print(msg, flush=True)

class AIStrategy:
    def __init__(self, model_name="llama3"):
        self.base_ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.generate_url = f"{self.base_ollama_url}/api/generate"
        self.tags_url = f"{self.base_ollama_url}/api/tags"
        self.pull_url = f"{self.base_ollama_url}/api/pull"
        self.model_name = model_name
        self.kb_path = 'bot_logic/knowledge_base.md'
        
        # Import prompt templates
        try:
            from bot_logic.prompt_templates import get_current_prompt_template
            self.get_prompt_template = get_current_prompt_template
        except ImportError:
            # Fallback to hardcoded template if prompt_templates module is not available
            self.get_prompt_template = self._get_hardcoded_prompt_template

    def ensure_model_available(self):
        log_pid(f"Checking Ollama connection at {self.base_ollama_url}...")
        try:
            r = requests.get(self.tags_url, timeout=5)
            r.raise_for_status()
            models = r.json().get('models', [])
            if any(self.model_name in m.get('name', '') for m in models):
                log_pid(f"OK: Model '{self.model_name}' is available.")
                return True
            return self.pull_model(self.model_name)
        except Exception as e:
            print(f"ERROR connecting to Ollama: {e}")
            return False

    def pull_model(self, model_name):
        print(f"Downloading/Verifying model '{model_name}'...")
        try:
            payload = {"name": model_name}
            with requests.post(self.pull_url, json=payload, stream=True, timeout=None) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        data = json.loads(line)
                        status = data.get('status', '')
                        print(f"\rStatus: {status}", end="", flush=True)
                print(f"\nModel '{model_name}' is ready!")
                return True
        except Exception as e:
            print(f"\nERROR downloading model: {e}")
            return False

    def update_knowledge_base(self, new_insight):
        if not new_insight or len(new_insight) < 5: return
        
        # Filter generic non-updates and hallucinations
        boilerplate = ["none needed", "no update", "optional. a new rule", "a new rule or insight", "optional material"]
        if any(b in new_insight.lower() for b in boilerplate):
            return

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d")
        entry = f"- **[Auto-Learned {timestamp}]:** {new_insight}"
        
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.kb_path), exist_ok=True)

            # Read existing content for deduplication
            content = ""
            if os.path.exists(self.kb_path):
                with open(self.kb_path, "r", encoding='utf-8') as f:
                    content = f.read()
            
            # Simple Deduplication: Check if the exact insight string already exists
            if new_insight.strip() in content:
                print(f"Skipping duplicate knowledge update: {new_insight[:50]}...")
                return

            # Append the new entry
            with open(self.kb_path, "a", encoding='utf-8') as f:
                f.write(f"\n{entry}")
            print(f"Knowledge Base Updated: {new_insight[:50]}...")
            
        except Exception as e:
            print(f"Could not update Knowledge Base: {e}")

    def ask_ai_opinion(self, current_tracked_symbols, market_summary, full_wallet_info, order_book, live_data, trade_summary, ml_score=0.5, thought_buffer=None, sentiment_score=0.0, min_notional=5.0, historical_trends=None, user_preferences=None):
        # ... (rest of the setup logic remains same)
        wallet_text = full_wallet_info.get('text', '')
        usdt_balance = next((float(b['free']) for b in full_wallet_info.get('balances', []) if b['asset'] == 'USDT'), 0.0)
        total_portfolio_worth = full_wallet_info.get('total_usd', 0.0)
        
        tracked_symbols_str = ", ".join(current_tracked_symbols)
        detailed_balances_list = full_wallet_info.get('detailed_balances_list', [])
        
        detailed_balances_prompt_section = "--- DETAILED ASSET BREAKDOWN ---"
        for item in detailed_balances_list:
            detailed_balances_prompt_section += f"- {item['asset']}: {item['balance']:.6f} (${item['usd_value']:.2f})\n"

        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                knowledge_base = f.read()
        except Exception:
            knowledge_base = "Knowledge base file not found. Using default strategies."

        # Format Scores
        ml_insight = f"ML Statistical Confidence: {ml_score*100:.1f}% "
        sent_insight = "BULLISH" if sentiment_score > 0.3 else "BEARISH" if sentiment_score < -0.3 else "NEUTRAL"
        sent_val = f"{sentiment_score:+.2f} ({sent_insight})"

        # Add Historical Trends and User Preferences
        historical_trends = historical_trends if historical_trends is not None else "Historical trends data not provided."
        user_preferences = user_preferences if user_preferences is not None else "User preferences not provided."

        # Recursive Prompt Buffer Injection
        recursive_history = ""
        if thought_buffer and len(thought_buffer) > 0:
            recursive_history = "\n--- RECURSIVE REASONING CHAIN (PREVIOUS CYCLES) ---\n"
            for i, thought in enumerate(thought_buffer):
                recursive_history += f"Cycle {i+1}: {thought}\n"
            recursive_history += "\nCRITICAL: Use your previous thoughts to refine or pivot your final decision. Do not ignore them.\n"

        # Use the dynamic prompt template
        prompt_template = self.get_prompt_template()
        
        # Extract price from live_data for the template
        live_price = live_data.get('price', 'N/A') if isinstance(live_data, dict) else 'N/A'
        
        prompt = prompt_template.format(
            knowledge_base=knowledge_base,
            tracked_symbols_str=tracked_symbols_str,
            wallet_text=wallet_text,
            total_portfolio_worth=total_portfolio_worth,
            usdt_balance=usdt_balance,
            min_notional=min_notional,
            detailed_balances_prompt_section=detailed_balances_prompt_section,
            trade_summary=trade_summary,
            market_summary=market_summary,
            live_price=live_price,
            order_book=order_book,
            ml_insight=ml_insight,
            sent_val=sent_val,
            historical_trends=historical_trends,
            user_preferences=user_preferences,
            recursive_history=recursive_history
        )
        print(f"Running hybrid analysis with {self.model_name}...")
        try:
            payload = {
                "model": self.model_name, "prompt": prompt, "stream": False, "format": "json",
                "options": { "temperature": 0.7, "num_predict": 800, "num_ctx": 16384 }
            }
            r = requests.post(self.generate_url, json=payload, timeout=120)
            r.raise_for_status()
            
            data = r.json().get('response', '{}')
            data_json = json.loads(data)

            decision = (data_json.get('decision') or 'HOLD').upper()
            
            # Robust quantity parsing
            raw_qty = data_json.get('quantity_pct')
            quantity = float(raw_qty) if raw_qty is not None else 0.0
            
            reasoning = data_json.get('reasoning') or 'No reasoning provided.'
            rule_citation = data_json.get('rule_citation') or 'No specific rule cited.'
            kb_update = data_json.get('knowledge_update')
            
            raw_add = data_json.get('add_symbols')
            add_syms = raw_add if isinstance(raw_add, list) else []
            
            raw_remove = data_json.get('remove_symbols')
            remove_syms = raw_remove if isinstance(raw_remove, list) else []

            thinking_cycles = int(data_json.get('thinking_cycles_requested', 0))
            thinking_cycles = max(0, min(5, thinking_cycles))

            return decision, reasoning, quantity, add_syms, remove_syms, kb_update, thinking_cycles, rule_citation
            
        except Exception as e:
            print(f"ERROR: AI Brain failed to regulate: {e}")
            traceback.print_exc()
            return "HOLD", str(e), 0.0, [], [], None, 0, "ERROR: Execution failed."
    
    def _get_hardcoded_prompt_template(self):
        """Fallback method to return the hardcoded prompt template."""
        return """
    ROLE: You are an Institutional-Grade Algorithmic Quant Executor on behalf of the USER.
    Your goal is not just to "trade", but to execute VALIDATED patterns from your Knowledge Base with extreme precision.
    You ignore market noise and only act when a specific core strategy or auto-learned quant rule is strictly triggered.
    CRITICAL: Implement the SNOWBALL STRATEGY - compound wealth aggressively by reinvesting ALL profits immediately.

    --- TRADING LAWS (KNOWLEDGE BASE) ---
    {knowledge_base}

    --- DATA STREAMS ---
    1. CURRENT PORTFOLIO & TRACKED SYMBOLS ({tracked_symbols_str}):
    {wallet_text}
    - Total Portfolio Worth: ${total_portfolio_worth:.2f} USD
    - Available USDT: ${usdt_balance:.2f}
    - Minimum Buy Notional: ${min_notional:.2f} USD

    {detailed_balances_prompt_section}

    {trade_summary}

    2. MARKET SIGNALS:
    {market_summary}
    Live Price: {live_price}
    Order Book: {order_book}
    ---
    HYBRID INTELLIGENCE:
    [ML STATISTICAL SCORE]: {ml_insight}
    [SENTIMENT SCORE]: {sent_val} (Range -1 to +1)
    [HISTORICAL TRENDS]: {historical_trends}
    [USER PREFERENCES]: {user_preferences}
    

    {recursive_history}

    --- QUANT REASONING PROCESS (Chain-of-Thought) ---
    1.  **Rule Match:** Scan the 'Auto-Learned Insights' and 'Core Strategies' above. Does the current market data strictly match ANY specific rule?
    2.  **Filter Noise:** Is this move just noise? If yes, HOLD. Do not "chase" unless a rule dictates.
    3.  **Risk Audit:** Check your 'Risk Management Rules'. Does this trade violate position sizing or capital preservation?
    4.  **Meta-Review:** If you have previous thoughts, how have the new data points changed your outlook?
    5.  **Final Execution:** Select decision, quantify precision, and cite the specific rule you are following.

    RESPONSE FORMAT (STRICT JSON ONLY):
    {{
      "reasoning": "Detailed technical analysis referencing specific data points...",
      "rule_citation": "Exact quote or date of the [Auto-Learned] or [Core] rule being applied",
      "decision": "BUY",
      "quantity_pct": 0.0,
      "thinking_cycles_requested": 0,
      "knowledge_update": "A single specific new insight or strategy you've learned. If NO new insight, use null.",
      "add_symbols": [],
      "remove_symbols": []
    }}
    
    QUANTITY RULE: quantity_pct must be 0.0 to 1.0 (representing 0% to 100% of available USDT). Ensure that quantity_pct * available USDT >= minimum buy notional. If the calculated amount would be below the minimum, increase quantity_pct to meet the minimum or HOLD if impossible.
    STRICTNESS: If no specific rule from the Knowledge Base qualifies, you MUST HOLD.
    PROFIT-TAKING: Actively look for opportunities to SELL and secure profits. Even small profits ($1+) are valuable. Consider selling partial positions (e.g., 30-50%) to lock in gains while letting the rest run.
    SELLING TRIGGERS: You MUST SELL under the following conditions:
    - If the current price is 1.5% below the entry price (stop-loss).
    - If the profit exceeds $1 (take profit).
    - If RSI > 70 (overbought conditions).
    - If the price drops below EMA20 (trend reversal).
    - If the Bid/Ask ratio < 0.3 (strong sell pressure).
    SNOWBALL STRATEGY: After securing profits, immediately reinvest the capital to compound wealth. The goal is to grow the portfolio exponentially through frequent reinvestment of small gains.
    CAPITAL UTILIZATION: Maintain high capital efficiency by keeping >90% of available USDT invested when market conditions are favorable per the Knowledge Base rules.
    """

    def get_sentiment_score(self, symbol, headlines):
        """Asks AI to score the sentiment of a list of headlines."""
        prompt = f"""
    ROLE: Financial Sentiment Analyst.
    TASK: Analyze the following headlines for {symbol} and provide a sentiment score.
    
    HEADLINES:
    {headlines}
    
    RULES:
    1. Score must be between -1.0 (Extreme Bearish/Fear) and +1.0 (Extreme Bullish/Greed).
    2. 0.0 is Neutral.
    3. Return ONLY the number. No text.
    
    SCORE:
    """
        try:
            payload = {
                "model": self.model_name, "prompt": prompt, "stream": False,
                "options": { "temperature": 0.0, "num_predict": 10 }
            }
            r = requests.post(self.generate_url, json=payload, timeout=30)
            r.raise_for_status()
            
            score_text = r.json().get('response', '0.0').strip()
            # Extract only the first number found
            import re
            match = re.search(r"(-?\d+\.?\d*)", score_text)
            if match:
                return float(match.group(1))
            return 0.0
        except Exception as e:
            print(f"Error scoring sentiment: {e}")
            return 0.0

    def summarize_expertise(self, title, content, url):
        """Distills professional expertise into a machine-executable algorithmic rule."""
        prompt = f"""
ROLE: Autonomous Algorithmic Quant.
TASK: Analyze the following content and extract a SINGLE high-standard trading rule or technical principle suitable for an automated bot.

SOURCE TITLE: {title}
SOURCE CONTENT:
{content[:10000]}

CRITICAL RULES FOR ALGORITHMIC BOT:
1. QUANTIFIABLE & ARCHITECTURAL: Extract specific numbers (e.g., "RSI > 70") OR specific architectural principles (e.g., "Use a 1.5x ATR-based dynamic stop-loss to account for volatility clustering").
2. ACADEMIC INSIGHT: If the source is an academic paper (arXiv, etc.), extract the core "Statistical Edge" or "Logical Hypothesis" mentioned (e.g., "Volume-weighted average price (VWAP) cross-overs are only valid when volatility is in the lower 25th percentile").
3. NO DISCRETION: Ignore "gut feelings" or manual market analysis.
4. FORMAT: Output only the rule (e.g., "[Quant Rule]: On BTCUSDT, if H4 EMA20 crosses above EMA50, enter long only if Volume is 1.5x above 20-period average.")
5. FILTER: Return "null" if the content is generic, marketing, or a landing page.

RESPONSE:
"""
        try:
            payload = {
                "model": self.model_name, "prompt": prompt, "stream": False,
                "options": { "temperature": 0.3, "num_predict": 150 }
            }
            r = requests.post(self.generate_url, json=payload, timeout=60)
            r.raise_for_status()
            
            summary = r.json().get('response', '').strip()
            # Robust check for both new and legacy tags
            if any(tag in summary for tag in ["[Quant Rule]", "[High-Standard Rule]"]):
                # Split at the first instance of ']:' or 'Rule]'
                if "]:" in summary:
                    return summary.split("]:")[-1].strip()
                return summary.split("]")[-1].strip()
            return "null"
        except Exception as e:
            print(f"Error distilling expertise: {e}")
            return "null"
    def generate_research_queries(self):
        """Asks AI to identify knowledge gaps and suggest research queries."""
        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                knowledge_base = f.read()
        except Exception:
            knowledge_base = "Empty knowledge base."

        prompt = f"""
ROLE: Autonomous Algorithmic Quant.
TASK: Analyze your Knowledge Base and generate 5 search queries to find specialized algorithmic, mathematical, or code-based trading strategies to improve your Bot's logic.

KNOWLEDGE BASE:
{knowledge_base[:3000]}

RULES FOR QUANT SEARCH:
1. FOCUS: Focus on "algorithmic", "quant", "python trading", "statistical arbitrage", "automated market making", and "machine learning finance".
2. DEPTH: Search for papers, whitepapers, or technical blogs (.pdf or technical articles).
3. EXECUTABLE: Queries must target logic that can be encoded into a Python bot (e.g., "vectorized backtesting strategies for mean reversion").
4. FORMAT: Return ONLY a JSON list of 5 strings.

FORMAT:
["query 1", "query 2", "query 3", "query 4", "query 5"]
"""
        try:
            payload = {
                "model": self.model_name, "prompt": prompt, "stream": False, "format": "json",
                "options": { "temperature": 0.5, "num_predict": 200 }
            }
            r = requests.post(self.generate_url, json=payload, timeout=60)
            r.raise_for_status()
            
            response_text = r.json().get('response', '[]')
            
            # Robust JSON Extraction: Find the first [ and last ]
            import re
            match = re.search(r"(\[.*\])", response_text, re.DOTALL)
            if match:
                clean_json = match.group(1)
                queries = json.loads(clean_json)
                if isinstance(queries, list) and len(queries) > 0:
                    return queries
            
            return []
        except Exception as e:
            log_pid(f"Error generating research queries: {e}")
            return []
