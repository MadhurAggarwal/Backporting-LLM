from constants import PACKAGE_NAME, OUTPUT_RESULT_PATH, BACKPORT_EXAMPLE, STDOUT_PATH, TEST_SPLIT_DATASET, PROMPT_DATA_FILE, PREPARED_PROMPTS, PATCH_TEST_FILE
from backporting_handler import BackportingHandler, CleanData
from llm_handler import RunLLM, TrainLLM
from prompt import PromptHandler
import json
import sys
from datasets import Dataset, load_dataset
from logger import Logger
import os

# Add BaseMain, FinetuneMain
class Main:
    def __init__(self):
        self.backportObj = BackportingHandler()
        self.promptsObj  = PromptHandler()
        self.llm = RunLLM()

        self.inputList, self.outputList = self.backportObj.load_input_output_data()
    
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

    def setLogger(self, cve_number):
        self.logger = Logger(cve_number)
        self.logger.log_info(f"Backporting for CVE: {cve_number}")
        # self.stdout_file = self.logger.create_stdout_log_file()

    def generateFromLLM(self, system_prompt, user_prompt, logging_statement):
        max_new_tokens = 2048
        print(f'Calling LLM to generate output for {logging_statement}...')
        self.logger.log_info(f"Calling LLM to generate output for {logging_statement}...")

        output = self.llm.generate_base_output_with_separate_prompts(system_prompt, user_prompt, max_new_tokens=max_new_tokens)

        print(f'LLM generation completed for {logging_statement}')
        self.logger.log_info(f"LLM generation completed for {logging_statement}")
        manual_test_file = self.logger.log_generated_output(logging_statement, output)
        self.manual_test_files.append(manual_test_file)

    def getPrompts(self, prompt_type):
        print('Getting prompts of type:', prompt_type)
        self.logger.log_info(f"Getting prompts of type: {prompt_type}")

        # Move this logic to PromptHandler class
        if prompt_type == 'BASE':
            system_prompt = self.promptsObj.get_base_system_prompt()
            user_prompt = self.promptsObj.get_base_user_prompt(self.cve_number, self.cve_description, self.upstream_patch, self.file_codes)
        
        self.logger.log_prompt(prompt_type + "_System_Prompt", system_prompt)
        self.logger.log_prompt(prompt_type + "_User_Prompt", user_prompt)
        return system_prompt, user_prompt
    
    def testPatch(self, patch, cve_number, statement = "MANUAL_PATCH_TEST"):
        pass

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
        print("Files for manually testing the LLM Generated Patch: ")
        for file in self.manual_test_files:
            print(file)
        print()
        print()
        return False

    def fixPatchCommonErrors(self, patch, cve_number):
        pass

def main():
    print(f"Backporting For {PACKAGE_NAME}...")

if __name__ == "__main__":
    main()