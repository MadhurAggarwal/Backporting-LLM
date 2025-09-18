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

    def log_input_prompt(self, prompt_type, prompt):
        log_file_path = os.path.join(self.log_dir, "input_prompt.json")

        # if it exists, read the existing content and append to it
        if os.path.exists(log_file_path):
            with open(log_file_path, "r") as log_file:
                existing_data = json.load(log_file)
        else:
            existing_data = {}
        existing_data[prompt_type] = prompt
        with open(log_file_path, "w") as log_file:
            json.dump(existing_data, log_file, ensure_ascii=False, indent=4)
        return

    def log_base_model_output(self, base_model_output, check_for = ""):
        file_name = "base_output.patch" if check_for == "" else f"base_output_{check_for}.patch"
        log_file_path = os.path.join(self.log_dir, file_name)

        with open(log_file_path, "w") as log_file:
            log_file.write(base_model_output)

        file_name = "manual_test_base_output_copy.patch" if check_for == "" else f"manual_test_base_output_{check_for}_copy.patch"
        log_file_path = os.path.join(self.log_dir, file_name)
        with open(log_file_path, "w") as log_file:
            log_file.write(base_model_output)
        
        return log_file_path
    
    def log_cleaned_base_model_output(self, cleaned_base_model_output):
        log_file_path = os.path.join(self.log_dir, "cleaned_base_output.patch")

        with open(log_file_path, "w") as log_file:
            log_file.write(cleaned_base_model_output)

    def log_base_patch_test_result(self, is_successful, error_type, error, check_for = ""):
        file_name = "base_patch_test_result.json" if check_for == "" else f"base_patch_test_result_{check_for}.json"
        log_file_path = os.path.join(self.log_dir, file_name)

        with open(log_file_path, "w") as log_file:
            json.dump({
                "IS_SUCCESSFUL": is_successful,
                "ERROR_TYPE": error_type,
                "ERROR": error
            }, log_file, ensure_ascii=False, indent=4)
    
    def log_finetuned_model_output(self, finetuned_model_output):
        log_file_path = os.path.join(self.log_dir, "finetuned_output.patch")

        with open(log_file_path, "w") as log_file:
            log_file.write(finetuned_model_output)

        log_file_path = os.path.join(self.log_dir, "manual_test_finetuned_output_copy.patch")
        with open(log_file_path, "w") as log_file:
            log_file.write(finetuned_model_output)
        
        return log_file_path


    def log_finetuned_patch_test_result(self, is_successful, error_type, error):
        log_file_path = os.path.join(self.log_dir, "finetuned_patch_test_result.json")

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