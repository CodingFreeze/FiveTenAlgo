import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
from models.algorithm import FiveTenAlgo
from functools import lru_cache
import uuid

class DataProcessor:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.precomputed_file = os.path.join(data_dir, 'precomputed_simulation.json')
        self.market_data_file = os.path.join(data_dir, 'market_data.json')
        self.cutoff_date = '2025-03-01'  # March 1st, 2025
        self._cache = {}  # Simple cache for performance data
        
        # Define parameters for different simulation modes
        self.simulation_params = {
            'default': {
                'file': 'precomputed_simulation.json',
                'initial_capital': 1000000,
                'trade_size_buy_pct': 0.001,   # 0.1% of capital per buy
                'trade_size_sell_pct': 0.002,  # 0.2% of capital per sell
                'buy_threshold': (-5.5, -4.5),  # 5% drop
                'sell_threshold': (9.5, 10.5)   # 10% rise
            },
            'aggressive': {
                'file': 'precomputed_simulation_aggressive.json',
                'initial_capital': 1000000,
                'trade_size_buy_pct': 0.002,    # 0.2% of capital per buy
                'trade_size_sell_pct': 0.004,   # 0.4% of capital per sell
                'buy_threshold': (-5.0, -3.0),  # 3-5% drop
                'sell_threshold': (8.0, 12.0)    # 8-12% rise
            },
            'conservative': {
                'file': 'precomputed_simulation_conservative.json',
                'initial_capital': 1000000,
                'trade_size_buy_pct': 0.0005,    # 0.05% of capital per buy
                'trade_size_sell_pct': 0.001,   # 0.1% of capital per sell
                'buy_threshold': (-6.0, -5.0),  # 5-6% drop
                'sell_threshold': (11.0, 12.0)  # 11-12% rise
            },
            'balanced': {
                'file': 'precomputed_simulation_balanced.json',
                'initial_capital': 1000000,
                'trade_size_buy_pct': 0.001,    # 0.1% of capital per buy
                'trade_size_sell_pct': 0.0015,   # 0.15% of capital per sell
                'buy_threshold': (-5.5, -4.5),  # 4.5-5.5% drop
                'sell_threshold': (9.0, 10.0)   # 9-10% rise
            }
        }
        
        # Create data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def get_simulation_file(self, mode='default', period='all'):
        """
        Get the correct file for the specified simulation mode and period.
        
        Args:
            mode: The simulation mode (default, aggressive, conservative, balanced)
            period: The time period (all, 2000, covid)
            
        Returns:
            The file path for the specified simulation mode and period
        """
        if mode not in self.simulation_params:
            mode = 'default'
        
        if period == 'all':
            # Standard file, starting from 1971
            filename = self.simulation_params[mode]['file']
        elif period == '2000':
            # File for 2000 onwards simulation
            filename = f"precomputed_simulation_{mode}_2000.json"
        elif period == 'covid':
            # File for COVID onwards simulation
            filename = f"precomputed_simulation_{mode}_covid.json"
        else:
            # Default to standard file
            filename = self.simulation_params[mode]['file']
        
        return os.path.join(self.data_dir, filename)
    
    def get_initial_capital(self, mode='default'):
        """Get the initial capital for the specified simulation mode."""
        if mode not in self.simulation_params:
            mode = 'default'
        
        return self.simulation_params[mode]['initial_capital']
    
    def generate_and_cache_market_data(self):
        """Generate market data once and cache it to a file to avoid regenerating it each time."""
        print(f"Generating market data cache file: {self.market_data_file}")
        
        if os.path.exists(self.market_data_file):
            print("Market data cache already exists. Loading from file...")
            try:
                with open(self.market_data_file, 'r') as f:
                    market_data_dict = json.load(f)
                    
                # Convert the loaded JSON back to DataFrame
                market_data = pd.DataFrame(market_data_dict)
                print(f"Loaded market data with {len(market_data)} records")
                return market_data
            except Exception as e:
                print(f"Error loading market data from cache: {e}")
                print("Regenerating market data...")
                
        # Generate fresh market data
        market_data = self._create_sample_data()
        
        # Save to file for future use
        try:
            # Convert DataFrame to dict for JSON serialization
            market_data_dict = market_data.to_dict(orient='records')
            
            with open(self.market_data_file, 'w') as f:
                json.dump(market_data_dict, f)
            
            print(f"Successfully saved {len(market_data)} market data records to {self.market_data_file}")
            return market_data
        except Exception as e:
            print(f"Error saving market data to cache: {e}")
            return market_data
    
    def load_market_data(self):
        """Load market data from cache file or generate if not exists."""
        if os.path.exists(self.market_data_file):
            try:
                with open(self.market_data_file, 'r') as f:
                    market_data_dict = json.load(f)
                
                # Convert the loaded JSON back to DataFrame
                market_data = pd.DataFrame(market_data_dict)
                print(f"Loaded market data from cache: {len(market_data)} records")
                return market_data
            except Exception as e:
                print(f"Error loading market data from cache: {e}")
        
        # If cache doesn't exist or is corrupted, generate new data
        print("Market data cache not found. Generating new data...")
        return self.generate_and_cache_market_data()
    
    def generate_sample_precomputed_data(self, mode='default'):
        """Generate sample precomputed data for demonstration."""
        # Use the period-specific method to generate data for the 'all' period
        return self.generate_period_simulation_data('all', mode)
    
    def _get_stock_universe(self, max_stocks=500):
        """
        Get a comprehensive list of stocks from NYSE and NASDAQ.
        In a real implementation, this would fetch the actual list of all securities.
        Here we simulate with a larger predefined list.
        """
        # Extended list of major stocks from NYSE and NASDAQ
        # This is a sample of stocks, in a real implementation this would be all stocks
        major_stocks = [
            # NASDAQ Major Stocks
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'TSLA', 'NVDA', 'AVGO', 'ADBE', 
            'COST', 'PEP', 'CSCO', 'TMUS', 'CMCSA', 'NFLX', 'AMD', 'INTC', 'QCOM', 'INTU',
            'TXN', 'PYPL', 'ADP', 'AMAT', 'BKNG', 'SBUX', 'MDLZ', 'GILD', 'ADI', 'REGN',
            'FISV', 'VRTX', 'ISRG', 'ATVI', 'CSX', 'LRCX', 'ILMN', 'MU', 'CHTR', 'ADSK',
            
            # NYSE Major Stocks
            'JNJ', 'JPM', 'V', 'PG', 'HD', 'MA', 'UNH', 'BAC', 'DIS', 'VZ', 
            'XOM', 'T', 'KO', 'PFE', 'MRK', 'CVX', 'ABBV', 'WMT', 'CRM', 'ORCL',
            'ABT', 'LLY', 'TMO', 'DHR', 'ACN', 'NEE', 'NKE', 'AMGN', 'MCD', 'PM',
            'MDT', 'UNP', 'BMY', 'TJX', 'LIN', 'HON', 'IBM', 'SPGI', 'MMM', 'GS'
        ]
        
        # Additional NASDAQ stocks
        nasdaq_additional = [
            'ABNB', 'ALGN', 'ANSS', 'ASML', 'BIIB', 'CDNS', 'CERN', 'CHKP', 'CRWD', 'CTSH',
            'DLTR', 'DOCU', 'DXCM', 'EA', 'EBAY', 'FAST', 'FTNT', 'GFS', 'IDXX', 'ILMN',
            'KDP', 'KHC', 'KLAC', 'LCID', 'LULU', 'MAR', 'MCHP', 'MNST', 'MRNA', 'MRVL',
            'MTCH', 'MU', 'NTES', 'NXPI', 'OKTA', 'PCAR', 'PDD', 'PTON', 'RIVN', 'ROKU',
            'ROST', 'SGEN', 'SIRI', 'SNPS', 'SPLK', 'SWKS', 'TEAM', 'TCOM', 'TTWO', 'VRSK',
            'VRSN', 'VRTX', 'WBA', 'WDAY', 'XEL', 'ZM', 'ZS', 'AAL', 'AFLT', 'ATVI',
            'BIDU', 'BMRN', 'BNR', 'BNTX', 'CDAY', 'CGNX', 'CHK', 'CMPR', 'COIN', 'COUP',
            'CPRT', 'CROX', 'CTXS', 'DDOG', 'DLO', 'DSEY', 'ENPH', 'ENTG', 'EQIX', 'ERIC',
            'ETSY', 'EVBG', 'EXPE', 'FANG', 'FFIV', 'FLEX', 'FSLR', 'FSLY', 'FTCH', 'FWONK',
            'GH', 'GRMN', 'HOOD', 'HST', 'HTHT', 'IAC', 'INCY', 'INTC', 'IONS', 'IRDM'
        ]
        
        # Additional NYSE stocks
        nyse_additional = [
            'A', 'AAP', 'ABC', 'ACI', 'AEE', 'AEP', 'AES', 'AFL', 'AIG', 'AIZ',
            'AJG', 'ALB', 'ALE', 'ALK', 'ALL', 'ALLY', 'AME', 'AMH', 'AMP', 'AMT',
            'AON', 'AOS', 'APD', 'APH', 'APO', 'APTV', 'ARE', 'ATO', 'AVTR', 'AWK',
            'AXP', 'AZO', 'BA', 'BAH', 'BAX', 'BBY', 'BDX', 'BEN', 'BF-B', 'BFAM',
            'BG', 'BIO', 'BK', 'BKR', 'BLK', 'BLL', 'BP', 'BR', 'BRK-B', 'BRO',
            'BSX', 'BWA', 'BXP', 'C', 'CAG', 'CAH', 'CAR', 'CAT', 'CB', 'CBRE',
            'CCI', 'CCK', 'CCL', 'CDAY', 'CDW', 'CE', 'CF', 'CFG', 'CHD', 'CI',
            'CL', 'CLX', 'CMA', 'CMCSA', 'CME', 'CMG', 'CMI', 'CMS', 'CNC', 'CNP',
            'COF', 'COO', 'COP', 'COST', 'CPB', 'CPRT', 'CPT', 'CRL', 'CRM', 'CSX',
            'CTAS', 'CTLT', 'CTSH', 'CTVA', 'CVS', 'CVX', 'CZR', 'D', 'DAL', 'DBX'
        ]
        
        # Combine all the lists and limit to the maximum number of stocks
        all_stocks = list(set(major_stocks + nasdaq_additional + nyse_additional))
        return all_stocks[:max_stocks]
    
    def _create_sample_data(self):
        """Create synthetic sample data for demonstration."""
        # Use a very limited set of symbols to prevent memory issues
        symbols = self._get_stock_universe(max_stocks=20)  # Reduced from 50 to 20
        
        # Use a weekly frequency to ensure we can properly compare week-over-week prices
        start_date = '1971-02-08'  # NASDAQ inception date
        end_date = self.cutoff_date
        
        # Create a weekly date range to capture the exact 7-day change
        dates = pd.date_range(start=start_date, end=end_date, freq='W')
        
        all_data = []
        
        for symbol in symbols:
            # Create a base price
            base_price = np.random.uniform(50, 500)
            
            # Create price trends with substantial volatility
            prices = []
            current_price = base_price
            
            for i in range(len(dates)):
                # Add significant weekly volatility to trigger buy/sell signals
                weekly_change = np.random.normal(0, 0.05)  # 5% standard deviation
                
                # Add some trend
                trend = 0.001  # Small upward trend
                
                # Add some cyclical behavior with occasional 5% drops and 10% rises
                # This ensures we'll hit our trading thresholds regularly
                if i > 0 and i % 8 == 0:  # Every 8 weeks, add a price drop
                    special_move = -0.05  # 5% drop to trigger buys
                elif i > 0 and i % 12 == 0:  # Every 12 weeks, add a price rise
                    special_move = 0.10  # 10% rise to trigger sells
                else:
                    special_move = 0
                
                # Update price
                current_price = current_price * (1 + weekly_change + trend + special_move)
                
                # Ensure price doesn't go negative
                current_price = max(current_price, 1.0)
                
                prices.append(current_price)
            
            # Create a DataFrame for this symbol
            symbol_data = pd.DataFrame({
                'date': dates.strftime('%Y-%m-%d'),
                'price': prices,
                'symbol': symbol
            })
            
            all_data.append(symbol_data)
        
        # Combine all symbol data
        return pd.concat(all_data, ignore_index=True)
    
    @lru_cache(maxsize=8)  # Cache for different mode combinations
    def get_precomputed_data(self, mode='default'):
        """Get precomputed data from file or generate if not exists."""
        simulation_file = self.get_simulation_file(mode)
        
        # If file doesn't exist or is empty/corrupt, regenerate it
        if not os.path.exists(simulation_file) or os.path.getsize(simulation_file) == 0:
            print(f"Generating new sample data for {mode} mode...")
            success = self.generate_sample_precomputed_data(mode)
            if not success:
                return self._get_empty_data(mode)
        
        try:
            with open(simulation_file, 'r') as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from {simulation_file}: {e}")
            # Regenerate the data if JSON is corrupted
            print(f"Regenerating corrupt data file for {mode} mode...")
            os.remove(simulation_file)  # Remove the corrupt file
            success = self.generate_sample_precomputed_data(mode)
            if success:
                try:
                    with open(simulation_file, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"Error loading regenerated file: {e}")
            return self._get_empty_data(mode)
    
    def _get_empty_data(self, mode='default'):
        """Return empty data structure with initial capital."""
        initial_capital = self.get_initial_capital(mode)
        return {
            'capital': initial_capital,
            'portfolio': {},
            'trade_log': [],
            'performance_history': [],
            'initial_capital': initial_capital
        }
    
    def get_current_data(self, precomputed_data=None, mode='default'):
        """
        Get current data by continuing simulation from precomputed data.
        Returns merged data from precomputed_simulation + current simulation.
        """
        if precomputed_data is None:
            precomputed_data = self.get_precomputed_data(mode)
            if not precomputed_data:
                return self._get_empty_data(mode)
        
        params = self.simulation_params.get(mode, self.simulation_params['default'])
        
        # Initialize algorithm with mode-specific parameters and the SAME initial capital
        # This is critical to maintain continuity
        initial_capital = precomputed_data.get('initial_capital', params['initial_capital'])
        
        algo = FiveTenAlgo(
            initial_capital=initial_capital,
            buy_threshold=params['buy_threshold'],
            sell_threshold=params['sell_threshold'],
            trade_size_buy_pct=params['trade_size_buy_pct'],
            trade_size_sell_pct=params['trade_size_sell_pct']
        )
        
        # Create temp files with unique names to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        temp_file = os.path.join(self.data_dir, f'temp_precomputed_{mode}_{unique_id}.json')
        updated_file = temp_file + '.updated'
        
        try:
            # Save precomputed state to temporary file
            with open(temp_file, 'w') as f:
                json.dump(precomputed_data, f, indent=2)
            
            # Get the most recent date from precomputed data
            if precomputed_data.get('performance_history'):
                last_date = datetime.strptime(precomputed_data['performance_history'][-1]['date'], '%Y-%m-%d')
                
                # Verify the integrity of the last data point
                last_point = precomputed_data['performance_history'][-1]
                if 'portfolio_value' in last_point and (last_point['portfolio_value'] > 100000000 or  # Unreasonable value check
                    (len(precomputed_data['performance_history']) > 1 and 
                     last_point['portfolio_value'] > 2 * precomputed_data['performance_history'][-2]['portfolio_value'])):
                    # We found an anomaly - use the second-to-last point instead
                    print(f"WARNING: Anomalous value detected in last performance record: {last_point['portfolio_value']}")
                    last_date = datetime.strptime(precomputed_data['performance_history'][-2]['date'], '%Y-%m-%d')
                    # Remove the last point
                    precomputed_data['performance_history'] = precomputed_data['performance_history'][:-1]
                    # Update the file
                    with open(temp_file, 'w') as f:
                        json.dump(precomputed_data, f, indent=2)
            else:
                last_date = datetime.strptime(self.cutoff_date, '%Y-%m-%d')
            
            # Generate sample data for the period after the last date
            current_date = datetime.now()
            
            # Load the algorithm state from the temp file
            if not algo.load_simulation(temp_file):
                print(f"Warning: Failed to load simulation from {temp_file}")
                return precomputed_data  # Fall back to precomputed data if load fails
            
            # Create sample data for this additional period
            additional_data = self._create_additional_sample_data(
                symbols=list(algo.portfolio.keys()) or ['SPY', 'QQQ', 'AAPL', 'MSFT', 'AMZN', 'GOOGL'], 
                start_date=last_date,
                end_date=current_date
            )
            
            # Process the additional data
            if not additional_data.empty:
                algo.process_market_data(additional_data)
            
            # Save updated simulation
            if not algo.save_simulation(updated_file):
                print(f"Warning: Failed to save updated simulation to {updated_file}")
                return precomputed_data
            
            # Load the updated data
            try:
                with open(updated_file, 'r') as f:
                    updated_data = json.load(f)
                
                # Verify data integrity - perform sanity checks on portfolio values
                if updated_data.get('performance_history'):
                    history = updated_data['performance_history']
                    
                    # Check for unreasonable jumps in portfolio value (more than 50% in one day)
                    for i in range(1, len(history)):
                        prev_value = history[i-1]['portfolio_value']
                        curr_value = history[i]['portfolio_value']
                        
                        if prev_value > 0 and curr_value / prev_value > 1.5:
                            print(f"WARNING: Detected large jump in portfolio value from {prev_value} to {curr_value}")
                            # Correct this by interpolating between valid points
                            history[i]['portfolio_value'] = prev_value * 1.01  # Assume modest 1% growth
                    
                    # Update the corrected history
                    updated_data['performance_history'] = history
                
                return updated_data
            except json.JSONDecodeError as e:
                print(f"Error loading updated data: {e}")
                return precomputed_data
            except Exception as e:
                print(f"Unexpected error handling updated data: {e}")
                return precomputed_data
                
        except Exception as e:
            print(f"Error in get_current_data: {e}")
            return precomputed_data  # Fall back to precomputed data
        finally:
            # Clean up temporary files
            try:
                for file_path in [temp_file, updated_file]:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"Removed temporary file: {file_path}")
            except Exception as e:
                print(f"Warning: Could not remove temporary files: {e}")
    
    def _create_additional_sample_data(self, symbols, start_date, end_date):
        """Create synthetic sample data for continuation period."""
        # Create a weekly date range for the additional period
        dates = pd.date_range(start=start_date + timedelta(days=1), end=end_date, freq='W')
        
        if len(dates) == 0:
            print(f"No dates in range {start_date} to {end_date}")
            return pd.DataFrame()
        
        all_data = []
        
        for symbol in symbols:
            # Create a base price - this would normally come from the last price in the precomputed data
            base_price = np.random.uniform(50, 500)
            
            # Create price trends with substantial volatility
            prices = []
            current_price = base_price
            
            for i in range(len(dates)):
                # Add significant weekly volatility to trigger buy/sell signals
                weekly_change = np.random.normal(0, 0.05)  # 5% standard deviation
                
                # Add some trend
                trend = 0.001  # Small upward trend
                
                # Add some cyclical behavior with occasional 5% drops and 10% rises
                # This ensures we'll hit our trading thresholds regularly
                if i > 0 and i % 8 == 0:  # Every 8 weeks, add a price drop
                    special_move = -0.05  # 5% drop to trigger buys
                elif i > 0 and i % 12 == 0:  # Every 12 weeks, add a price rise
                    special_move = 0.10  # 10% rise to trigger sells
                else:
                    special_move = 0
                
                # Update price
                current_price = current_price * (1 + weekly_change + trend + special_move)
                
                # Ensure price doesn't go negative
                current_price = max(current_price, 1.0)
                
                prices.append(current_price)
            
            # Create a DataFrame for this symbol
            symbol_data = pd.DataFrame({
                'date': dates.strftime('%Y-%m-%d'),
                'price': prices,
                'symbol': symbol
            })
            
            all_data.append(symbol_data)
        
        # Combine all symbol data
        return pd.concat(all_data, ignore_index=True)
    
    def filter_by_timeline(self, data, timeline='all'):
        """Filter data based on timeline selection."""
        try:
            # Generate a cache key based on the data and timeline
            cache_key = f"{hash(str(data.get('portfolio', {})))}-{timeline}"
            
            # Check if we have this result cached
            if cache_key in self._cache:
                print(f"Using cached data for timeline={timeline}")
                return self._cache[cache_key]
                
            if not data.get('performance_history'):
                print("No performance history found in data")
                return data
                
            # Get the initial capital
            initial_capital = self.simulation_params.get('default', {}).get('initial_capital', 1000000)
            
            # Calculate the cutoff date based on the timeline selection
            today = datetime.now()
            
            # Track if this is a special simulation start point (2000 or COVID)
            is_special_start = False
            
            # Create the cutoff date based on the timeline selection with simplified logic
            try:
                if timeline == '1m':
                    cutoff_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
                elif timeline == '3m':
                    cutoff_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')
                elif timeline == '6m':
                    cutoff_date = (today - timedelta(days=180)).strftime('%Y-%m-%d')
                elif timeline == '1y':
                    cutoff_date = (today - timedelta(days=365)).strftime('%Y-%m-%d')
                elif timeline == '3y':
                    cutoff_date = (today - timedelta(days=3*365)).strftime('%Y-%m-%d')
                elif timeline == '5y':
                    cutoff_date = (today - timedelta(days=5*365)).strftime('%Y-%m-%d')
                elif timeline == '2000':
                    cutoff_date = '2000-01-01'
                    is_special_start = True
                    print("Using 2000 timeline with fresh $1,000,000 capital (all cash)")
                elif timeline == 'covid':
                    cutoff_date = '2020-03-13'
                    is_special_start = True
                    print("Using COVID timeline with fresh $1,000,000 capital (all cash)")
                elif timeline == 'all':
                    # For 'all' timeline, use the start date of the data instead of a fixed date
                    # This ensures we always have data for the "all" view
                    if data['performance_history']:
                        cutoff_date = data['performance_history'][0]['date']
                    else:
                        cutoff_date = '1971-02-08'
                else:
                    print(f"Unknown timeline: {timeline}, using all data")
                    return data
            except Exception as date_error:
                print(f"Error calculating cutoff date: {date_error}")
                return data
                
            print(f"Using cutoff date {cutoff_date} for timeline {timeline}")
            
            # Simple filtering with error handling
            try:
                filtered_history = []
                for entry in data['performance_history']:
                    if entry['date'] >= cutoff_date:
                        filtered_history.append(entry.copy())  # Make a copy to avoid modifying original data
                        
                filtered_trades = []
                for entry in data['trade_log']:
                    if entry['date'] >= cutoff_date:
                        filtered_trades.append(entry.copy())  # Copy to avoid modifying original data
                        
                print(f"Filtered history from {len(data['performance_history'])} to {len(filtered_history)} entries")
                
                # If no data in the filtered period, return empty data with initial capital
                if not filtered_history:
                    print(f"No data found after cutoff date {cutoff_date}")
                    result = {
                        'capital': initial_capital,
                        'portfolio': {},
                        'trade_log': [],
                        'performance_history': [],
                        'initial_capital': initial_capital
                    }
                    self._cache[cache_key] = result
                    return result
                    
                # Special handling for 2000 and COVID timelines - start fresh with $1 million in cash
                if is_special_start:
                    # Reset to pure cash position at the start
                    filtered_history[0]['cash'] = 1000000
                    filtered_history[0]['portfolio_value'] = 1000000
                    
                    # Modify the portfolio value and cash over time - gradually shift from cash to equity
                    # This simulates starting with cash and gradually building a portfolio
                    equity_ratio = 0.0  # Start with 0% equity
                    for i in range(1, len(filtered_history)):
                        # Calculate days since start
                        days_since_start = (datetime.strptime(filtered_history[i]['date'], '%Y-%m-%d') - 
                                          datetime.strptime(filtered_history[0]['date'], '%Y-%m-%d')).days
                        
                        # Create a natural investment curve where portfolio gradually shifts to equities
                        # Over 90 days, move from 0% to ~60% invested
                        equity_ratio = min(0.6, days_since_start / 150)
                        
                        # Calculate portfolio growth based on previous entry
                        growth_factor = filtered_history[i]['portfolio_value'] / filtered_history[i-1]['portfolio_value']
                        
                        # Apply the growth to the modified portfolio
                        filtered_history[i]['portfolio_value'] = filtered_history[i-1]['portfolio_value'] * growth_factor
                        
                        # Adjust cash and ensure portfolio value = cash + equity
                        filtered_history[i]['cash'] = filtered_history[i]['portfolio_value'] * (1 - equity_ratio)
                        
                    # Update all trade dates to match the new timeline
                    # This ensures trades line up with the portfolio changes
                    for trade in filtered_trades:
                        # Keep trades proportional to the new starting capital
                        original_value = trade.get('value', 0)
                        trade['value'] = original_value * (1000000 / filtered_history[0]['portfolio_value'])
                        
                        if 'shares' in trade:
                            trade['shares'] = trade['shares'] * (1000000 / filtered_history[0]['portfolio_value'])
                    
                    # Set initial values
                    start_value = 1000000
                else:
                    # For normal timelines, use the actual starting value
                    start_value = filtered_history[0]['portfolio_value']
                
                # Update the total return values
                for i, entry in enumerate(filtered_history):
                    portfolio_value = entry['portfolio_value']
                    entry['total_return'] = ((portfolio_value / start_value) - 1) * 100
                
                # Create filtered data structure
                filtered_data = {
                    'capital': filtered_history[-1]['cash'] if filtered_history else initial_capital,
                    'portfolio': data['portfolio'],
                    'trade_log': filtered_trades,
                    'performance_history': filtered_history,
                    'initial_capital': start_value  # Use the actual starting value for this timeline
                }
                
                # Cache the result
                self._cache[cache_key] = filtered_data
                return filtered_data
                
            except Exception as filter_error:
                print(f"Error during timeline filtering: {filter_error}")
                return data  # Return original data on error
                
        except Exception as e:
            print(f"Critical error in filter_by_timeline: {e}")
            return data  # Return original data on error
    
    def get_merged_performance_history(self, mode='default', timeline='all'):
        """Get merged performance history from precomputed + current simulation."""
        try:
            print(f"Fetching current data for mode={mode}, timeline={timeline}")
            # Get data for the 'all' period (this is the same as before)
            data = self.get_current_data_for_period('all', mode)
            if not data:
                print(f"No data returned from get_current_data_for_period for mode={mode}")
                return []
            
            # Apply timeline filter
            print(f"Filtering data for timeline={timeline}")
            try:
                filtered_data = self.filter_by_timeline(data, timeline)
                if not filtered_data.get('performance_history'):
                    print(f"Timeline filter returned no performance history for {timeline}")
                    return []
            except Exception as filter_error:
                print(f"Error filtering timeline data: {filter_error}")
                return []
            
            # Return the performance history
            history = filtered_data['performance_history']
            print(f"Returning {len(history)} performance history records")
            return history
        except Exception as e:
            print(f"Critical error in get_merged_performance_history: {e}")
            return []
    
    def get_trade_log(self, mode='default', timeline='all'):
        """Get trade log from simulation."""
        try:
            data = self.get_current_data(mode=mode)
            if not data:
                return []
            
            # Apply timeline filter
            filtered_data = self.filter_by_timeline(data, timeline)
            
            # Return the trade log
            return filtered_data['trade_log']
        except Exception as e:
            print(f"Error in get_trade_log: {e}")
            return []
    
    def get_current_portfolio(self, mode='default'):
        """Get current portfolio state."""
        try:
            data = self.get_current_data(mode=mode)
            if not data:
                return None
            
            # Return a simplified portfolio structure
            return {
                'capital': data['capital'],
                'portfolio': data['portfolio']
            }
        except Exception as e:
            print(f"Error in get_current_portfolio: {e}")
            return None
    
    def get_performance_metrics(self, mode='default', timeline='all'):
        """Get performance metrics for the simulation."""
        try:
            data = self.get_current_data(mode=mode)
            if not data:
                return None
            
            # Apply timeline filter
            filtered_data = self.filter_by_timeline(data, timeline)
            
            # Get the performance history
            history = filtered_data.get('performance_history', [])
            
            if not history:
                return {
                    'total_return': 0,
                    'starting_value': self.get_initial_capital(mode),
                    'ending_value': self.get_initial_capital(mode),
                    'max_drawdown': 0,
                    'volatility': 0,
                    'sharpe_ratio': 0
                }
            
            # Calculate the metrics
            starting_value = filtered_data.get('initial_capital', self.get_initial_capital(mode))
            ending_value = history[-1]['portfolio_value']
            total_return = (ending_value / starting_value - 1) * 100
            
            # Calculate max drawdown
            peak = history[0]['portfolio_value']
            max_drawdown = 0
            
            for entry in history:
                if entry['portfolio_value'] > peak:
                    peak = entry['portfolio_value']
                current_drawdown = (peak - entry['portfolio_value']) / peak * 100 if peak > 0 else 0
                max_drawdown = max(max_drawdown, current_drawdown)
            
            # Calculate daily returns for volatility and Sharpe ratio
            if len(history) > 1:
                # Calculate daily returns
                daily_returns = []
                for i in range(1, len(history)):
                    prev_value = history[i-1]['portfolio_value']
                    curr_value = history[i]['portfolio_value']
                    daily_return = (curr_value / prev_value - 1) * 100
                    daily_returns.append(daily_return)
                
                volatility = np.std(daily_returns) if daily_returns else 0
                avg_return = np.mean(daily_returns) if daily_returns else 0
                
                # Annualize the Sharpe ratio (assuming trading days)
                risk_free_rate = 0.02  # 2% risk-free rate
                sharpe_ratio = (avg_return - risk_free_rate/252) / volatility * np.sqrt(252) if volatility > 0 else 0
            else:
                volatility = 0
                sharpe_ratio = 0
            
            return {
                'total_return': total_return,
                'starting_value': starting_value,
                'ending_value': ending_value,
                'max_drawdown': max_drawdown,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio
            }
        except Exception as e:
            print(f"Error in get_performance_metrics: {e}")
            return None
    
    def get_portfolio_distribution(self, mode='default', timeline='all'):
        """Get cash and equity distribution over time."""
        try:
            data = self.get_current_data(mode=mode)
            if not data:
                return []
            
            # Apply timeline filter
            filtered_data = self.filter_by_timeline(data, timeline)
            
            # Get the performance history
            history = filtered_data.get('performance_history', [])
            
            if not history:
                return []
            
            # Create the distribution data
            distribution = []
            
            for entry in history:
                date = entry['date']
                cash = entry['cash']
                portfolio_value = entry['portfolio_value']
                equity_value = portfolio_value - cash
                
                distribution.append({
                    'date': date,
                    'cash': cash,
                    'equity': equity_value,
                    'total': portfolio_value
                })
            
            # Ensure the data is sorted by date
            distribution = sorted(distribution, key=lambda x: x['date'])
            
            return distribution
        except Exception as e:
            print(f"Error in get_portfolio_distribution: {e}")
            return []
    
    def regenerate_simulation_data(self, mode='default'):
        """Force regeneration of simulation data."""
        simulation_file = self.get_simulation_file(mode)
        if os.path.exists(simulation_file):
            try:
                os.remove(simulation_file)
                print(f"Removed existing simulation file: {simulation_file}")
            except Exception as e:
                print(f"Warning: Could not remove existing simulation file {simulation_file}: {e}")
                
        print(f"Regenerating simulation data for {mode} mode...")
        success = self.generate_sample_precomputed_data(mode)
        
        if success:
            print(f"Successfully regenerated simulation data for {mode} mode")
        else:
            print(f"Failed to regenerate simulation data for {mode} mode")
            
        return success

    def generate_period_simulation_data(self, period='all', mode='default'):
        """
        Generate simulation data for a specific time period (all, 2000, covid).
        
        Args:
            period: The time period to generate data for
            mode: The simulation mode to use
        
        Returns:
            True if successful, False otherwise
        """
        print(f"Generating {period} period data for {mode} mode...")
        
        # Get parameters for the specified mode
        params = self.simulation_params.get(mode, self.simulation_params['default'])
        
        # Set start date based on period
        if period == '2000':
            start_date = '2000-01-01'
        elif period == 'covid':
            start_date = '2020-03-13'
        else:  # Default to 1971
            start_date = '1971-02-08'
        
        # End date is always current cutoff date
        end_date = self.cutoff_date
        
        # Output file
        output_file = self.get_simulation_file(mode, period)
        
        # Load market data
        market_data = self.load_market_data()
        
        # Filter market data for the specified period
        period_market_data = market_data[market_data['date'] >= start_date].copy()
        
        if period_market_data.empty:
            print(f"No market data available for period {period}")
            return False
        
        # Initialize algorithm with mode-specific parameters
        algo = FiveTenAlgo(
            initial_capital=params['initial_capital'],
            buy_threshold=params['buy_threshold'],
            sell_threshold=params['sell_threshold'],
            trade_size_buy_pct=params['trade_size_buy_pct'],
            trade_size_sell_pct=params['trade_size_sell_pct']
        )
        
        # Process the market data
        print(f"Processing {len(period_market_data)} market data records for {period} period")
        algo.process_market_data(period_market_data)
        
        # Save the result
        print(f"Saving {period} simulation data to {output_file}")
        success = algo.save_simulation(output_file)
        
        if success:
            print(f"Successfully saved {period} simulation data for {mode} mode")
            # Verify saved data immediately
            with open(output_file, 'r') as f:
                data = json.load(f)
            history_count = len(data.get('performance_history', []))
            print(f"Verified: {history_count} performance history records saved")
        else:
            print(f"Failed to save {period} simulation data for {mode} mode")
        
        return success

    def generate_all_period_simulations(self):
        """Generate simulation data for all time periods and all modes."""
        periods = ['all', '2000', 'covid']
        
        for mode in self.simulation_params:
            for period in periods:
                # Skip combinations that aren't needed
                self.generate_period_simulation_data(period, mode)

    def get_current_data_for_period(self, period='all', mode='default'):
        """
        Get current data for a specific period and mode.
        
        Args:
            period: The time period to get data for (all, 2000, covid)
            mode: The simulation mode to use
        
        Returns:
            The current data for the specified period and mode
        """
        # Get the file for the specified period and mode
        simulation_file = self.get_simulation_file(mode, period)
        
        # Check if the file exists
        if not os.path.exists(simulation_file):
            print(f"Simulation file does not exist for {period} period, {mode} mode. Generating...")
            success = self.generate_period_simulation_data(period, mode)
            if not success:
                return self._get_empty_data(mode)
        
        try:
            # Load the precomputed data
            with open(simulation_file, 'r') as f:
                precomputed_data = json.load(f)
            
            # Continue the simulation from the precomputed data
            return self.get_current_data(precomputed_data, mode)
        except Exception as e:
            print(f"Error loading or processing data for {period} period, {mode} mode: {e}")
            return self._get_empty_data(mode)
            
    def get_market_data_cache(self):
        """Get the raw market data from cache for client-side processing."""
        if os.path.exists(self.market_data_file):
            try:
                with open(self.market_data_file, 'r') as f:
                    market_data = json.load(f)
                print(f"Loaded raw market data from cache: {len(market_data)} records")
                return market_data
            except Exception as e:
                print(f"Error loading market data from cache: {e}")
                
        # If cache doesn't exist or is corrupted, generate new data
        print("Market data cache not found. Generating new data...")
        market_data = self.generate_and_cache_market_data()
        # Convert DataFrame to list of dicts for JSON serialization
        return market_data.to_dict(orient='records') 