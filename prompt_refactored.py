from constants import PACKAGE_NAME

class Prompts:
    ############################################ BASE PROMPTS ############################################
    BASE_SYSTEM_PROMPT = """
    You are a Patch Fixer.
    You will be given an upstream patch and downstream file code.
    Downstream file code has diverged from the upstream.
    Update upstream patch to apply cleanly on downstream file code.

    Only output the final patch in STANDARD GIT diff format.
    """

    BASE_USER_PROMPT = """
    The upstream patch in Standard Git Diff format is:
    <Patch>
        {UPSTREAM_PATCH}
    <end>

    This Patch was meant to fix the following issue in the {PACKAGE_NAME} package:
    <CVE>
        CVE Number: {CVE_NUMBER}
        CVE Description:
        {CVE_DESCRIPTION}
    <end>

    The downstream file code has diverged from upstream.
    The relevant lines of the downstream file code in the format <line_number>: <line_content> is guven below:
    <Downstream_Code>
        {FILE_CODES}
    <end>

    Update the patch so that line number, and the line content, including number and positions of tabs and spaces properly matches the downstream file code.
    Ensure that patch logic remains the same, only change what is necessary to make the patch apply cleanly to the downstream file code.
    Only output the final patch in STANDARD GIT diff format.
    """

    ############################################ CHECK PATCH LOGIC ############################################

    ############################################ LINE NUMBER FIX PROMPTS ############################################

    ############################################ WHITESPACE, TABS FIX PROMPTS ############################################

    ############################################ HANDLER ############################################

    def getPrompts(self, prompt_type, cve_number, cve_description, upstream_patch, file_code):
        if prompt_type == 'BASE':
            system_prompt = self.BASE_SYSTEM_PROMPT
            user_prompt = self.BASE_USER_PROMPT.format(
                PACKAGE_NAME=PACKAGE_NAME,
                CVE_NUMBER=cve_number,
                CVE_DESCRIPTION=cve_description,
                UPSTREAM_PATCH=upstream_patch,
                FILE_CODES=file_code
            )
            return system_prompt, user_prompt
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")

    def getExpectedOutput(self, prompt_type, azurelinux_patch):
        if prompt_type == 'BASE':
            return azurelinux_patch
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")