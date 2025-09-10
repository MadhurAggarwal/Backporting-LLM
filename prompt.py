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

    checkForLineNumberMismatch = """
        You are a patch checker. You need to check if the line numbers in the given patch match the line numbers in the given file codes.

        <example_patch>
        @@ -100,3 +100,3 @@ RandomFunction (int a, int b)
            print("Hello World")
        -   x = 23 + y
        +   x = 23 * y
            print("Goodbye World")
        <end>
        
        <example_file>
        103: print("Hello World")
        104: x = 23 + y
        105: print("Goodbye World")
        <end>

        <Read_Hunk>
        In the Patch hunk,
        Lines in Original File (-) are:
        print("Hello World")
        x = 23 + y
        print("Goodbye World")

        Lines in New File (+) are:
        print("Hello World")
        x = 23 * y
        print("Goodbye World")

        Now, for the original File, hunk is @@ -100,3
        Starting Line = 100, Total Lines = 3
        So, the lines in the hunk are:
        100: print("Hello World")
        101: x = 23 + y
        102: print("Goodbye World")
        <end>

        <Read_File_Codes>
        In the File Codes, the lines are:
        103: print("Hello World")
        104: x = 23 + y
        105: print("Goodbye World")
        <end>

        <example_thought_process>
        The line numbers in the patch hunk do NOT match the line numbers in the file codes.
        First Line of Patch = print("Hello World") 
        Line Number in Patch = 100
        Hunk = @@ -100,3 +100,3 @@

        First Line of File Codes = print("Hello World")
        Line Number in File Codes = 103
        Updated Hunk = @@ -103,3 +103,3 @@
        <end>

        <example_output>
        @@ -103,3 +103,3 @@ RandomFunction (int a, int b)
            print("Hello World")
        -   print("Hello Universe")
        +   print("Hello Galaxy")
            print("Goodbye World")
        <end>

        Now, perform the above task on the below patch and file code:
        <input_patch>
        {PATCH}
        <end>

        <input_file>
        {FILE_CODES}
        <end>

        Do NOT add <input> <end> <output> or ``` or any other token.
        Read Hunk, Read File Codes, complete thought process.
        Then give the updated patch in STANDARD GIT diff format:
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

    def getCheckLineNumberPrompt(self, patch, files):
        return self.checkForLineNumberMismatch.format(
            PATCH=patch,
            FILE_CODES=files
        )