import subprocess
import os
from constants import PACKAGE_REPO_WITH_GIT_HISTORY, PACKAGE_VERSION, COMMITS_LIST, COMMITS_DETAILS

def run_git_command(repo_path, args):
    result = subprocess.run(
        ["git"] + args,
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        raise Exception(f"Git command failed: {result.stderr}")
    return result.stdout.strip()

def get_commits_since_tag(repo_path, tag=PACKAGE_VERSION):
    commits = run_git_command(repo_path, ["log", f"{tag}..HEAD", "--pretty=format:%H"])
    return commits.splitlines()

def get_commit_details(repo_path, commit_id):
    details = run_git_command(repo_path, ["show", commit_id])
    return details

def main():
    repo_path = PACKAGE_REPO_WITH_GIT_HISTORY
    commit_ids = get_commits_since_tag(repo_path, PACKAGE_VERSION)
    print(f"Found {len(commit_ids)} commits since {PACKAGE_VERSION}")

    with open(COMMITS_LIST, "w") as f:
        for commit_id in commit_ids:
            f.write(f"{commit_id}\n")
    print(f"✅ Commit IDs written to {COMMITS_LIST}")

    os.makedirs(COMMITS_DETAILS, exist_ok=True)
    for commit_id in commit_ids:
        details = get_commit_details(repo_path, commit_id)
        commit_file = os.path.join(COMMITS_DETAILS, f"{commit_id}.txt")
        with open(commit_file, "w", encoding="utf-8") as f:
            f.write(details)

    print(f"✅ Commit details written to {COMMITS_DETAILS}")

if __name__ == "__main__":
    main()