import requests
import json

BASE_URL = "https://r4.smarthealthit.org"

    # Search for patients instead of hardcoding an ID
    # _count is a parameter that limits results, Give me 5 patients
response = requests.get(
    f"{BASE_URL}/Patient",
    params={"_count": 5},
        # tells the server: "Please send back the data in FHIR JSON format, not just JSON"
    headers={"Accept": "application/fhir+json"}
)

data = response.json()
print(json.dumps(data, indent=2))