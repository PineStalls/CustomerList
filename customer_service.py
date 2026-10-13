import json
import requests

# 1. Configuration variables
COMPANY_ID = "YOUR_COMPANY_ID"
ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
# Use '://intuit.com' for sandbox, '://intuit.com' for production
BASE_URL = "https://://intuit.com" 

# 2. Set up API headers
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "text/plain"
}

# 3. Define the QBO SQL-like query to select customers
query = "SELECT Id, DisplayName FROM Customer"
url = f"{BASE_URL}/v3/company/{COMPANY_ID}/query?query={query}"

try:
    # 4. Make the API request
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # Extract customers from the QueryResponse
        raw_customers = data.get("QueryResponse", {}).get("Customer", [])
        
        # Format the JSON cleanly
        customer_list = [{"id": c.get("Id"), "name": c.get("DisplayName")} for c in raw_customers]
        
        # Save to file
        with open("qbo_customers.json", "w", encoding="utf-8") as file:
            json.dump(customer_list, file, indent=4)
            
        print("Successfully saved customer list to qbo_customers.json")
    else:
        print(f"API Error: Status {response.status_code} - {response.text}")

except Exception as e:
    print(f"An error occurred: {e}")
