#!/usr/bin/env python3
"""
Dynamic prompt templates for the trading bot.
This module allows the researcher to update and improve prompt templates.
"""

# Base prompt template
BASE_PROMPT_TEMPLATE = """
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

# File to store the current prompt template
PROMPT_TEMPLATE_FILE = "bot_logic/current_prompt_template.txt"

# Current active prompt template (starts as base template)
CURRENT_PROMPT_TEMPLATE = BASE_PROMPT_TEMPLATE

# Load the prompt template from file if it exists
def _load_prompt_template():
    """Load the prompt template from file."""
    global CURRENT_PROMPT_TEMPLATE
    try:
        with open(PROMPT_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            CURRENT_PROMPT_TEMPLATE = f.read()
        print(f"Loaded prompt template from file. Length: {len(CURRENT_PROMPT_TEMPLATE)} characters")
    except FileNotFoundError:
        # If file doesn't exist, use the base template
        CURRENT_PROMPT_TEMPLATE = BASE_PROMPT_TEMPLATE
        print("No saved prompt template found. Using base template.")
    except Exception as e:
        print(f"Error loading prompt template: {e}")
        CURRENT_PROMPT_TEMPLATE = BASE_PROMPT_TEMPLATE

# Load the prompt template at module import time
_load_prompt_template()

def get_current_prompt_template():
    """Get the current active prompt template."""
    return CURRENT_PROMPT_TEMPLATE

def update_prompt_template(new_template):
    """Update the current active prompt template and save to file."""
    global CURRENT_PROMPT_TEMPLATE
    CURRENT_PROMPT_TEMPLATE = new_template
    
    # Save the updated template to file
    try:
        with open(PROMPT_TEMPLATE_FILE, 'w', encoding='utf-8') as f:
            f.write(new_template)
        print(f"Prompt template updated and saved to file. New template length: {len(new_template)} characters")
    except Exception as e:
        print(f"Error saving prompt template: {e}")

def reset_prompt_template():
    """Reset the prompt template to the base template."""
    global CURRENT_PROMPT_TEMPLATE
    CURRENT_PROMPT_TEMPLATE = BASE_PROMPT_TEMPLATE
    
    # Save the reset template to file
    try:
        with open(PROMPT_TEMPLATE_FILE, 'w', encoding='utf-8') as f:
            f.write(BASE_PROMPT_TEMPLATE)
        print("Prompt template reset to base template and saved to file")
    except Exception as e:
        print(f"Error saving reset prompt template: {e}")