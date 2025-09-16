from logger_refactored import Logger
from finetuning.finetuning_prompts import FinetuningPrompts
from backporting_handler import BackportingHandler
from finetuning.constants import COMMITS_DETAILS
from finetuning.logger import FinetuneLogger
from finetuning.constants import MODEL_NAME, QnA_DATA_FILE
import os
import re

class Generate_Q_A_Dataset:
    def __init__(self):
        self.prompts = FinetuningPrompts()
        self.logger  = FinetuneLogger()

        print("Starting Q&A Dataset Generation Process")
        self.logger.log_info("Starting Q&A Dataset Generation Process")

    def fetch_cve_patches(self):
        self.logger.log_info("Fetching CVE List and Corresponding Patches")
        self.patch_data = {}
        self.backporting_handler = BackportingHandler()
        self.all_cves = self.backporting_handler.getCVEList()
        for cve in self.all_cves:
            self.patch_data[cve] = self.backporting_handler.getUpstreamPatchForCVE(cve)

        self.logger.log_info(f"Total CVEs fetched: {len(self.all_cves)}")
        print(f"Total CVEs fetched: {len(self.all_cves)}")

    def generate_from_llm(self, system_prompt, user_prompt, prompt_type, commitfile, cve=None):
        statement = f"Generating Q&A pairs for {prompt_type}, commit {commitfile}"
        if cve:
            statement += f", CVE {cve}"
        self.logger.log_info(f"{statement}...")
        print(statement + "...")

        if MODEL_NAME.startswith("gpt-"):
            pass 
        else:
            pass

        print(f"Q&A pairs for {prompt_type} generated from LLM")
        self.logger.log_info(f"Q&A pairs for {prompt_type} generated from LLM")
        self.logger.log_generated_output(prompt_type, output, commit=commitfile, cve_number=cve)

        output = """
        [
        {  "question": "This is a test question.", 
            "answer": "This is a test answer."
        }
        ]
        """ 
        return output

    def getPrompts(self, prompt_type, commit_data, commitfile, cve=None, cve_hunk=None):
        self.logger.log_info(f"Generating prompts for {prompt_type}")

        system_prompt, user_prompt = self.prompts.getPrompts(prompt_type, PATCH_HUNK=cve_hunk, COMMIT_DATA=commit_data)

        self.logger.log_info(f"Prompts generated for {prompt_type}")
        self.logger.log_prompt(f"{prompt_type}_system", system_prompt, commit=commitfile, cve_number=cve)
        self.logger.log_prompt(f"{prompt_type}_user", user_prompt, commit=commitfile, cve_number=cve)
        return system_prompt, user_prompt

    def store_qna_pairs(self, qna_pairs, prompt_type):
        self.logger.log_info(f"Storing Q&A pairs for {prompt_type}...")
        for qna in eval(qna_pairs):
            question = qna.get("question", "").strip()
            answer = qna.get("answer", "").strip()
            with open(QnA_DATA_FILE, "a") as qna_file:
                qna_file.write(f'{{"question": "{question}", "answer": "{answer}"}}\n')
        
        print(f"Q&A pairs for {prompt_type} appended to {QnA_DATA_FILE}")
        self.logger.log_info(f"Q&A pairs for {prompt_type} appended to {QnA_DATA_FILE}")

    def generate_dataset(self):
        self.fetch_cve_patches()

        for commitfile in os.listdir(COMMITS_DETAILS):
            self.logger.log_info(f"\nProcessing commit file: {commitfile}")

            filepath = os.path.join(COMMITS_DETAILS, commitfile)
            with open(filepath, 'r') as f:
                commit_data = f.read()
            
            self.logger.log_info(f"Commit data read from {commitfile}")
            self.logger.log_input("commit_data", commit_data, commit=commitfile)

            system_prompts, user_prompts = self.getPrompts("COMMIT_DETAILS", commit_data=commit_data, commitfile=commitfile)
            output = self.generate_from_llm(system_prompts, user_prompts, "COMMIT_DETAILS", commitfile)
            self.store_qna_pairs(output)

            self.logger.log_info("Processing patch hunks for the commit")
            print("Processing patch hunks for the commit...")
            for cve in self.all_cves:
                patch = self.patch_data.get(cve, "")
                hunks = split_git_patch(patch)

                self.logger.log_info(f"Total hunks found for CVE {cve}: {len(hunks)}")
                for hunk in hunks:
                    prompt_types = ["COMMIT_TO_HUNK_CHANGES", "PATCH_BACKPORT"]
                    for prompt_type in prompt_types:
                        system_prompts, user_prompts = self.getPrompts(prompt_type, commit_data=commit_data, commitfile=commitfile, cve_hunk=hunk, cve=cve)
                        output = self.generate_from_llm(system_prompts, user_prompts, prompt_type, commitfile, cve)
                        self.store_qna_pairs(output, prompt_type)
                
                self.logger.log_info(f"Completed processing for CVE {cve}")
                print(f"Completed processing for CVE {cve}")
            
            self.logger.log_info(f"Completed processing for commit file: {commitfile}")
            print(f"Completed processing for commit file: {commitfile}")

        self.logger.log_info("✅ Q&A Dataset Generation Process Completed")
        print("✅ Q&A Dataset Generation Process Completed")

def split_git_patch(patch_text):
    file_splits = re.split(r'(?=^diff --git )', patch_text, flags=re.MULTILINE)
    hunks = []

    for file_block in file_splits:
        if not file_block.strip():
            continue
        hunk_matches = list(re.finditer(r'(^@@.*?@@.*?(?=^@@|\Z))', file_block, flags=re.MULTILINE | re.DOTALL))
        file_header_match = re.split(r'^@@', file_block, 1, flags=re.MULTILINE)
        file_header = file_header_match[0] if len(file_header_match) > 1 else ""

        for match in hunk_matches:
            hunk_content = match.group(0)
            full_hunk = file_header + hunk_content
            hunks.append(full_hunk.strip("\n"))

    return hunks

def main():
    generator = Generate_Q_A_Dataset()
    generator.generate_dataset()

def test_git_patch_split():
    test_patch = """
From a1b2c3d4e5f6g7h8i9j0 Mon Sep 17 00:00:00 2001
From: Jane Doe <jane@example.com>
Date: Mon, 16 Sep 2024 12:34:56 +0530
Subject: [PATCH] Refactor logging and fix buffer handling

Co-Author: John Smith <john@example.com>
---
 src/logger.c   | 6 +++---
 src/buffer.c   | 7 ++++---
 2 files changed, 7 insertions(+), 6 deletions(-)

diff --git a/src/logger.c b/src/logger.c
index 1234567..89abcde 100644
--- a/src/logger.c
+++ b/src/logger.c
@@ -10,7 +10,7 @@ void init_logger() {
     log_level = LOG_INFO;
-    fprintf(stderr, "Logger initialized\n");
+    fprintf(stdout, "Logger initialized at INFO level\n");
 }
 
@@ -25,6 +25,7 @@ void log_message(const char *msg) {
-    fprintf(stderr, "LOG: %s\n", msg);
+    fprintf(stdout, "[LOG] %s\n", msg);
+    fflush(stdout);
 }

diff --git a/src/buffer.c b/src/buffer.c
index abc1234..def5678 100644
--- a/src/buffer.c
+++ b/src/buffer.c
@@ -42,7 +42,7 @@ int buffer_write(Buffer *buf, const char *data, size_t len) {
-    if (len > buf->capacity) {
-        return -1;
-    }
+    if (len >= buf->capacity) {
+        fprintf(stderr, "Buffer overflow attempt\n");
+        return -1;
+    }
     memcpy(buf->data, data, len);
     buf->size = len;
     return 0;
@@ -75,6 +75,7 @@ void buffer_clear(Buffer *buf) {
     buf->size = 0;
-    memset(buf->data, 0, buf->capacity);
+    memset(buf->data, 0, buf->capacity);
+    fprintf(stdout, "Buffer cleared\n");
 }
-- 
GitLab
    """

    hunks = split_git_patch(test_patch)
    for i, hunk in enumerate(hunks):
        print(f"\n--- HUNK {i} ---\n")
        print(hunk)

if __name__ == "__main__":
    test_git_patch_split()