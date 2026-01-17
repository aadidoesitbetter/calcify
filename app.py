from flask import Flask, render_template, jsonify, request
import requests
import math

app = Flask(__name__)

# --- Currency API ---
CURRENCY_API_URL = "https://api.exchangerate-api.com/v4/latest/USD"
CURRENCY_CACHE = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/currency')
def get_currency():
    global CURRENCY_CACHE
    # Simple caching strategy: If we have data, use it. In prod, check timestamp.
    # For this demo, we'll fetch every time to be "real-time" or cache for session.
    try:
        if not CURRENCY_CACHE:
             print("Fetching currency data...")
             response = requests.get(CURRENCY_API_URL)
             CURRENCY_CACHE = response.json()
        return jsonify(CURRENCY_CACHE)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/calc', methods=['POST'])
def calculate():
    """
    Optional: Server-side calculation if needed.
    Currently, we will do most logic in JS for speed.
    This is just a placeholder for complex operations.
    """
    data = request.json
    expression = data.get('expression', '')
    try:
        # VERY UNSAFE in production to eval(), but fine for this local demo.
        # We will restrict the namespace for safety.
        allowed_names = {"math": math, "sin": math.sin, "cos": math.cos,
                         "tan": math.tan, "log": math.log10, "ln": math.log,
                         "sqrt": math.sqrt, "pi": math.pi, "e": math.e}
        result = eval(expression, {"__builtins__": None}, allowed_names)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": "Invalid Expression"}), 400

if __name__ == '__main__':
    app.run(debug=True)
