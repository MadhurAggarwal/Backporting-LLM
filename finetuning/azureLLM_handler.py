import os
from openai import OpenAI
from dotenv import load_dotenv

class AzureLLMHandler:
    def __init__(self):
        load_dotenv()

        self.api_key          = os.getenv("AZURE_OPENAI_API_KEY")
        self.api_endpoint     = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")

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
            return None

def main():
    system_prompt = """
    You are an expert software developer. Answer the questions about DSA.
    """

    user_prompt = "Give code for quick sort in python."

    azure_handler = AzureLLMHandler()
    response = azure_handler.call_azure_openai(system_prompt, user_prompt)
    print(response)

if __name__ == "__main__":
    main()