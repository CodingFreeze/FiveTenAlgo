import argparse
import os
import sys
from models.algorithm import FiveTenAlgo
from models.data_processor import DataProcessor

def generate_precomputed_data(args):
    """Generate precomputed data for a specified date range."""
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    output_file = os.path.join(data_dir, 'precomputed_simulation.json')
    
    # Use default symbols if none provided
    symbols = args.symbols.split(',') if args.symbols else ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA']
    
    print(f"Generating precomputed data for {len(symbols)} symbols from {args.start_date} to {args.end_date}...")
    print(f"Symbols: {', '.join(symbols)}")
    
    # Initialize algorithm
    algo = FiveTenAlgo(initial_capital=args.initial_capital)
    
    # Generate precomputed data
    success = algo.generate_precomputed_data(args.start_date, args.end_date, symbols, output_file)
    
    if success:
        print(f"Successfully generated precomputed data and saved to {output_file}")
        
        # Print summary statistics
        print("\nSummary Statistics:")
        print(f"Initial Capital: ${args.initial_capital:.2f}")
        print(f"Final Capital: ${algo.capital:.2f}")
        print(f"Portfolio Holdings: {len(algo.portfolio)} symbols")
        print(f"Total Trades: {len(algo.trade_log)}")
        
        if algo.performance_history:
            initial_value = args.initial_capital
            final_value = algo.performance_history[-1]['portfolio_value']
            total_return = (final_value / initial_value - 1) * 100
            print(f"Total Return: {total_return:.2f}%")
            print(f"Final Portfolio Value: ${final_value:.2f}")
    else:
        print("Failed to generate precomputed data")

def run_simulation(args):
    """Run a simulation from scratch or continue from existing data."""
    data_processor = DataProcessor(data_dir='data')
    
    if args.continue_from_precomputed:
        if not os.path.exists(os.path.join('data', 'precomputed_simulation.json')):
            print("Error: Precomputed data file does not exist. Generate it first.")
            return
            
        print("Continuing simulation from precomputed data...")
        current_data = data_processor.get_current_data()
        
        if current_data:
            # Print summary
            print("\nSimulation Results:")
            if 'performance_history' in current_data and current_data['performance_history']:
                initial_value = 1000000  # Default initial capital
                final_value = current_data['performance_history'][-1]['portfolio_value']
                total_return = (final_value / initial_value - 1) * 100
                
                print(f"Initial Capital: ${initial_value:.2f}")
                print(f"Final Capital: ${current_data['capital']:.2f}")
                print(f"Portfolio Holdings: {len(current_data['portfolio'])} symbols")
                print(f"Total Trades: {len(current_data['trade_log'])}")
                print(f"Total Return: {total_return:.2f}%")
                print(f"Final Portfolio Value: ${final_value:.2f}")
                print(f"Last Simulation Date: {current_data['performance_history'][-1]['date']}")
            else:
                print("No performance history available.")
        else:
            print("Failed to continue simulation from precomputed data.")
    else:
        print("Generating sample precomputed data...")
        success = data_processor.generate_sample_precomputed_data()
        
        if success:
            print("Successfully generated sample precomputed data.")
            # Get metrics
            metrics = data_processor.get_performance_metrics()
            
            if metrics:
                print("\nSimulation Results:")
                print(f"Total Return: {metrics['total_return_pct']:.2f}%")
                print(f"Annualized Return: {metrics['annualized_return']:.2f}%")
                print(f"Maximum Drawdown: {metrics['max_drawdown']:.2f}%")
                print(f"Final Portfolio Value: ${metrics['latest_value']:.2f}")
                print(f"Latest Date: {metrics['latest_date']}")
            else:
                print("No metrics available.")
        else:
            print("Failed to generate sample precomputed data.")

def parse_args():
    parser = argparse.ArgumentParser(description='FiveTenAlgo CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Add generate-market-data command
    generate_market_parser = subparsers.add_parser('generate-market-data', 
                                              help='Generate and cache market data')
    
    # Add generate command
    generate_parser = subparsers.add_parser('generate', 
                                              help='Generate precomputed simulation data')
    generate_parser.add_argument('--start-date', type=str, default='1971-02-08',
                               help='Start date for simulation (YYYY-MM-DD)')
    generate_parser.add_argument('--end-date', type=str, default='2025-03-01',
                               help='End date for simulation (YYYY-MM-DD)')
    generate_parser.add_argument('--mode', type=str, default='default',
                               choices=['default', 'aggressive', 'conservative', 'balanced'],
                               help='Simulation mode')
    generate_parser.add_argument('--symbols', type=str, default=None,
                               help='Comma-separated list of symbols to include')
    generate_parser.add_argument('--initial-capital', type=float, default=1000000,
                               help='Initial capital for simulation')
    
    # Add regenerate-all command to fix corrupted data
    regenerate_parser = subparsers.add_parser('regenerate-all', 
                                            help='Regenerate all simulation data to fix corrupted files')
    
    # Add run command
    run_parser = subparsers.add_parser('run', help='Run the FiveTenAlgo application')
    run_parser.add_argument('--port', type=int, default=8080,
                           help='Port to run the server on')
    run_parser.add_argument('--continue-from-precomputed', action='store_true',
                          help='Continue simulation from precomputed data')
    
    return parser.parse_args()

def generate_market_data():
    """Generate and cache market data for all simulations."""
    print("Generating market data...")
    data_processor = DataProcessor()
    market_data = data_processor.generate_and_cache_market_data()
    print(f"Market data generation complete. Generated {len(market_data)} records.")
    
def generate_simulation(args):
    """Generate precomputed simulation data."""
    data_processor = DataProcessor()
    
    # Update cutoff date
    data_processor.cutoff_date = args.end_date
    
    # Generate data
    print(f"Generating {args.mode} simulation data...")
    success = data_processor.generate_sample_precomputed_data(args.mode)
    
    if success:
        print("Simulation data generated successfully.")
    else:
        print("Failed to generate simulation data.")

def regenerate_all_simulations():
    """Regenerate all simulation data files to fix corrupted data."""
    data_processor = DataProcessor()
    
    # First, ensure we have market data
    print("Ensuring market data is available...")
    data_processor.generate_and_cache_market_data()
    
    # Delete existing simulation files
    for mode in data_processor.simulation_params:
        file_path = data_processor.get_simulation_file(mode)
        if os.path.exists(file_path):
            try:
                print(f"Removing existing file: {file_path}")
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not remove {file_path}: {e}")
    
    # Generate new data for all simulation modes
    for mode in data_processor.simulation_params:
        print(f"Regenerating {mode} mode simulation data...")
        success = data_processor.generate_sample_precomputed_data(mode)
        if success:
            print(f"Successfully regenerated {mode} simulation data")
        else:
            print(f"Failed to regenerate {mode} simulation data")
    
    print("All simulation data regenerated.")

def run_app(args):
    """Run the Flask application."""
    from app import run_app
    print(f"Starting FiveTenAlgo on port {args.port}...")
    run_app(port=args.port)

def main():
    args = parse_args()
    
    if args.command == 'generate-market-data':
        generate_market_data()
    elif args.command == 'generate':
        generate_simulation(args)
    elif args.command == 'regenerate-all':
        regenerate_all_simulations()
    elif args.command == 'run':
        run_app(args)
    else:
        print("No command specified. Use --help for usage information.")

if __name__ == '__main__':
    main() 