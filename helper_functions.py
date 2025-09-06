from constants import PACKAGE_REPO, PATCH_TEST_FILE
import os
import subprocess

def run_git_reset(PACKAGE_PATH):
    if not os.path.isdir(PACKAGE_PATH):
        raise FileNotFoundError(f"Path does not exist: {PACKAGE_PATH}")

    try:
        print(f"Running 'git reset --hard' on '{PACKAGE_PATH}'")
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], 
                       cwd=PACKAGE_PATH, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "reset", "--hard"], cwd=PACKAGE_PATH, check=True)
        subprocess.run(["git", "clean", "-fd"], cwd=PACKAGE_PATH, check=True)

        print(f"✅ Successfully reset repo at {PACKAGE_PATH}")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git command failed: {e}")

def apply_one_patch(PACKAGE_PATH, patch):
    print(f"Applying patch to {PACKAGE_PATH}")
    with open(PATCH_TEST_FILE, "w", encoding="utf-8") as f:
        f.write(patch)
    
    try:
        subprocess.run(
            ["patch", "-p1", "--fuzz=0", "-i", PATCH_TEST_FILE],
            cwd=PACKAGE_PATH,
            check=True
        )
        print(f"✅ Patch applied successfully")
    except subprocess.CalledProcessError as e:
        error_msg = (
            f"❌ Failed to apply patch {PATCH_TEST_FILE} in {PACKAGE_PATH}\n"
            f"Exit Code: {e.returncode}\n"
            f"Stdout: {e.stdout}\n"
            f"Stderr: {e.stderr}"
        )
        raise RuntimeError(error_msg) from e