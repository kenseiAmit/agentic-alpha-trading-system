import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

class CSVStorage:
    def __init__(self):
        # Create storage directory if it doesn't exist
        self.storage_dir = "data_storage"
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Define CSV file paths
        self.trading_signals_file = os.path.join(self.storage_dir, "trading_signals.csv")
        self.trading_decisions_file = os.path.join(self.storage_dir, "trading_decisions.csv")
        self.screened_stocks_file = os.path.join(self.storage_dir, "screened_stocks.csv")
        
        # Initialize CSV files with headers if they don't exist
        self._initialize_csv_files()
    
    def _initialize_csv_files(self):
        """Initialize CSV files with proper headers if they don't exist"""
        
        # Trading signals CSV
        if not os.path.exists(self.trading_signals_file):
            signals_df = pd.DataFrame(columns=[
                'id', 'symbol', 'signal_type', 'strategy', 'confidence', 'timestamp'
            ])
            signals_df.to_csv(self.trading_signals_file, index=False)
        
        # Trading decisions CSV
        if not os.path.exists(self.trading_decisions_file):
            decisions_df = pd.DataFrame(columns=[
                'id', 'symbol', 'decision', 'confidence', 'agent_name', 'created_at'
            ])
            decisions_df.to_csv(self.trading_decisions_file, index=False)
        
        # Audit trail CSV for detailed supervisor and regulatory decisions
        self.audit_trail_file = os.path.join(self.storage_dir, "audit_trail.csv")
        if not os.path.exists(self.audit_trail_file):
            audit_df = pd.DataFrame(columns=[
                'id', 'symbol', 'timestamp', 'decision_type', 'action', 'confidence', 
                'rationale', 'compliance_status', 'risk_level', 'position_size', 'blocked_trades'
            ])
            audit_df.to_csv(self.audit_trail_file, index=False)
        
        # Screened stocks CSV
        if not os.path.exists(self.screened_stocks_file):
            stocks_df = pd.DataFrame(columns=[
                'id', 'symbol', 'company_name', 'current_price', 'average_volume', 'last_updated'
            ])
            stocks_df.to_csv(self.screened_stocks_file, index=False)
    
    def add_signal(self, symbol: str, signal_type: str, strategy: str, confidence: float):
        """Add a trading signal to CSV"""
        try:
            # Read existing data
            if os.path.exists(self.trading_signals_file):
                df = pd.read_csv(self.trading_signals_file)
            else:
                df = pd.DataFrame(columns=['id', 'symbol', 'signal_type', 'strategy', 'confidence', 'timestamp'])
            
            # Create new row
            new_id = len(df) + 1
            new_row = {
                'id': new_id,
                'symbol': symbol,
                'signal_type': signal_type,
                'strategy': strategy,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            }
            
            # Add row and save
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(self.trading_signals_file, index=False)
            
        except Exception as e:
            print(f"Error saving signal to CSV: {str(e)}")
    
    def save_trading_decision(self, symbol: str, decision: str, confidence: float, agent_name: str = 'supervisor'):
        """Save a trading decision to CSV"""
        try:
            # Read existing data
            if os.path.exists(self.trading_decisions_file):
                df = pd.read_csv(self.trading_decisions_file)
            else:
                df = pd.DataFrame(columns=['id', 'symbol', 'decision', 'confidence', 'agent_name', 'created_at'])
            
            # Create new row
            new_id = len(df) + 1
            new_row = {
                'id': new_id,
                'symbol': symbol,
                'decision': decision,
                'confidence': confidence,
                'agent_name': agent_name,
                'created_at': datetime.now().isoformat()
            }
            
            # Add row and save
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(self.trading_decisions_file, index=False)
            
        except Exception as e:
            print(f"Error saving trading decision to CSV: {str(e)}")
    
    def get_latest_trading_decisions(self, symbol: str, limit: int = 2) -> List[Dict]:
        """Get the latest trading decisions for a symbol"""
        try:
            if not os.path.exists(self.trading_decisions_file):
                return []
            
            df = pd.read_csv(self.trading_decisions_file)
            
            # Filter by symbol and sort by created_at (most recent first)
            symbol_df = df[df['symbol'] == symbol].copy()
            if len(symbol_df) == 0:
                return []
            
            symbol_df['created_at'] = pd.to_datetime(symbol_df['created_at'])
            symbol_df = symbol_df.sort_values('created_at', ascending=False)
            
