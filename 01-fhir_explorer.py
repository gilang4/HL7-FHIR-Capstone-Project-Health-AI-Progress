import requests
import json

BASE_URL = "https://r4.smarthealthit.org"

# Pull a real test patient from test FHIR server

    # The f at the front (f-string) just tells Python to insert the value of BASE_URL into the curly braces
response = requests.get(
    f"{BASE_URL}/Patient/smart-1288992",
    headers={"Accept": "application/fhir+json"}
)

data = response.json()
print(json.dumps(data, indent=2))
