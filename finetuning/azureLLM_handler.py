import os
from openai import OpenAI, AzureOpenAI
from dotenv import load_dotenv
import json

class AzureLLMHandler:
    def __init__(self):
        load_dotenv()

        self.api_key          = os.getenv("AZURE_OPENAI_API_KEY")
        self.api_endpoint     = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.finetuned_deployment = os.getenv("AZURE_OPENAI_FINETUNED_DEPLOYEMENT")
        self.finetuned_endpoint = os.getenv("AZURE_OPENAI_FINETUNED_ENDPOINT")

        if not self.api_endpoint:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT environment variable is required.\n"
                "Set it with: export AZURE_OPENAI_ENDPOINT='https://your-resource-name.openai.azure.com/'"
            )

        if not self.api_key:
            raise ValueError(
                "AZURE_OPENAI_API_KEY environment variable is required.\n"
                "Set it with: export AZURE_OPENAI_API_KEY='your_api_key'"
            )

        print(f"Using Azure OpenAI Endpoint: {self.api_endpoint}")
        print(f"Using Azure OpenAI Deployment: {self.azure_deployment}")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_endpoint,
            )

        self.finetuned_client = AzureOpenAI(
            api_version="2024-12-01-preview",
            api_key=self.api_key,
            base_url=self.finetuned_endpoint,
        )

    def call_azure_openai(self, system_prompt, user_prompt, temperature=0.7, max_tokens=4000, top_p=0.9):
        try:
            response = self.client.chat.completions.create(
                model=self.azure_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )

            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error calling Azure OpenAI: {e}")
            return ""

    def call_azure_openai_finetuned(self, system_prompt, user_prompt, temperature=0.7, max_tokens=4000, top_p=0.9):
        try:
            response = self.finetuned_client.chat.completions.create(
                model=self.finetuned_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )

            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error calling Azure OpenAI Finetuned: {e}")
            return ""

    def call_azure_openai_for_qna_schema(self, system_prompt, user_prompt, temperature=0.7, max_tokens=4000, top_p=0.9):
        try:
            response = self.client.chat.completions.create(
                model=self.azure_deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "qa_array",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "qa_pairs": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "question": {"type": "string"},
                                            "answer": {"type": "string"}
                                        },
                                        "required": ["question", "answer"]
                                    }
                                }
                            },
                            "required": ["qa_pairs"]
                        }
                    }
                }
            )
            raw_content = response.choices[0].message.content
            parsed = json.loads(raw_content)
            output = parsed.get("qa_pairs", [])
        except Exception as e:
            print(f"Error calling Azure OpenAI with JSON schema: {e}")
            output = []

        return output

def main():
    # system_prompt = """
    # You are an expert software developer. Answer the questions about DSA.
    # DO NOT Give explanations, only code.
    # """

    # user_prompt = "question-1: Give code for quick sort in python. question-2: give code for binary search in python"

    # system_prompt = """
    # You are an expert software developer. Answer the questions about DSA.
    # DO NOT Give explanations, only code.
    # """

    # user_prompt = "question-1: Give code for quick sort in python. question-2: give code for binary search in python"

    # azure_handler = AzureLLMHandler()
    # response = azure_handler.call_azure_openai_finetuned(system_prompt, user_prompt)
    # print(response)

    endpoint = "https://aipkgmgmnt-resource.cognitiveservices.azure.com/"
    model_name = "gpt-4o"
    deployment = "gpt-4o-2024-08-06-commit-history-libsoup-1"

    load_dotenv()
    subscription_key = os.getenv("AZURE_OPENAI_API_KEY")
    api_version = "2024-12-01-preview"

    client = AzureOpenAI(
        api_version=api_version,
        azure_endpoint=endpoint,
        api_key=subscription_key,
    )

    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant, with understanding of libsoup commit history. Based on commit history, find the likely location of backporting",
            },
            {
                "role": "user",
                "content": """
                In Latest Version of Libsoup, the function read_internal is defined in the file 'soup-message-io-data.c'.
                Was this function moved? if yes, from which file to which file? 
"""
#                 "content": """I have a patch on the LATEST liboup repo that contains changes to 
#                 --- a/libsoup/http-1/sb-output-stream.c
# +++ b/libsoup/http-1/sb-output-stream.c
# @@ -349,7 +349,11 @@ soup_body_output_stream_create_source (GPollableOutputStream *stream,
 

# Based on your knowledge of git commit history, & how filenames, function names & contents have changed with commits,
# what is the likely location (filename, functionname) of the backporting commit in the OLD libsoup git repository?
#                 """,
            }
        ],
        max_tokens=4096,
        temperature=0.5,
        top_p=1.0,
        model=deployment
    )

    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()