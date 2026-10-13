import os
import time
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# 1. Fetch Credentials from Render Environment Variables
COMPANY_ID = os.environ.get("COMPANY_ID", "").strip()
CLIENT_ID = os.environ.get("CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "").strip()

# Global runtime variables to store tokens in server memory
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "").strip()
REFRESH_TOKEN = os.environ.get("REFRESH_TOKEN", "").strip()

# Configuration Settings
BASE_URL = "https://intuit.com"  # Change to "https://intuit.com" for production
TOKEN_URL = "https://intuit.com"

# In-Memory Cache Variables
CACHE_DURATION = 300  # 5 minutes
customer_cache = None
last_fetch_time = 0

def refresh_qbo_tokens():
    """Uses the REFRESH_TOKEN to get a brand new ACCESS_TOKEN from Intuit."""
    global ACCESS_TOKEN, REFRESH_TOKEN
    print("Attempting to refresh expired QuickBooks access token...")
    
    # Intuit requires OAuth2 token requests to use Basic Auth header containing Client ID & Secret
    auth = (CLIENT_ID, CLIENT_SECRET)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }

    try:
        response = requests.post(TOKEN_URL, auth=auth, headers=headers, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            # Update global variables in memory
            ACCESS_TOKEN = token_data.get("access_token")
            # Intuit might issue a brand new refresh token alongside the access token
            if "refresh_token" in token_data:
                REFRESH_TOKEN = token_data.get("refresh_token")
                
            print("Successfully refreshed tokens! New Access Token loaded.")
            return True
        else:
            print(f"Failed to refresh tokens. Intuit response: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error occurred during token refresh loop: {e}")
        return False

def fetch_from_quickbooks(retry_on_401=True):
    """Executes the raw query call to QBO and attempts a self-healing token reset on a 401 error."""
    global ACCESS_TOKEN, customer_cache, last_fetch_time

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}/v3/company/{COMPANY_ID}/query"
    params = {"query": "SELECT Id, DisplayName FROM Customer"}

    try:
        response = requests.get(url, headers=headers, params=params)
        
        # Catch 401 Unauthorized (Expired Access Token)
        if response.status_code == 401 and retry_on_401:
            print("Detected an expired Access Token (401 Error). Initiating self-heal...")
            if refresh_qbo_tokens():
                # Re-run this exact function once more with the brand new access token
                return fetch_from_quickbooks(retry_on_401=False)
        
        if response.status_code == 200:
            data = response.json()
            raw_customers = data.get("QueryResponse", {}).get("Customer", [])
            
            # Reformat list cleanly for internal use
            customer_list = [{"id": c.get("Id"), "name": c.get("DisplayName")} for c in raw_customers]
            
            # Cache it
            customer_cache = customer_list
            last_fetch_time = time.time()
            return {"status": "success", "data": customer_list}
            
        return {"status": "error", "code": response.status_code, "text": response.text}

    except Exception as e:
        return {"status": "error", "text": str(e)}

@app.route("/customers", methods=["GET"])
def get_customers():
    """Standard raw json endpoint."""
    current_time = time.time()
    if customer_cache and (current_time - last_fetch_time < CACHE_DURATION):
        return jsonify(customer_cache), 200

    result = fetch_from_quickbooks()
    if result["status"] == "success":
        return jsonify(result["data"]), 200
    return jsonify({"error": f"QBO API Error {result.get('code')}", "details": result.get("text")}), 500

@app.route("/jotform-customers", methods=["GET"])
def get_jotform_customers():
    """Jotform targeted endpoint format mapping out text/value properties."""
    current_time = time.time()
    
    # Serve cached data if valid
    if customer_cache and (current_time - last_fetch_time < CACHE_DURATION):
        jotform_data = [{"text": c["name"], "value": c["id"]} for c in customer_cache]
        return jsonify(jotform_data), 200

    result = fetch_from_quickbooks()
    if result["status"] == "success":
        jotform_data = [{"text": c["name"], "value": c["id"]} for c in result["data"]]
        return jsonify(jotform_data), 200
        
    # Return a safe, empty structural list so Jotform's form doesn't display a broken element
    return jsonify([]), 200

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
