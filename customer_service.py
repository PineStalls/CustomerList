import os
import time
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# Pull values directly from Render Environment variables
COMPANY_ID = os.environ.get("COMPANY_ID", "").strip()
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "").strip()

# Clean QuickBooks base URL (No paths or trailing slashes)
BASE_URL = "https://sandbox-quickbooks.api.intuit.com"

CACHE_DURATION = 300  
customer_cache = None
last_fetch_time = 0

@app.route("/customers", methods=["GET"])
def get_customers():
    global customer_cache, last_fetch_time
    
    if not COMPANY_ID or not ACCESS_TOKEN:
        return jsonify({
            "error": "Configuration Missing",
            "details": "COMPANY_ID or ACCESS_TOKEN environment variable is not populated on Render."
        }), 500
        
    current_time = time.time()
    if customer_cache and (current_time - last_fetch_time < CACHE_DURATION):
        return jsonify(customer_cache), 200

    # Header parameters optimized for the QuickBooks query endpoint
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/text"
    }

    # Absolute standard QuickBooks query endpoint structure
    url = f"{BASE_URL}/v3/company/{COMPANY_ID}/query"
    
    # Query must be sent as a direct string parameter
    params = {
        "query": "SELECT Id, DisplayName FROM Customer"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            raw_customers = data.get("QueryResponse", {}).get("Customer", [])
            
            customer_list = [{"id": c.get("Id"), "name": c.get("DisplayName")} for c in raw_customers]
            
            customer_cache = customer_list
            last_fetch_time = current_time
            return jsonify(customer_list), 200
        else:
            return jsonify({
                "error": f"API Error: {response.status_code}", 
                "details": response.text,
                "endpoint_attempted": url
            }), 500

    except Exception as e:
        return jsonify({"error": "Connection Failed", "details": str(e)}), 500

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
