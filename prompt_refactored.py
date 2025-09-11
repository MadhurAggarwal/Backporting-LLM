from constants import PACKAGE_NAME

class Prompts:
    ############################################ BASE PROMPTS ############################################
    BASE_SYSTEM_PROMPT = """
    You are a Git Diff Patch Generator.
    You will be given a patch for a file.
    That file is now slightly modified and patch does not apply cleanly.
    Update the patch so that it applies cleanly to the modified file.
    """

    BASE_USER_PROMPT = """
    The upstream patch in Standard Git Diff format is:
    <Patch>
{UPSTREAM_PATCH}
    <end>

    This Patch was meant to fix the following issue in the {PACKAGE_NAME} package:
    <CVE>
{CVE_DESCRIPTION}
    <end>

    The downstream file code has diverged from upstream.
    Downstream file code in format <line_number>: <line_content> is given below:
    <Downstream_Code>
{FILE_CODES}
    <end>

    TASK:
    Update the patch so that it cleanly applies to the downstream file code.
        1. Find the hunk content from the patch in the downstream file code.
        2. Adjust the line numbers in the patch hunk headers to match the downstream file code
        3. Adjust whitespace, '\t' in the patch hunk content to match the downstream file code.
        4. Ensure that the patch logic is NOT changed.
        5. Do NOT give any extra tokens like diff ``` or <patch>. Only give final patch that applies cleanly to downstream file code.
    Only output the final patch in STANDARD GIT diff format.
    """

    ############################################ CHECK FOR EXTRA TOKENS ############################################

    ############################################ CHECK PATCH LOGIC ############################################

    ############################################ CHECK MISSING / EXTRA LINES ############################################

    ############################################ LINE NUMBER FIX PROMPTS ############################################
    FIRST_LINE_CONTENT_ANALYZER_SYSTEM_PROMPT = """
    You are a Patch Analyzer.
    Given a patch in the Standard Git Diff format, analyze the patch for the given task.
    """

    FIRST_LINE_CONTENT_ANALYZER_USER_PROMPT = """
    The Patch in standard Git Format is:
    <patch>
{PATCH}
    <end>

    TASK:
    Hunk Content in the patch contain some unchanged lines mentioned at start of hunk content. It is followed by changed lines which start with '+' or '-'.
    Find out the content of First Mentioned Unchanged Line in the Patch.
    Then Find the content First Changed Line in the Patch (First Removed (-) Line / Newly Added (+) Line)
    Only output the following:
    Output:
    First Mentioned Unchanged Line: <line content>
    First Changed Line: <line content>
    """

    FIRST_LINE_NUMBER_SYSTEM_PROMPT = """
    You are a software developer, you need to find line number of a line given line content and complete file code.
    The line could be present multiple times in the file code, return the line number of the occurance that corresponds to the context of a given patch.
    """

    FIRST_LINE_NUMBER_USER_PROMPT = """
    The Patch in standard Git Format is:
    <patch>
{PATCH}
    <end>

    As per this patch:
{FIRST_LINE_CONTENT}

    Now, from the following file code, find the line number of the above lines.
    In case the line is present multiple times in the file code, use the patch as ONLY REFERENCE to find the correct occurance.
    <file_code>
{FILE_CODE}
    <end>

    Find line numbers of the First Mentioned Unchanged Line and the First Changed Line in this code file.
    DO NOT output any extra tokens, only the line numbers in the following format:
    Output:
    First Mentioned Unchanged Line Number: <line number>: <line content>
    First Changed Line Number: <line number>: <line content>
    """

    LINE_NUMBER_FIX_SYSTEM_PROMPT = """
    You are a Git Diff Patch Generator.
    Given a patch in the Standard Git Diff format, update the patch as per the given task.
    ONLY output the final updated patch in STANDARD GIT diff format.
    """

    LINE_NUMBER_FIX_USER_PROMPT = """
    The Patch in standard Git Format is:
    <patch>
{PATCH}
    <end>

    The First Mentioned Unchanged Line and First Changed Line in the patch are:
{FIRST_LINE_CONTENT}

    Their line numbers in the downstream file are now:
{LINE_NUMBERS}

    Update the line numbers in the hunk header of patch to match the FIRST MENTIONED UNCHANGED LINE number.
    Do NOT change the patch logic.
    Only output the final updated patch in STANDARD GIT diff format with NO any extra tokens like ```diff or <patch>.
    """

    ############################################ WHITESPACE, TABS FIX PROMPTS ############################################

    ############################################ HANDLER ############################################

    def format_file_codes(self, file_codes):
        prompt = ""
        for key, value in file_codes.items():
            prompt += f"File: {key}\n"
            for line in value:
                prompt += f"{line}"
                if not line.endswith("\n"):
                    prompt += "\n"
            prompt += "\n"
        return prompt

    def getPrompts(
        self,
        prompt_type,
        cve_number=None,
        cve_description=None,
        upstream_patch=None,
        file_code=None,
        first_line_content=None,
        first_line_numbers=None,
    ):
        def base_prompts():
            return (
                self.BASE_SYSTEM_PROMPT,
                self.BASE_USER_PROMPT.format(
                    PACKAGE_NAME=PACKAGE_NAME,
                    CVE_DESCRIPTION=cve_description,
                    UPSTREAM_PATCH=upstream_patch,
                    FILE_CODES=self.format_file_codes(file_code),
                ),
            )

        def first_line_content_prompts():
            return (
                self.FIRST_LINE_CONTENT_ANALYZER_SYSTEM_PROMPT,
                self.FIRST_LINE_CONTENT_ANALYZER_USER_PROMPT.format(
                    PATCH=upstream_patch,
                ),
            )

        def first_line_number_prompts():
            return (
                self.FIRST_LINE_NUMBER_SYSTEM_PROMPT,
                self.FIRST_LINE_NUMBER_USER_PROMPT.format(
                    PATCH=upstream_patch,
                    FIRST_LINE_CONTENT=first_line_content,
                    FILE_CODE=self.format_file_codes(file_code),
                ),
            )

        def line_number_fix_prompts():
            return (
                self.LINE_NUMBER_FIX_SYSTEM_PROMPT,
                self.LINE_NUMBER_FIX_USER_PROMPT.format(
                    PATCH=upstream_patch,
                    FIRST_LINE_CONTENT=first_line_content,
                    LINE_NUMBERS=first_line_numbers,
                ),
            )

        prompt_map = {
            "BASE"               : base_prompts,
            "FIRST_LINE_CONTENT" : first_line_content_prompts,
            "FIRST_LINE_NUMBER"  : first_line_number_prompts,
            "LINE_NUMBER_FIX"    : line_number_fix_prompts,
        }

        try:
            return prompt_map[prompt_type]()
        except KeyError:
            raise ValueError(f"Unknown prompt type: {prompt_type}")


    def getExpectedOutput(self, prompt_type, azurelinux_patch):
        if prompt_type == 'BASE':
            return azurelinux_patch
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")