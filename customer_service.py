import os
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# 1. Configuration (Set these via Render Environment Variables)
COMPANY_ID = os.environ.get("COMPANY_ID", "YOUR_COMPANY_ID")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "YOUR_ACCESS_TOKEN")

# Correct Base URL (Change to "https://intuit.com" for production)
BASE_URL = "https://intuit.com"

@app.route("/customers", methods=["GET"])
def get_customers():
    # 2. Configure standard API headers (Fixed Content-Type to application/json)
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # 3. Correct QBO Data query path (Removed /public/us/)
    query = "SELECT Id, DisplayName FROM Customer"
    url = f"{BASE_URL}/v3/company/{COMPANY_ID}/query"
    
    # Pass the query via params to avoid URL encoding issues
    params = {
        "query": query
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            raw_customers = data.get("QueryResponse", {}).get("Customer", [])
            
            # Reformat payload structure cleanly
            customer_list = [{"id": c.get("Id"), "name": c.get("DisplayName")} for c in raw_customers]
            return jsonify(customer_list), 200
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
