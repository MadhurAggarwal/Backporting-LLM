from constants import PACKAGE_NAME, OUTPUT_RESULT_PATH, BACKPORT_EXAMPLE, STDOUT_PATH, TEST_SPLIT_DATASET, PROMPT_DATA_FILE, PREPARED_PROMPTS, PATCH_TEST_FILE
from backporting_handler import BackportingHandler, CleanData
from llm_handler import RunLLM, TrainLLM
from prompt_refactored import Prompts
import json
import sys
from datasets import Dataset, load_dataset
from logger_refactored import Logger
import os

# Add BaseMain, FinetuneMain
class Main:
    def __init__(self):
        self.backportObj = BackportingHandler()
        self.promptsObj  = Prompts()
        self.llm = RunLLM()

        self.inputList, self.outputList = self.backportObj.getData()
    
    def setCVE(self, cve_number):
        print('Setting CVE to:', cve_number)
        self.cve_number = cve_number

        self.setLogger(self.cve_number)
        self.manual_test_files = []

        for (cve_num, cve_description, upstream_patch, file_codes), azurelinux_patch in zip(self.inputList, self.outputList):
            if cve_num == self.cve_number:
                self.cve_description = cve_description
                self.upstream_patch = upstream_patch
                self.file_codes = file_codes
                self.azurelinux_patch = azurelinux_patch
                break
        
        self.logger.log_input("CVE_DESCRIPTION", self.cve_description)
        self.logger.log_input("UPSTREAM_PATCH", self.upstream_patch)
        self.logger.log_input("FILE_CODES", self.file_codes)
        self.logger.log_input("AZURELINUX_PATCH", self.azurelinux_patch)

    def setLogger(self, cve_number):
        self.logger = Logger(cve_number)
        self.logger.log_info(f"Backporting for CVE: {cve_number}")
        
        self.log_file = self.logger.get_log_file_path()

    def generateFromLLM(self, system_prompt, user_prompt, logging_statement):
        max_new_tokens = 2048
        print(f'Calling LLM to generate output for {logging_statement}...')
        self.logger.log_info(f"Calling LLM to generate output for {logging_statement}...")

        output = self.llm.generate_base_output_with_separate_prompts(system_prompt, user_prompt, max_new_tokens=max_new_tokens)

        print(f'LLM generation completed for {logging_statement}')
        self.logger.log_info(f"LLM generation completed for {logging_statement}")
        manual_test_file = self.logger.log_generated_output(logging_statement, output)
        self.manual_test_files.append(manual_test_file)

        return output

    def getPrompts(self, prompt_type):
        print('Getting prompts of type:', prompt_type)
        self.logger.log_info(f"Getting prompts of type: {prompt_type}")

        system_prompt, user_prompt = self.promptsObj.getPrompts(prompt_type, self.cve_number, self.cve_description, self.upstream_patch, self.file_codes)
        
        self.logger.log_prompt(prompt_type + "_System_Prompt", system_prompt)
        self.logger.log_prompt(prompt_type + "_User_Prompt", user_prompt)
        return system_prompt, user_prompt
    
    def testPatch(self, patch, cve_number, statement = "MANUAL_PATCH_TEST"):
        isSuccess, err = self.backportObj.testPatch(patch, cve_number)
        
        if isSuccess:
            print(f"✅ Patch test for {statement} SUCCESS")
            self.logger.log_info(f"✅ Patch test for {statement} SUCCESS")
        else:
            print(f"❌ Patch test for {statement} FAILED")
            self.logger.log_info(f"❌ Patch test for {statement} FAILED")
            self.logger.log_info(f"Error: {err}")
            self.logger.log_test_result(statement, patch, str(err))

    def backportOneCVE(self, cve_number):
        print()
        print()
        self.setCVE(cve_number)
        system_prompt, user_prompt = self.getPrompts('BASE')
        output = self.generateFromLLM(system_prompt, user_prompt, "BASE_MODEL_OUTPUT")

        isSuccess = self.testPatch(output, cve_number, "BASE_PATCH_TEST")
        if isSuccess:
            print(f"✅ Backporting successful for {cve_number}")
            self.logger.log_info(f"✅ Backporting successful for {cve_number}")
            return True
        
        output = self.fixPatchCommonErrors(output, cve_number)
        isSuccess = self.testPatch(output, cve_number, "BASE_FIXED_PATCH_TEST")

        if isSuccess:
            print(f"✅ Backporting successful after fixing common patch errors, for {cve_number}")
            self.logger.log_info(f"✅ Backporting successful after fixing common patch errors, for {cve_number}")
            return True
    
        print(f"❌ Backporting failed for {cve_number}")
        self.logger.log_info(f"❌ Backporting failed for {cve_number}")
        print()
        print("Check Logs in: ", self.log_file)
        print("Files for manually testing the LLM Generated Patch: ")
        for file in self.manual_test_files:
            print(file)
        print()
        print()
        return False

    def fixPatchCommonErrors(self, patch, cve_number):
        # TODO: Fix line number in hunk, check line content for each line, check whitespace and tab characters.
        return patch

def main():
    print(f"Backporting For {PACKAGE_NAME}...")
    MainObj = Main()
    MainObj.backportOneCVE("CVE-2025-32052")

if __name__ == "__main__":
    main()