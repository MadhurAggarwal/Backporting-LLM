# Backporting-LLM
Designed for Team AzureLinux, Cloud+AI Microsoft  
<br>When a new bug/vulnerability is discovered in any package, fixes are generally available for the latest versions only. If you are using any older version, then Maintaining Your Version is a task that is left for developers to do manually, from understanding the fix and the latest package version to adapting it to the older version currently in use.  
<br>This manual work is what we try to reduce.  
<br>This LLM Framework has been designed for Backporting - taking Patches written for latest versions, view the context of an older version and update the Patch to apply cleanly to the older package version.

## Simple Backports
<img width="1328" height="759" alt="image" src="https://github.com/user-attachments/assets/433190fb-7311-4da1-a908-28d3d6b05a87" />

For changes where the file paths have NOT been changed, we can simply traverse the files and fetch code-blocks with any relevant lines, that match with the patch.  
The data about the CVE (vulnerability), Upstream Patch, and extracted Codeblocks are all passed with backporting prompts to the LLM.  
The output from these LLMs is then tested against the actual package.  
Base Models used for this purpose include [codellama/CodeLlama-13b-Instruct-hf](https://huggingface.co/codellama/CodeLlama-13b-Instruct-hf) and  [Qwen/Qwen2.5-Coder-32B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct), with Qwen2.5-Coder-32B-Instruct significantly outperforming Codellama-13B-Instruct, in giving Patches in the Standard Git Diff Format.  
Base models typically always struggle with 
  - Adding correct line number in hunk header (@@ -X,Y +A,B @@)
  - Tabs, whitespace Character Differences
  - Missing some lines in the hunk content (if new lines were added / removed in the upstream)

These issues are fixable using few-shot prompts & prompt chaining.  
By Providing specialized prompts, and chaining their outputs together, we show how these base models can be used to generate valid patches.

## Prompt-Chain Example
From Logs Dir: logs/libsoup/CVE-2025-32052/12-SEP-2025_14-36  
Consider the upstream Patch:
```
    --- a/libsoup/content-sniffer/soup-content-sniffer.c
    +++ b/libsoup/content-sniffer/soup-content-sniffer.c
    @@ -524,7 +524,7 @@ sniff_unknown (SoupContentSniffer *sniffer, GBytes *buffer,
                guint index_pattern = 0;
                gboolean skip_row = FALSE;
    
    -			while ((index_stream < resource_length) &&
    +			while ((index_stream < resource_length - 1) &&
                    (index_pattern <= type_row->pattern_length)) {
                    /* Skip insignificant white space ("WS" in the spec) */
                    if (type_row->pattern[index_pattern] == ' ') {
    -- 
    GitLab
```
To be backported to the file:
```
{
    "libsoup/content-sniffer/soup-content-sniffer.c": [
        "527: \t\tif (type_row->has_ws) {\n",
        "528: \t\t\tguint index_stream = 0;\n",
        "529: \t\t\tguint index_pattern = 0;\n",
        "530: \t\t\tgboolean skip_row = FALSE;\n",
        "531: \n",
        "532: \t\t\twhile ((index_stream < resource_length) &&\n",
        "533: \t\t\t       (index_pattern <= type_row->pattern_length)) {\n",
        "534: \t\t\t\t/* Skip insignificant white space (\"WS\" in the spec) */\n",
        "535: \t\t\t\tif (type_row->pattern[index_pattern] == ' ') {\n",
        "536: \t\t\t\t\tif (resource[index_stream] == '\\x09' ||\n",
    ]
}
```
The base LLM response gives hunk @@ -532,7 +532,7 @@ which is incorrect:
```
@@ -532,7 +532,7 @@ sniff_unknown (SoupContentSniffer *sniffer, GBytes *buffer,
                guint index_stream = 0;
                guint index_pattern = 0;
                gboolean skip_row = FALSE;
 
-			while ((index_stream < resource_length) &&
+			while ((index_stream < resource_length - 1) &&
                    (index_pattern <= type_row->pattern_length)) {
                    /* Skip insignificant white space ("WS" in the spec) */
                    if (type_row->pattern[index_pattern] == ' ') {
-- 
```
The output from the base llm would not be directly applicable. This we fix using prompt-chains, designed by analyzing common-errors in patch generations.  
By using prompt chaining, we can get the following outputs from the llm:
```
First Mentioned Unchanged Line:                guint index_stream = 0;
First Changed Line: -			while ((index_stream < resource_length) &&

First Mentioned Unchanged Line Number: 528: guint index_stream = 0;
First Changed Line Number: 532: 			while ((index_stream < resource_length) &&
```
And hence the updated patch:
```
@@ -528,7 +528,7 @@ sniff_unknown (SoupContentSniffer *sniffer, GBytes *buffer,
                guint index_stream = 0;
                guint index_pattern = 0;
                gboolean skip_row = FALSE;
 
-			while ((index_stream < resource_length) &&
+			while ((index_stream < resource_length - 1) &&
                    (index_pattern <= type_row->pattern_length)) {
                    /* Skip insignificant white space ("WS" in the spec) */
                    if (type_row->pattern[index_pattern] == ' ') {
```
which fixes the line number as required.
Similarly, multiple other issues with LLMs, like not handling tabs & whitespaces, missing lines, incorrect hunk headers, etc can be fixed with specialized prompts as used in this repository.

## Complex Backports
When the old version of a package contains large differences - changes to file paths or function signatures, or even refactoring / modularization of functions, it becomes very difficult for models to generate patches directly.  

So, we feed the entire COMMIT HISTORY of the desired Package to an LLM in a question-answer format  
This allows the model to be able to map old versions, paths and function signatures to the new versions.  

To do this, we build the following pipeline:  

![Input Data (2)](https://github.com/user-attachments/assets/97d36457-000e-4698-8d09-db84e63ba68e)

Example Dataset:
```
{"messages": [{"role": "system", "content": "\n        You are an expert software developer with deep knowlege of c programming language.\n        You have in-depth knowlege about the commit history of libsoup package.\n        Answer questions about how the files, functions and lines of code were changed over range of commits.\n    "}, {"role": "user", "content": "Has the file path of 'libsoup/soup-cache-input-stream.c' changed? What is the new path?"}, {"role": "assistant", "content": "Yes, the file path changed. Old Path: 'libsoup/soup-cache-input-stream.c', New Path: 'libsoup/cache/soup-cache-input-stream.c'."}]}
{"messages": [{"role": "system", "content": "\n        You are an expert software developer with deep knowlege of c programming language.\n        You have in-depth knowlege about the commit history of libsoup package.\n        Answer questions about how the files, functions and lines of code were changed over range of commits.\n    "}, {"role": "user", "content": "What changes were made to the function 'read_internal' in the file 'libsoup/http-1/soup-message-io-data.c'?"}, {"role": "assistant", "content": "The function 'read_internal' was modified. New code blocks were added to handle cases for 'SOUP_ENCODING_CONTENT_LENGTH' and 'SOUP_ENCODING_EOF'. Additionally, new variables 'soup_random_size' and 'soup_buffer' were introduced. Code changes:\n\n**Old Version:**\n```c\ncase SOUP_ENCODING_CHUNKED:\n    return soup_body_input_stream_read_chunked(bistream, buffer, count, blocking, cancellable, error);\n\ncase SOUP_ENCODING_CONTENT_LENGTH:\ncase SOUP_ENCODING_EOF:\n    return soup_body_input_stream_read_raw(bistream, buffer, count, blocking, cancellable, error);\n```\n\n**New Version:**\n```c\ncase SOUP_ENCODING_CHUNKED:\n    return soup_body_input_stream_read_chunked(bistream, buffer, count, blocking, cancellable, error);\n\ncase SOUP_ENCODING_CONTENT_LENGTH:\n    return soup_random_size;\n\ncase SOUP_ENCODING_EOF:\n    return soup_body_input_stream_read_raw(bistream, buffer, count, blocking, cancellable, error);\n\nif (nread == 0) {\n    priv->eof = TRUE;\n}\nif (priv->encoding != SOUP_ENCODING_EOF) {\n    g_set_error_literal(error, G_IO_ERROR, G_IO_ERROR_PARTIAL_INPUT, _(\"Connection terminated unexpectedly\"));\n    return -1;\n}\n```"}]}
{"messages": [{"role": "system", "content": "\n        You are an expert software developer with deep knowlege of c programming language.\n        You have in-depth knowlege about the commit history of libsoup package.\n        Answer questions about how the files, functions and lines of code were changed over range of commits.\n    "}, {"role": "user", "content": "Has the file path of 'libsoup/soup-converter-wrapper.c' changed? What is the new path?"}, {"role": "assistant", "content": "Yes, the file path changed. Old Path: 'libsoup/soup-converter-wrapper.c', New Path: 'libsoup/content-decoder/soup-converter-wrapper.c'."}]}
```
Here, the dataset is designed to enable model to map changes from latest version to the chosen version (Libsoup tag 3.4.4)

### Finetuning Dataset:
Find the generated dataset here:
  - [Training-dataset.jsonl](https://github.com/MadhurAggarwal/Backporting-LLM/blob/main/finetuning/data/training_data/gpt-4o_training_data.jsonl)
  - [Validation-dataset.jsonl](https://github.com/MadhurAggarwal/Backporting-LLM/blob/main/finetuning/data/training_data/gpt-4o_validation_data.jsonl)  
(Scope of Improvement: the validation dataset is too short)

## Finetuning Details:
Chosen Hyper-Parametres: 
  - Batch Size = 2
  - Epochs = 7
  - learning rate = 0.9  
The small batch size help the model learn each individual example well. This enables the model to learn the commit history like paths and changes to specific hunks  
Time taken to finetune gpt-4o: 12 hours GPU waiting queue, 6.5 hours for finetuning.  
### Training Loss:
<img width="1766" height="1285" alt="image" src="https://github.com/user-attachments/assets/32b80189-21ad-4f35-82a7-aec043f360fb" />

### Validation Loss:
<img width="1764" height="1263" alt="image" src="https://github.com/user-attachments/assets/bf110b7f-f7de-48b0-8fe5-544e047eca29" />

### Training Token Accuracy:
<img width="1902" height="1277" alt="image" src="https://github.com/user-attachments/assets/a862e33f-e51c-4c9f-8fcd-477c1f253388" />

### Validation Token Accuracy:
<img width="1903" height="1290" alt="image" src="https://github.com/user-attachments/assets/f05d7759-f7af-4d21-ae32-068779a85e55" />

## How To Run
### To Run Simple Backports:  
Download the Following Outside this Repo:
```
1. Download Azure Linux Repository: https://github.com/microsoft/azurelinux
2. Download Libsoup 3.4.4 Version (Package Used for testing)
```
Download Any LLM Model (Used Model: [Qwen-2.5-Coder-32B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct))
```
git lfs install
git clone https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct
hf download Qwen/Qwen2.5-Coder-32B-Instruct
```
install python dependencies from requirements.txt (or view the VM Setup below)  
Update the Paths for the repositories, dataset (if changed), LLM Model in the [Constants.py](https://github.com/MadhurAggarwal/Backporting-LLM/blob/main/constants.py) file  
Now, just Run [Main-refactored.py](https://github.com/MadhurAggarwal/Backporting-LLM/blob/main/main_refactored.py) file!

### To Create Finetuning Dataset
1. Create `.env` in `Backporting-LLM/finetuning` with the fields (`AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT`). Use [this file](https://github.com/MadhurAggarwal/Backporting-LLM/blob/main/finetuning/azureLLM_handler.py) as reference for env.
2. Update the desired Paths in BOTH the Constants files: finetuning/constants.py, constants.py
3. Run `finetuning/fetch_commit_history.py` file to fetch commits from mentioned Package Version / Commit till latest Origin/master HEAD
4. Run main() function in file `generate_q_a_dataset.py` to generate question-answer pairs, and prepare_dataset_in_proper_format() to convert it into training data format.
5. The dataset will be ready & added to `finetuning/data/training_data/` directory.

### To Test the Finetuned Model
[![View Test README](https://img.shields.io/badge/docs-Test--README-blue)](https://github.com/MadhurAggarwal/Backporting-LLM/blob/main/libsoup_custom_changes_for_swe_test/test_patches/test-readme.md)

## Additional
View [VM Setup](https://www.notion.so/VM-setup-2493774dee53802d8378ffbd953f1a0e?source=copy_link) used for running this framework
