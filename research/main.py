#!/usr/bin/env python3
"""
Main script for prompt engineering research.
This script provides a flexible environment to experiment with different prompts,
models, and configurations for the trading bot.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.dev")

# Add bot_logic to the Python path
import sys
import os

# Get the absolute path to bot_logic directory
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
bot_logic_path = os.path.join(project_root, "bot_logic")

if bot_logic_path not in sys.path:
    sys.path.append(bot_logic_path)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Debug: Print the Python path
logger.info(f"Python path: {sys.path}")

def analyze_trading_bot_prompt():
    """Analyze and optimize the trading bot's prompt."""
    logger.info("Analyzing trading bot prompt...")
    
    # Load the current prompt structure
    # Use relative import to ensure bot_logic is found
    import importlib.util
    
    # Try to import using the path we added
    try:
        from bot_logic.strategy import AIStrategy
    except ImportError:
        # Fallback: manually load the module
        strategy_path = os.path.join(bot_logic_path, "strategy.py")
        spec = importlib.util.spec_from_file_location("bot_logic.strategy", strategy_path)
        strategy_module = importlib.util.module_from_spec(spec)
        sys.modules["bot_logic.strategy"] = strategy_module
        spec.loader.exec_module(strategy_module)
        AIStrategy = strategy_module.AIStrategy
    
    # Initialize the strategy to access the prompt
    strategy = AIStrategy()
    
    # Example data for prompt generation
    current_tracked_symbols = ["BTCUSDT", "ETHUSDT"]
    market_summary = "Market is showing signs of recovery."
    full_wallet_info = {
        "text": "Portfolio includes BTC and ETH.",
        "balances": [{"asset": "USDT", "free": "1000.0"}],
        "total_usd": 1000.0,
        "detailed_balances_list": [{"asset": "BTC", "balance": 0.1, "usd_value": 500.0}]
    }
    order_book = "Bid: 50000, Ask: 50010"
    live_data = {"price": "50000"}
    trade_summary = "No recent trades."
    ml_score = 0.7
    sentiment_score = 0.5
    min_notional = 5.0
    historical_trends = "Historical data shows upward trend."
    user_preferences = "User prefers low-risk trades."
    
    # Generate the prompt
    decision, reasoning, quantity, add_syms, remove_syms, kb_update, thinking_cycles, rule_citation = strategy.ask_ai_opinion(
        current_tracked_symbols, market_summary, full_wallet_info, order_book, live_data, trade_summary,
        ml_score, None, sentiment_score, min_notional, historical_trends, user_preferences
    )
    
    logger.info(f"Decision: {decision}")
    logger.info(f"Reasoning: {reasoning}")
    logger.info(f"Quantity: {quantity}")
    
    # Analyze the reasoning and decision to identify areas for prompt improvement
    prompt_optimizations = analyze_reasoning_and_decision(reasoning, decision, rule_citation)
    
    # Apply the optimizations to the prompt
    if prompt_optimizations:
        logger.info("Applying prompt optimizations...")
        apply_prompt_optimizations(strategy, prompt_optimizations)
    else:
        logger.info("No prompt optimizations identified.")
    
def main():
    """Main function to run prompt engineering research."""
    logger.info("Starting prompt engineering research environment...")
    
    # Analyze and optimize the trading bot's prompt
    analyze_trading_bot_prompt()
    

def analyze_reasoning_and_decision(reasoning, decision, rule_citation):
    """Analyze the reasoning and decision to identify areas for prompt improvement."""
    logger.info("Analyzing reasoning and decision for prompt optimizations...")
    
    # Enhanced analysis with more sophisticated criteria
    optimizations = []
    
    # Analyze the quality of reasoning
    reasoning_lower = reasoning.lower()
    
    # Check if reasoning could be more specific about rule application
    if "rule" in reasoning_lower and "specifically" not in reasoning_lower and "exactly" not in reasoning_lower:
        optimizations.append({
            "type": "clarity",
            "description": "Reasoning mentions rules but could be more specific about exact rule application. Enhance prompt to require more precise rule citation.",
            "action": "Update QUANT REASONING PROCESS to require explicit rule text citation and specific condition matching."
        })
    
    # Check if sentiment analysis could be more detailed
    if "sentiment" in reasoning_lower and ("score" not in reasoning_lower or "bullish" not in reasoning_lower):
        optimizations.append({
            "type": "data_utilization",
            "description": "Sentiment is mentioned but not quantified. Enhance prompt to require specific sentiment score analysis.",
            "action": "Update HYBRID INTELLIGENCE section to provide more detailed sentiment score interpretation guidance."
        })
    
    # Check if ML confidence could be better utilized
    if "ml" in reasoning_lower and "confidence" in reasoning_lower and "statistical" not in reasoning_lower:
        optimizations.append({
            "type": "data_utilization",
            "description": "ML confidence is mentioned but not tied to statistical analysis. Enhance prompt to connect ML scores to specific trading rules.",
            "action": "Update CRITICAL ANALYSIS section to provide specific thresholds for ML score interpretation."
        })
    
    # Check if risk analysis could be more comprehensive
    if "risk" not in reasoning_lower and decision == "BUY":
        optimizations.append({
            "type": "risk_analysis",
            "description": "Buy decision made without explicit risk analysis. Enhance prompt to require risk assessment for all trades.",
            "action": "Update QUANT REASONING PROCESS to include explicit risk percentage calculation and position sizing justification."
        })
    
    # Check if the reasoning could benefit from more historical context
    if "historical" not in reasoning_lower and "trend" in reasoning_lower:
        optimizations.append({
            "type": "context_enhancement",
            "description": "Trends are mentioned but not placed in historical context. Enhance prompt to require historical pattern analysis.",
            "action": "Update prompt to include specific guidance on using historical trends to confirm current patterns."
        })
    
    # Check if quantity justification could be more detailed
    if "quantity" in reasoning_lower and "calculat" not in reasoning_lower:
        optimizations.append({
            "type": "quantity_justification",
            "description": "Quantity is mentioned but calculation not explained. Enhance prompt to require explicit quantity calculation reasoning.",
            "action": "Update QUANTITY RULE section to require step-by-step quantity calculation justification."
        })
    
    return optimizations

def apply_prompt_optimizations(strategy, optimizations):
    """Apply the identified optimizations to the prompt."""
    logger.info("Applying prompt optimizations...")
    
    # Import the prompt templates module
    try:
        # Try direct import first
        from bot_logic.prompt_templates import get_current_prompt_template, update_prompt_template
        current_template = get_current_prompt_template()
        logger.info("Successfully imported bot_logic.prompt_templates module")
    except ImportError as e:
        logger.error(f"Could not import prompt_templates module: {e}")
        
        # Try alternative import methods for different environments
        try:
            # Method 1: Import from parent directory
            import sys
            import os
            
            # Add current directory to path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            
            # Try adding bot_logic directory explicitly
            bot_logic_path = os.path.join(parent_dir, "bot_logic")
            if os.path.exists(bot_logic_path) and bot_logic_path not in sys.path:
                sys.path.append(bot_logic_path)
                
            # Try importing again
            from bot_logic.prompt_templates import get_current_prompt_template, update_prompt_template
            current_template = get_current_prompt_template()
            logger.info("Successfully imported bot_logic.prompt_templates after path adjustment")
            
        except ImportError as e2:
            logger.error(f"Still could not import after path adjustment: {e2}")
            
            # Method 2: Try importing as a module from the parent
            try:
                # Navigate to parent directory and try relative import
                original_path = sys.path.copy()
                sys.path.insert(0, parent_dir)
                
                import bot_logic.prompt_templates
                get_current_prompt_template = bot_logic.prompt_templates.get_current_prompt_template
                update_prompt_template = bot_logic.prompt_templates.update_prompt_template
                current_template = get_current_prompt_template()
                logger.info("Successfully imported bot_logic.prompt_templates using module import")
                
            except (ImportError, AttributeError) as e3:
                logger.error(f"Module import also failed: {e3}")
                logger.error("All import methods failed. Prompt optimization will not be applied.")
                return
    
    # Apply each optimization to the prompt template
    updated_template = current_template
    
    for optimization in optimizations:
        logger.info(f"Applying optimization: {optimization['description']}")
        
        # Update the knowledge base with more specific rules
        if optimization["type"] == "rule_citation":
            new_rule = "[Auto-Learned 2026-01-06]: If the ML Statistical Confidence score is above 70% and the sentiment score is positive, consider a BUY signal."
            strategy.update_knowledge_base(new_rule)
            logger.info(f"Updated knowledge base with new rule: {new_rule}")
        
        # Enhance data utilization in the prompt
        elif optimization["type"] == "data_utilization":
            if "HYBRID INTELLIGENCE:" in updated_template:
                # Check if CRITICAL ANALYSIS already exists
                if "CRITICAL ANALYSIS:" not in updated_template:
                    enhanced_section = """HYBRID INTELLIGENCE:
[ML STATISTICAL SCORE]: {ml_insight}
[SENTIMENT SCORE]: {sent_val} (Range -1 to +1)
[HISTORICAL TRENDS]: {historical_trends}
[USER PREFERENCES]: {user_preferences}

CRITICAL ANALYSIS:
- If ML Statistical Confidence > 70% AND Sentiment Score > +0.3, this indicates a strong bullish signal.
- If ML Statistical Confidence < 30% AND Sentiment Score < -0.3, this indicates a strong bearish signal.
- Consider the historical trends and user preferences as additional confirmation factors.
- Always quantify sentiment impact: +0.3 to +0.5 = Moderate Bullish, +0.5 to +0.8 = Strong Bullish, > +0.8 = Extreme Bullish"""
                    
                    # Replace the HYBRID INTELLIGENCE section
                    start_idx = updated_template.find("HYBRID INTELLIGENCE:")
                    end_idx = updated_template.find("\n\n", start_idx + 20)
                    if end_idx != -1:
                        updated_template = updated_template[:start_idx] + enhanced_section + updated_template[end_idx:]
                        logger.info("Enhanced HYBRID INTELLIGENCE section with CRITICAL ANALYSIS")
                else:
                    # If CRITICAL ANALYSIS exists, enhance it further
                    critical_start = updated_template.find("CRITICAL ANALYSIS:")
                    if critical_start != -1:
                        # Find the end of the critical analysis section
                        critical_end = updated_template.find("\n\n", critical_start + 20)
                        if critical_end != -1:
                            # Add sentiment quantification guidance
                            sentiment_guidance = "\n- Always quantify sentiment impact: +0.3 to +0.5 = Moderate Bullish, +0.5 to +0.8 = Strong Bullish, > +0.8 = Extreme Bullish"
                            updated_template = updated_template[:critical_end] + sentiment_guidance + updated_template[critical_end:]
                            logger.info("Added sentiment quantification guidance to CRITICAL ANALYSIS")
        
        # Enhance clarity in the reasoning process
        elif optimization["type"] == "clarity":
            if "QUANT REASONING PROCESS" in updated_template:
                # Check if ADDITIONAL GUIDANCE already exists
                if "ADDITIONAL GUIDANCE:" not in updated_template:
                    enhanced_reasoning = """--- QUANT REASONING PROCESS (Chain-of-Thought) ---
1.  **Rule Match:** Scan the 'Auto-Learned Insights' and 'Core Strategies' above. Does the current market data strictly match ANY specific rule? Be explicit about which rule is matched and quote the exact rule text.
2.  **Filter Noise:** Is this move just noise? If yes, HOLD. Do not "chase" unless a rule dictates. Provide specific evidence for why this is or isn't noise, including statistical measures.
3.  **Risk Audit:** Check your 'Risk Management Rules'. Does this trade violate position sizing or capital preservation? Calculate the exact risk percentage and explain your position sizing rationale.
4.  **Meta-Review:** If you have previous thoughts, how have the new data points changed your outlook? Be specific about what changed and why, referencing specific data points.
5.  **Final Execution:** Select decision, quantify precision, and cite the specific rule you are following. Include the exact rule text in your citation and explain how each condition is met.

ADDITIONAL GUIDANCE:
- Always prioritize rules with the highest statistical confidence and strongest sentiment alignment.
- When multiple rules could apply, choose the one with the most specific conditions that are met and explain your choice.
- If no rule applies but market conditions are exceptionally strong, you may consider a discretionary trade but must explicitly justify why with reference to specific market data.
- For every decision, provide a confidence score (0-100%) based on how well the market data matches the rule conditions."""
                    
                    # Replace the QUANT REASONING PROCESS section
                    start_idx = updated_template.find("--- QUANT REASONING PROCESS")
                    end_idx = updated_template.find("\n\nRESPONSE FORMAT", start_idx)
                    if end_idx != -1:
                        updated_template = updated_template[:start_idx] + enhanced_reasoning + updated_template[end_idx:]
                        logger.info("Enhanced QUANT REASONING PROCESS with ADDITIONAL GUIDANCE")
                else:
                    # If ADDITIONAL GUIDANCE exists, enhance it further
                    guidance_start = updated_template.find("ADDITIONAL GUIDANCE:")
                    if guidance_start != -1:
                        # Find the end of the guidance section
                        guidance_end = updated_template.find("\n\n", guidance_start + 20)
                        if guidance_end != -1:
                            # Add confidence score requirement
                            confidence_requirement = "\n- For every decision, provide a confidence score (0-100%) based on how well the market data matches the rule conditions."
                            updated_template = updated_template[:guidance_end] + confidence_requirement + updated_template[guidance_end:]
                            logger.info("Added confidence score requirement to ADDITIONAL GUIDANCE")
        
        # Add risk analysis requirements
        elif optimization["type"] == "risk_analysis":
            if "QUANT REASONING PROCESS" in updated_template:
                # Find the Risk Audit step and enhance it
                risk_start = updated_template.find("3.  **Risk Audit:**")
                if risk_start != -1:
                    # Find the end of this step
                    risk_end = updated_template.find("\n4.", risk_start)
                    if risk_end != -1:
                        enhanced_risk = """3.  **Risk Audit:** Check your 'Risk Management Rules'. Does this trade violate position sizing or capital preservation? Calculate the exact risk percentage and explain your position sizing rationale. Include:
    - Maximum potential loss based on stop-loss placement
    - Position size as percentage of total portfolio
    - Risk-reward ratio calculation
    - How this trade fits within overall portfolio risk limits"""
                        
                        updated_template = updated_template[:risk_start] + enhanced_risk + updated_template[risk_end:]
                        logger.info("Enhanced Risk Audit step with detailed risk analysis requirements")
        
        # Add historical context requirements
        elif optimization["type"] == "context_enhancement":
            if "QUANT REASONING PROCESS" in updated_template:
                # Add historical context requirement to the reasoning process
                reasoning_start = updated_template.find("--- QUANT REASONING PROCESS")
                if reasoning_start != -1:
                    # Find the end of the reasoning process section
                    reasoning_end = updated_template.find("\n\nRESPONSE FORMAT", reasoning_start)
                    if reasoning_end != -1:
                        historical_context = """

HISTORICAL CONTEXT REQUIREMENT:
- For any trend-based decision, analyze how the current pattern compares to historical examples
- Reference specific historical dates/periods where similar patterns occurred and their outcomes
- Explain why the current situation is similar to or different from historical precedents"""
                        
                        updated_template = updated_template[:reasoning_end] + historical_context + updated_template[reasoning_end:]
                        logger.info("Added HISTORICAL CONTEXT REQUIREMENT to reasoning process")
        
        # Add quantity justification requirements
        elif optimization["type"] == "quantity_justification":
            if "QUANTITY RULE:" in updated_template:
                # Enhance the quantity rule section
                quantity_start = updated_template.find("QUANTITY RULE:")
                if quantity_start != -1:
                    # Find the end of the quantity rule section
                    quantity_end = updated_template.find("\nSTRICTNESS:", quantity_start)
                    if quantity_end != -1:
                        enhanced_quantity = """QUANTITY RULE: quantity_pct must be 0.0 to 1.0 (representing 0% to 100% of available USDT). Ensure that quantity_pct * available USDT >= minimum buy notional. If the calculated amount would be below the minimum, increase quantity_pct to meet the minimum or HOLD if impossible.

QUANTITY JUSTIFICATION REQUIREMENT:
- Explain your quantity calculation step-by-step
- Show the mathematical calculation: (available USDT * quantity_pct) = position size
- Justify why this position size is appropriate given the risk-reward profile
- Explain how this quantity fits within your overall portfolio diversification strategy"""
                        
                        updated_template = updated_template[:quantity_start] + enhanced_quantity + updated_template[quantity_end:]
                        logger.info("Enhanced QUANTITY RULE with detailed justification requirements")
    
    # Update the prompt template if changes were made
    if updated_template != current_template:
        update_prompt_template(updated_template)
        logger.info("Prompt template updated successfully")
    else:
        logger.info("No changes made to prompt template")

if __name__ == "__main__":
    main()