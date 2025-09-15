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
#     HUNK_EXTRACT_SYSTEM_PROMPT = """
#     You are a Patch Analyzer.
#     You are given a Standard Git Diff format Patch.
#     Extract the file lines EXACTLY as they appear in the patch, including whitespace, newline and tabs, exactly as the patch.
#     """

#     HUNK_EXTRACT_USER_PROMPT = """
#     The Patch in standard Git Format is:
#     <patch>
# {PATCH}
#     <end>

#     TASK:
#     1. Find each hunk in the patch.
#     2. For each hunk, there is a hunk header and a hunk content which contains file lines.
#     3. From the hunk content, extract file lines. File Lines should be exactly as they appear in the patch, including whitespace, newline and tabs, exactly as the patch.
#        DO NOT miss any tab/whitespace/newline or anything else.
#     4. Only output the extracted lines, do NOT output any extra tokens like ```diff or <patch>.

#     Output:
#     <hunk1>
#     <extracted lines>

#     <hunk2>
#     <extracted lines>
#     """

    HUNK_FILE_CONTENT_EXTRACT_SYSTEM_PROMPT = """
    You are a software developer. 
    You are given a patch, and extracted lines from the patch, with proper formatting (whitespace, tabs, newlines etc.)
    You are also given a code file. 
    Return corresponding lines in the code file that match the extracted lines from the patch.
    """

    HUNK_FILE_CONTENT_EXTRACT_USER_PROMPT = """
    The Patch in standard Git Format is:
    <patch>
{PATCH}
    <end>

    The downstream codefile has diverged a bit from the upstream file for which this patch was created.
    The downstream code file in format <line_number>: <line_content> is:
    <code_file>
{FILE_CODE}
    <end>

    TASK:
    1. Find the corresponding Hunk Content from the patch in the file code.
        The Corresponding hunk in the file code could have some extra / missing lines.
        There could also be some whitespace / tab differences or newline differences.
    2. Give me ONLY the corresponding lines from the patch in the file code.
       Ensure that format (whitespace, tabs, newlines etc.) of the lines is exactly as in the file code.
       If there are some extra / missing lines in the corresponding hunk in the file code, INCLUDE them as well.
    3. Ensure that lines extracted are as close to the patch hunk as possible.
       
    I want to know what the corresponding hunk in the downstream file code looks like.
    Do not give any lines outside the corresponding hunk or any extra formatting tokens like ``` or <>
    Output:
    <corresponding_hunk_in_file_code>
    """

    HUNK_CONTENT_FIX_SYSTEM_PROMPT = """
    You are Git Diff Patch Fixer.
    Given a patch in the Standard Git Diff format, update the patch as per the given task.
    ONLY output the final updated patch in STANDARD GIT diff format.
    """

    HUNK_CONTENT_FIX_USER_PROMPT = """
    The upstream patch in Standard Git Diff format is:
    <Patch>
{UPSTREAM_PATCH}
    <end>

    The downstream file code has diverged from upstream.
    Here, the line content in the diverged file is:
{LINE_CONTENT}

    TASK:
    The upstream patch uses different whitespace, tabs etc. than the downstream code
    Also some lines could be missing / extra in the new file code, from when the patch was created.
    So, update the patch to the new line content.

    Ensure that the patch logic is NOT changed.
    Ensure that line content like newlines, tabs, whitespace etc matches the downstream file code.

    Do NOT give any extra tokens like diff ``` or <patch>.
    Only output the final patch in STANDARD GIT diff format.
"""

    ############################################ CHANGED FILE EXTRACT ############################################

    CHANGED_CODE_EXTRACT_SYSTEM_PROMPT = """
    You are a software developer.
    Given a patch in the Standard Git Diff format, and complete file code
    The patch does not cleanly apply to the file code due to some extra / missing lines in the file code.
    Apply the patch to the file code, and return the changed code from the file code after
    """

    CHANGED_CODE_EXTRACT_USER_PROMPT = """
    The Patch in standard Git Format is:
    <patch>
{PATCH}
    <end>

    Downstream file code in format <line_number>: <line_content> is given below:
    <Downstream_Code>
{FILE_CODES}
    <end>

    The First Mentioned Unchanged Line and First Changed Line in the patch are:
{FIRST_LINE_NUMBERS}

    TASK:
    1. The Patch and file code have diverged, with some extra / missing lines in the file code.
    2. Identify the line changed in the patch, find the line in file code, and apply the patch.
    3. Only Return the changed code from CODE FILE, (Not The Patch, the Code File), after applying the patch on it.
    4. Ensure that missing / extra lines from the code file Are PRESERVED. The output should be exactly as per the code file, with only changes from the patch applied.
        Do not give any other tokens.
    Output:
    <changed_code>
    """

    CHANGED_CODE_FIX_SYSTEM_PROMPT = """
    You are a patch generator.
    You are given an upstream Patch in Standard Git Diff Format.
    Also, you are given a diverged downstream code, and code after applying the patch.
    Fix the patch so that it cleanly applies to the diverged downstream code.
    ONLY output the final updated patch in STANDARD GIT diff format.
    """

    CHANGED_CODE_EXTRACT_USER_PROMPT = """
    The upstream patch in Standard Git Diff format is:
    <Patch>
{UPSTREAM_PATCH}
    <end>

    The ORIGINAL downstream file code has diverged from upstream.
    Here, the file code before applying the patch is:
{FILE_CODE}
    <end>

    The file code after applying the patch is:
{CHANGED_FILE_CODE}

    Update the Patch so that it cleanly applies to the ORIGINAL downstream file code.
    Ensure that the patch logic is NOT changed.
    Ensure that line content like newlines, tabs, whitespace etc matches the downstream file code.
    Do NOT give any extra tokens like diff ``` or <patch>.

    Only output the final patch in STANDARD GIT diff format.
    """

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
        hunk_file_content=None,
        changed_file_code=None,
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
        
        def extract_hunk_content_from_file_prompts():
            return (
                self.HUNK_FILE_CONTENT_EXTRACT_SYSTEM_PROMPT,
                self.HUNK_FILE_CONTENT_EXTRACT_USER_PROMPT.format(
                    PATCH=upstream_patch,
                    FILE_CODE=self.format_file_codes(file_code),
                ),
            )

        def fix_hunk_content_prompts():
            return (
                self.HUNK_CONTENT_FIX_SYSTEM_PROMPT,
                self.HUNK_CONTENT_FIX_USER_PROMPT.format(
                    UPSTREAM_PATCH=upstream_patch,
                    LINE_CONTENT=hunk_file_content,
                ),
            )
        
        def extract_changed_code():
            return (
                self.CHANGED_CODE_EXTRACT_SYSTEM_PROMPT,
                self.CHANGED_CODE_EXTRACT_USER_PROMPT.format(
                    PATCH=upstream_patch,
                    FILE_CODES=self.format_file_codes(file_code),
                    FIRST_LINE_NUMBERS=first_line_numbers,
                ),
            )
        
        def fix_changed_code():
            return (
                self.CHANGED_CODE_FIX_SYSTEM_PROMPT,
                self.CHANGED_CODE_EXTRACT_USER_PROMPT.format(
                    UPSTREAM_PATCH=upstream_patch,
                    FILE_CODE=self.format_file_codes(file_code),
                    CHANGED_FILE_CODE=changed_file_code,
                ),
            )

        prompt_map = {
            "BASE"                      : base_prompts,
            "FIRST_LINE_CONTENT"        : first_line_content_prompts,
            "FIRST_LINE_NUMBER"         : first_line_number_prompts,
            "LINE_NUMBER_FIX"           : line_number_fix_prompts,
            "HUNK_FILE_CONTENT_EXTRACT" : extract_hunk_content_from_file_prompts,
            "HUNK_CONTENT_FIX"          : fix_hunk_content_prompts,
            "CHANGED_CODE_EXTRACT"      : extract_changed_code,
            "CHANGED_CODE_FIX"          : fix_changed_code,
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