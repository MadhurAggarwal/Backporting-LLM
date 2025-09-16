from constants import LOG_DIR, PACKAGE_NAME, MODEL_NAME
import os
import json
from datetime import datetime

class FinetuneLogger:
    def __init__(self):
        timestamp = datetime.now().strftime("%d-%b-%Y_%H-%M").upper()
        self.log_dir = f"{LOG_DIR}/{PACKAGE_NAME}/{timestamp}"
        if os.path.exists(self.log_dir):
            self.log_dir += f"-{datetime.now().strftime('%S')}"
        os.makedirs(self.log_dir, exist_ok=True)

        self.log_file = os.path.join(self.log_dir, "log.txt")
        with open(self.log_file, "a") as log_file:
            log_file.write(f'Logger initialized.\n')
            log_file.write(f"Finetuning Attempt for PACKAGE: {PACKAGE_NAME}\n")
            log_file.write(f"LLM Used: {MODEL_NAME}\n\n")
    
    def get_log_file_path(self):
        return self.log_file
    
    def log_info(self, message):
        with open(self.log_file, "a") as log_file:
            log_file.write(f"[INFO] {message}\n")

    def _get_file_name(self, base, key, commit = None, cve_number = None):
        filename = f"{base}/"
        if commit:
            filename += f"{commit}/"
        if cve_number:
            filename += f"{cve_number}/"
        filename += f"{key}.txt"
        return filename
        
    def log_input(self, key, value, commit = None, cve_number = None):
        file_path = self._get_file_name("input", key, commit, cve_number)
        file_path = os.path.join(self.log_dir, file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as input_file:
            input_file.write(value)
    
    def log_prompt(self, prompt_type, prompt, commit = None, cve_number = None):
        filename = self._get_file_name("prompts", prompt_type, commit, cve_number)
        file_path = os.path.join(self.log_dir, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as prompt_file:
            prompt_file.write(prompt)
    
    def log_generated_output(self, key, output, commit = None, cve_number = None):
        filename = self._get_file_name("output", key, commit, cve_number)
        file_path = os.path.join(self.log_dir, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as output_file:
            output_file.write(output)