from flask import Flask, render_template, jsonify, request, current_app, redirect, url_for
import os
import json
from models.data_processor import DataProcessor
from functools import lru_cache
import time

app = Flask(__name__)
data_processor = DataProcessor(data_dir='data')

# Add an in-memory cache with expiration
cache = {}
CACHE_TIMEOUT = 60  # seconds

def get_cached_data(key, callback, *args, **kwargs):
    """Simple cache implementation with timeout"""
    current_time = time.time()
    if key in cache and current_time - cache[key]['timestamp'] < CACHE_TIMEOUT:
        return cache[key]['data']
    
    try:
        # Call the function to get fresh data
        data = callback(*args, **kwargs)
        
        # Store in cache
        cache[key] = {
            'data': data,
            'timestamp': current_time
        }
        
        return data
    except Exception as e:
        print(f"Error retrieving data for {key}: {e}")
        # If there was a cached version, use it even if expired
        if key in cache:
            print(f"Using expired cache for {key}")
            return cache[key]['data']
        # Otherwise return a default value (empty list or dict)
        return [] if key.startswith(('performance_history', 'trade_log', 'distribution')) else {}

# Initialize data before server starts
def initialize_data():
    """Initialize data before starting the server."""
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Clear the cache
    global cache
    cache = {}
    
    # First, generate and cache market data (done only once)
    print("Checking for cached market data...")
    data_processor.generate_and_cache_market_data()
    
    # Force regeneration of all simulation modes to use the updated date range
    print("Generating simulation data files for all periods...")
    
    # Generate separate files for each period (all, 2000, covid) and each mode
    periods = ['all', '2000', 'covid']
    for mode in data_processor.simulation_params:
        for period in periods:
            print(f"Generating {period} period data for {mode} mode...")
            file_path = data_processor.get_simulation_file(mode, period)
            
            # Remove existing file
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Removed existing file: {file_path}")
                except Exception as e:
                    print(f"Warning: Could not remove {file_path}: {e}")
            
            # Generate new data
            data_processor.generate_period_simulation_data(period, mode)
    
    print("Data generation complete.")

# Call initialize data at startup
initialize_data()

@app.route('/')
def index():
    """Render the landing page."""
    return render_template('landing.html')

@app.route('/dashboard')
def dashboard():
    """Render the dashboard page."""
    return render_template('index.html')

@app.route('/api/performance_history')
def get_performance_history():
    """API endpoint to get performance history."""
    try:
        simulation_mode = request.args.get('mode', 'default')
        timeline = request.args.get('timeline', 'all')
        period = request.args.get('period', 'all')  # New parameter for period (all, 2000, covid)
        
        print(f"Fetching performance history for mode={simulation_mode}, period={period}, timeline={timeline}")
        
        cache_key = f"performance_history_{simulation_mode}_{period}_{timeline}"
        
        # Try to get data from the processor
        try:
            # For period=all, filter by timeline
            # For period=2000 or period=covid, get data for that specific period
            if period in ['2000', 'covid']:
                # Get data from period-specific file
                data = data_processor.get_current_data_for_period(period, simulation_mode)
                # Apply timeline filtering if needed
                if timeline != 'all':
                    data = data_processor.filter_by_timeline(data, timeline)
                history = data.get('performance_history', [])
            else:
                # Use merged performance history with timeline filtering
                history = data_processor.get_merged_performance_history(simulation_mode, timeline)
            
            if not history:
                print(f"Warning: Empty performance history returned for {simulation_mode}/{period}/{timeline}")
        except Exception as e:
            print(f"Error getting performance history directly: {e}")
            # Fall back to cached data or an empty list
            history = cache.get(cache_key, {}).get('data', []) if cache_key in cache else []
        
        # Ensure the data is sorted by date
        if history:
            try:
                history = sorted(history, key=lambda x: x['date'])
                print(f"Successfully prepared {len(history)} data points for {simulation_mode}/{period}/{timeline}")
            except Exception as sorting_error:
                print(f"Error sorting history data: {sorting_error}")
        else:
            print("Returning empty history list")
            
        return jsonify(history)
    except Exception as e:
        print(f"Critical error in performance_history endpoint: {e}")
        return jsonify([])

@app.route('/api/trade_log')
def get_trade_log():
    """API endpoint to get trade log."""
    try:
        simulation_mode = request.args.get('mode', 'default')
        timeline = request.args.get('timeline', 'all')
        period = request.args.get('period', 'all')  # New parameter for period
        
        cache_key = f"trade_log_{simulation_mode}_{period}_{timeline}"
        
        if period in ['2000', 'covid']:
            # Get data from period-specific file
            data = data_processor.get_current_data_for_period(period, simulation_mode)
            # Apply timeline filtering if needed
            if timeline != 'all':
                data = data_processor.filter_by_timeline(data, timeline)
            log = data.get('trade_log', [])
        else:
            # Use standard approach
            log = get_cached_data(
                cache_key,
                data_processor.get_trade_log,
                simulation_mode, 
                timeline
            )
        
        # Ensure the data is sorted by date
        if log:
            log = sorted(log, key=lambda x: x['date'])
            
        return jsonify(log)
    except Exception as e:
        print(f"Error in trade_log endpoint: {e}")
        return jsonify([])

@app.route('/api/portfolio')
def get_portfolio():
    """API endpoint to get current portfolio state."""
    try:
        simulation_mode = request.args.get('mode', 'default')
        period = request.args.get('period', 'all')  # New parameter for period
        
        cache_key = f"portfolio_{simulation_mode}_{period}"
        
        if period in ['2000', 'covid']:
            # Get data from period-specific file
            data = data_processor.get_current_data_for_period(period, simulation_mode)
            portfolio = {
                'capital': data.get('capital', 0),
                'portfolio': data.get('portfolio', {})
            }
        else:
            # Use standard approach
            portfolio = get_cached_data(
                cache_key,
                data_processor.get_current_portfolio,
                simulation_mode
            )
        
        return jsonify(portfolio if portfolio else {'capital': 0, 'portfolio': {}})
    except Exception as e:
        print(f"Error in portfolio endpoint: {e}")
        return jsonify({'capital': 0, 'portfolio': {}})

@app.route('/api/metrics')
def get_metrics():
    """API endpoint to get performance metrics."""
    try:
        simulation_mode = request.args.get('mode', 'default')
        timeline = request.args.get('timeline', 'all')
        period = request.args.get('period', 'all')  # New parameter for period
        
        cache_key = f"metrics_{simulation_mode}_{period}_{timeline}"
        
        if period in ['2000', 'covid']:
            # Get data from period-specific file
            data = data_processor.get_current_data_for_period(period, simulation_mode)
            # Apply timeline filtering if needed
            if timeline != 'all':
                data = data_processor.filter_by_timeline(data, timeline)
            
            # Calculate metrics
            history = data.get('performance_history', [])
            
            if not history:
                metrics = {
                    'total_return': 0,
                    'starting_value': 1000000,
                    'ending_value': 1000000,
                    'max_drawdown': 0,
                    'volatility': 0,
                    'sharpe_ratio': 0
                }
            else:
                starting_value = 1000000  # Always start with $1M for these periods
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
                
                metrics = {
                    'total_return': total_return,
                    'starting_value': starting_value,
                    'ending_value': ending_value,
                    'max_drawdown': max_drawdown
                }
        else:
            # Use standard approach
            metrics = get_cached_data(
                cache_key,
                data_processor.get_performance_metrics,
                simulation_mode, 
                timeline
            )
        
        return jsonify(metrics if metrics else {})
    except Exception as e:
        print(f"Error in metrics endpoint: {e}")
        return jsonify({})

@app.route('/api/status')
def get_status():
    """API endpoint to get the application status."""
    precomputed_exists = os.path.exists(os.path.join('data', 'precomputed_simulation.json'))
    
    return jsonify({
        'status': 'ready' if precomputed_exists else 'initializing',
        'precomputed_data_available': precomputed_exists,
        'cutoff_date': data_processor.cutoff_date
    })

@app.route('/api/distribution')
def get_distribution():
    """API endpoint to get cash/equity distribution over time."""
    try:
        simulation_mode = request.args.get('mode', 'default')
        timeline = request.args.get('timeline', 'all')
        period = request.args.get('period', 'all')  # New parameter for period
        
        cache_key = f"distribution_{simulation_mode}_{period}_{timeline}"
        
        if period in ['2000', 'covid']:
            # Get data from period-specific file
            data = data_processor.get_current_data_for_period(period, simulation_mode)
            # Apply timeline filtering if needed
            if timeline != 'all':
                data = data_processor.filter_by_timeline(data, timeline)
            
            # Extract distribution data
            history = data.get('performance_history', [])
            
            distribution = []
            for entry in history:
                distribution.append({
                    'date': entry['date'],
                    'cash': entry.get('cash', 0),
                    'equity': entry['portfolio_value'] - entry.get('cash', 0),
                    'total': entry['portfolio_value']
                })
        else:
            # Use standard approach
            distribution = get_cached_data(
                cache_key,
                data_processor.get_portfolio_distribution,
                simulation_mode, 
                timeline
            )
        
        return jsonify(distribution)
    except Exception as e:
        print(f"Error in distribution endpoint: {e}")
        return jsonify([])

@app.route('/api/test')
def test_endpoint():
    """Simple test endpoint to verify server is running properly."""
    return jsonify({"status": "ok", "message": "Server is running correctly"})

def run_app(port=8080):
    """Run the Flask application."""
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    run_app() 