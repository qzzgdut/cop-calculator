import requests
import json

url = "http://127.0.0.1:5001/calculate"
payload = {
    "refrigerant": "R454B",
    "t_evap_c": 10,
    "t_cond_c": 37.78,
    "superheat_k": 11.1,
    "subcooling_k": 8.3,
    "is_efficiency": 0.82,
    "motor_efficiency": 0.9
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:", json.dumps(response.json(), indent=2))
    except:
        print("Response Text:", response.text)
except Exception as e:
    print(f"Request failed: {e}")
