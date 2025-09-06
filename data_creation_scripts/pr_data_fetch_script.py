import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_ACCESS_TOKEN')
if not GITHUB_TOKEN:
    raise EnvironmentError("GITHUB_TOKEN not set in .env file")

print("GITHUB_TOKEN is set.")

REPO_OWNER = 'microsoft'
REPO_NAME = 'azurelinux'

headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
}

def get_pr_metadata(repo_owner, repo_name, pr_number):
    """Fetch PR title, user, date, etc."""
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}'
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR metadata: {response.status_code} - {response.text}")

    pr = response.json()
    return {
        'pr_name': pr['title'],
        'pr_date': pr['created_at'],
        'user': pr['user']['login'],
        'url': pr['html_url'],
        'merged': pr['merged'],
        'state': pr['state'],
    }


def get_files_changed(repo_owner, repo_name, pr_number):
    """Fetch file changes (diffs) for PR."""
    url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/files'
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch file changes: {response.status_code} - {response.text}")

    files_info = response.json()
    file_changes = []

    for file in files_info:
        file_changes.append({
            'filename': file['filename'],
            'status': file['status'],
            'additions': file['additions'],
            'deletions': file['deletions'],
            'changes': file['changes'],
            'patch': file.get('patch', None)
        })

    return file_changes

def save_dataset(pr_dataset, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(pr_dataset, f, indent=2)
    print(f"Saved dataset to {filename}")

def fetch_and_store_pr_data(pr_numbers, filename):
    dataset = {}

    for pr_number in pr_numbers:
        print(f"Processing PR #{pr_number}...")

        try:
            metadata = get_pr_metadata(REPO_OWNER, REPO_NAME, pr_number)
            file_changes = get_files_changed(REPO_OWNER, REPO_NAME, pr_number)

            dataset[str(pr_number)] = {
                **metadata,
                'code': file_changes
            }

        except Exception as e:
            print(f"Error fetching PR #{pr_number}: {e}")

    save_dataset(dataset, filename)

if __name__ == "__main__":
    PR_LIST = [14381] # pass it list generated using the pr_number_fetch_script.py
    dataset_file = 'dataset-scripts/pr_dataset.json'
    fetch_and_store_pr_data(PR_LIST, dataset_file)