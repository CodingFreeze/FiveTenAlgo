# FiveTenAlgo 

![GitHub](https://img.shields.io/github/license/CodingFreeze/FiveTenAlgo?style=flat-square)
![Python Version](https://img.shields.io/badge/python-3.7%2B-blue?style=flat-square)
![Flask](https://img.shields.io/badge/flask-2.0%2B-green?style=flat-square)

A trading algorithm that monitors securities on NYSE and NASDAQ, comparing real-time prices to those exactly one week prior and executing trades based on predetermined thresholds.

## Live Demo

[**View Live Dashboard**](https://five-ten-algo.vercel.app)

## Overview

This implementation uses Python with Flask for the backend and HTML/CSS with Plotly.js for the frontend charts. It avoids using JavaScript frameworks like React, Angular, or Vue.js, as well as TypeScript.

### Trading Strategy

- **Buy Signal**: When a security's price drops by about 5% (between -4.5% and -5.5%) compared to one week earlier, buy $5 worth.
- **Sell Signal**: When a security's price rises by about 10% (between 9.5% and 10.5%) compared to one week earlier, sell $10 worth.
- **Signal Confirmation**: Requires price change to remain stable for 1-5 minutes before executing trades, reducing false signals.

### Implementation Approach

FiveTenAlgo uses a hybrid approach to simulation and execution:

1. **Precomputed Simulation**: Historical data from NASDAQ founding to March 1st, 2025 is precomputed and stored as JSON.
2. **Current Data Processing**: When visiting the dashboard, the simulation continues from that point to the current date.
3. **Data Integration**: The two simulations are merged to provide a complete performance history.

## Performance Metrics

The algorithm's performance is evaluated using several key metrics:

- **Total Return**: Overall portfolio growth since inception
- **Annualized Return**: Yearly equivalent return rate
- **Maximum Drawdown**: Largest percentage drop from peak to trough
- **Volatility**: Standard deviation of returns
- **Sharpe Ratio**: Risk-adjusted return metric

## Known Limitations

This project is a first attempt at building an algorithmic trading system and has several known limitations that will be addressed in future updates:

- **Simulation Accuracy**: The backtesting may not fully account for real-world factors like slippage, liquidity constraints, and market impact.
- **Transaction Costs**: While basic transaction fees are modeled, complex fee structures and broker-specific costs may not be accurately represented.
- **Data Limitations**: Historical data might have gaps or inaccuracies that affect simulation results.
- **Implementation Simplifications**: Certain aspects of the algorithm have been simplified for educational purposes and may require refinement for production use.

These issues are being tracked and will be improved in subsequent versions of the algorithm.

## Features

- **Interactive Dashboard**: Visual representation of trading performance
- **Real-Time Updates**: Continues simulation up to the current date
- **Performance Metrics**: Total return, annualized return, maximum drawdown
- **Trade History**: Log of all executed trades
- **Current Portfolio**: View of current holdings
- **Different Modes**: Default, Aggressive, Conservative, and Balanced trading strategies
- **Timeline Options**: View performance over different time periods (All time, 5Y, 3Y, 1Y, etc.)
- **Multiple Starting Points**: Choose between different historical starting points (NASDAQ founding, 2000, COVID crash)

## Installation

### Quick Start

```bash
# Clone the repository
git clone https://github.com/CodingFreeze/FiveTenAlgo.git
cd FiveTenAlgo

# Set up the environment and run the application
./run.sh
```

The `run.sh` script will:
1. Create a virtual environment if it doesn't exist
2. Install the required dependencies
3. Generate precomputed simulation data if needed
4. Start the Flask web application

### Manual Setup

If you prefer to set up the application manually:

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate precomputed data
python cli.py run

# Start the application
python app.py
```

## CLI Usage

The application provides a command-line interface for managing simulations:

```bash
# Generate precomputed data with custom settings
python cli.py generate --start-date 2020-01-01 --end-date 2025-03-01 --symbols AAPL,MSFT,GOOGL

# Run a simulation using precomputed data
python cli.py run --continue-from-precomputed
```

## Project Structure

- `/models`: Contains the trading algorithm and simulation logic
- `/data`: Stores precomputed simulation data
- `/templates`: HTML templates for the web interface
- `/static`: CSS and other static assets
- `app.py`: Main Flask application
- `cli.py`: Command-line interface
- `requirements.txt`: Python dependencies

## Simulation Modes

The algorithm offers several simulation modes that adjust the trading parameters:

- **Default**: Buy at -4.5% to -5.5%, Sell at 9.5% to 10.5%
- **Aggressive**: Buy at -3.0% to -5.0%, Sell at 8.0% to 12.0%
- **Conservative**: Buy at -6.0% to -7.0%, Sell at 11.0% to 12.0%
- **Balanced**: Buy at -4.5% to -5.5%, Sell at 9.0% to 10.0%

## Timeline Options

View performance across different time periods:

- **All Time**: From NASDAQ founding (February 8, 1971) to present
- **From 2000**: January 1, 2000 to present
- **COVID Crisis**: March 13, 2020 to present
- **Specific Periods**: 5Y, 3Y, 1Y, 6M, 3M, 1M

## Technology Stack

- **Backend**: Python, Flask
- **Data Processing**: Pandas, NumPy, yfinance
- **Visualization**: Plotly
- **Frontend**: HTML, CSS (no JavaScript frameworks)

## Contributing

To contribute to the project:

1. Fork the repository
2. Create a new branch for your feature
3. Implement your changes
4. Submit a pull request

## Testing the API

You can test the API endpoints directly using your browser or tools like curl:

```bash
# Get status
curl http://localhost:8082/api/status

# Get performance history
curl http://localhost:8082/api/performance_history?mode=default&period=all&timeline=1y
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 