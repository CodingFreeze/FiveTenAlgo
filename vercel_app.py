from flask import Flask, render_template, jsonify, redirect

app = Flask(__name__)

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
    # For Vercel, we'll use pre-computed data
    return jsonify({"message": "Using precomputed data in production"})

@app.route('/api/trade_log')
def get_trade_log():
    """API endpoint to get trade log."""
    # For Vercel, we'll use pre-computed data
    return jsonify([])

@app.route('/api/portfolio')
def get_portfolio():
    """API endpoint to get current portfolio state."""
    # For Vercel, we'll use pre-computed data
    return jsonify({'capital': 0, 'portfolio': {}})

# This is needed for Vercel deployment
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080) 