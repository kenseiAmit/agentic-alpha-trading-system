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

