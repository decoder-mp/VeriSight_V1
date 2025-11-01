import requests

# Backend endpoint
url = "http://127.0.0.1:5000/api/verify"

# Replace with the JWT token you got after login
token = "YOUR_JWT_TOKEN_HERE"

# Path to the file you want to verify
file_path = "C:/path/to/file.jpg"

# Prepare files and headers
files = {"file": open(file_path, "rb")}
headers = {"Authorization": f"Bearer {token}"}

# Make the POST request
response = requests.post(url, files=files, headers=headers)

# Print the result
print(response.json())
