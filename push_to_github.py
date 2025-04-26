import os
import json
import requests
import base64
from dotenv import load_dotenv

load_dotenv()  # Load .env variables

# GitHub repository details
repo_owner = 'Vicky-816'
repo_name = 'telegram-apk-bot'
file_path = 'data.json'

# Read token securely from environment variable
token = os.environ.get('GITHUB_PAT')

if not token:
    print("❌ GitHub token not found in environment variable GITHUB_PAT")
    exit()

# GitHub API URL for file updates
api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}'

# Read the data from the local file
with open(file_path, 'r') as f:
    content = json.load(f)

# Encode content to base64
content_encoded = base64.b64encode(json.dumps(content, indent=2).encode('utf-8')).decode('utf-8')

# Get current file sha (if exists)
headers = {'Authorization': f'token {token}'}
response = requests.get(api_url, headers=headers)
sha = response.json().get('sha') if response.status_code == 200 else None

# Prepare payload
payload = {
    'message': '🔗 Update links in data.json',
    'content': content_encoded,
    'committer': {
        'name': 'Vicky-816',
        'email': 'vicky7165u@gmail.com'
    }
}
if sha:
    payload['sha'] = sha

# Push update to GitHub
response = requests.put(api_url, json=payload, headers=headers)

# Print result
if response.status_code in [200, 201]:
    print("✅ Data pushed successfully to GitHub.")
else:
    print(f"❌ Failed to push data. Status code: {response.status_code}")
    print(response.text)
