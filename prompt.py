from constants import PACKAGE_NAME

class PromptHandler:
    backport_input = """
        You are a patch updater. You need to update a given patch for {PACKAGE_NAME} Package as per given file codes.

        <INPUT>
        CVE_DESCRIPTION:
        {CVE_DESCRIPTION}

        UPSTREAM_PATCH
        Format: STANDARD_GIT_DIFF_FORMAT
        {UPSTREAM_PATCH}

        RELEVANT_FILE_CODE_LATEST_VERSION:
        Format: "<LINE_NUMBER>: <LINE_CONTENT>"

        {FILE_CODES}
        </INPUT>

        <TASK>
        Update the upstream patch so it applies cleanly to the latest files.
        - ONLY output the final patch in STANDARD GIT diff format.
        - Adjust line numbers, and patch fixes if required as per CVE description & file code
        - Output patch should be COMPLETE and END properly as per the STANDARD GIT diff format. (-- Gitlab)
        - Do NOT add any extra formatting like ", ` or brackets. 
          The Output should ONLY be the patch in STANDARD GIT diff format.
          DO NOT wrap it in any <Output> token, just give me the directly applicable patch
        </TASK>

        <COMMON_MISTAKES>
        DO NOT make the following mistakes while generating the patch:
        - The whitespace characters in the patch should be exactly as per the FILE_CODE LINES, NOT the Upstream lines. Even a single space or tab difference can cause the patch to fail.
        - In a Hunk, line numbers are that of the first mentioned line in the hunk, not necessarily the first changed line.

        @@ -100,2 +100,2 @@ RandomFunction (int a, int b)
            unchanged_line_1
            unchanged_line_2
        -   changed_line_1
        +   changed_line_2
            unchanged_line_3

            The line number 100 is the line number of unchanged_line_1, not changed_line_1 or changed_line_2.
        - DO NOT remove any spaces in the codelines. For example, if (== ' ') is present, do not convert it to (=='')
        </COMMON_MISTAKES>
    """

    backport_output = """
        {AZURELINUX_PATCH}
        </OUTPUT>
        <<<END>>>
    """
    
    def getBackportingInputPrompt(self, cve_number, cve_description, upstream_patch, file_codes):
        upstream_patch = upstream_patch.encode("utf-8").decode("unicode_escape")
        return self.backport_input.format(
            PACKAGE_NAME=PACKAGE_NAME,
            CVE_DESCRIPTION=cve_description,
            UPSTREAM_PATCH=upstream_patch,
            FILE_CODES=file_codes
        )
    
    def getBackportingOutputPrompt(self, azurelinux_patch):
        return self.backport_output.format(
            AZURELINUX_PATCH=azurelinux_patch
        )
