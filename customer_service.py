import os
import time
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# 1. Configuration (Set these via Render Environment Variables)
COMPANY_ID = os.environ.get("COMPANY_ID", "YOUR_COMPANY_ID")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "YOUR_ACCESS_TOKEN")

# Correct Base URL (Change to "https://intuit.com" for production)
BASE_URL = "https://intuit.com"

# 2. In-Memory Cache variables to prevent 429 Rate Limiting
CACHE_DURATION = 300  # Cache data for 5 minutes (300 seconds)
customer_cache = None
last_fetch_time = 0

@app.route("/customers", methods=["GET"])
def get_customers():
    global customer_cache, last_fetch_time
    
    current_time = time.time()
    
    # Check if we have a valid, recent cache of the customer data
    if customer_cache and (current_time - last_fetch_time < CACHE_DURATION):
        print("Returning customer list from local cache...")
        return jsonify(customer_cache), 200

    print("Cache expired or empty. Fetching fresh data from QuickBooks Online API...")
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    query = "SELECT Id, DisplayName FROM Customer"
    url = f"{BASE_URL}/v3/company/{COMPANY_ID}/query"
    params = {"query": query}

    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            raw_customers = data.get("QueryResponse", {}).get("Customer", [])
            
            # Format payload structure cleanly
            customer_list = [{"id": c.get("Id"), "name": c.get("DisplayName")} for c in raw_customers]
            
            # Update cache and timestamp
            customer_cache = customer_list
            last_fetch_time = current_time
            
            return jsonify(customer_list), 200
        
        elif response.status_code == 429:
            # If still throttled, return the old cached data if it exists rather than breaking
            if customer_cache:
                return jsonify({"warning": "API Throttled. Returning stale data.", "data": customer_cache}), 200
            return jsonify({"error": "API Throttled (429)", "details": "QuickBooks rate limit exceeded. Please wait a few minutes."}), 429
        else:
            return jsonify({"error": f"API Error: {response.status_code}", "details": response.text}), 500

    except Exception as e:
        return jsonify({"error": "Connection Failed", "details": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
