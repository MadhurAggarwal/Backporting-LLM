from constants import LOG_DIR, PACKAGE_NAME, LLM_PATH
import os
import json
from datetime import datetime

class Logger:
    def __init__(self, cve_number, manual_test=False):
        self.cve_number = cve_number
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        if not manual_test:
            self.log_dir = f"{LOG_DIR}/{PACKAGE_NAME}/{self.cve_number}/{timestamp}"
        else:
            self.log_dir = f"{LOG_DIR}/{PACKAGE_NAME}/{self.cve_number}/manual_test/{timestamp}"
        os.makedirs(self.log_dir, exist_ok=True)

        readme_file_path = os.path.join(self.log_dir, "readme.md")
        with open(readme_file_path, "w") as readme_file:
            readme_file.write(f"Backporting Attempt for CVE: {self.cve_number}\n")
            readme_file.write(f"Package: {PACKAGE_NAME}\n")
            readme_file.write(f"LLM Used: {LLM_PATH}\n")
            
            if manual_test:
                readme_file.write("\n\nMANUAL TEST: Testing Manually Edited Patch.\n")

            else:
                readme_file.write("\n\nApproach Used (To be Added Manually Later):\n")

    def log_cve_info(self, cve_number, cve_description, upstream_patch, file_codes, azurelinux_patch):
        log_file_path = os.path.join(self.log_dir, "cve_data.json")
        with open(log_file_path, "w") as log_file:
            json.dump({
                "CVE_NUMBER": cve_number,
                "CVE_DESCRIPTION": cve_description,
                "UPSTREAM_PATCH": upstream_patch,
                "FILE_CODES": file_codes,
                "AZURELINUX_PATCH": azurelinux_patch
            }, log_file, ensure_ascii=False, indent=4)
    
    def create_stdout_log_file(self):
        log_file_path = os.path.join(self.log_dir, "stdout.txt")
        with open(log_file_path, "w") as log_file:
            log_file.write("Stdout log\n\n")
        return log_file_path

    def log_input_prompt(self, empty_prompt, input_prompt):
        log_file_path = os.path.join(self.log_dir, "input_prompt.json")

        with open(log_file_path, "w") as log_file:
            json.dump({
                "PROMPT_STATEMENT": empty_prompt,
                "INPUT_PROMPT": input_prompt
            }, log_file, ensure_ascii=False, indent=4)

    def log_base_model_output(self, base_model_output):
        log_file_path = os.path.join(self.log_dir, "base_output.patch")

        with open(log_file_path, "w") as log_file:
            log_file.write(base_model_output)

        log_file_path = os.path.join(self.log_dir, "manual_test_base_output_copy.patch")
        with open(log_file_path, "w") as log_file:
            log_file.write(base_model_output)
        
        return log_file_path
    
    def log_cleaned_base_model_output(self, cleaned_base_model_output):
        log_file_path = os.path.join(self.log_dir, "cleaned_base_output.patch")

        with open(log_file_path, "w") as log_file:
            log_file.write(cleaned_base_model_output)

    def log_base_patch_test_result(self, is_successful, error_type, error):
        log_file_path = os.path.join(self.log_dir, "base_patch_test_result.json")

        with open(log_file_path, "w") as log_file:
            json.dump({
                "IS_SUCCESSFUL": is_successful,
                "ERROR_TYPE": error_type,
                "ERROR": error
            }, log_file, ensure_ascii=False, indent=4)

    def log_manual_patch(self, manual_patch):
        log_file_path = os.path.join(self.log_dir, "manual_patch.patch")

        with open(log_file_path, "w") as log_file:
            log_file.write(manual_patch)

    def log_manual_patch_test_result(self, is_successful, error_type, error):
        log_file_path = os.path.join(self.log_dir, "manual_patch_test_result.json")

        with open(log_file_path, "w") as log_file:
            json.dump({
                "IS_SUCCESSFUL": is_successful,
                "ERROR_TYPE": error_type,
                "ERROR": error
            }, log_file, ensure_ascii=False, indent=4)