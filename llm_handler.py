from constants import LLM_PATH, FINETUNED_LLM_WEIGHTS
# use  conda activate codellama

from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, TrainingArguments, pipeline
from peft import PeftModel, PeftConfig, LoraConfig, get_peft_model
import torch
from trl import SFTTrainer
import gc

class TrainLLM:
    def __init__(self):
        pass
    
    def finetune_llm(self, train_dataset, test_dataset=None):
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16
        )

        tokenizer = AutoTokenizer.from_pretrained(LLM_PATH)
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = 'right'

        model = AutoModelForCausalLM.from_pretrained(
            LLM_PATH,
            quantization_config=bnb_config,
            device_map="auto"
        )

        peft_config = LoraConfig(
            r=64,
            lora_alpha=16,
            lora_dropout=0.1,
            bias="none",
            task_type="CAUSAL_LM"
        )

        training_args = TrainingArguments(
            per_device_train_batch_size=1,
            gradient_accumulation_steps=4,
            warmup_steps=5,
            max_steps=50,
            learning_rate=2e-4,
            fp16=True,
            logging_steps=5,
            output_dir=FINETUNED_LLM_WEIGHTS,
            save_strategy="steps",
            save_steps=50,
            eval_strategy="steps" if test_dataset else "no",
            eval_steps=25,
            save_total_limit=2,
            remove_unused_columns=False
        )

        def formatting_prompts_func(example):
            text = f"""You are a patch generator.
                <INPUT>
                CVE_DESCRIPTION:
                {example['CVE_DESCRIPTION']}

                UPSTREAM_PATCH:
                {example['UPSTREAM_PATCH']}

                FILE_CODE_LATEST_VERSION:
                {example['FILE_CODES']}
                </INPUT>

                <TASK>
                Update the upstream patch so it applies cleanly to the latest version.
                - DO NOT repeat the input sections.
                - ONLY output the final patch in unified diff format.
                </TASK>

                <OUTPUT>
                {example['AZURELINUX_PATCH']}
                </OUTPUT>
            """
            return text

        trainer = SFTTrainer(
            model=model,
            train_dataset=train_dataset,
            eval_dataset=test_dataset,
            peft_config=peft_config,
            args=training_args,
            formatting_func=formatting_prompts_func
        )

        trainer.train()

        trainer.model.save_pretrained(FINETUNED_LLM_WEIGHTS)
        tokenizer.save_pretrained(FINETUNED_LLM_WEIGHTS)
        print("✅ QLoRA fine-tuning complete, QLoRA weights saved to", FINETUNED_LLM_WEIGHTS)

class RunLLM:
    def __init__(self, create_finetuned_pipeline=False):
        gc.collect()
        torch.cuda.empty_cache()

        if create_finetuned_pipeline:
            self.finetuned_pipeline = self.finetuned_llm_pipeline()
        else:
            self.base_pipeline = self.base_llm_pipeline()

    def check_cuda(self):
        print("Is CUDA Available: ", torch.cuda.is_available())
        print("CUDA Device Name:  ", torch.cuda.get_device_name(0))
        print()

    # def base_llm_pipeline(self):
    #     tokenizer = AutoTokenizer.from_pretrained(LLM_PATH)
    #     model = AutoModelForCausalLM.from_pretrained(LLM_PATH, torch_dtype=torch.float16, device_map="auto")

    #     return pipeline("text-generation", model=model, tokenizer=tokenizer, device_map="auto")

    # def base_llm_pipeline(self):
    #     self.base_tokenizer = AutoTokenizer.from_pretrained(LLM_PATH, use_fast=False)
    #     model = AutoModelForCausalLM.from_pretrained(
    #         LLM_PATH,
    #         torch_dtype=torch.bfloat16,
    #         device_map="auto",
    #         trust_remote_code=True
    #     )
    #     model.eval()

    #     return pipeline(
    #         "text-generation",
    #         model=model,
    #         tokenizer=self.base_tokenizer,
    #         device_map="auto",
    #     )

    def base_llm_pipeline(self):
        self.base_tokenizer = AutoTokenizer.from_pretrained(LLM_PATH, use_fast=False)
        self.base_model = AutoModelForCausalLM.from_pretrained(
            LLM_PATH,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True
        )
        self.base_model.eval()
        return self.base_model

    # def generate_base_output(self, prompt, max_new_tokens=200):
    #     output = self.base_pipeline(prompt, max_new_tokens=max_new_tokens, do_sample=True, return_full_text=False)[0]['generated_text']
    #     return output

    def generate_base_output(self, prompt, max_new_tokens=512, temperature=0.0, top_p=1.0, top_k=0):
        print('Calling Base LLM To Generate Output...')

        inputs = self.base_tokenizer(prompt, return_tensors="pt").to(self.base_model.device)

        outputs = self.base_model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repetition_penalty=1.05,
            pad_token_id=self.base_tokenizer.eos_token_id,
            eos_token_id=self.base_tokenizer.eos_token_id,
        )

        gen_tokens = outputs[0][inputs["input_ids"].shape[1]:]

        decoded = self.base_tokenizer.decode(
            gen_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )

        return decoded


        # print('Calling Base LLM To Generate Output...')
        # outputs = self.base_pipeline(
        #     prompt,
        #     max_new_tokens=max_new_tokens,
        #     # do_sample=True,
        #     # temperature=0.3,         # low randomness, good for deterministic patching
        #     # top_p=0.9,               # nucleus sampling
        #     # top_k=40,                # reduce unlikely tokens
        #     # repetition_penalty=1.05, # avoid duplicated lines
        #     do_sample=False,
        #     temperature=0.0,
        #     top_p=1.0,
        #     top_k=0,
        #     repetition_penalty=1.05,
        #     num_return_sequences=1,

        #     eos_token_id=self.base_pipeline.tokenizer.eos_token_id,
        #     pad_token_id=self.base_pipeline.tokenizer.eos_token_id,
        #     return_full_text=False,
        # )

        # tokens = outputs[0]["generated_token_ids"] if "generated_token_ids" in outputs[0] else None
        # print('Got Tokens.')
        # if tokens is not None:
        #     print('Tokens is Not NONE returning decoded tokens as output text.')
        #     return self.base_pipeline.tokenizer.decode(
        #         tokens,
        #         skip_special_tokens=True,
        #         clean_up_tokenization_spaces=False,
        #     )
        # else:
        #     print('TOKENS IS NONE, RETURNING GENERATED TEXT INSTEAD')
        #     return outputs[0]['generated_text']

    def generate_base_output_with_separate_prompts(self, system_prompt, user_prompt, max_new_tokens=512, temperature=0.0, top_p=1.0, top_k=0):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        prompt = self.base_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        return self.generate_base_output(prompt, max_new_tokens=max_new_tokens, temperature=temperature, top_p=top_p, top_k=top_k)

    def finetuned_llm_pipeline(self):
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )

        tokenizer = AutoTokenizer.from_pretrained(LLM_PATH)
        tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            LLM_PATH,
            quantization_config=bnb_config,
            device_map="auto",
            # low_cpu_mem_usage=True
        )

        model = PeftModel.from_pretrained(
            model,
            FINETUNED_LLM_WEIGHTS,
            device_map="auto"
        )

        # weight diff analysis

        return pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            device_map="auto",
            batch_size=1
        )


    def generate_finetuned_output(self, prompt, max_new_tokens=200):
        if self.finetuned_pipeline:
            print('Calling Finetuned LLM To Generate Output...')
            output = self.finetuned_pipeline(
                prompt, 
                max_new_tokens=max_new_tokens, 
                do_sample=False,
                temperature=0.0,
                top_p=1.0,
                top_k=0,
                repetition_penalty=1.05,
                num_return_sequences=1,
                return_full_text=False
                )[0]['generated_text']
            return output
        return None

def testPrompt():
    llm = RunLLM(create_finetuned_pipeline=False)
    llm.check_cuda()
    
#     system_prompt = """
#     You are a patch Analyzer. Given a patch in the standard diff format, analyze the patch for the given task.
# """

    system_prompt = """

    You are a patch fixer. You will be given an upstream patch that may have incorrect indentation.
    Given a reference code file with the correct indentation,
    find the lines of the patch and fix them to match the indentation (tabs and spaces) as per the reference code file.
"""

    user_prompt = """
    The Patch in standard Git Format is:
    <patch>
    From f182429e5b1fc034050510da20c93256c4fa9652 Mon Sep 17 00:00:00 2001
    From: Patrick Griffis <pgriffis@igalia.com>
    Date: Sat, 16 Nov 2024 12:07:30 -0600
    Subject: [PATCH] Fix heap buffer overflow in soup_content_sniffer_sniff

    Co-Author: Ar Jun <pkillarjun@protonmail.com>
    ---
    libsoup/content-sniffer/soup-content-sniffer.c | 2 +-
    1 file changed, 1 insertion(+), 1 deletion(-)

    diff --git a/libsoup/content-sniffer/soup-content-sniffer.c b/libsoup/content-sniffer/soup-content-sniffer.c
    index de0985eac..b62e48889 100644
    --- a/libsoup/content-sniffer/soup-content-sniffer.c
    +++ b/libsoup/content-sniffer/soup-content-sniffer.c
    @@ -524,7 +524,7 @@ sniff_unknown (SoupContentSniffer *sniffer, GBytes *buffer,
            guint index_pattern = 0;
            gboolean skip_row = FALSE;

    -		while ((index_stream < resource_length) &&
    +		while ((index_stream < resource_length - 1) &&
                (index_pattern <= type_row->pattern_length)) {
                if (type_row->pattern[index_pattern] == ' ') {
    -- 
    GitLab
    <end>
"""

#     user_prompt += """
#     Task:
#     Step 1:
#     The hunk content contains some unchanged lines at first, then changed lines (removed and added lines) and finally some unchanged lines again.   
#     Find out the content of First Mentioned Unchanged Line in the Patch.
#     Then Find the content First Changed Line in the Patch (First Removed Line / Newly Added Line)
    
#     Output for step one:
#     First Mentioned Unchanged Line: <line content>
#     First Changed Line: <line content>
# """

#     user_prompt += """
#     Task:

#     As per this patch,
#     First Mentioned Unchanged Line: `        guint index_pattern = 0;`
#     First Changed Line: `-          while ((index_stream < resource_length) &&`
    
#     Now, look at the following code:
#     "libsoup/content-sniffer/soup-content-sniffer.c": [
#             "524: \t\tif (!sniff_scriptable && type_row->scriptable)\n",
#             "525: \t\t\tcontinue;\n",
#             "526: \n",
#             "527: \t\tif (type_row->has_ws) {\n",
#             "528: \t\t\tguint index_stream = 0;\n",
#             "529: \t\t\tguint index_pattern = 0;\n",
#             "530: \t\t\tgboolean skip_row = FALSE;\n",
#             "531: \n",
#             "532: \t\t\twhile ((index_stream < resource_length) &&\n",
#             "533: \t\t\t       (index_pattern <= type_row->pattern_length)) {\n",
#             "534: \t\t\t\t/* Skip insignificant white space (\"WS\" in the spec) */\n",
#             "535: \t\t\t\tif (type_row->pattern[index_pattern] == ' ') {\n",
#             "536: \t\t\t\t\tif (resource[index_stream] == '\\x09' ||\n",
#             "537: \t\t\t\t\t    resource[index_stream] == '\\x0a' ||\n",
#             "538: \t\t\t\t\t    resource[index_stream] == '\\x0c' ||\n",
#             "539: \t\t\t\t\t    resource[index_stream] == '\\x0d' ||\n",
#             "540: \t\t\t\t\t    resource[index_stream] == '\\x20')\n",
#             "541: \t\t\t\t\t\tindex_stream++;\n",
#             "542: \t\t\t\t\telse\n",
#             "543: \t\t\t\t\t\tindex_pattern++;\n",
#             "544: \t\t\t\t} else {\n",
#             "545: \t\t\t\t\tif ((type_row->mask[index_pattern] & resource[index_stream]) != type_row->pattern[index_pattern]) {\n",
#             "546: \t\t\t\t\t\tskip_row = TRUE;\n",
#             "547: \t\t\t\t\t\tbreak;\n",
#             "548: \t\t\t\t\t}\n"
#         ]

#     Find line numbers of the First Mentioned Unchanged Line and the First Changed Line in this code file.

#     Output For this step:
#     First Mentioned Unchanged Line Number: <line number>
#     First Changed Line Number: <line number>
# """

    # user_prompt += """
    
    # Now, You need to fix the given patch.

    # The line number in the patch hunk, it should be the line number of the first unchanged line in the downstream code.
    # Output only the fixed patch in Standard Git Diff Format.
    # """

    user_prompt += """

    Now, look at the following code file with line number and line content:
    "libsoup/content-sniffer/soup-content-sniffer.c": [
            "524: \t\tif (!sniff_scriptable && type_row->scriptable)\n",
            "525: \t\t\tcontinue;\n",
            "526: \n",
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
            "537: \t\t\t\t\t    resource[index_stream] == '\\x0a' ||\n",
            "538: \t\t\t\t\t    resource[index_stream] == '\\x0c' ||\n",
            "539: \t\t\t\t\t    resource[index_stream] == '\\x0d' ||\n",
            "540: \t\t\t\t\t    resource[index_stream] == '\\x20')\n",
            "541: \t\t\t\t\t\tindex_stream++;\n",
            "542: \t\t\t\t\telse\n",
            "543: \t\t\t\t\t\tindex_pattern++;\n",
            "544: \t\t\t\t} else {\n",
            "545: \t\t\t\t\tif ((type_row->mask[index_pattern] & resource[index_stream]) != type_row->pattern[index_pattern]) {\n",
            "546: \t\t\t\t\t\tskip_row = TRUE;\n",
            "547: \t\t\t\t\t\tbreak;\n",
            "548: \t\t\t\t\t}\n"
        ]

    The patch hunk contains whitespaces instead of tabs in some lines.
    The patch should match EXACTLY the indentation (tabs and spaces) as per the reference code file.
    Fix so that correct number of tab characters, space characters are present in the patch.
    Output only the fixed patch in standard git diff format.

    # TODO: Try this with patch given as repr(patch)
"""

    output = llm.generate_base_output_with_separate_prompts(system_prompt, user_prompt, max_new_tokens=512)

    print("Generated Patch Output:\n")
    print(output)

    print()
    print()

    print(repr(output))

def main():
    llm = RunLLM(create_finetuned_pipeline=False)
    llm.check_cuda()
    
    # prompt = """
    # You are a Patch Fixer.
    # You will be given an upstream patch that may have incorrect line numbers.
    # You need to look at the upstream patch and find which lines are changed. Then you need to look at file code, find out what the new corresponding line numbers are, and make the necessary changes.

    # <UPSTREAM_PATCH>
    # From f182429e5b1fc034050510da20c93256c4fa9652 Mon Sep 17 00:00:00 2001
    # From: Patrick Griffis <pgriffis@igalia.com>
    # Date: Sat, 16 Nov 2024 12:07:30 -0600
    # Subject: [PATCH] Fix heap buffer overflow in soup_content_sniffer_sniff

    # Co-Author: Ar Jun <pkillarjun@protonmail.com>
    # ---
    # libsoup/content-sniffer/soup-content-sniffer.c | 2 +-
    # 1 file changed, 1 insertion(+), 1 deletion(-)

    # diff --git a/libsoup/content-sniffer/soup-content-sniffer.c b/libsoup/content-sniffer/soup-content-sniffer.c
    # index de0985eac..b62e48889 100644
    # --- a/libsoup/content-sniffer/soup-content-sniffer.c
    # +++ b/libsoup/content-sniffer/soup-content-sniffer.c
    # @@ -524,7 +524,7 @@ sniff_unknown (SoupContentSniffer *sniffer, GBytes *buffer,
    #             guint index_pattern = 0;
    #             gboolean skip_row = FALSE;
    
    # -			while ((index_stream < resource_length) &&
    # +			while ((index_stream < resource_length - 1) &&
    #                 (index_pattern <= type_row->pattern_length)) {
    #                 /* Skip insignificant white space ("WS" in the spec) */
    #                 if (type_row->pattern[index_pattern] == ' ') {
    # -- 
    # GitLab
    # </UPSTREAM_PATCH>

    # <CODE_FILES>
    # "libsoup/content-sniffer/soup-content-sniffer.c": [
    #         "524: \t\tif (!sniff_scriptable && type_row->scriptable)\n",
    #         "525: \t\t\tcontinue;\n",
    #         "526: \n",
    #         "527: \t\tif (type_row->has_ws) {\n",
    #         "528: \t\t\tguint index_stream = 0;\n",
    #         "529: \t\t\tguint index_pattern = 0;\n",
    #         "530: \t\t\tgboolean skip_row = FALSE;\n",
    #         "531: \n",
    #         "532: \t\t\twhile ((index_stream < resource_length) &&\n",
    #         "533: \t\t\t       (index_pattern <= type_row->pattern_length)) {\n",
    #         "534: \t\t\t\t/* Skip insignificant white space (\"WS\" in the spec) */\n",
    #         "535: \t\t\t\tif (type_row->pattern[index_pattern] == ' ') {\n",
    #         "536: \t\t\t\t\tif (resource[index_stream] == '\\x09' ||\n",
    #         "537: \t\t\t\t\t    resource[index_stream] == '\\x0a' ||\n",
    #         "538: \t\t\t\t\t    resource[index_stream] == '\\x0c' ||\n",
    #         "539: \t\t\t\t\t    resource[index_stream] == '\\x0d' ||\n",
    #         "540: \t\t\t\t\t    resource[index_stream] == '\\x20')\n",
    #         "541: \t\t\t\t\t\tindex_stream++;\n",
    #         "542: \t\t\t\t\telse\n",
    #         "543: \t\t\t\t\t\tindex_pattern++;\n",
    #         "544: \t\t\t\t} else {\n",
    #         "545: \t\t\t\t\tif ((type_row->mask[index_pattern] & resource[index_stream]) != type_row->pattern[index_pattern]) {\n",
    #         "546: \t\t\t\t\t\tskip_row = TRUE;\n",
    #         "547: \t\t\t\t\t\tbreak;\n",
    #         "548: \t\t\t\t\t}\n"
    #     ]
    # </CODE_FILES>

    # <TASK>
    # Update the upstream patch so it applies cleanly to the latest files.
    # - ONLY output the final patch in STANDARD GIT diff format.
    # - Keep Tabs and spaces exactly as per the FILE_CODE LINES, do not change them.
    # - in a Hunk, @@ -X,a +Y,b @@, 
    #     X is the line number of the first unchanged line in the hunk, 
    #     a is the number of lines in the original file that are part of the hunk, 
    #     Y is the line number of the first unchanged line in the new file that are part of the hunk, 
    #     b is the number of lines in the new file that are part of the hunk.

    #     Changed Line number = 100
    #     and we are preparing a hunk as:
    #             [line 98]  
    #             [line 99]
    #         -   [old line 100]
    #         +   [new line 100]
    #         +   [new line 101]
    #             [old line 101, new line 102]
    #     The hunks start at line 98, even though the change is on line 100.
    #     Also, number of old hunk lines = 4 (98, 99, 100, 101), 
    #     number of new hunk lines = 5 (98, 99, 100, 101, 102), 
    #     so the hunk header will be: @@ -98,4 +98,5 @@
    # - Output patch should be COMPLETE and END properly as per the STANDARD GIT diff format. (-- Gitlab)
    # - Do NOT add any extra formatting like ", ` or brackets.
    # - DO NOT REMOVE ANY SPACE CHARACTERS, for example in (type_row->pattern[index_pattern] == ' '), do not change it to (type_row->pattern[index_pattern] =='').
    # </TASK>

    # <EXAMPLE>

    # <EXAMPLE_UPSTREAM_PATCH>
    # @@ -9,4 +9,4 @@
    # \nvoid traverseArray(int arr[], int size) {
    # -    for (int i = 0; i < size; i++) {
    # +    for (int i = 0; i < size - 1; i+=2) {
    #     printf("Element at index %d: %d\\n", i, arr[i]);
    #             }
    # </EXAMPLE_UPSTREAM_PATCH>

    # <EXAMPLE_CODE_FILE>
    # "myfile.c": [
    #     "20: \t// Function to traverse and print array elements\n",
    #     "21: \tvoid traverseArray(int arr[], int size) {\n",
    #     "22: \t\tfor (int i = 0; i < size; i++) {\n",
    #     "23: \t\t\tprintf(\"Element at index %d: %d\\n\", i, arr[i]);\n",
    #     "24: \t\t}\n",
    #     "25: \t}\n"
    # ]
    # </EXAMPLE_CODE_FILE>

    # <CORRECT_OUTPUT_FOR_EXAMPLE>
    # @@ -20,4 +20,4 @@
    # \tvoid traverseArray(int arr[], int size) {\n"
    # -\t\tfor (int i = 0; i < size; i++) {\n
    # +\t\tfor (int i = 0; i < size; i++) {\n
    # \t\t\tprintf(\"Element at index %d: %d\\n\", i, arr[i]);\n
    # \t\t}\n
    # </CORRECT_OUTPUT_FOR_EXAMPLE>

    # <INCORRECT_OUTPUT_FOR_EXAMPLE>
    # @@ -9,4 +9,4 @@
    # \tvoid traverseArray(int arr[], int size) {\n"
    # -\t\tfor (int i = 0; i < size; i++) {\n
    # +\t\tfor (int i = 0; i < size; i++) {\n
    # \t\t\tprintf(\"Element at index %d: %d\\n\", i, arr[i]);\n
    # \t\t}\n

    # Here, the line number in given patch is 9, but according to given lines it should be 20.
    # </INCORRECT_OUTPUT_FOR_EXAMPLE>

    # <INCORRECT_OUTPUT_FOR_EXAMPLE>
    # @@ -21,4 +21,4 @@
    # \tvoid traverseArray(int arr[], int size) {\n"
    # -\t\tfor (int i = 0; i < size; i++) {\n
    # +\t\tfor (int i = 0; i < size; i++) {\n
    # \t\t\tprintf(\"Element at index %d: %d\\n\", i, arr[i]);\n
    # \t\t}\n

    # Here, Even though the change is in line 21, the first mentioned unchanged line is line 20, so that should be mentioned. it should be @@ -20,4 +20,4 @@ instead.
    # </INCORRECT_OUTPUT_FOR_EXAMPLE>

    # <CORRECT_OUTPUT_FOR_EXAMPLE>
    # @@ -21,4 +21,4 @@
    # -\t\tfor (int i = 0; i < size; i++) {\n
    # +\t\tfor (int i = 0; i < size; i++) {\n
    # \t\t\tprintf(\"Element at index %d: %d\\n\", i, arr[i]);\n
    # \t\t}\n

    # Here, hunk starts at 21, and that is the first line mentioned in the diff as well.
    # </CORRECT_OUTPUT_FOR_EXAMPLE>

    # <INCORRECT_OUTPUT_FOR_EXAMPLE>
    # @@ -20,4 +20,4 @@
    #     void traverseArray(int arr[], int size) {\n"
    # -       for (int i = 0; i < size; i++) {\n
    # +       for (int i = 0; i < size; i++) {\n
    #             printf(\"Element at index %d: %d\\n\", i, arr[i]);\n
    #         }\n

    # Here, tabs in the CODE_LINES have been replaced with spaces in the output patch, which is incorrect. Tabs and spaces must match exactly as per the FILE_CODE lines.
    # </INCORRECT_OUTPUT_FOR_EXAMPLE>

    # generate the output in the standard git diff format without any extra formatting or tokens.
    # ENSURE that if there are any empty lines in the hunk, KEEP THEM.
    # Hunk should have all lines as per the FILE_CODE, including new lines, empty lines, etc.
    # """

    system_prompt = """

You are an upstream patch fixer. Given an upstream patch, and a code file with diverged downstream code, 
you need to fix the upstream patch so it applies cleanly to the downstream code.

Output only the generated patch in standard git diff format, without any extra description or formatting.

Rules you must follow:
- Always adjust hunk headers (@@ -X,Y +A,B @@) so that line numbers exactly match the downstream code context provided. 
- If the upstream patch modifies lines starting at 524, but in downstream those lines appear at 533, 
  update the hunk header to start at 533 (or the correct line number as per <SOURCE>).
- Ensure indentation, tabs, and spaces match exactly the downstream code.
- Do not invent or remove unrelated changes.

"""

    user_prompt = """
Upstream patch content starts in the next line after label <PATCH> and ends
at label <END>

<PATCH>
From f182429e5b1fc034050510da20c93256c4fa9652 Mon Sep 17 00:00:00 2001
From: Patrick Griffis <pgriffis@igalia.com>
Date: Sat, 16 Nov 2024 12:07:30 -0600
Subject: [PATCH] Fix heap buffer overflow in soup_content_sniffer_sniff

Co-Author: Ar Jun <pkillarjun@protonmail.com>
---
 libsoup/content-sniffer/soup-content-sniffer.c | 2 +-
 1 file changed, 1 insertion(+), 1 deletion(-)

diff --git a/libsoup/content-sniffer/soup-content-sniffer.c b/libsoup/content-sniffer/soup-content-sniffer.c
index de0985eac..b62e48889 100644
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
<END>

The downstream code has diverged from the upstream. 
Look at the upstream patch above, the lines added and removed, and adjust the upstream patch as per downstream code.

Important:
- Match the downstream context exactly.
- Recalculate hunk headers so starting line numbers are correct with respect to <SOURCE>.
- Ensure line numbers, tabs, and spaces match exactly as per the downstream code.
- Make sure that hunk line number begins at first matched line (without changes) rather than the first changed line.

Only return the final patch in the standard git diff format.

The downstream version of the code file is given in the next section starting with label <SOURCE> and ending with label <SOURCE_END>, and line number is mentioned along with every line.

<SOURCE>
     1	/* -*- Mode: C; tab-width: 8; indent-tabs-mode: nil; c-basic-offset: 8 -*- */
     2	/*
     3	 * soup-content-sniffer.c
     4	 *
     5	 * Copyright (C) 2009, 2013 Gustavo Noronha Silva.
     6	 *
     7	 * This code implements the following specification:
     8	 *
     9	 *  http://mimesniff.spec.whatwg.org/ as of 11 June 2013
    10	 */
    11	
    12	#ifdef HAVE_CONFIG_H
    13	#include <config.h>
    14	#endif
    15	
    16	#include <string.h>
    17	
    18	#include "soup-content-sniffer.h"
    19	#include "soup-session-feature-private.h"
    20	#include "soup-content-processor.h"
    21	#include "soup-content-sniffer-stream.h"
    22	#include "soup-message-private.h"
    23	#include "soup-message-headers-private.h"
    24	#include "soup-session-feature-private.h"
    25	
    26	/**
    27	 * SoupContentSniffer:
    28	 *
    29	 * Sniffs the mime type of messages.
    30	 *
    31	 * A #SoupContentSniffer tries to detect the actual content type of
    32	 * the files that are being downloaded by looking at some of the data
    33	 * before the [class@Message] emits its [signal@Message::got-headers] signal.
    34	 * #SoupContentSniffer implements [iface@SessionFeature], so you can add
    35	 * content sniffing to a session with [method@Session.add_feature] or
    36	 * [method@Session.add_feature_by_type].
    37	 **/
    38	
    39	static void soup_content_sniffer_session_feature_init (SoupSessionFeatureInterface *feature_interface, gpointer interface_data);
    40	
    41	static SoupContentProcessorInterface *soup_content_sniffer_default_content_processor_interface;
    42	static void soup_content_sniffer_content_processor_init (SoupContentProcessorInterface *interface, gpointer interface_data);
    43	
    44	struct _SoupContentSniffer {
    45	        GObject parent_instance;
    46	};
    47	
    48	G_DEFINE_FINAL_TYPE_WITH_CODE (SoupContentSniffer, soup_content_sniffer, G_TYPE_OBJECT,
    49				       G_IMPLEMENT_INTERFACE (SOUP_TYPE_SESSION_FEATURE,
    50							      soup_content_sniffer_session_feature_init)
    51				       G_IMPLEMENT_INTERFACE (SOUP_TYPE_CONTENT_PROCESSOR,
    52							      soup_content_sniffer_content_processor_init))
    53	
    54	
    55	static GInputStream *
    56	soup_content_sniffer_content_processor_wrap_input (SoupContentProcessor *processor,
    57							   GInputStream *base_stream,
    58							   SoupMessage *msg,
    59							   GError **error)
    60	{
    61		return g_object_new (SOUP_TYPE_CONTENT_SNIFFER_STREAM,
    62				     "base-stream", base_stream,
    63				     "message", msg,
    64				     "sniffer", SOUP_CONTENT_SNIFFER (processor),
    65				     NULL);
    66	}
    67	
    68	static void
    69	soup_content_sniffer_content_processor_init (SoupContentProcessorInterface *processor_interface,
    70	                                            gpointer interface_data)
    71	{
    72		soup_content_sniffer_default_content_processor_interface =
    73			g_type_default_interface_peek (SOUP_TYPE_CONTENT_PROCESSOR);
    74	
    75		processor_interface->processing_stage = SOUP_STAGE_BODY_DATA;
    76		processor_interface->wrap_input = soup_content_sniffer_content_processor_wrap_input;
    77	}
    78	
    79	static void
    80	soup_content_sniffer_init (SoupContentSniffer *content_sniffer)
    81	{
    82	}
    83	
    84	typedef struct {
    85		const guchar *mask;
    86		const guchar *pattern;
    87		guint         pattern_length;
    88		const char   *sniffed_type;
    89	} SoupContentSnifferMediaPattern;
    90	
    91	static char*
    92	sniff_media (SoupContentSniffer *sniffer,
    93		     GBytes *buffer,
    94		     SoupContentSnifferMediaPattern table[],
    95		     int table_length)
    96	{
    97	
    98	        gsize resource_length;
    99	        const guchar *resource = g_bytes_get_data (buffer, &resource_length);
   100	        resource_length = MIN (512, resource_length);
   101		int i;
   102	
   103		for (i = 0; i < table_length; i++) {
   104			SoupContentSnifferMediaPattern *type_row = &(table[i]);
   105			guint j;
   106	
   107			if (resource_length < type_row->pattern_length)
   108				continue;
   109	
   110			for (j = 0; j < type_row->pattern_length; j++) {
   111				if ((type_row->mask[j] & resource[j]) != type_row->pattern[j])
   112					break;
   113			}
   114	
   115			/* This means our comparison above matched completely */
   116			if (j == type_row->pattern_length)
   117				return g_strdup (type_row->sniffed_type);
   118		}
   119	
   120		return NULL;
   121	}
   122	
   123	/* This table is based on the MIMESNIFF spec;
   124	 * See 6.1 Matching an image type pattern
   125	 */
   126	static SoupContentSnifferMediaPattern image_types_table[] = {
   127	
   128		/* Windows icon signature. */
   129		{ (const guchar *)"\xFF\xFF\xFF\xFF",
   130		  (const guchar *)"\x00\x00\x01\x00",
   131		  4,
   132		  "image/x-icon" },
   133	
   134		/* Windows cursor signature. */
   135		{ (const guchar *)"\xFF\xFF\xFF\xFF",
   136		  (const guchar *)"\x00\x00\x02\x00",
   137		  4,
   138		  "image/x-icon" },
   139	
   140		/* BMP. */
   141		{ (const guchar *)"\xFF\xFF",
   142		  (const guchar *)"BM",
   143		  2,
   144		  "image/bmp" },
   145	
   146		/* GIFs. */
   147		{ (const guchar *)"\xFF\xFF\xFF\xFF\xFF\xFF",
   148		  (const guchar *)"GIF87a",
   149		  6,
   150		  "image/gif" },
   151	
   152		{ (const guchar *)"\xFF\xFF\xFF\xFF\xFF\xFF",
   153		  (const guchar *)"GIF89a",
   154		  6,
   155		  "image/gif" },
   156	
   157		/* WEBP. */
   158		{ (const guchar *)"\xFF\xFF\xFF\xFF\x00\x00\x00\x00\xFF\xFF\xFF\xFF\xFF\xFF",
   159		  (const guchar *)"RIFF\x00\x00\x00\x00WEBPVP",
   160		  14,
   161		  "image/webp" },
   162	
   163		/* PNG. */
   164		{ (const guchar *)"\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF",
   165		  (const guchar *)"\x89PNG\x0D\x0A\x1A\x0A",
   166		  8,
   167		  "image/png" },
   168	
   169		/* JPEG. */
   170		{ (const guchar *)"\xFF\xFF\xFF",
   171		  (const guchar *)"\xFF\xD8\xFF",
   172		  3,
   173		  "image/jpeg" },
   174	};
   175	
   176	static char*
   177	sniff_images (SoupContentSniffer *sniffer, GBytes *buffer)
   178	{
   179		return sniff_media (sniffer,
   180				    buffer,
   181				    image_types_table,
   182				    G_N_ELEMENTS (image_types_table));
   183	}
   184	
   185	/* This table is based on the MIMESNIFF spec;
   186	 * See 6.2 Matching an audio or video type pattern
   187	 */
   188	static SoupContentSnifferMediaPattern audio_video_types_table[] = {
   189		{ (const guchar *)"\xFF\xFF\xFF\xFF",
   190		  (const guchar *)"\x1A\x45\xDF\xA3",
   191		  4,
   192		  "video/webm" },
   193	
   194		{ (const guchar *)"\xFF\xFF\xFF\xFF",
   195		  (const guchar *)".snd",
   196		  4,
   197		  "audio/basic" },
   198	
   199	
   200		{ (const guchar *)"\xFF\xFF\xFF\xFF\x00\x00\x00\x00\xFF\xFF\xFF\xFF",
   201		  (const guchar *)"FORM\0\0\0\0AIFF",
   202		  12,
   203		  "audio/aiff" },
   204	
   205		{ (const guchar *)"\xFF\xFF\xFF",
   206		  (const guchar *)"ID3",
   207		  3,
   208		  "audio/mpeg" },
   209	
   210		{ (const guchar *)"\xFF\xFF\xFF\xFF\xFF",
   211		  (const guchar *)"OggS\0",
   212		  5,
   213		  "application/ogg" },
   214	
   215		{ (const guchar *)"\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF",
   216		  (const guchar *)"MThd\x00\x00\x00\x06",
   217		  8,
   218		  "audio/midi" },
   219	
   220		{ (const guchar *)"\xFF\xFF\xFF\xFF\x00\x00\x00\x00\xFF\xFF\xFF\xFF",
   221		  (const guchar *)"RIFF\x00\x00\x00\x00AVI ",
   222		  12,
   223		  "video/avi" },
   224	
   225		{ (const guchar *)"\xFF\xFF\xFF\xFF\x00\x00\x00\x00\xFF\xFF\xFF\xFF",
   226		  (const guchar *)"RIFF\x00\x00\x00\x00WAVE",
   227		  12,
   228		  "audio/wave" },
   229	};
   230	
   231	static gboolean
   232	data_has_prefix (const char *data, const char *prefix, gsize max_length)
   233	{
   234	        if (strlen (prefix) > max_length)
   235	                return FALSE;
   236	
   237	        return memcmp (data, prefix, strlen (prefix)) == 0;
   238	}
   239	
   240	static gboolean
   241	sniff_mp4 (SoupContentSniffer *sniffer, GBytes *buffer)
   242	{
   243		gsize resource_length;
   244		const char *resource = g_bytes_get_data (buffer, &resource_length);
   245		resource_length = MIN (512, resource_length);
   246		guint32 box_size = *((guint32*)resource);
   247		guint i;
   248	
   249	#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
   250		box_size = ((box_size >> 24) |
   251			    ((box_size << 8) & 0x00FF0000) |
   252			    ((box_size >> 8) & 0x0000FF00) |
   253			    (box_size << 24));
   254	#endif
   255	
   256		if (resource_length < 12 || resource_length < box_size || box_size % 4 != 0)
   257			return FALSE;
   258	
   259		if (!data_has_prefix (resource + 4, "ftyp", resource_length - 4))
   260			return FALSE;
   261	
   262		if (!data_has_prefix (resource + 8, "mp4", resource_length - 8))
   263			return FALSE;
   264	
   265		for (i = 16; i < box_size && i < resource_length; i = i + 4) {
   266			if (data_has_prefix (resource + i, "mp4", resource_length - i))
   267				return TRUE;
   268		}
   269	
   270		return FALSE;
   271	}
   272	
   273	static char*
   274	sniff_audio_video (SoupContentSniffer *sniffer, GBytes *buffer)
   275	{
   276		char *sniffed_type;
   277	
   278		sniffed_type = sniff_media (sniffer,
   279					    buffer,
   280					    audio_video_types_table,
   281					    G_N_ELEMENTS (audio_video_types_table));
   282	
   283		if (sniffed_type != NULL)
   284			return sniffed_type;
   285	
   286		if (sniff_mp4 (sniffer, buffer))
   287			return g_strdup ("video/mp4");
   288	
   289		return NULL;
   290	}
   291	
   292	/* This table is based on the MIMESNIFF spec;
   293	 * See 7.1 Identifying a resource with an unknown MIME type
   294	 */
   295	typedef struct {
   296		/* @has_ws is TRUE if @pattern contains "generic" whitespace */
   297		gboolean      has_ws;
   298		/* @has_tag_termination is TRUE if we should check for a tag-terminating
   299		 * byte (0x20 " " or 0x3E ">") after the pattern match.
   300		 */
   301		gboolean      has_tag_termination;
   302		const guchar *mask;
   303		const guchar *pattern;
   304		guint         pattern_length;
   305		const char   *sniffed_type;
   306		gboolean      scriptable;
   307	} SoupContentSnifferPattern;
   308	
   309	
   310	/* When has_ws is TRUE, spaces in the pattern will indicate where insignificant space
   311	 * is allowed. Those spaces are marked with \x00 on the mask.
   312	 */
   313	static SoupContentSnifferPattern types_table[] = {
   314		/* Scriptable types. */
   315	
   316		{ TRUE, TRUE,
   317		  (const guchar *)"\x00\xFF\xFF\xDF\xDF\xDF\xDF\xDF\xDF\xDF\xFF\xDF\xDF\xDF\xDF",
   318		  (const guchar *)" <!DOCTYPE HTML",
   319		  14,
   320		  "text/html",
   321		  TRUE },
   322	
   323		{ TRUE, TRUE,
   324		  (const guchar *)"\x00\xFF\xDF\xDF\xDF\xDF",
   325		  (const guchar *)" <HTML",
   326		  5,
   327		  "text/html",
   328		  TRUE },
   329	
   330		{ TRUE, TRUE,
   331		  (const guchar *)"\x00\xFF\xDF\xDF\xDF\xDF",
   332		  (const guchar *)" <HEAD",
   333		  5,
   334		  "text/html",
   335		  TRUE },
   336	
   337		{ TRUE, TRUE,
   338		  (const guchar *)"\x00\xFF\xDF\xDF\xDF\xDF\xDF\xDF",
   339		  (const guchar *)" <SCRIPT",
   340		  7,
   341		  "text/html",
   342		  TRUE },
   343	
   344		{ TRUE, TRUE,
   345		  (const guchar *)"\x00\xFF\xDF\xDF\xDF\xDF\xDF\xDF",
   346		  (const guchar *)" <IFRAME",
   347		  7,
   348		  "text/html",
   349		  TRUE },
   350	
   351		{ TRUE, TRUE,
   352		  (const guchar *)"\x00\xFF\xDF\xFF",
   353		  (const guchar *)" <H1",
   354		  3,
   355		  "text/html",
   356		  TRUE },
   357	
   358		{ TRUE, TRUE,
   359		  (const guchar *)"\x00\xFF\xDF\xDF\xDF",
   360		  (const guchar *)" <DIV",
   361		  4,
   362		  "text/html",
   363		  TRUE },
   364	
   365		{ TRUE, TRUE,
   366		  (const guchar *)"\x00\xFF\xDF\xDF\xDF\xDF",
   367		  (const guchar *)" <FONT",
   368		  5,
   369		  "text/html",
   370		  TRUE },
   371	
   372		{ TRUE, TRUE,
   373		  (const guchar *)"\x00\xFF\xDF\xDF\xDF\xDF\xDF",
   374		  (const guchar *)" <TABLE",
   375		  6,
   376		  "text/html",
   377		  TRUE },
   378	
   379		{ TRUE, TRUE,
   380		  (const guchar *)"\x00\xFF\xDF",
   381		  (const guchar *)" <A",
   382		  2,
   383		  "text/html",
   384		  TRUE },
   385	
   386		{ TRUE, TRUE,
   387		  (const guchar *)"\x00\xFF\xDF\xDF\xDF\xDF\xDF",
   388		  (const guchar *)" <STYLE",
   389		  6,
   390		  "text/html",
   391		  TRUE },
   392	
   393		{ TRUE, TRUE,
   394		  (const guchar *)"\x00\xFF\xDF\xDF\xDF\xDF\xDF",
   395		  (const guchar *)" <TITLE",
   396		  6,
   397		  "text/html",
   398		  TRUE },
   399	
   400		{ TRUE, TRUE,
   401		  (const guchar *)"\x00\xFF\xDF",
   402		  (const guchar *)" <B",
   403		  2,
   404		  "text/html",
   405		  TRUE },
   406	
   407		{ TRUE, TRUE,
   408		  (const guchar *)"\x00\xFF\xDF\xDF\xDF\xDF",
   409		  (const guchar *)" <BODY",
   410		  5,
   411		  "text/html",
   412		  TRUE },
   413	
   414		{ TRUE, TRUE,
   415		  (const guchar *)"\x00\xFF\xDF\xDF",
   416		  (const guchar *)" <BR",
   417		  3,
   418		  "text/html",
   419		  TRUE },
   420	
   421		{ TRUE, TRUE,
   422		  (const guchar *)"\x00\xFF\xDF",
   423		  (const guchar *)" <P",
   424		  2,
   425		  "text/html",
   426		  TRUE },
   427	
   428		{ TRUE, TRUE,
   429		  (const guchar *)"\x00\xFF\xFF\xFF\xFF",
   430		  (const guchar *)" <!--",
   431		  4,
   432		  "text/html",
   433		  TRUE },
   434	
   435		{ TRUE, FALSE,
   436		  (const guchar *)"\x00\xFF\xFF\xFF\xFF\xFF",
   437		  (const guchar *)" <?xml",
   438		  5,
   439		  "text/xml",
   440		  TRUE },
   441	
   442		{ FALSE, FALSE,
   443		  (const guchar *)"\xFF\xFF\xFF\xFF\xFF",
   444		  (const guchar *)"%PDF-",
   445		  5,
   446		  "application/pdf",
   447		  TRUE },
   448	
   449		/* Non-scriptable types. */
   450		{ FALSE, FALSE,
   451		  (const guchar *)"\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF",
   452		  (const guchar *)"%!PS-Adobe-",
   453		  11,
   454		  "application/postscript",
   455		  FALSE },
   456	
   457		{ FALSE, FALSE, /* UTF-16BE BOM */
   458		  (const guchar *)"\xFF\xFF\x00\x00",
   459		  (const guchar *)"\xFE\xFF\x00\x00",
   460		  4,
   461		  "text/plain",
   462		  FALSE },
   463	
   464		{ FALSE, FALSE, /* UTF-16LE BOM */
   465		  (const guchar *)"\xFF\xFF\x00\x00",
   466		  (const guchar *)"\xFF\xFE\x00\x00",
   467		  4,
   468		  "text/plain",
   469		  FALSE },
   470	
   471		{ FALSE, FALSE, /* UTF-8 BOM */
   472		  (const guchar *)"\xFF\xFF\xFF\x00",
   473		  (const guchar *)"\xEF\xBB\xBF\x00",
   474		  4,
   475		  "text/plain",
   476		  FALSE },
   477	};
   478	
   479	/* Whether a given byte looks like it might be part of binary content.
   480	 * Source: HTML5 spec; borrowed from the Chromium mime sniffer code,
   481	 * which is BSD-licensed
   482	 */
   483	static char byte_looks_binary[] = {
   484		1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 1,  /* 0x00 - 0x0F */
   485		1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1,  /* 0x10 - 0x1F */
   486		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  /* 0x20 - 0x2F */
   487		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  /* 0x30 - 0x3F */
   488		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  /* 0x40 - 0x4F */
   489		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  /* 0x50 - 0x5F */
   490		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  /* 0x60 - 0x6F */
   491		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  /* 0x70 - 0x7F */
   492		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  /* 0x80 - 0x8F */
   493		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  /* 0x90 - 0x9F */
   494		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  /* 0xA0 - 0xAF */
   495		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  /* 0xB0 - 0xBF */
   496		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  /* 0xC0 - 0xCF */
   497		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  /* 0xD0 - 0xDF */
   498		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  /* 0xE0 - 0xEF */
   499		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  /* 0xF0 - 0xFF */
   500	};
   501	
   502	/* HTML5: 2.7.4 Content-Type sniffing: unknown type */
   503	static char*
   504	sniff_unknown (SoupContentSniffer *sniffer, GBytes *buffer,
   505		       gboolean sniff_scriptable)
   506	{
   507		char *sniffed_type = NULL;
   508		gsize resource_length;
   509		const guchar *resource = g_bytes_get_data (buffer, &resource_length);
   510		resource_length = MIN (512, resource_length);
   511		guint i;
   512	
   513	        if (resource_length == 0)
   514	                return g_strdup ("text/plain");
   515	
   516		for (i = 0; i < G_N_ELEMENTS (types_table); i++) {
   517			SoupContentSnifferPattern *type_row = &(types_table[i]);
   518	
   519			if (!sniff_scriptable && type_row->scriptable)
   520				continue;
   521	
   522			if (!sniff_scriptable && type_row->scriptable)
   523				continue;
   524	
   525			if (!sniff_scriptable && type_row->scriptable)
   526				continue;
   527			count = 0;
   528			if (type_row->has_ws) {
   529				foo=0;
   530				bar=0;
   531				baz=0;
   532				guint index_stream = 0;
   533				guint index_pattern = 0;
   534				gboolean skip_row = FALSE;
   535	
   536				while ((index_stream < resource_length) &&
   537				       (index_pattern <= type_row->pattern_length)) {
   538					/* Skip insignificant white space ("WS" in the spec) */
   539					if (type_row->pattern[index_pattern] == ' ') {
   540						if (resource[index_stream] == '\x09' ||
   541						    resource[index_stream] == '\x0a' ||
   542						    resource[index_stream] == '\x0c' ||
   543						    resource[index_stream] == '\x0d' ||
   544						    resource[index_stream] == '\x20')
   545							index_stream++;
   546						else
   547							index_pattern++;
   548					} else {
   549						if ((type_row->mask[index_pattern] & resource[index_stream]) != type_row->pattern[index_pattern]) {
   550							skip_row = TRUE;
   551							break;
   552						}
   553						index_pattern++;
   554						index_stream++;
   555					}
   556				}
   557	
   558				if (skip_row)
   559					continue;
   560	
   561				if (index_pattern > type_row->pattern_length) {
   562					if (type_row->has_tag_termination &&
   563					    resource[index_stream] != '\x20' &&
   564					    resource[index_stream] != '\x3E')
   565						continue;
   566	
   567					return g_strdup (type_row->sniffed_type);
   568				}
   569			} else {
   570				guint j;
   571	
   572				if (resource_length < type_row->pattern_length)
   573					continue;
   574	
   575				for (j = 0; j < type_row->pattern_length; j++) {
   576					if ((type_row->mask[j] & resource[j]) != type_row->pattern[j])
   577						break;
   578				}
   579	
   580				/* This means our comparison above matched completely */
   581				if (j == type_row->pattern_length)
   582					return g_strdup (type_row->sniffed_type);
   583			}
   584		}
   585	
   586		sniffed_type = sniff_images (sniffer, buffer);
   587	
   588		if (sniffed_type != NULL)
   589			return sniffed_type;
   590	
   591		sniffed_type = sniff_audio_video (sniffer, buffer);
   592	
   593		if (sniffed_type != NULL)
   594			return sniffed_type;
   595	
   596		for (i = 0; i < resource_length; i++) {
   597			if (byte_looks_binary[resource[i]])
   598				return g_strdup ("application/octet-stream");
   599		}
   600	
   601		return g_strdup ("text/plain");
   602	}
   603	
   604	/* MIMESNIFF: 7.2 Sniffing a mislabeled binary resource */
   605	static char*
   606	sniff_text_or_binary (SoupContentSniffer *sniffer, GBytes *buffer)
   607	{
   608		gsize resource_length;
   609		const guchar *resource = g_bytes_get_data (buffer, &resource_length);
   610		resource_length = MIN (512, resource_length);
   611		gboolean looks_binary = FALSE;
   612		int i;
   613	
   614		/* 2. Detecting UTF-16BE, UTF-16LE BOMs means it's text/plain */
   615		if (resource_length >= 2) {
   616			if ((resource[0] == 0xFE && resource[1] == 0xFF) ||
   617			    (resource[0] == 0xFF && resource[1] == 0xFE))
   618				return g_strdup ("text/plain");
   619		}
   620	
   621		/* 3. UTF-8 BOM. */
   622		if (resource_length >= 3) {
   623			if (resource[0] == 0xEF && resource[1] == 0xBB && resource[2] == 0xBF)
   624				return g_strdup ("text/plain");
   625		}
   626	
   627		/* 4. Look to see if any of the first n bytes looks binary */
   628		for (i = 0; i < resource_length; i++) {
   629			if (byte_looks_binary[resource[i]]) {
   630				looks_binary = TRUE;
   631				break;
   632			}
   633		}
   634	
   635		if (!looks_binary)
   636			return g_strdup ("text/plain");
   637	
   638		/* 5. Execute 7.1 Identifying a resource with an unknown MIME type.
   639		 * TODO: sniff-scriptable needs to be unset.
   640		 */
   641		return sniff_unknown (sniffer, buffer, TRUE);
   642	}
   643	
   644	static gboolean
   645	skip_insignificant_space (const char *resource, gsize *pos, gsize resource_length)
   646	{
   647	        if (*pos >= resource_length)
   648		        return TRUE;
   649	
   650		while ((resource[*pos] == '\x09') ||
   651		       (resource[*pos] == '\x20') ||
   652		       (resource[*pos] == '\x0A') ||
   653		       (resource[*pos] == '\x0D')) {
   654			*pos = *pos + 1;
   655	
   656			if (*pos > resource_length)
   657				return TRUE;
   658		}
   659	
   660		return FALSE;
   661	}
   662	
   663	static char*
   664	sniff_feed_or_html (SoupContentSniffer *sniffer, GBytes *buffer)
   665	{
   666		gsize resource_length;
   667		const char *resource = g_bytes_get_data (buffer, &resource_length);
   668		resource_length = MIN (512, resource_length);
   669		gsize pos = 0;
   670	
   671		if (resource_length < 3)
   672			goto text_html;
   673	
   674		/* Skip a leading UTF-8 BOM */
   675		if ((guchar)resource[0] == 0xEF && (guchar)resource[1] == 0xBB && (guchar)resource[2] == 0xBF)
   676			pos = 3;
   677	
   678	 look_for_tag:
   679		if (skip_insignificant_space (resource, &pos, resource_length))
   680			goto text_html;
   681	
   682		if (resource[pos] != '<')
   683			return g_strdup ("text/html");
   684	
   685		pos++;
   686	
   687		if ((pos + 2) > resource_length)
   688			goto text_html;
   689	
   690		/* Skip comments. */
   691		if (data_has_prefix (resource + pos, "!--", resource_length - pos)) {
   692			pos = pos + 3;
   693	
   694			if ((pos + 2) > resource_length)
   695				goto text_html;
   696	
   697			while (!data_has_prefix (resource + pos, "-->", resource_length - pos)) {
   698				pos++;
   699	
   700				if ((pos + 2) > resource_length)
   701					goto text_html;
   702			}
   703	
   704			pos = pos + 3;
   705	
   706			goto look_for_tag;
   707		}
   708	
   709		if (pos > resource_length)
   710			goto text_html;
   711	
   712		if (resource[pos] == '!') {
   713			do {
   714				pos++;
   715	
   716				if (pos > resource_length)
   717					goto text_html;
   718			} while (resource[pos] != '>');
   719	
   720			pos++;
   721	
   722			goto look_for_tag;
   723		} else if (resource[pos] == '?') {
   724			do {
   725				pos++;
   726	
   727				if ((pos + 1) > resource_length)
   728					goto text_html;
   729			} while (!data_has_prefix (resource + pos, "?>", resource_length - pos));
   730	
   731			pos = pos + 2;
   732	
   733			goto look_for_tag;
   734		}
   735	
   736		if ((pos + 3) > resource_length)
   737			goto text_html;
   738	
   739		if (data_has_prefix (resource + pos, "rss", resource_length - pos))
   740			return g_strdup ("application/rss+xml");
   741	
   742		if ((pos + 4) > resource_length)
   743			goto text_html;
   744	
   745		if (data_has_prefix (resource + pos, "feed", resource_length - pos))
   746			return g_strdup ("application/atom+xml");
   747	
   748		if ((pos + 7) > resource_length)
   749			goto text_html;
   750	
   751		if (data_has_prefix (resource + pos, "rdf:RDF", resource_length - pos)) {
   752			pos = pos + 7;
   753	
   754			if (skip_insignificant_space (resource, &pos, resource_length))
   755				goto text_html;
   756	
   757			if ((pos + 32) > resource_length)
   758				goto text_html;
   759	
   760			if (data_has_prefix (resource + pos, "xmlns=\"http://purl.org/rss/1.0/\"", resource_length - pos)) {
   761				pos = pos + 32;
   762	
   763				if (skip_insignificant_space (resource, &pos, resource_length))
   764					goto text_html;
   765	
   766				if ((pos + 55) > resource_length)
   767					goto text_html;
   768	
   769				if (data_has_prefix (resource + pos, "xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\"", resource_length - pos))
   770					return g_strdup ("application/rss+xml");
   771			}
   772	
   773			if ((pos + 55) > resource_length)
   774				goto text_html;
   775	
   776			if (data_has_prefix (resource + pos, "xmlns:rdf=\"http://www.w3.org/1999/02/22-rdf-syntax-ns#\"", resource_length - pos)) {
   777				pos = pos + 55;
   778	
   779				if (skip_insignificant_space (resource, &pos, resource_length))
   780					goto text_html;
   781	
   782				if ((pos + 32) > resource_length)
   783					goto text_html;
   784	
   785				if (data_has_prefix (resource + pos, "xmlns=\"http://purl.org/rss/1.0/\"", resource_length - pos))
   786					return g_strdup ("application/rss+xml");
   787			}
   788		}
   789	
   790	 text_html:
   791		return g_strdup ("text/html");
   792	}
   793	
   794	/**
   795	 * soup_content_sniffer_sniff:
   796	 * @sniffer: a #SoupContentSniffer
   797	 * @msg: the message to sniff
   798	 * @buffer: a buffer containing the start of @msg's response body
   799	 * @params: (element-type utf8 utf8) (out) (transfer full) (nullable): return
   800	 *   location for Content-Type parameters (eg, "charset"), or %NULL
   801	 *
   802	 * Sniffs @buffer to determine its Content-Type.
   803	 *
   804	 * The result may also be influenced by the Content-Type declared in @msg's
   805	 * response headers.
   806	 *
   807	 * Returns: the sniffed Content-Type of @buffer; this will never be %NULL,
   808	 *   but may be `application/octet-stream`.
   809	 */
   810	char *
   811	soup_content_sniffer_sniff (SoupContentSniffer *sniffer, SoupMessage *msg,
   812				    GBytes *buffer, GHashTable **params)
   813	{
   814		const char *content_type;
   815		const char *x_content_type_options;
   816		char *sniffed_type = NULL;
   817		gboolean no_sniff = FALSE;
   818	
   819		content_type = soup_message_headers_get_content_type (soup_message_get_response_headers (msg), params);
   820	
   821		/* MIMESNIFF: 7 Determining the sniffed MIME type of a resource. */
   822	
   823		x_content_type_options = soup_message_headers_get_one_common (soup_message_get_response_headers (msg), SOUP_HEADER_X_CONTENT_TYPE_OPTIONS);
   824		if (!g_strcmp0 (x_content_type_options, "nosniff"))
   825			no_sniff = TRUE;
   826	
   827		/* 1. Unknown/undefined supplied type with sniff-scritable = !nosniff. */
   828		if ((content_type == NULL) ||
   829		    !g_ascii_strcasecmp (content_type, "unknown/unknown") ||
   830		    !g_ascii_strcasecmp (content_type, "application/unknown") ||
   831		    !g_ascii_strcasecmp (content_type, "*/*"))
   832			return sniff_unknown (sniffer, buffer, !no_sniff);
   833	
   834		/* 2. If nosniff is specified in X-Content-Type-Options use the supplied MIME type. */
   835		if (no_sniff)
   836			return g_strdup (content_type);
   837	
   838		/* 3. check-for-apache-bug */
   839		if ((content_type != NULL) &&
   840		    (g_str_equal (content_type, "text/plain") ||
   841		     g_str_equal (content_type, "text/plain; charset=ISO-8859-1") ||
   842		     g_str_equal (content_type, "text/plain; charset=iso-8859-1") ||
   843		     g_str_equal (content_type, "text/plain; charset=UTF-8")))
   844			return sniff_text_or_binary (sniffer, buffer);
   845	
   846		/* 4. XML types sent by the server are always used. */
   847		if (g_str_has_suffix (content_type, "+xml") ||
   848		    !g_ascii_strcasecmp (content_type, "text/xml") ||
   849		    !g_ascii_strcasecmp (content_type, "application/xml"))
   850			return g_strdup (content_type);
   851	
   852		/* 5. Distinguish feed from HTML. */
   853		if (!g_ascii_strcasecmp (content_type, "text/html"))
   854			return sniff_feed_or_html (sniffer, buffer);
   855	
   856		/* 6. Image types.
   857		 */
   858		if (!g_ascii_strncasecmp (content_type, "image/", 6)) {
   859			sniffed_type = sniff_images (sniffer, buffer);
   860			if (sniffed_type != NULL)
   861				return sniffed_type;
   862			return g_strdup (content_type);
   863		}
   864	
   865		/* 7. Audio and video types. */
   866		if (!g_ascii_strncasecmp (content_type, "audio/", 6) ||
   867		    !g_ascii_strncasecmp (content_type, "video/", 6) ||
   868		    !g_ascii_strcasecmp (content_type, "application/ogg")) {
   869		        sniffed_type = sniff_audio_video (sniffer, buffer);
   870		        if (sniffed_type != NULL)
   871			        return sniffed_type;
   872			return g_strdup (content_type);
   873	        }
   874	
   875		/* If we got text/plain, use text_or_binary */
   876		if (g_str_equal (content_type, "text/plain")) {
   877			return sniff_text_or_binary (sniffer, buffer);
   878		}
   879	
   880		return g_strdup (content_type);
   881	}
   882	
   883	static void
   884	soup_content_sniffer_request_queued (SoupSessionFeature *feature,
   885					     SoupMessage        *msg)
   886	{
   887		soup_message_set_content_sniffer (msg, SOUP_CONTENT_SNIFFER (feature));
   888	}
   889	
   890	static void
   891	soup_content_sniffer_request_unqueued (SoupSessionFeature *feature,
   892					       SoupMessage        *msg)
   893	{
   894		soup_message_set_content_sniffer (msg, NULL);
   895	}
   896	
   897	static void
   898	soup_content_sniffer_class_init (SoupContentSnifferClass *content_sniffer_class)
   899	{
   900	}
   901	
   902	static void
   903	soup_content_sniffer_session_feature_init (SoupSessionFeatureInterface *feature_interface,
   904						   gpointer interface_data)
   905	{
   906		feature_interface->request_queued = soup_content_sniffer_request_queued;
   907		feature_interface->request_unqueued = soup_content_sniffer_request_unqueued;
   908	}
   909	
   910	/**
   911	 * soup_content_sniffer_new:
   912	 *
   913	 * Creates a new #SoupContentSniffer.
   914	 *
   915	 * Returns: a new #SoupContentSniffer
   916	 **/
   917	SoupContentSniffer *
   918	soup_content_sniffer_new (void)
   919	{
   920		return g_object_new (SOUP_TYPE_CONTENT_SNIFFER, NULL);
   921	}
<SOURCE_END>
"""

    base_output = llm.generate_base_output_with_separate_prompts(system_prompt, user_prompt, max_new_tokens=1000)

    print("\n\nBase Output:")
    print(base_output)

if __name__ == "__main__":
    # main()
    testPrompt()


    # def finetune_llm(self, train_dataset, test_dataset=None):
    #     bnb_config = BitsAndBytesConfig(
    #         load_in_4bit=True,
    #         bnb_4bit_use_double_quant=True,
    #         bnb_4bit_quant_type="nf4",
    #         bnb_4bit_compute_dtype=torch.float16
    #     )

    #     tokenizer = AutoTokenizer.from_pretrained(LLM_PATH)
    #     tokenizer.pad_token = tokenizer.eos_token

    #     # Load Model in Quantized (4bit) Way
    #     model = AutoModelForCausalLM.from_pretrained(
    #         LLM_PATH,
    #         quantization_config=bnb_config,
    #         device_map="auto"
    #     )

    #     # LoRA config
    #     peft_config = LoraConfig(
    #         r=64,
    #         lora_alpha=16,
    #         lora_dropout=0.1,
    #         bias="none",
    #         task_type="CAUSAL_LM"
    #     )

    #     # Training arguments
    #     training_args = TrainingArguments(
    #         per_device_train_batch_size=1,
    #         gradient_accumulation_steps=4,
    #         warmup_steps=5,
    #         max_steps=50,
    #         learning_rate=2e-4,
    #         fp16=True,
    #         logging_steps=5,
    #         output_dir=FINETUNED_LLM_WEIGHTS,
    #         save_strategy="steps",
    #         save_steps=50,
    #         eval_strategy="steps" if test_dataset else "no",   # run evaluation during training
    #         eval_steps=25,                                           # how often to evaluate
    #         save_total_limit=2                                       # keep only 2 checkpoints
    #     )

    #     def tokenize_fn(example):
    #         prompt = f"""
    #             You are a patch generator.

    #             <INPUT>
    #             CVE_DESCRIPTION:
    #             {example['CVE_DESCRIPTION']}

    #             UPSTREAM_PATCH:
    #             {example['UPSTREAM_PATCH']}

    #             FILE_CODE_LATEST_VERSION:
    #             {example['FILE_CODES']}
    #             </INPUT>

    #             <TASK>
    #             Update the upstream patch so it applies cleanly to the latest version.
    #             - DO NOT repeat the input sections.
    #             - ONLY output the final patch in unified diff format.
    #             </TASK>

    #             <OUTPUT>
    #         """

    #         output = f"""
    #             {example['AZURELINUX_PATCH']}
    #             </OUTPUT>
    #         """

    #         # Tokenize separately
    #         prompt_ids = tokenizer(prompt, truncation=True, add_special_tokens=True)["input_ids"]
    #         output_ids = tokenizer(output, truncation=True, add_special_tokens=False)["input_ids"]

    #         # Mask labels so loss is only on the output part
    #         labels = [-100] * len(prompt_ids) + output_ids

    #         return {
    #             "input_ids": prompt_ids + output_ids,
    #             "attention_mask": [1] * (len(prompt_ids) + len(output_ids)),
    #             "labels": labels
    #         }

    #     tokenized_train = train_dataset.map(tokenize_fn, remove_columns=train_dataset.column_names)
    #     tokenized_test = None
    #     if test_dataset is not None:
    #         tokenized_test = test_dataset.map(tokenize_fn, remove_columns=test_dataset.column_names)

    #     trainer = SFTTrainer(
    #         model=model,
    #         train_dataset=tokenized_train,
    #         eval_dataset=tokenized_test,
    #         peft_config=peft_config,
    #         args=training_args
    #     )

    #     trainer.train()

    #     trainer.model.save_pretrained(FINETUNED_LLM_WEIGHTS)
    #     tokenizer.save_pretrained(FINETUNED_LLM_WEIGHTS)
    #     print("✅ QLoRA fine-tuning complete, LoRA saved to", FINETUNED_LLM_WEIGHTS)