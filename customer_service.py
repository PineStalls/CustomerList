import json
from quickbooks import QuickBooks
from quickbooks.objects.customer import Customer
from intuitlib.client import AuthClient

# 1. Initialize Authentication (replace placeholders with your tokens)
auth_client = AuthClient(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    environment="sandbox",
    redirect_uri="YOUR_REDIRECT_URI",
)
auth_client.access_token = "YOUR_ACCESS_TOKEN"
auth_client.refresh_token = "YOUR_REFRESH_TOKEN"

qbo_client = QuickBooks(
    auth_client=auth_client,
    refresh_token=auth_client.refresh_token,
    company_id="YOUR_COMPANY_ID",
)

# 2. Fetch Customers
customers = Customer.all(qb=qbo_client)

# 3. Parse into a list of dictionaries
customer_list = []
for customer in customers:
    customer_list.append({
        "id": customer.Id,
        "name": customer.DisplayName
    })

# 4. Convert the list to a JSON string
json_output = json.dumps(customer_list, indent=4)

# Print the final JSON payload
print(json_output)
