import os
import json
import requests
import base64

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

# Encode content to base64 as required by GitHub API
content_encoded = base64.b64encode(json.dumps(content, indent=2).encode('utf-8')).decode('utf-8')

# Get the current file sha (if exists)
headers = {'Authorization': f'token {token}'}
response = requests.get(api_url, headers=headers)
sha = response.json().get('sha') if response.status_code == 200 else None

# Prepare the payload
payload = {
    'message': '🔗 Update links in data.json',
    'content': content_encoded,
    'committer': {
        'name': 'Your Name',
        'email': 'your-email@example.com'
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
