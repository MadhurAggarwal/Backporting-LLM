import os
import re
import requests
import json

def get_pr_base_branch(pr_url: str) -> str:
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError("Invalid GitHub PR URL format")

    owner, repo, pr_number = match.groups()

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    token = os.getenv("GITHUB_ACCESS_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch PR details: {response.status_code} - {response.text}")

    pr_data = response.json()
    return pr_data["base"]["ref"]

def main():
    filename = "/home/sumsharma/madhur/backporting-llm/training_llm/data/PR-changelog-libsoup.json"
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for pr_number, pr_info in data.items():
        url = pr_info.get("url")
        if url:
            branch_name = get_pr_base_branch(url)
            data[pr_number]["base_branch"] = branch_name

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    main()
