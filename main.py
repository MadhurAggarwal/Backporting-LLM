from constants import PACKAGE_NAME, OUTPUT_RESULT_PATH, BACKPORT_EXAMPLE, STDOUT_PATH, TEST_SPLIT_DATASET, PROMPT_DATA_FILE, PREPARED_PROMPTS, PATCH_TEST_FILE
from backporting_handler import BackportingHandler, CleanData
from llm_handler import RunLLM, TrainLLM
from prompt import PromptHandler
import json
import sys
from datasets import Dataset, load_dataset
from logger import Logger
import os

def createPrompts():
    print(f"For Package {PACKAGE_NAME}")

    print("\nFetching Backporting Data")
    backportObj = BackportingHandler()
    inputList, outputList = backportObj.getData()
    p = PromptHandler()

    for (cve_number, cve_description, upstream_patch, file_codes), azurelinux_patch in zip(inputList, outputList):
        with open(PROMPT_DATA_FILE, "r", encoding="utf-8") as f:
            prompt_data = json.load(f)
        prompt_data[cve_number] = {
            "CVE_DESCRIPTION": cve_description,
            "UPSTREAM_PATCH": upstream_patch,
            "RELEVANT_FILE_CODE": file_codes,
            "EXPECTED_OUTPUT": azurelinux_patch
        }

        with open(PROMPT_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(prompt_data, f, ensure_ascii=False, indent=4)
        

        input_prompt  = p.getBackportingInputPrompt(cve_number, cve_description, upstream_patch, file_codes)
        output_prompt = p.getBackportingOutputPrompt(azurelinux_patch)

        with open(PREPARED_PROMPTS, "r", encoding="utf-8") as f:
            prepared_prompts = json.load(f)
        
        prepared_prompts[cve_number] = {
            "INPUT_PROMPT": input_prompt,
            "OUTPUT_PROMPT": output_prompt
        }

        with open(PREPARED_PROMPTS, "w", encoding="utf-8") as f:
            json.dump(prepared_prompts, f, ensure_ascii=False, indent=4)

# def runFinetunedModel():
#     index = 12
#     print(f"For Package {PACKAGE_NAME}")

#     print("\nFetching Backporting Data")
#     backportObj = BackportingHandler()
#     inputList, outputList = backportObj.getData()
#     cve_number, cve_description, upstream_patch, file_codes = inputList[index]

#     print("\nGenerating Prompt")
#     p = PromptHandler()
#     prompt = p.getBackportingInputPrompt(cve_number, cve_description, upstream_patch, file_codes)

#     print(f"Length of Prompt = {len(prompt)} (should be <= Context Length of the Model)")

#     print("\nGenerating LLM Output")
#     llm = RunLLM(create_finetuned_pipeline=True)
#     finetuned_model_output = llm.generate_finetuned_output(prompt=prompt, max_new_tokens=2500)

#     print("\nClean Model Output")
#     cleanObj = CleanData()
#     cleaned_output = cleanObj.extractOutputFromGeneratedPatch(finetuned_model_output)

#     print("\nTesting Output Generated From LLM")
#     isSuccessful, error = backportObj.testPatch(cve_number, cleaned_output)

#     result = {
#         'expected_output': outputList[index],
#         'finetuned_model_output': finetuned_model_output,
#         'cleaned_output': cleaned_output
#     }

#     if not isSuccessful:
#         result['finetuned_error'] = {
#             "type": type(error).__name__,
#             "message": str(error),
#         }

#     with open(OUTPUT_RESULT_PATH, "r", encoding="utf-8") as f:
#         existing_data = json.load(f)
#     existing_data['finetuned'] = result

#     with open(OUTPUT_RESULT_PATH, "w", encoding="utf-8") as f:
#         json.dump(existing_data, f, ensure_ascii=False, indent=4)

def finetuneLLM():
    backportObj = BackportingHandler()
    inputList, outputList = backportObj.getData()
    training_examples = []

    for (cve_number, cve_description, upstream_patch, file_codes), azurelinux_patch in zip(inputList, outputList):
        training_examples.append({
            "CVE_DESCRIPTION": cve_description,
            "UPSTREAM_PATCH": upstream_patch,
            "FILE_CODES": file_codes,
            "AZURELINUX_PATCH": azurelinux_patch
        })

    dataset = Dataset.from_list(training_examples)
    dataset = dataset.train_test_split(test_size=0.2, seed=42)

    train_dataset = dataset["train"]
    test_dataset = dataset["test"]

    llmTrainer = TrainLLM()
    llmTrainer.finetune_llm(train_dataset, test_dataset=test_dataset)
    # llmTrainer.finetune_llm(dataset)

    # test_dataset.to_json(TEST_SPLIT_DATASET)
    # test_dataset = load_dataset("json", data_files=TEST_SPLIT_DATASET)["train"]

def setBackportingExample():
    index = 0

    backportObj = BackportingHandler()
    inputList, outputList = backportObj.getData()
    cve_number, cve_description, upstream_patch, file_codes = inputList[index]
    output = outputList[index]

    with open(BACKPORT_EXAMPLE, "w", encoding="utf-8") as f:
        json.dump({
            'cve_number': cve_number,
            'cve_description': cve_description,
            'upstream_patch': upstream_patch,
            'file_codes': file_codes,
            'output': output
        }, f, ensure_ascii=False, indent=4)

# def test_output_manually():
#     index = 0
#     patch = """
#         diff --git a/libsoup/soup-multipart.c b/libsoup/soup-multipart.c
#         index b6135ae6..fd7c99c2 100644
#         --- a/libsoup/soup-multipart.c
#         +++ b/libsoup/soup-multipart.c
#         @@ -184,7 +184,7 @@ soup_multipart_new_from_message (SoupMessageHeaders *headers,
#                                                     end - 2 - split);
#                             g_ptr_array_add (multipart->bodies, part_body);
                    
#         -                start = end;
#         +                start = end;
        
#                             boundary_len = strlen (boundary);
#                             end = find_boundary (start, body_end, boundary, boundary_len);
#                             if (!end)
#                                     goto error;
#     """

#     backportObj = BackportingHandler()
#     inputList, outputList = backportObj.getData()
#     cve_number, cve_description, upstream_patch, file_codes = inputList[index]

#    isSuccessful, error = backportObj.testPatch(cve_number, patch)
#    print(error)

def manually_test_generated_patch():
    cve_number = ""
    patch = """
    """

    with open(PATCH_TEST_FILE, "r", encoding="utf-8") as f:
        patch = f.read()

    backportObj = BackportingHandler()
    output = backportObj.testPatch(cve_number, patch)
    print(f"Tested Patch for {cve_number}")
    print(f"Result:\n{output}\n\n")



def runBaseModel():
    cves = ["CVE-2025-32052"]
    backportObj = BackportingHandler()
    inputList, outputList = backportObj.getData()

    for (cve_number, cve_description, upstream_patch, file_codes), azurelinux_patch in zip(inputList, outputList):
        if cve_number in cves:
            print("Handling CVE:", cve_number)
            logger = Logger(cve_number, manual_test=False)
            logger.log_cve_info(cve_number, cve_description, upstream_patch, file_codes, azurelinux_patch)

            # Direct the stdout and stderr to a log file for this CVE
            stdout_file = logger.create_stdout_log_file()

            print(f"Logging stdout and stderr to: {stdout_file}")
            with open(stdout_file, "w") as f:
                sys.stdout = f
                sys.stderr = f

                print(f"\nGenerating Prompt for {cve_number}")
                p = PromptHandler()
                prompt = p.getBackportingInputPrompt(cve_number, cve_description, upstream_patch, file_codes)

                logger.log_input_prompt("EMPTY_PROMPT_STATEMENT", p.getBackportingInputPrompt("", "", "", ""))
                logger.log_input_prompt("INPUT_PROMPT", prompt)
                print(f"Length of Prompt = {len(prompt)} (should be <= Context Length of the Model)")

                print("\nGenerating LLM Output")
                llm = RunLLM(create_finetuned_pipeline=False)
                base_model_output = llm.generate_base_output(prompt=prompt, max_new_tokens=2500)
                manual_test_file = logger.log_base_model_output(base_model_output)

                # print("\nClean Model Output")
                # cleanObj = CleanData()
                # cleaned_output = cleanObj.extractOutputFromGeneratedPatch(base_model_output, prompt)
                # logger.log_cleaned_base_model_output(cleaned_output)

                print("\nTesting Output Generated From LLM")
                isSuccessful, error = backportObj.testPatch(cve_number, base_model_output)

                logger.log_base_patch_test_result(isSuccessful, type(error).__name__ if error else "NO_ERROR", str(error) if error else "NO_ERROR")

                if isSuccessful:
                    print("✅ Base Model Generated Patch Successful for:", cve_number)
                else:
                    # check for line number mismatch 
                    print("❌ Base Model Generated Patch Failed for:", cve_number)
                    print(f"Error Type: {type(error).__name__}")
                    print(f"Error Message: {str(error)}")
                    print(f"Logs In: {stdout_file}")
                    print(f"Manual Test File For Base Model: {manual_test_file}")

                    print("\n\nChecking For Line Number Mismatch in Base Model Output:")
                    prompt = p.getCheckLineNumberPrompt(base_model_output, file_codes)
                    logger.log_input_prompt("CHECK_LINE_NUMBER_PROMPT", prompt)

                    base_model_output_line_check = llm.generate_base_output(prompt=prompt, max_new_tokens=2500)
                    manual_test_file = logger.log_base_model_output(base_model_output_line_check, check_for="line_number_check")

                    print("\nTesting Output Generated From Base Model Line Number Check")
                    isSuccessful, error = backportObj.testPatch(cve_number, base_model_output_line_check)
                    logger.log_base_patch_test_result(isSuccessful, type(error).__name__ if error else "NO_ERROR", str(error) if error else "NO_ERROR", check_for="line_number_check")

                    if isSuccessful:
                        print("✅ Base Model Line Number Check Patch Successful for:", cve_number)
                    else:
                        print("❌ Base Model Line Number Check Patch Failed for:", cve_number)
                        print(f"Error Type: {type(error).__name__}")
                        print(f"Error Message: {str(error)}")
                        print(f"Logs In: {stdout_file}")
                        print(f"Manual Test File For Base Model Line Number Check: {manual_test_file}")

                    # check for line content mismatch
                    # check for whitespace character mismatch 

            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

            if isSuccessful:
                print("✅ Base Model Generated Patch Successful for:", cve_number)
            else:
                print("❌ Base Model Generated Patch Failed for:", cve_number)
                print(f"Error Type: {type(error).__name__}")
                print(f"Error Message: {str(error)}")
                print(f"Logs In: {stdout_file}")
                print(f"Manual Test File For Base Model: {manual_test_file}")
            print(f"Finished handling CVE: {cve_number}\n\n")

def runFinetunedModel():
    cves = ["CVE-2025-32052"]
    backportObj = BackportingHandler()
    inputList, outputList = backportObj.getData()

    for (cve_number, cve_description, upstream_patch, file_codes), azurelinux_patch in zip(inputList, outputList):
        if cve_number in cves:
            print("Handling CVE:", cve_number)
            logger = Logger(cve_number, manual_test=False)
            logger.log_cve_info(cve_number, cve_description, upstream_patch, file_codes, azurelinux_patch)

            # Direct the stdout and stderr to a log file for this CVE
            stdout_file = logger.create_stdout_log_file()

            print(f"Logging stdout and stderr to: {stdout_file}")
            with open(stdout_file, "w") as f:
                sys.stdout = f
                sys.stderr = f

                print(f"\nGenerating Prompt for {cve_number}")
                p = PromptHandler()
                prompt = p.getBackportingInputPrompt(cve_number, cve_description, upstream_patch, file_codes)

                logger.log_input_prompt("EMPTY_PROMPT_STATEMENT", p.getBackportingInputPrompt("", "", "", ""))
                logger.log_input_prompt("INPUT_PROMPT", prompt)
                print(f"Length of Prompt = {len(prompt)} (should be <= Context Length of the Model)")

                print("\nGenerating LLM Output (Finetuned)")
                llm = RunLLM(create_finetuned_pipeline=True)
                finetuned_model_output = llm.generate_finetuned_output(prompt=prompt, max_new_tokens=2500)
                manual_test_file = logger.log_finetuned_model_output(finetuned_model_output)

                # print("\nClean Model Output")
                # cleanObj = CleanData()
                # cleaned_output = cleanObj.extractOutputFromGeneratedPatch(finetuned_model_output, prompt)
                # logger.log_cleaned_finetuned_model_output(cleaned_output)

                print("\nTesting Output Generated From Finetuned LLM")
                isSuccessful, error = backportObj.testPatch(cve_number, finetuned_model_output)

                logger.log_finetuned_patch_test_result(
                    isSuccessful,
                    type(error).__name__ if error else "NO_ERROR",
                    str(error) if error else "NO_ERROR"
                )

                if isSuccessful:
                    print("✅ Finetuned Model Generated Patch Successful for:", cve_number)
                else:
                    print("❌ Finetuned Model Generated Patch Failed for:", cve_number)
                    print(f"Error Type: {type(error).__name__}")
                    print(f"Error Message: {str(error)}")
                    print(f"Logs In: {stdout_file}")
                    print(f"Manual Test File For Finetuned Model: {manual_test_file}")

            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

            if isSuccessful:
                print("✅ Finetuned Model Generated Patch Successful for:", cve_number)
            else:
                print("❌ Finetuned Model Generated Patch Failed for:", cve_number)
                print(f"Error Type: {type(error).__name__}")
                print(f"Error Message: {str(error)}")
                print(f"Logs In: {stdout_file}")
                print(f"Manual Test File For Finetuned Model: {manual_test_file}")
            print(f"Finished handling CVE: {cve_number}\n\n")


def test_output_manually(manual_test_file):
    parts = os.path.normpath(manual_test_file).split(os.sep)
    if len(parts) < 3:
        raise ValueError("Invalid manual_test_file path format, cannot extract CVE number.")
    cve_number = parts[-3]
    logger = Logger(cve_number, manual_test=True)

    with open(manual_test_file, "r", encoding="utf-8") as f:
        patch = f.read()
    logger.log_manual_patch(patch)

    stdout_file = logger.create_stdout_log_file()
    with open(stdout_file, "w") as f:
        sys.stdout = f
        sys.stderr = f

        backportObj = BackportingHandler()
        isSuccessful, error = backportObj.testPatch(cve_number, patch)

        logger.log_base_patch_test_result(isSuccessful, type(error).__name__ if error else "NO_ERROR", str(error) if error else "NO_ERROR")

        print(f"Tested Patch for {cve_number}")
        if isSuccessful:
            print("✅ Manual Test Patch Successful for:", cve_number)
        else:
            print("❌ Manual Test Patch Failed for:", cve_number)
            print(f"Error Type: {type(error).__name__}")
            print(f"Error Message: {str(error)}")
            print(f"Logs In: {stdout_file}")

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__ 

    if isSuccessful:
        print("✅ Manual Test Patch Successful for:", cve_number)
    else:
        print("❌ Manual Test Patch Failed for:", cve_number)
        print(f"Error Type: {type(error).__name__}")
        print(f"Error Message: {str(error)}")
        print(f"Logs In: {stdout_file}")
            

if __name__ == "__main__":

    # patchfile = "/home/sumsharma/madhur/backporting-llm/training_llm/logs/libsoup/CVE-2025-32052/20250904-084219/manual_test_base_output_copy.patch"
    # test_output_manually(patchfile)

    runBaseModel()

    # finetuneLLM()
    # runFinetunedModel()
    # createPrompts()