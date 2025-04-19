import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from storage.csv_storage import CSVStorage
from data.market_data import MarketData
from agents.pydantic_agents import PydanticTradingAgentSystem, Dependencies

# Initialize components
storage = CSVStorage()
market_data = MarketData()


# Initialize PydanticAI system
@st.cache_resource
def get_pydantic_agents():
    return PydanticTradingAgentSystem(use_openai=True)

def extract_readable_text(analysis_obj, field_name, field_name2):
    if hasattr(analysis_obj, field_name):
        return getattr(analysis_obj, field_name)
    elif hasattr(analysis_obj, field_name2):
        return getattr(analysis_obj, field_name2)
    else:
        return str(analysis_obj)
            
# Individual Agent Functions
def run_market_analyst():
    """Run Market Analyst Agent individually"""
    try:
        pydantic_system = get_pydantic_agents()
        print(f"📈 Running Market Analyst for {st.session_state.symbol}...")
        
        #TODO:  This is optional.  We collect three types of information in the market analysis call and preserve
        # them in the session state for later use by other agents.  Right now this is convenient but 
        # can you change the code so that the strategy agent and risk manager do not depend on the market analysis call
        # but instead run on their own calls.  
        market_results = pydantic_system.run_market_analysis(st.session_state.symbol, st.session_state.data)
        
        if "error" in market_results:
            return {"error": market_results["error"]}
        
        market_analysis = market_results.get("market_analysis", {}).get("analysis", "No market analysis available")
        
        market_text = extract_readable_text(market_analysis, "market_analysis", "analysis")
        
        return {
            "analysis": market_text,
            "confidence": 0.8,
            "raw_results": market_results,
            "timestamp": pd.Timestamp.now()
        }
    except Exception as e:
        return {"error": str(e)}

def run_strategy_agent(symbol=None):
    """Run Strategy Agent individually - Requires Market Analyst to run first"""
    if symbol is None:
        symbol = st.session_state.symbol
    
    # Check if Market Analyst agent has already run in session
    if 'market_analysis' not in st.session_state or not st.session_state.market_analysis:
        return {"error": "❌ Market Analyst agent must be run first before Strategy Agent! Order: Market ➔ Strategy ➔ Risk."}
    
    try:
        pydantic_system = get_pydantic_agents()
        print(f"🎯 Running Strategy Agent for {symbol}...")
        data = st.session_state.get('data', None)
        
        # Strategy Agent runs on its own call using get_market_data tool which calls get_stock_data(...)
        strategy_res = pydantic_system.run_strategy_analysis(symbol, data)
        if "error" in strategy_res:
            # Fallback to market_results from session state if available
            if 'market_analysis' in st.session_state and st.session_state.market_analysis and "raw_results" in st.session_state.market_analysis:
                market_results = st.session_state.market_analysis["raw_results"]
                strategy_analysis = market_results.get("strategy_analysis", {}).get("analysis", "No strategy analysis available")
                strategy_text = extract_readable_text(strategy_analysis, "rationale", "rationale")
                confidence = 0.75
            else:
                return {"error": strategy_res["error"]}
        else:
            strategy_data = strategy_res.get("strategy_analysis", strategy_res)
            strategy_analysis = strategy_data.get("analysis", "No strategy analysis available")
            strategy_text = extract_readable_text(strategy_analysis, "rationale", "rationale")
            confidence = strategy_data.get("confidence", 0.75)
        
        return {
            "analysis": strategy_text,
            "confidence": confidence,
            "timestamp": pd.Timestamp.now()
        }
    except Exception as e:
        return {"error": str(e)}

def run_risk_manager(symbol=None):
    """Run Risk Manager Agent individually - Requires Market Analyst and Strategy Agent to run first"""
    if symbol is None:
        symbol = st.session_state.symbol
    
    # Check if Market Analyst and Strategy Agent have already run in session
    missing_agents = []
    if 'market_analysis' not in st.session_state or not st.session_state.market_analysis:
        missing_agents.append("Market Analyst")
    if 'strategy_analysis' not in st.session_state or not st.session_state.strategy_analysis:
        missing_agents.append("Strategy Agent")
    
    if missing_agents:
        return {"error": f"❌ Please run {' and '.join(missing_agents)} first before Risk Manager! Order: Market ➔ Strategy ➔ Risk."}
    
    try:
        pydantic_system = get_pydantic_agents()
        print(f"⚠️ Running Risk Manager for {symbol}...")
        data = st.session_state.get('data', None)
        
        # Risk Manager runs on its own call
        risk_res = pydantic_system.run_risk_analysis(symbol, data)
        if "error" in risk_res:
            if 'market_analysis' in st.session_state and st.session_state.market_analysis and "raw_results" in st.session_state.market_analysis:
                market_results = st.session_state.market_analysis["raw_results"]
                risk_analysis = market_results.get("risk_analysis", {}).get("analysis", "No risk analysis available")
                risk_text = extract_readable_text(risk_analysis, "rationale", "rationale")
                confidence = 0.85
            else:
                return {"error": risk_res["error"]}
        else:
            risk_data = risk_res.get("risk_analysis", risk_res)
            risk_analysis = risk_data.get("analysis", "No risk analysis available")
            risk_text = extract_readable_text(risk_analysis, "rationale", "rationale")
            confidence = risk_data.get("confidence", 0.85)
        
        return {
            "analysis": risk_text,
            "confidence": confidence,
            "timestamp": pd.Timestamp.now()
        }
    except Exception as e:
        return {"error": str(e)}

def run_regulatory_agent(symbol=None):
    """Run Regulatory Agent individually - Requires Market, Strategy, and Risk to run first"""
    if symbol is None:
        symbol = st.session_state.symbol
    
    # Enforce strict order: Market, Strategy, and Risk must run first!
    missing_agents = []
    if 'market_analysis' not in st.session_state or not st.session_state.market_analysis:
        missing_agents.append("Market Analyst")
    if 'strategy_analysis' not in st.session_state or not st.session_state.strategy_analysis:
        missing_agents.append("Strategy Agent")
    if 'risk_analysis' not in st.session_state or not st.session_state.risk_analysis:
        missing_agents.append("Risk Manager")
    
    if missing_agents:
        return {"error": f"❌ Please run {', '.join(missing_agents)} first before Regulatory Agent! Order: Market ➔ Strategy ➔ Risk ➔ Regulatory."}
    
    try:
        pydantic_system = get_pydantic_agents()
        print(f"🏛️ Running Regulatory Agent for {symbol}...")
        
        # Build market results context from preceding completed agents
        if 'market_analysis' in st.session_state and st.session_state.market_analysis and "raw_results" in st.session_state.market_analysis:
            market_results = dict(st.session_state.market_analysis["raw_results"])
        else:
            market_results = {}
        market_results["market_analysis"] = {"analysis": st.session_state.market_analysis.get("analysis", "")}
        market_results["strategy_analysis"] = {"analysis": st.session_state.strategy_analysis.get("analysis", "")}
        market_results["risk_analysis"] = {"analysis": st.session_state.risk_analysis.get("analysis", "")}
            
        regulatory_results = pydantic_system.run_regulatory_compliance(symbol, market_results)
        
        compliance_data = regulatory_results.get("analysis", "No regulatory analysis")
        if hasattr(compliance_data, 'explanation'):
            compliance_text = compliance_data.explanation
            status = compliance_data.compliance_status.value if hasattr(compliance_data.compliance_status, 'value') else str(compliance_data.compliance_status)
            recommendation = compliance_data.recommendation
        else:
            compliance_text = str(compliance_data)
            status = "PROCESSED_BY_PYDANTICAI"
            recommendation = "SEE_AGENT_OUTPUT"
        
        result = {
            "analysis": compliance_text,
            "compliance_status": status,
            "recommendation": recommendation,
            "confidence": 0.9,
            "timestamp": pd.Timestamp.now()
        }
        
        # Save audit entry for regulatory compliance
        storage.save_audit_entry(
            symbol=symbol,
            decision_type="REGULATORY",
            action=recommendation,
            confidence=0.9,
            rationale=compliance_text,
            compliance_status=status
        )
        
        return result
    except Exception as e:
        return {"error": str(e)}

def run_trading_signal_agent(symbol=None):
    """Run Trading Signal Agent individually producing type-safe TradingDecision"""
    if symbol is None:
        symbol = st.session_state.symbol
    
    # Enforce strict order: Market, Strategy, Risk, and Regulatory must run first!
    missing_agents = []
    if 'market_analysis' not in st.session_state or not st.session_state.market_analysis:
        missing_agents.append("Market Analyst")
    if 'strategy_analysis' not in st.session_state or not st.session_state.strategy_analysis:
        missing_agents.append("Strategy Agent")
    if 'risk_analysis' not in st.session_state or not st.session_state.risk_analysis:
        missing_agents.append("Risk Manager")
    if 'regulatory_analysis' not in st.session_state or not st.session_state.regulatory_analysis:
        missing_agents.append("Regulatory Agent")
    
    if missing_agents:
        return {"error": f"❌ Please run {', '.join(missing_agents)} first before Trading Signal Agent!"}
    
    try:
        pydantic_system = get_pydantic_agents()
        print(f"⚡ Running Trading Signal Agent for {symbol}...")
        data = st.session_state.get('data', None)
        signal_results = pydantic_system.run_trading_signal_agent(symbol, data)
        
        if "error" in signal_results:
            return {"error": signal_results["error"]}
            
        decision_obj = signal_results.get("decision")
        if decision_obj is None:
            return {"error": "No trading decision returned by agent"}
            
        decision_val = decision_obj.decision.value if hasattr(decision_obj.decision, 'value') else str(decision_obj.decision)
        risk_val = decision_obj.risk_level.value if hasattr(decision_obj.risk_level, 'value') else str(decision_obj.risk_level)
        
        result = {
            "decision": decision_val,
            "risk_level": risk_val,
            "confidence": decision_obj.confidence,
            "entry_price": decision_obj.entry_price,
            "exit_price": decision_obj.exit_price,
            "position_size_percent": decision_obj.position_size_percent,
            "rationale": decision_obj.rationale,
            "raw_decision": decision_obj,
            "timestamp": pd.Timestamp.now()
        }
        
        storage.save_audit_entry(
            symbol=symbol,
            decision_type="TRADING_SIGNAL",
            action=decision_val,
            confidence=decision_obj.confidence,
            rationale=decision_obj.rationale,
            compliance_status=f"Risk:{risk_val}"
        )
        storage.save_trading_decision(
            symbol=symbol,
            decision=f"SIGNAL:{decision_val} | Risk:{risk_val}",
            confidence=decision_obj.confidence,
            agent_name="trading_signal_agent"
        )
        
        return result
    except Exception as e:
        return {"error": str(e)}

def run_supervisor_agent(symbol=None):
    """Run Supervisor Agent individually - Requires ALL 5 prior agents to run first"""
    if symbol is None:
        symbol = st.session_state.symbol
    
    # Enforce strict order: Check if ALL 5 other agents have run
    missing_agents = []
    if 'market_analysis' not in st.session_state or not st.session_state.market_analysis:
        missing_agents.append("Market Analyst")
    if 'strategy_analysis' not in st.session_state or not st.session_state.strategy_analysis:
        missing_agents.append("Strategy Agent")
    if 'risk_analysis' not in st.session_state or not st.session_state.risk_analysis:
        missing_agents.append("Risk Manager")
    if 'regulatory_analysis' not in st.session_state or not st.session_state.regulatory_analysis:
        missing_agents.append("Regulatory Agent")
    if 'trading_signal_analysis' not in st.session_state or not st.session_state.trading_signal_analysis:
        missing_agents.append("Trading Signal Agent")
    
    if missing_agents:
        return {"error": f"❌ Please run {', '.join(missing_agents)} first - Supervisor needs ALL agent analysis"}
    
    try:
        pydantic_system = get_pydantic_agents()
        print(f"🎯 Running Supervisor Agent for {symbol}...")
        
        # Synthesize analyses from all preceding completed agents
        if 'market_analysis' in st.session_state and st.session_state.market_analysis and "raw_results" in st.session_state.market_analysis:
            all_analysis = dict(st.session_state.market_analysis["raw_results"])
        else:
            all_analysis = {}
        all_analysis["market_analysis"] = {"agent": "market_analyst", "analysis": st.session_state.market_analysis.get("analysis", "")}
        all_analysis["strategy_analysis"] = {"agent": "strategy_agent", "analysis": st.session_state.strategy_analysis.get("analysis", "")}
        all_analysis["risk_analysis"] = {"agent": "risk_manager", "analysis": st.session_state.risk_analysis.get("analysis", "")}
        all_analysis["regulatory_analysis"] = {"agent": "regulatory_agent", "analysis": st.session_state.regulatory_analysis.get("analysis", "")}
        all_analysis["trading_signal_analysis"] = {"agent": "trading_signal_agent", "analysis": f"Decision: {st.session_state.trading_signal_analysis.get('decision')} | Risk: {st.session_state.trading_signal_analysis.get('risk_level')} | Rationale: {st.session_state.trading_signal_analysis.get('rationale')}"}
        
        supervisor_results = pydantic_system.run_supervisor_decision(symbol, all_analysis)
        
        supervisor_data = supervisor_results.get("decision", "No supervisor decision available")
        if hasattr(supervisor_data, 'rationale'):
            decision_signal = supervisor_data.final_decision.value if hasattr(supervisor_data.final_decision, 'value') else str(supervisor_data.final_decision)
            decision_text = f"FINAL DECISION: {decision_signal}\n\nANALYSIS: {supervisor_data.rationale}"
            confidence = supervisor_data.confidence
        else:
            decision_text = str(supervisor_data)
            confidence = supervisor_results.get("confidence", 0.8)
            decision_signal = "HOLD"
        
        result = {
            "analysis": decision_text,
            "decision": decision_signal,
            "confidence": confidence,
            "timestamp": pd.Timestamp.now()
        }
        
        # Save audit entry for supervisor decision
        storage.save_audit_entry(
            symbol=symbol,
            decision_type="SUPERVISOR", 
            action=decision_signal,
            confidence=confidence,
            rationale=decision_text
        )
        
        return result
    except Exception as e:
        return {"error": str(e)}

def save_trade_to_database(symbol):
    """Save all agent results to CSV database when Trade button is clicked"""
    try:
        # Check if supervisor has run (which means all agents should have run)
        if 'supervisor_analysis' not in st.session_state or not st.session_state.supervisor_analysis:
            return "❌ Please run all agents first, especially Supervisor Agent, before executing trade"
        
        # Save each agent's decision to CSV
        if 'market_analysis' in st.session_state and st.session_state.market_analysis:
            storage.save_trading_decision(symbol, "Market Analysis Completed", 
                                        st.session_state.market_analysis['confidence'], 'market_analyst')
        
        if 'strategy_analysis' in st.session_state and st.session_state.strategy_analysis:
            storage.save_trading_decision(symbol, "Strategy Analysis Completed", 
                                        st.session_state.strategy_analysis['confidence'], 'strategy_agent')
        
        if 'risk_analysis' in st.session_state and st.session_state.risk_analysis:
            storage.save_trading_decision(symbol, "Risk Analysis Completed", 
                                        st.session_state.risk_analysis['confidence'], 'risk_manager')
        
        if 'regulatory_analysis' in st.session_state and st.session_state.regulatory_analysis:
            storage.save_trading_decision(symbol, st.session_state.regulatory_analysis['recommendation'], 
                                        st.session_state.regulatory_analysis['confidence'], 'regulatory_agent')
        
        if 'trading_signal_analysis' in st.session_state and st.session_state.trading_signal_analysis:
            sig = st.session_state.trading_signal_analysis
            storage.save_trading_decision(
                symbol,
                f"Signal: {sig['decision']} | Risk: {sig['risk_level']} | Entry: {sig['entry_price']:.2f} | Target: {sig['exit_price']:.2f}",
                sig['confidence'],
                'trading_signal_agent'
            )

        if 'supervisor_analysis' in st.session_state and st.session_state.supervisor_analysis:
            storage.save_trading_decision(symbol, st.session_state.supervisor_analysis['decision'], 
                                        st.session_state.supervisor_analysis['confidence'], 'supervisor')
        
        return f"✅ Trade executed and saved to database for {symbol} at {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
    except Exception as e:
        return f"❌ Error saving trade: {str(e)}"



# Streamlit UI for AI Agent Teaching
st.set_page_config(page_title="AI Agent Hedgefund", layout="wide")

# Initialize session state
if 'signals' not in st.session_state:
    st.session_state.signals = None
if 'trend_analysis' not in st.session_state:
    st.session_state.trend_analysis = None
if 'sentiment_analysis' not in st.session_state:
    st.session_state.sentiment_analysis = None
if 'regulatory_analysis' not in st.session_state:
    st.session_state.regulatory_analysis = None
if 'trading_signal_analysis' not in st.session_state:
    st.session_state.trading_signal_analysis = None
if 'market_analysis' not in st.session_state:
    st.session_state.market_analysis = None
if 'strategy_analysis' not in st.session_state:
    st.session_state.strategy_analysis = None
if 'risk_analysis' not in st.session_state:
    st.session_state.risk_analysis = None
if 'supervisor_analysis' not in st.session_state:
    st.session_state.supervisor_analysis = None
if 'decision' not in st.session_state:
    st.session_state.decision = None
if 'symbol' not in st.session_state:
    st.session_state.symbol = "AAPL"
if 'data' not in st.session_state:
    st.session_state.data = None
if 'chart_ready' not in st.session_state:
    st.session_state.chart_ready = False

# Main dashboard - single focused view
st.title("🤖 AI Agent Interaction Teaching Dashboard")

# Educational content about AI agents
st.markdown("""
This dashboard demonstrates how **PydanticAI** (the type-safe Python agent framework) enables AI agents to collaborate:
- **Market Analyst Agent**: Uses advanced tools to fetch stock data, calculate Fibonacci levels, and analyze sentiment
- **Strategy Agent**: Develops trading strategies using technical indicators and generates buy/sell signals
- **Risk Manager Agent**: Assesses portfolio risk, volatility patterns, and position sizing
- **Regulatory Agent**: Ensures SEC Regulation M compliance and maintains detailed audit trails
- **Trading Signal Agent**: Type-safe Pydantic agent generating structured `TradingDecision` objects with strict `TradingSignal` and `RiskLevel` enums
- **Supervisor Agent**: Makes final decisions by analyzing all agent inputs and managing portfolio exposure

""")

# Sidebar for symbol selection and controls
st.sidebar.markdown("### 📊 Stock Selection")

# Add popular symbols for easy selection
popular_symbols = market_data.get_popular_symbols()
selected_from_list = st.sidebar.selectbox("Choose a popular stock:",
                                          options=[''] + popular_symbols,
                                          format_func=lambda x: f"{x}"
                                          if x else "Select a symbol...")

# Manual input
new_symbol = st.sidebar.text_input("Or enter any symbol:",
                                   value=st.session_state.symbol)

# Use selected symbol if one was chosen from dropdown
if selected_from_list:
    new_symbol = selected_from_list

# Check if symbol changed
if new_symbol != st.session_state.symbol:
    st.session_state.symbol = new_symbol
    st.session_state.chart_ready = False
    st.session_state.data = None
    st.session_state.signals = None
    st.session_state.trend_analysis = None
    st.session_state.sentiment_analysis = None
    st.session_state.regulatory_analysis = None
    st.session_state.trading_signal_analysis = None
    st.session_state.market_analysis = None
    st.session_state.strategy_analysis = None
    st.session_state.risk_analysis = None
    st.session_state.supervisor_analysis = None
    st.session_state.decision = None

load_data_button = st.sidebar.button("Load Stock Data")
# Individual Agent Buttons - Replace old analyze button
st.sidebar.write("**🤖 Run Individual AI Agents:**")

market_button = st.sidebar.button("📈 Market Analyst", use_container_width=True, key="market_btn")
strategy_button = st.sidebar.button("🎯 Strategy Agent", use_container_width=True, key="strategy_btn") 
risk_button = st.sidebar.button("⚠️ Risk Manager", use_container_width=True, key="risk_btn")
regulatory_button = st.sidebar.button("🏛️ Regulatory Agent", use_container_width=True, key="regulatory_btn")
trading_signal_button = st.sidebar.button("⚡ Trading Signal Agent", use_container_width=True, key="trading_signal_btn")
supervisor_button = st.sidebar.button("🎯 Supervisor Agent", use_container_width=True, key="supervisor_btn")

st.sidebar.write("---")
st.sidebar.write("**💰 Execute Trade:**")
trade_button = st.sidebar.button("🚀 EXECUTE TRADE", type="primary", use_container_width=True, key="trade_btn")


# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Price Chart with Technical Indicators")

    if load_data_button or st.session_state.chart_ready:
        with st.spinner(f"Loading data for {st.session_state.symbol}..."):
            if load_data_button or st.session_state.data is None:
                data = market_data.get_stock_data(st.session_state.symbol)
                if not data.empty:
                    data = market_data.calculate_technical_indicators(data)
                    st.session_state.data = data
                    st.session_state.chart_ready = True
                else:
                    st.error(
                        f"No data available for {st.session_state.symbol}. Please try another symbol."
                    )
                    fig = go.Figure()
                    st.plotly_chart(fig, use_container_width=True)
                    st.session_state.chart_ready = False
            else:
                data = st.session_state.data

        if st.session_state.chart_ready and not data.empty:
            fig = go.Figure()

            # Candlestick chart
            fig.add_trace(
                go.Candlestick(x=data.index,
                               open=data['Open'],
                               high=data['High'],
                               low=data['Low'],
                               close=data['Close'],
                               name='OHLC'))

            # Bollinger Bands if available
            if 'Upper_Band' in data.columns and 'Lower_Band' in data.columns and pd.notna(
                    data['Upper_Band'].iloc[-1]):
                fig.add_trace(
                    go.Scatter(x=data.index,
                               y=data['Upper_Band'],
                               name='Upper Band',
                               line=dict(color='gray', dash='dash')))

                fig.add_trace(
                    go.Scatter(x=data.index,
                               y=data['Lower_Band'],
                               name='Lower Band',
                               line=dict(color='gray', dash='dash'),
                               fill='tonexty'))

            fig.update_layout(title=f"{st.session_state.symbol} Stock Price")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(
            f"Click 'Load Stock Data' to view the price chart for {st.session_state.symbol}"
        )

# Handle Individual Agent Button Clicks
if 'data' in st.session_state and st.session_state.data is not None and not st.session_state.data.empty:
    symbol = st.session_state.symbol
    
    # Market Analyst Button
    if market_button:
        with st.spinner("📈 Running Market Analyst..."):
            result = run_market_analyst()
            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state.market_analysis = result
                st.success("✅ Market Analyst completed!")
                st.rerun()
    
    # Strategy Agent Button
    if strategy_button:
        if 'market_analysis' not in st.session_state or not st.session_state.market_analysis:
            st.error("❌ Market Analyst agent must be run first before Strategy Agent! Order: Market ➔ Strategy ➔ Risk.")
        else:
            with st.spinner("🎯 Running Strategy Agent..."):
                result = run_strategy_agent()
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state.strategy_analysis = result
                    st.success("✅ Strategy Agent completed!")
                    st.rerun()
    
    # Risk Manager Button
    if risk_button:
        missing = []
        if 'market_analysis' not in st.session_state or not st.session_state.market_analysis:
            missing.append("Market Analyst")
        if 'strategy_analysis' not in st.session_state or not st.session_state.strategy_analysis:
            missing.append("Strategy Agent")
        if missing:
            st.error(f"❌ Prior agent(s) must be run first: {', '.join(missing)}! Order: Market ➔ Strategy ➔ Risk.")
        else:
            with st.spinner("⚠️ Running Risk Manager..."):
                result = run_risk_manager()
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state.risk_analysis = result
                    st.success("✅ Risk Manager completed!")
                    st.rerun()
    
    # Regulatory Agent Button
    if regulatory_button:
        missing = []
        if 'market_analysis' not in st.session_state or not st.session_state.market_analysis:
            missing.append("Market Analyst")
        if 'strategy_analysis' not in st.session_state or not st.session_state.strategy_analysis:
            missing.append("Strategy Agent")
        if 'risk_analysis' not in st.session_state or not st.session_state.risk_analysis:
            missing.append("Risk Manager")
        if missing:
            st.error(f"❌ Prior agent(s) must be run first: {', '.join(missing)}! Order: Market ➔ Strategy ➔ Risk ➔ Regulatory.")
        else:
            with st.spinner("🏛️ Running Regulatory Agent..."):
                result = run_regulatory_agent()
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state.regulatory_analysis = result
                    st.success("✅ Regulatory Agent completed!")
                    st.rerun()
    
    # Trading Signal Agent Button
    if trading_signal_button:
        missing = []
        if 'market_analysis' not in st.session_state or not st.session_state.market_analysis:
            missing.append("Market Analyst")
        if 'strategy_analysis' not in st.session_state or not st.session_state.strategy_analysis:
            missing.append("Strategy Agent")
        if 'risk_analysis' not in st.session_state or not st.session_state.risk_analysis:
            missing.append("Risk Manager")
        if 'regulatory_analysis' not in st.session_state or not st.session_state.regulatory_analysis:
            missing.append("Regulatory Agent")
        if missing:
            st.error(f"❌ Prior agent(s) must be run first: {', '.join(missing)}!")
        else:
            with st.spinner("⚡ Running Trading Signal Agent..."):
                result = run_trading_signal_agent()
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state.trading_signal_analysis = result
                    st.success("✅ Trading Signal Agent completed!")
                    st.rerun()
    
    # Supervisor Agent Button
    if supervisor_button:
        missing = []
        if 'market_analysis' not in st.session_state or not st.session_state.market_analysis:
            missing.append("Market Analyst")
        if 'strategy_analysis' not in st.session_state or not st.session_state.strategy_analysis:
            missing.append("Strategy Agent")
        if 'risk_analysis' not in st.session_state or not st.session_state.risk_analysis:
            missing.append("Risk Manager")
        if 'regulatory_analysis' not in st.session_state or not st.session_state.regulatory_analysis:
            missing.append("Regulatory Agent")
        if 'trading_signal_analysis' not in st.session_state or not st.session_state.trading_signal_analysis:
            missing.append("Trading Signal Agent")
        if missing:
            st.error(f"❌ Prior agent(s) must be run first: {', '.join(missing)}! Supervisor needs all agent analysis.")
        else:
            with st.spinner("🎯 Running Supervisor Agent..."):
                result = run_supervisor_agent(symbol)
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.session_state.supervisor_analysis = result
                    st.success("✅ Supervisor Agent completed!")
                    st.rerun()
    
    # Trade Button
    if trade_button:
        if 'supervisor_analysis' not in st.session_state or not st.session_state.supervisor_analysis:
            st.error("❌ Please run all agents first, especially Supervisor Agent, before executing trade")
        else:
            with st.spinner("💰 Executing trade and saving to database..."):
                trade_result = save_trade_to_database(symbol)
                if "❌" in trade_result:
                    st.error(trade_result)
                else:
                    st.success(trade_result)
                    st.rerun()
else:
    if market_button or strategy_button or risk_button or regulatory_button or trading_signal_button or supervisor_button or trade_button:
        st.error("Please load stock data first by clicking 'Load Stock Data'.")

with col2:
    st.subheader("🤖 Individual AI Agent Results")
    
    # Show execution progress
    agents_run = 0
    total_agents = 6
    
    if 'market_analysis' in st.session_state and st.session_state.market_analysis:
        agents_run += 1
    if 'strategy_analysis' in st.session_state and st.session_state.strategy_analysis:
        agents_run += 1
    if 'risk_analysis' in st.session_state and st.session_state.risk_analysis:
        agents_run += 1
    if 'regulatory_analysis' in st.session_state and st.session_state.regulatory_analysis:
        agents_run += 1
    if 'trading_signal_analysis' in st.session_state and st.session_state.trading_signal_analysis:
        agents_run += 1
    if 'supervisor_analysis' in st.session_state and st.session_state.supervisor_analysis:
        agents_run += 1
    
    progress = agents_run / total_agents
    st.write(f"**Analysis Progress: {agents_run}/{total_agents} agents completed**")
    st.progress(progress)
    
    if agents_run == total_agents:
        st.success("🎉 All agents completed! Click Execute Trade to save results to database.")
    elif agents_run > 0:
        st.info(f"📊 {agents_run} agents completed. Continue running remaining agents.")

    # Market Analyst Results
    if 'market_analysis' in st.session_state and st.session_state.market_analysis:
        with st.expander("📈 Market Analyst Results", expanded=False):
            result = st.session_state.market_analysis
            st.write(result['analysis'])
            st.write(f"**Confidence:** {result['confidence']:.1%}")
            st.write(f"**Completed:** {result['timestamp'].strftime('%H:%M:%S')}")
    else:
        st.info("📈 Market Analyst: Not run yet - Click button in sidebar")
    
    # Strategy Agent Results
    if 'strategy_analysis' in st.session_state and st.session_state.strategy_analysis:
        with st.expander("🎯 Strategy Agent Results", expanded=False):
            result = st.session_state.strategy_analysis
            st.write(result['analysis'])
            st.write(f"**Confidence:** {result['confidence']:.1%}")
            st.write(f"**Completed:** {result['timestamp'].strftime('%H:%M:%S')}")
    else:
        st.info("🎯 Strategy Agent: Not run yet - Click button in sidebar")
    
    # Risk Manager Results
    if 'risk_analysis' in st.session_state and st.session_state.risk_analysis:
        with st.expander("⚠️ Risk Manager Results", expanded=False):
            result = st.session_state.risk_analysis
            st.write(result['analysis'])
            st.write(f"**Confidence:** {result['confidence']:.1%}")
            st.write(f"**Completed:** {result['timestamp'].strftime('%H:%M:%S')}")
    else:
        st.info("⚠️ Risk Manager: Not run yet - Click button in sidebar")
    
    # Regulatory Agent Results
    if 'regulatory_analysis' in st.session_state and st.session_state.regulatory_analysis:
        with st.expander("🏛️ Regulatory Agent Results", expanded=False):
            result = st.session_state.regulatory_analysis
            st.write(result['analysis'])
            st.write(f"**Status:** {result['compliance_status']}")
            st.write(f"**Recommendation:** {result['recommendation']}")
            st.write(f"**Confidence:** {result['confidence']:.1%}")
            st.write(f"**Completed:** {result['timestamp'].strftime('%H:%M:%S')}")
    else:
        st.info("🏛️ Regulatory Agent: Not run yet - Click button in sidebar")
    
    # Trading Signal Agent Results
    if 'trading_signal_analysis' in st.session_state and st.session_state.trading_signal_analysis:
        with st.expander("⚡ Trading Signal Agent Results", expanded=False):
            result = st.session_state.trading_signal_analysis
            st.write(f"**Signal Decision:** `{result['decision']}`")
            st.write(f"**Risk Level:** `{result['risk_level']}`")
            st.write(f"**Confidence:** {result['confidence']:.1%}")
            st.write(f"**Entry Price:** ${result['entry_price']:.2f}")
            st.write(f"**Exit Target:** ${result['exit_price']:.2f}")
            st.write(f"**Position Size:** {result['position_size_percent']:.1f}%")
            st.write(f"**Rationale:** {result['rationale']}")
            st.write(f"**Completed:** {result['timestamp'].strftime('%H:%M:%S')}")
    else:
        st.info("⚡ Trading Signal Agent: Not run yet - Click button in sidebar")
    
    # Supervisor Agent Results
    if 'supervisor_analysis' in st.session_state and st.session_state.supervisor_analysis:
        with st.expander("🎯 Supervisor Agent Results", expanded=False):
            result = st.session_state.supervisor_analysis
            st.write(result['analysis'])
            st.write(f"**Final Decision:** {result['decision']}")
            st.write(f"**Confidence:** {result['confidence']:.1%}")
            st.write(f"**Completed:** {result['timestamp'].strftime('%H:%M:%S')}")
    else:
        st.info("🎯 Supervisor Agent: Not run yet - Click button in sidebar")

    if st.session_state.trend_analysis:
        st.write("**Market Trend Analysis:**")
        for timeframe, analysis in st.session_state.trend_analysis.items():
            st.write(f"- {timeframe}: {analysis['analysis']}")

    if st.session_state.sentiment_analysis:
        st.write("**Sentiment Analysis:**")
        for timeframe, analysis in st.session_state.sentiment_analysis.items():
            st.write(f"- {timeframe}: {analysis['analysis']}")


    # Final supervisor decision
    if st.session_state.decision:
        st.write("---")
        st.write("**🎯 Supervisor Agent Final Decision:**")
        st.write(
            st.session_state.decision.get('decision', 'No decision available'))
        st.write(
            f"**Confidence:** {st.session_state.decision.get('confidence', 0.0):.2f}"
        )

        # Note: PydanticAI agents automatically save decisions using their built-in tools
        # This demonstrates how agents can use storage tools independently
        st.info(
            "💡 **PydanticAI Integration**: The agents automatically saved their decisions using built-in storage tools during analysis!"
        )

# Add a data viewer section at the bottom
st.write("---")
st.subheader("📁 Stored AI Agent Data")

# Show recent decisions in an expandable section
with st.expander("View Recent Agent Decisions", expanded=False):
    try:
        summary = storage.get_all_decisions_summary()

        if summary["total_decisions"] > 0:
            st.write(
                f"**Total Decisions Stored:** {summary['total_decisions']}")
            st.write(f"**Active Agents:** {', '.join(summary['agents'])}")
            st.write(f"**Analyzed Symbols:** {', '.join(summary['symbols'])}")

            st.write("**Recent Decisions:**")
            recent_df = pd.DataFrame(summary["latest_decisions"])
            if len(recent_df) > 0:
                # Format the dataframe for better display
                recent_df['created_at'] = pd.to_datetime(
                    recent_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
                recent_df['confidence'] = recent_df['confidence'].round(2)
                # Keep full decision text without truncation

                st.dataframe(recent_df[[
                    'symbol', 'agent_name', 'decision', 'confidence',
                    'created_at'
                ]],
                             use_container_width=True,
                             hide_index=True)
        else:
            st.info(
                "No agent decisions stored yet. Run an analysis to see data appear here!"
            )

    except Exception as e:
        st.error(f"Error reading stored data: {str(e)}")

# Show PydanticAI Tools Integration
with st.expander("🛠️ PydanticAI Tools & Agent Actions", expanded=False):
    st.markdown("""
    **Advanced Tool Integration with PydanticAI:**
    
    PydanticAI provides type-safe tools and structured responses that our AI agents use to perform complex analysis:
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **📊 Market Analysis Tools:**
        - `get_stock_data()` - Fetches real-time stock data with technical indicators
        - `calculate_fibonacci_levels()` - Computes retracement levels for entry/exit points  
        - `analyze_market_sentiment()` - Processes price action and volume for sentiment analysis
        
        **🏛️ Compliance Tools:**
        - `check_regulation_m_compliance()` - Monitors SEC regulation violations
        - `save_audit_entry()` - Maintains detailed compliance audit trails
        - `get_audit_trail()` - Retrieves historical compliance decisions
        """)

    with col2:
        st.markdown("""
        **💾 Storage & Analysis Tools:**
        - `save_trading_decision()` - Stores agent decisions with confidence scores
        - `analyze_decision_patterns()` - Identifies trends in agent decision-making
        - `get_trading_decisions_summary()` - Provides comprehensive decision analytics
        
        """)


# Show audit trail for compliance review
with st.expander("📋 Audit Trail & Compliance Review", expanded=False):
    try:
        audit_summary = storage.get_audit_summary()

        if audit_summary["total_entries"] > 0:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Audit Entries",
                          audit_summary["total_entries"])
            with col2:
                st.metric("Supervisor Decisions",
                          audit_summary["supervisor_decisions"])
            with col3:
                st.metric("Regulatory Reviews",
                          audit_summary["regulatory_decisions"])

            st.write("**Recent Audit Entries:**")
            audit_trail = storage.get_audit_trail(limit=10)

            if audit_trail:
                audit_df = pd.DataFrame(audit_trail)
                # Format for display
                audit_df['timestamp'] = pd.to_datetime(
                    audit_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
                audit_df['confidence'] = audit_df['confidence'].round(2)
                # Keep full rationale text without truncation

                display_columns = [
                    'symbol', 'decision_type', 'action', 'confidence',
                    'compliance_status', 'timestamp'
                ]
                st.dataframe(audit_df[display_columns],
                             use_container_width=True,
                             hide_index=True)

                # Show detailed view for specific symbol
                if st.session_state.symbol:
                    symbol_audit = storage.get_audit_trail(
                        symbol=st.session_state.symbol, limit=5)
                    if symbol_audit:
                        st.write(
                            f"**Detailed Audit for {st.session_state.symbol}:**"
                        )
                        for entry in symbol_audit:
                            with st.container():
                                st.markdown(
                                    f"**{entry['decision_type']}** - {entry['action']} (Confidence: {entry['confidence']:.2f})"
                                )
                                st.text(f"Time: {entry['timestamp']}")
                                
                                # Handle compliance status with NaN checking
                                compliance = entry.get('compliance_status', '')
                                if compliance and str(compliance).lower() not in ['nan', 'none', '']:
                                    st.text(f"Compliance: {compliance}")
                                
                                # Handle blocked trades with NaN checking  
                                blocked = entry.get('blocked_trades', '')
                                if blocked and str(blocked).lower() not in ['nan', 'none', '']:
                                    st.text(f"Blocked Trades: {blocked}")
                                
                                # Handle rationale with NaN checking
                                rationale = entry.get('rationale', '')
                                if rationale and str(rationale).lower() not in ['nan', 'none', '']:
                                    st.text(f"Rationale: {rationale}")
                                st.markdown("---")
        else:
            st.info(
                "No audit entries yet. Run an analysis to create audit trail!")

    except Exception as e:
        st.error(f"Error reading audit trail: {str(e)}")

# Show file locations for educational purposes
with st.expander("📂 Data Storage Information", expanded=False):
    st.markdown("""
    **Dual-Sync Storage Architecture (Database & CSV):**
    - All AI agent decisions and audit records are persisted simultaneously to an ACID-compliant Database (SQLite / PostgreSQL) and CSV files.
    - Synchronized dual-write ensures high reliability, instant inspection, and historical persistence.
    
    **Storage Locations:**
    - `data_storage/trading.db` - SQLite relational database storing trading signals, decisions, and audit trails
    - `data_storage/trading_decisions.csv` - All agent decisions and analysis results
    - `data_storage/trading_signals.csv` - Individual trading signals  
    - `data_storage/screened_stocks.csv` - Stock screening results
    - `data_storage/audit_trail.csv` - **Detailed audit trail for compliance review**
    
    """)

    if st.button("🗑️ Clear All Stored Data"):
        try:
            import os
            files_to_clear = [
                "data_storage/trading_decisions.csv",
                "data_storage/trading_signals.csv",
                "data_storage/screened_stocks.csv",
                "data_storage/audit_trail.csv",
                "data_storage/trading.db"
            ]

            for file_path in files_to_clear:
                if os.path.exists(file_path):
                    os.remove(file_path)

            # Reinitialize the storage
            storage._initialize_csv_files()
            st.success("All stored data cleared!")
            st.rerun()
        except Exception as e:
            st.error(f"Error clearing data: {str(e)}")
