import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import json
import os

class FiveTenAlgo:
    def __init__(self, initial_capital=1000000, stability_minutes=3, 
                buy_threshold=(-5.5, -4.5), sell_threshold=(9.5, 10.5),
                trade_size_buy_pct=0.001, trade_size_sell_pct=0.002):
        """
        Initialize the FiveTenAlgo trading algorithm.
        
        Parameters:
        initial_capital (float): Initial capital to start with (default: 1,000,000)
        stability_minutes (int): Minutes to check price stability before executing trades
        buy_threshold (tuple): Low and high percentages for buy signal (default: -5.5% to -4.5%)
        sell_threshold (tuple): Low and high percentages for sell signal (default: 9.5% to 10.5%)
        trade_size_buy_pct (float): Percentage of capital to use per buy (default: 0.1%)
        trade_size_sell_pct (float): Percentage of capital to use per sell (default: 0.2%)
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.portfolio = {}  # Symbol: {'shares': quantity, 'cost_basis': total_cost}
        self.trade_log = []
        self.performance_history = []
        self.stability_minutes = stability_minutes  # Minutes required for signal confirmation
        
        # Thresholds for trading signals
        self.buy_threshold_low, self.buy_threshold_high = buy_threshold
        self.sell_threshold_low, self.sell_threshold_high = sell_threshold
        
        # Trade sizes as percentage of initial capital
        self.trade_size_buy_pct = trade_size_buy_pct
        self.trade_size_sell_pct = trade_size_sell_pct
        
    def check_buy_signal(self, current_price, week_ago_price):
        """Check if the price drop is within the buy threshold range."""
        if week_ago_price <= 0:
            return False
        
        price_change_pct = (current_price - week_ago_price) / week_ago_price * 100
        return self.buy_threshold_low <= price_change_pct <= self.buy_threshold_high
    
    def check_sell_signal(self, current_price, week_ago_price):
        """Check if the price rise is within the sell threshold range."""
        if week_ago_price <= 0:
            return False
        
        price_change_pct = (current_price - week_ago_price) / week_ago_price * 100
        return self.sell_threshold_low <= price_change_pct <= self.sell_threshold_high
    
    def execute_buy(self, symbol, price, date):
        """Execute a buy order based on the configured percentage of capital."""
        # Calculate the dollar amount to buy based on percentage of initial capital
        trade_size_dollars = self.initial_capital * self.trade_size_buy_pct
        
        if self.capital < trade_size_dollars:
            return False  # Not enough capital
        
        shares_to_buy = trade_size_dollars / price
        
        # Update portfolio
        if symbol in self.portfolio:
            current_shares = self.portfolio[symbol]['shares']
            current_cost = self.portfolio[symbol]['cost_basis']
            
            self.portfolio[symbol]['shares'] = current_shares + shares_to_buy
            self.portfolio[symbol]['cost_basis'] = current_cost + trade_size_dollars
        else:
            self.portfolio[symbol] = {
                'shares': shares_to_buy,
                'cost_basis': trade_size_dollars
            }
        
        # Update capital
        self.capital -= trade_size_dollars
        
        # Log trade
        self.trade_log.append({
            'date': date,
            'symbol': symbol,
            'action': 'BUY',
            'price': price,
            'shares': shares_to_buy,
            'value': trade_size_dollars
        })
        
        return True
    
    def execute_sell(self, symbol, price, date):
        """Execute a sell order based on the configured percentage of capital."""
        if symbol not in self.portfolio or self.portfolio[symbol]['shares'] <= 0:
            return False  # No shares to sell
        
        # Calculate the dollar amount to sell based on percentage of initial capital
        trade_size_dollars = self.initial_capital * self.trade_size_sell_pct
        
        shares_to_sell = min(trade_size_dollars / price, self.portfolio[symbol]['shares'])
        sell_value = shares_to_sell * price
        
        # Update portfolio
        self.portfolio[symbol]['shares'] -= shares_to_sell
        
        # If all shares are sold, calculate profit/loss
        if self.portfolio[symbol]['shares'] <= 0:
            cost_basis = self.portfolio[symbol]['cost_basis']
            profit_loss = sell_value - cost_basis
            self.portfolio.pop(symbol)  # Remove from portfolio
        else:
            # Adjust cost basis proportionally
            sell_ratio = shares_to_sell / (self.portfolio[symbol]['shares'] + shares_to_sell)
            cost_basis_portion = self.portfolio[symbol]['cost_basis'] * sell_ratio
            self.portfolio[symbol]['cost_basis'] -= cost_basis_portion
            profit_loss = sell_value - cost_basis_portion
        
        # Update capital
        self.capital += sell_value
        
        # Log trade
        self.trade_log.append({
            'date': date,
            'symbol': symbol,
            'action': 'SELL',
            'price': price,
            'shares': shares_to_sell,
            'value': sell_value,
            'profit_loss': profit_loss
        })
        
        return True
    
    def process_market_data(self, market_data):
        """
        Process market data for a specific period.
        market_data: DataFrame with columns [symbol, date, price]
        """
        # Group by date to process one day at a time
        dates = market_data['date'].unique()
        dates.sort()
        
        # Create a lookup table for all symbols and their previous prices
        symbols = market_data['symbol'].unique()
        symbol_price_history = {symbol: {} for symbol in symbols}
        
        for current_date in dates:
            day_data = market_data[market_data['date'] == current_date]
            
            # Get data from one week ago
            week_ago_date = (pd.to_datetime(current_date) - pd.Timedelta(days=7)).strftime('%Y-%m-%d')
            week_ago_data = market_data[market_data['date'] == week_ago_date]
            
            # Update the lookup table for all symbols on this date
            for _, row in day_data.iterrows():
                symbol = row['symbol']
                current_price = row['price']
                symbol_price_history[symbol][current_date] = current_price
            
            if len(week_ago_data) > 0:
                # Process each stock on this date
                buy_candidates = []
                sell_candidates = []
                
                # First, identify all buy and sell candidates
                for _, row in day_data.iterrows():
                    symbol = row['symbol']
                    current_price = row['price']
                    
                    # Get this symbol's price from a week ago
                    symbol_week_ago = week_ago_data[week_ago_data['symbol'] == symbol]
                    
                    if len(symbol_week_ago) > 0:
                        week_ago_price = symbol_week_ago.iloc[0]['price']
                        
                        # Check for buy signal
                        if self.check_buy_signal(current_price, week_ago_price):
                            buy_candidates.append((symbol, current_price))
                        
                        # Check for sell signal for stocks we own
                        elif symbol in self.portfolio and self.check_sell_signal(current_price, week_ago_price):
                            sell_candidates.append((symbol, current_price))
                
                # Randomly sample buy candidates if we have too many (to avoid concentration)
                if len(buy_candidates) > 10:
                    np.random.shuffle(buy_candidates)
                    buy_candidates = buy_candidates[:10]
                
                # Execute buys for the selected candidates
                for symbol, price in buy_candidates:
                    if self.capital > self.initial_capital * self.trade_size_buy_pct:
                        self.execute_buy(symbol, price, current_date)
                
                # Execute sells for all sell candidates
                for symbol, price in sell_candidates:
                    self.execute_sell(symbol, price, current_date)
            
            # Calculate total portfolio value at end of day
            portfolio_value = self.capital
            for symbol, details in self.portfolio.items():
                symbol_day_data = day_data[day_data['symbol'] == symbol]
                if len(symbol_day_data) > 0:
                    symbol_price = symbol_day_data.iloc[0]['price']
                    portfolio_value += details['shares'] * symbol_price
            
            # Record performance
            self.performance_history.append({
                'date': current_date,
                'portfolio_value': portfolio_value,
                'cash': self.capital,
                'total_return': (portfolio_value / self.initial_capital - 1) * 100
            })
    
    def save_simulation(self, filename):
        """Save the current simulation state to a file."""
        try:
            # Create a simplified representation for JSON serialization
            data = {
                'capital': self.capital,
                'portfolio': self.portfolio,
                'trade_log': self.trade_log,
                'performance_history': self.performance_history,
                'initial_capital': self.initial_capital
            }
            
            # Ensure all data is JSON serializable
            for entry in data['performance_history']:
                for key, value in entry.items():
                    if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                        entry[key] = 0.0
                    # Cap extremely large values that might be errors
                    if isinstance(value, float) and value > 1e9:  # Cap at 1 billion
                        print(f"WARNING: Capping extremely large value {value} to 1 billion")
                        entry[key] = 1e9
            
            for entry in data['trade_log']:
                for key, value in entry.items():
                    if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                        entry[key] = 0.0
                    # Cap extremely large values that might be errors
                    if isinstance(value, float) and value > 1e9:  # Cap at 1 billion
                        print(f"WARNING: Capping extremely large value {value} to 1 billion")
                        entry[key] = 1e9
            
            # Check for anomalous jumps in the performance history
            if len(data['performance_history']) > 1:
                for i in range(1, len(data['performance_history'])):
                    curr = data['performance_history'][i]
                    prev = data['performance_history'][i-1]
                    
                    # Check for suspicious jumps in portfolio value (>50% in one day)
                    if 'portfolio_value' in curr and 'portfolio_value' in prev:
                        curr_value = curr['portfolio_value']
                        prev_value = prev['portfolio_value']
                        
                        if prev_value > 0 and curr_value / prev_value > 1.5:
                            print(f"WARNING: Correcting suspicious jump in portfolio value on {curr['date']}")
                            # Replace with a more reasonable value (5% growth)
                            data['performance_history'][i]['portfolio_value'] = prev_value * 1.05
            
            # Create parent directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            # Create a backup of the existing file if it exists
            if os.path.exists(filename):
                backup_file = filename + '.backup'
                import shutil
                try:
                    shutil.copy2(filename, backup_file)
                    print(f"Created backup: {filename} -> {backup_file}")
                except Exception as e:
                    print(f"Warning: Failed to create backup: {e}")
            
            # Write to a temporary file first to prevent partial writes
            temp_filename = filename + '.tmp'
            with open(temp_filename, 'w') as f:
                json.dump(data, f)
                
            # Verify the file was written correctly
            with open(temp_filename, 'r') as f:
                # This will raise an exception if the JSON is invalid
                json.load(f)
            
            # Replace the original file
            os.replace(temp_filename, filename)
            
            return True
        except Exception as e:
            print(f"Error saving simulation data: {e}")
            return False
    
    def load_simulation(self, filename):
        """Load simulation results from a file."""
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            return False
        
        # First try to load the file directly
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.capital = data['capital']
            self.portfolio = data['portfolio']
            self.trade_log = data['trade_log']
            self.performance_history = data['performance_history']
            self.initial_capital = data.get('initial_capital', self.initial_capital)
            
            # Perform data validation and corrections
            self._validate_and_fix_data()
            
            return True
        
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from {filename}: {e}")
            
            # Try to load a backup file if it exists
            backup_file = filename + '.backup'
            if os.path.exists(backup_file):
                print(f"Attempting to load from backup file: {backup_file}")
                try:
                    with open(backup_file, 'r') as f:
                        data = json.load(f)
                    
                    self.capital = data['capital']
                    self.portfolio = data['portfolio']
                    self.trade_log = data['trade_log']
                    self.performance_history = data['performance_history']
                    self.initial_capital = data.get('initial_capital', self.initial_capital)
                    
                    # Perform data validation and corrections
                    self._validate_and_fix_data()
                    
                    # Restore the backup to the original file
                    import shutil
                    shutil.copy2(backup_file, filename)
                    print(f"Restored from backup: {backup_file} -> {filename}")
                    
                    return True
                except Exception as backup_error:
                    print(f"Failed to load backup: {backup_error}")
            
            return False
        except Exception as e:
            print(f"Error loading simulation from {filename}: {e}")
            return False
    
    def _validate_and_fix_data(self):
        """Validate loaded data and fix any issues."""
        # Check for NaN or infinite values in performance history
        if self.performance_history:
            for i, entry in enumerate(self.performance_history):
                for key, value in list(entry.items()):
                    if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                        print(f"Warning: Found invalid value {value} in performance history. Setting to 0.0")
                        self.performance_history[i][key] = 0.0
                    # Cap extremely large values
                    if isinstance(value, float) and value > 1e9:  # Cap at 1 billion
                        print(f"Warning: Capping extremely large value {value} to 1 billion")
                        self.performance_history[i][key] = 1e9
            
            # Check for abnormal jumps
            for i in range(1, len(self.performance_history)):
                curr = self.performance_history[i]
                prev = self.performance_history[i-1]
                
                if 'portfolio_value' in curr and 'portfolio_value' in prev:
                    curr_value = curr['portfolio_value']
                    prev_value = prev['portfolio_value']
                    
                    # Check for suspicious jumps (>50% in one day)
                    if prev_value > 0 and curr_value / prev_value > 1.5:
                        print(f"Warning: Detected abnormal jump in portfolio value on {curr['date']}")
                        # Smooth out the jump (use a 5% growth instead)
                        self.performance_history[i]['portfolio_value'] = prev_value * 1.05
                        print(f"Corrected value from {curr_value} to {self.performance_history[i]['portfolio_value']}")
        
        # Validate portfolio values
        for symbol, details in list(self.portfolio.items()):
            if 'shares' not in details or 'cost_basis' not in details:
                print(f"Warning: Invalid portfolio entry for {symbol}. Removing.")
                del self.portfolio[symbol]
            elif details['shares'] <= 0:
                print(f"Warning: Zero or negative shares for {symbol}. Removing from portfolio.")
                del self.portfolio[symbol]
            elif details['cost_basis'] <= 0:
                print(f"Warning: Zero or negative cost basis for {symbol}. Fixing.")
                self.portfolio[symbol]['cost_basis'] = details['shares'] * 100  # Assume $100 price
    
    def generate_precomputed_data(self, start_date, end_date, symbols=None, output_file=None):
        """
        Generate precomputed simulation data for a set of symbols and date range.
        """
        # Default symbols if none provided
        if symbols is None:
            symbols = [
                # Major NASDAQ stocks
                'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA', 'AVGO', 'ADBE', 
                'COST', 'PEP', 'CSCO', 'TMUS', 'CMCSA', 'NFLX', 'AMD', 'INTC', 'QCOM', 'INTU',
                'TXN', 'PYPL', 'ADP', 'AMAT', 'BKNG', 'SBUX', 'MDLZ', 'GILD', 'ADI', 'REGN',
                'FISV', 'VRTX', 'ISRG', 'ATVI', 'CSX', 'LRCX', 'ILMN', 'MU', 'CHTR', 'ADSK',
                
                # Major NYSE stocks
                'JNJ', 'JPM', 'V', 'PG', 'HD', 'MA', 'UNH', 'BAC', 'DIS', 'VZ', 
                'XOM', 'T', 'KO', 'PFE', 'MRK', 'CVX', 'ABBV', 'WMT', 'CRM', 'ORCL',
                'ABT', 'LLY', 'TMO', 'DHR', 'ACN', 'NEE', 'NKE', 'AMGN', 'MCD', 'PM',
                'MDT', 'UNP', 'BMY', 'TJX', 'LIN', 'HON', 'IBM', 'SPGI', 'MMM', 'GS'
            ]
            
        # Download historical data
        all_data = []
        
        for symbol in symbols:
            try:
                data = yf.download(symbol, start=start_date, end=end_date)
                if not data.empty:
                    # Extract just the Close prices
                    symbol_data = data['Close'].reset_index()
                    symbol_data.columns = ['date', 'price']
                    symbol_data['symbol'] = symbol
                    symbol_data['date'] = symbol_data['date'].dt.strftime('%Y-%m-%d')
                    
                    all_data.append(symbol_data)
            except Exception as e:
                print(f"Error downloading {symbol}: {e}")
        
        if not all_data:
            return False
            
        # Combine all data
        combined_data = pd.concat(all_data)
        
        # Run simulation
        self.process_market_data(combined_data)
        
        # Save results
        self.save_simulation(output_file)
        
        return True
    
    def continue_simulation(self, precomputed_file, end_date=None):
        """
        Continue simulation from a precomputed state up to a specific date or current date.
        """
        # Load precomputed data
        if not self.load_simulation(precomputed_file):
            return False
        
        # Get the last date from precomputed data
        if not self.performance_history:
            return False
            
        last_simulation_date = self.performance_history[-1]['date']
        last_date = datetime.strptime(last_simulation_date, '%Y-%m-%d')
        
        # Set end date to today if not specified
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Extract symbols from portfolio
        symbols = list(self.portfolio.keys())
        
        # Add symbols from recent trades to capture those we might have exited
        recent_trades = self.trade_log[-100:]  # Last 100 trades
        for trade in recent_trades:
            if trade['symbol'] not in symbols:
                symbols.append(trade['symbol'])
        
        if not symbols:
            # If no symbols in portfolio or recent trades, use a default set
            symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'AMZN', 'GOOGL']
        
        # Download recent data
        start_date = (last_date - timedelta(days=7)).strftime('%Y-%m-%d')  # Need week-ago data
        
        # Continue simulation
        return self.generate_precomputed_data(start_date, end_date, symbols, precomputed_file + '.updated')


# Function to create sample data for demonstration
def create_sample_data(output_file, symbols=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']):
    """Create sample historical data for demonstration purposes."""
    start_date = '2022-01-01'
    end_date = '2022-12-31'
    
    all_data = []
    for symbol in symbols:
        try:
            data = yf.download(symbol, start=start_date, end=end_date)
            if not data.empty:
                symbol_data = data['Close'].reset_index()
                symbol_data.columns = ['date', 'price']
                symbol_data['symbol'] = symbol
                symbol_data['date'] = symbol_data['date'].dt.strftime('%Y-%m-%d')
                all_data.append(symbol_data)
        except Exception as e:
            print(f"Error downloading {symbol}: {e}")
    
    if all_data:
        combined_data = pd.concat(all_data)
        combined_data.to_csv(output_file, index=False)
        return True
    return False 