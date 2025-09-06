import os
import requests
import json
from dotenv import load_dotenv

# Load GitHub token from .env
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

OWNER = "microsoft"
REPO = "azurelinux"
TARGET_BRANCHES = ["fasttrack/3.0", "3.0-dev"]
GITHUB_API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/pulls"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_pr_numbers(base_branch):
    pr_numbers = set()
    page = 1

    while True:
        params = {
            "state": "all",
            "base": base_branch,
            "per_page": 100,
            "page": page
        }
        print(f"🔄 Fetching page {page} for branch '{base_branch}'...")

        response = requests.get(GITHUB_API_URL, headers=HEADERS, params=params)
        if response.status_code != 200:
            print(f"❌ Failed to fetch PRs for base '{base_branch}', page {page}: {response.status_code}")
            break

        data = response.json()
        if not data:
            print(f"✅ No more PRs on page {page} for '{base_branch}'")
            break

        for pr in data:
            pr_numbers.add(pr["number"])

        print(f"✔️  Page {page} fetched: total PRs collected so far = {len(pr_numbers)}")

        page += 1

    return pr_numbers

def main():
    unique_pr_numbers = set()

    for branch in TARGET_BRANCHES:
        print(f"\n🚀 Starting fetch for branch: {branch}")
        pr_numbers = get_pr_numbers(branch)
        unique_pr_numbers.update(pr_numbers)

    # Convert to sorted list for consistency
    pr_list = sorted(list(unique_pr_numbers))

    # Write to file
    with open("pr_numbers.json", "w") as f:
        json.dump(pr_list, f, indent=2)

    print(f"\n✅ Finished! Total unique PRs across all branches: {len(pr_list)}")
    print(f"📄 PR numbers written to 'pr_numbers.json'")

if __name__ == "__main__":
    main()
