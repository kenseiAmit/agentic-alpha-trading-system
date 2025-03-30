"""PydanticAI-based trading agents with enhanced type safety and structured responses"""

import os
import certifi
import pandas as pd
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
from pydantic_ai import Agent, RunContext

# Configure SSL certificate handling for secure sandboxed requests
os.environ["SSL_CERT_FILE"] = certifi.where()

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import Config
from models.trading_models import (
    MarketAnalysisResponse, TradingDecision, SupervisorDecision,
    ComplianceResponse, TradingSignal, RiskLevel
)
from tools.pydantic_market_tools import (
    get_stock_data, calculate_fibonacci_levels, 
    analyze_market_sentiment, check_regulation_m_compliance
)
from tools.pydantic_storage_tools import (
    save_trading_decision, save_audit_entry, get_audit_trail,
    get_trading_decisions_summary, analyze_decision_patterns
)

# This is another way to maintain state in the backend of the program.
class Dependencies(BaseModel):
    """Dependencies for all agents"""
    symbol: Optional[str] = None
    user_context: Optional[str] = None
    data: Optional[pd.DataFrame] = None 

    class Config:
        arbitrary_types_allowed = True

class PydanticTradingAgentSystem:
    """Advanced trading agent system using PydanticAI framework with structured responses"""
    
    def __init__(self, use_openai: bool = True):
        """Initialize the multi-agent trading system with PydanticAI"""
        try:
            # Set OpenAI API Key and OpenAI-compatible base URL
            api_key = os.environ.get("OPENAI_API_KEY") or getattr(Config, "OPENAI_API_KEY", "")
            if api_key and api_key != "your_openai_api_key_here":
                os.environ["OPENAI_API_KEY"] = api_key
            
            base_url = os.environ.get("OPENAI_BASE_URL") or getattr(Config, "OPENAI_BASE_URL", "https://api.openai.com/v1")
            if base_url:
                os.environ["OPENAI_BASE_URL"] = base_url

            if use_openai and api_key and api_key != "your_openai_api_key_here":
                self.model_name = "openai:gpt-4o"
            else:
                # Check if we have Anthropic key from config or env
                anthropic_key = os.environ.get("ANTHROPIC_API_KEY") or getattr(Config, "ANTHROPIC_API_KEY", "")
                if anthropic_key and anthropic_key != "your_anthropic_api_key_here":
                    self.model_name = "anthropic:claude-sonnet-4-20250514"
                    os.environ["ANTHROPIC_API_KEY"] = anthropic_key
                else:
                    self.model_name = "openai:gpt-4o"
        except Exception as e:
            print(f"Model initialization issue: {e}")
            self.model_name = "openai:gpt-4o"
        
        # Create specialized trading agents
        self.agents = self._create_agents()
        
    def _create_agents(self):
        """Create specialized trading agents with PydanticAI"""
        
        # 1. Market Data Analyst Agent
        market_agent = Agent(
            model=self.model_name,
            deps_type=Dependencies,
            output_type=MarketAnalysisResponse
        )
        
        @market_agent.system_prompt
        def market_system_prompt(ctx: RunContext[Dependencies]) -> str:
            return f"""You are a Market Data Analyst specializing in technical analysis and market sentiment for {ctx.deps.symbol}.
            
            Your role:
            - Analyze stock data, technical indicators, and market trends
            - Calculate Fibonacci levels and sentiment analysis  
            - Provide clear, data-driven market insights
            - Use available tools to fetch and analyze real market data
            
            Always provide structured analysis with confidence scores and specific recommendations."""
        
        @market_agent.tool
        def get_market_data(ctx: RunContext[Dependencies], period: str = "1mo") -> str:
            """Get comprehensive stock data with technical indicators"""
            stock_data = get_stock_data(ctx.deps.symbol, period, data=ctx.deps.data)
            return f"Stock data retrieved: {stock_data.model_dump_json()}"
        
        @market_agent.tool  
        def get_fibonacci_analysis(ctx: RunContext[Dependencies], lookback_days: int = 20) -> str:
            """Calculate Fibonacci retracement levels and trading signals"""
            fib_data = calculate_fibonacci_levels(ctx.deps.symbol, lookback_days)
            return f"Fibonacci analysis: {fib_data.model_dump_json()}"
        
        @market_agent.tool
        def get_sentiment_analysis(ctx: RunContext[Dependencies], timeframe: str = "3d") -> str:
            """Analyze market sentiment using price action and volume"""
            sentiment_data = analyze_market_sentiment(ctx.deps.symbol, timeframe)
            return f"Sentiment analysis: {sentiment_data.model_dump_json()}"
        
        # 2. Strategy & Trading Agent
        strategy_agent = Agent(
            model=self.model_name,
            deps_type=Dependencies,
            output_type=TradingDecision
        )
        
        @strategy_agent.system_prompt
        def strategy_system_prompt(ctx: RunContext[Dependencies]) -> str:
            return f"""You are a Strategy Agent specializing in trading strategy development and signal generation for {ctx.deps.symbol}.
            
            Your role:
            - Develop comprehensive trading strategies using technical analysis
            - Generate buy/sell/hold signals with confidence scores
            - Provide specific entry/exit points and position sizing
            - Save trading decisions for audit purposes
            
            Always provide actionable trading recommendations with clear rationale."""
        
        @strategy_agent.tool
        def get_market_data(ctx: RunContext[Dependencies], period: str = "1mo") -> str:
            """Get comprehensive stock data with technical indicators"""
            stock_data = get_stock_data(ctx.deps.symbol, period, data=ctx.deps.data)
            return f"Stock data retrieved: {stock_data.model_dump_json()}"
        
        @strategy_agent.tool
        def get_fibonacci_analysis(ctx: RunContext[Dependencies], lookback_days: int = 20) -> str:
            """Calculate Fibonacci retracement levels and trading signals"""  
            fib_data = calculate_fibonacci_levels(ctx.deps.symbol, lookback_days)
            return f"Fibonacci analysis: {fib_data.model_dump_json()}"
        
        @strategy_agent.tool
        def save_strategy_decision(ctx: RunContext[Dependencies], decision: str, confidence: float) -> str:
            """Save trading decision to audit trail"""
            return save_trading_decision(ctx.deps.symbol, decision, confidence, "strategy_agent")
        
