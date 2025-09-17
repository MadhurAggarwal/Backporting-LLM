from constants import PACKAGE_NAME
from string import Template

############################################ CODEBASE UNDERSTANDING PROMPTS ############################################

############################################ COMMIT DETAILS PROMPTS ############################################
COMMIT_DETAILS_SYSTEM_PROMPT = """
    You are an expert software developer. Generate a high-quality training data for finetuning an assistant with good knowledge of commit history of a codebase.
    ONLY OUTPUT VALID JSON ARRAY.
"""

COMMIT_DETAILS_USER_PROMPT = """
    Commit Details for the {PACKAGE_NAME} Package are:
    <commit_start>
{COMMIT_DATA}
    <end>

    Generate an Array of JSONs with Question-Answer Pairs, that ask about changes made across commits in the codebase.
    This commit history training data will be used to finetune an assistant, to enable it to backport changes from new versions to old versions of the codebase.
    So, focus on changes that help the model map the new positions of code lines to the old positions.
    
    Focus on:
        1. Changes to File Name or File Paths.
        2. Changes to function signature or function name.
        3. Changes to function structure - if 2 functions are merged into one, or one function is split into two or more.
        4. Changes to variable names or variable datatypes.
        5. Addition or removal of lines of codes.
        6. Major Changes to logic or algorithms.
        7. Changes to comments or formatting that affect line numbers significantly.
        8. Changes to dependencies or imports.

    ONLY put a question in the dataset if the commit changes the answer to that question.
    If the answer to a question is NO_CHANGE, do NOT include that question in the dataset.

    Return the response as a JSON array of objects, where each object has:
        - "question": A specific question about changes to the codebase in the commit
        - "answer": A brief, focused answer containing only the change.

    The answers should be very brief and to the point with no grammar.
    The questions should be VERY SPECIFIC.

    Example format:
        [
        {{
            "question": "The variable 'x' of datatype 'long' is declared as 'long x = 23l' in function 'y' of file 'a/b/c.py'. What was this variable in the old version?",
            "answer": "Datatype: int,
                       Declaration: int x = 23;
                       Function_name: y()
                       Filename: a/b/c.py"
        }},
        {{
            "question": "Has the path of file c.py changed? What was the old path of the file 'a/b/c.py'?",
            "answer": "Yes, path of file was changed.
                       Old Path: a/b_old/c.py"
        }},
        {{  "question": "The linenumber 125 is 'foo = bar()' in function 'baz()' of the file 'a/b/c.py'.
                         What was the previous function name to which this line belonged before refactoring?",
            "answer": "The Line 'foo = bar()' was at linenumber 120, in Function qux of Signature qux(), in the file a/b/c.py"
        }},
        ...
        ]
    
    Note that All questions asked are specific - they contain proper information about the variable / function / file etc.
    Answers are brief and to the point, containing only the change, but they contain Proper Information about the change.
    The question-answer pair will be used to train an LLM model, so make sure they contain full context about the change. 
    Vague questions / answers are NOT allowed.

    Do NOT generate generic questions that do not depend on the commit details or questions that have NO_CHANGE or SAME_AS_BEFORE as answer.
    In case of no significant changes in the commit, return an empty array [].
    Generate atmost 30 question-answer pairs.

    ONLY OUTPUT valid JSON.
    DO NOT include any formatting tokens like ```json ... ```.

    OUTPUT:
    <valid JSON array of objects with "question" and "answer" keys only.>
"""

############################################ HUNK CHANGES PROMPTS ############################################

COMMIT_TO_HUNK_CHANGES_SYSTEM_PROMPT = """
    You are an expert software developer, your task is to generate a high quality dataset of question-answer pairs as an array of JSON objects.
    Given a Patch and the commit, generate question-answer pairs about how the commit affected the patch, and what patch would look like before the commit was made.
    ONLY OUTPUT VALID JSON ARRAY.
"""

COMMIT_TO_HUNK_CHANGES_USER_PROMPT = """
    Look at this hunk from a Patch for {PACKAGE_NAME} package:
    <patch_start>
{PATCH_HUNK}
    <end>

    For the following git commit, check if the commit affected same file of this patch hunk.
    <commit_start>
{COMMIT_DATA}
    <end>

    Does the commit affect the same file as the patch hunk?
    if YES, generate an Array of JSONs with Question-Answer Pairs, that ask about changes made in the commit that affect the patch hunk.
    The Patch Hunk is for the latest version, which includes the changes due to the given commit. You need to generate questions that help map the latest version of the hunk to the older version before the commit was made.

    Focus on:
        1. Changes to File Name or File Paths in the commit that affect the patch hunk.
        2. Changes to Function Signature or Function Name that affect the hunk header or hunk content.
        3. Addition or removal of lines of codes in the hunk content, and what lines of codes should be in the hunk for the older version?
        4. Changes to variable names or variable datatypes in commit that affect lines in patch hunk.

    Example format:
    [
    {{ "question": "The hunk header in Patch is @@ -10,7 +10,8 @@ soup_select(self, selector, dict) for the latest version, with filename = 'a/b.c'. Was the function signature changed? if yes, give the old function signature and the old hunk header.",
        "answer": " Yes, function name was changed:
                    New Function Name: 'soup_select(self, selector, dict)'
                    Old Function Name: 'soup_old_select(selector, old_dict)'
                    Old Hunk Header: @@ -10,7 +10,8 @@ soup_old_select(selector, old_dict)
                    The filename and path is same as in the patch: 'a/b.c'"
    }},
    {{"question": "The hunk content 
                    for function fetch_data(url) in file utils/network.py from the latest patch is:
                        int x = get_value();
                        x += foo();
                        x -= bar();
                    +   if (x > 0) {
                    +       return x;
                    +   }

                        return x+1
                    
                    Were some lines added in this hunk content by any commit?
                    What was the previous version of the hunk content?",
        "answer": " Yes,
                    2 Extra Lines: 
                        x += foo(); 
                        x -= bar(); 
                    were added in the function fetch_data(url) in file utils/network.py.
                    So, in the older version the hunk content should be:

                        int x = get_value();
                    +   if (x > 0) {
                    +       return x;
                    +   }

                        return x+1"
    }},
    {{"question": "The hunk for function fetch_data(url) in file utils/network.py from the latest patch is:
                    @@ -257,5 +257,5 @@ def fetch_data(url): 
                        long_response = requests.get(url, timeout=10)
                        return long_response.json()

                    indicates that line number for 'long_response = requests.get(url, timeout=10)' is 257. 
                    How many lines were added or removed above this line in the commit, and what should be the line number for this line in the patch for older version?",
        "answer": "3 Lines:
                    +    foo = bar()
                    +    if foo:
                    +        return None
                    were added above line 257 in the file utils/network.py. 
                So line number for 'long_response = requests.get(url, timeout=10)' should be 254 in the patch for older version."
    }}
    ...
    ]

    Generate only high quality training-dataset that are very specific to the commit details provided.
    You are allowed to generate multiple questions about the same change, but the questions must be VERY SPECIFIC and DIFFERENT.

    Ensure that the questions are VERY SPECIFIC - they contain proper information about the linenumber and content / variable / function / filename or path etc.
    The answers will be used to train a LLM model, so make sure they contain full context about the change. 
    Vague questions / answers are NOT allowed.

    Generate atmost 30 question-answer pairs.
    If the Commit did NOT affect the same file / lines of codes as the Patch Hunk,
    Return ONLY an empty array [].

    ONLY OUTPUT valid JSON.
    DO NOT include any formatting tokens like ```json ... ```.

    OUTPUT:
    <valid JSON array of objects with "question" and "answer" keys only.>
"""

############################################ HUNK EXTRACT PROMPTS ############################################


############################################ PATCH UPDATE PROMPTS ############################################

PATCH_BACKPORT_SYSTEM_PROMPT = """
    You are an expert software developer.
    Given a Patch, your task is to Analyze each hunk in the patch and obtain the desired ORIGINAL_HUNK_DATA information.
    Then, look at a commit that was made before the patch was created.
    You need to find out how the patch would look like for the older version of the codebase, before the commit was made.
    Generate the output as a pair of question-answer JSON objects for each hunk in the patch.
    ONLY OUTPUT VALID JSON ARRAY.
"""

PATCH_BACKPORT_USER_PROMPT = """
    Look at this Patch for {PACKAGE_NAME} package:
    <patch_start>
{PATCH_HUNK}
    <end>

    This Patch is for the latest version of the package.
    First, find out every hunk in the patch.
    A hunk starts with @@ +a,b -c,d @@ where a,b,c,d are line numbers, and is followed by lines starting with +, - or space.
    The hunk ends when the next hunk starts or the patch ends.

    For each hunk in the given patch, You need to create a dataset containing the following information:
    ORIGINAL_HUNK_DATA:
        File_PATH: <path of file which the hunk modifies, as per the patch>
        HUNK_START_LINE_NUMBER: <line number as per the hunk header of the patch (the 'a' in @@ +a,b -c,d @@)>
        FUNCTION_SIGNATURE: <function signature as per the hunk header of the patch>
        HUNK_START_LINE_CONTENT: <the first mentioned unchanged line, which follows the hunk header & the function signature in the patch>
        FIRST_CHANGED_LINE_NUMBER: <line number of the first added / removed (+/-) line in the hunk content. Calculate using the number of lines between this line and the hunk start line number>
        FIRST_CHANGED_LINE_CONTENT: <the content of the first added / removed (+/-) line in the hunk content>
        HUNK_LINES: <all the lines in the hunk content of the patch, from the first unchanged line after the function signature to the end of the hunk. keep original formatting.>

    Now, look at this commit:
    <commit_start>
{COMMIT_DATA}
    <end>

    This commit was made, and AFTER the commit the above patch was created. You need to backport the given Patch for the old version of the codebase, BEFORE this commit was made.
    So, based on the commit data, check what the hunk data would be for the older version.
    Result:

    BACKPORTED_HUNK_DATA:
        FILE_PATH: If the commit changed the file name or path, give the file name / path before the commit
                    else filepath same as in the original patch.
        HUNK_START_LINE_NUMBER: If the commit added or removed lines above the first linenumber of the hunk, adjust the line number accordingly.
                    For example if 2 lines were added above the hunk start line in the commit, increase the hunk start line number by 2.
        FUNCTION_SIGNATURE: If the commit changed the function signature or function name, give the old function signature before the commit.
                    else give the same as in the original patch.
        HUNK_START_LINE_CONTENT: If the commit changed the lines in the hunk, give the first unchanged line after the function signature as per the older version.
                    for example, if a line (int x=20) was made (long x=20l) in the commit, give the old line (int x=20) as the hunk start line content.
        FIRST_CHANGED_LINE_NUMBER: If the commit added or removed lines above the first changed line (with a + or -) in the hunk, adjust the line number accordingly.
                    This is line number of the first line with (+ or -) in the HUNK content, adjusted based on the patch.
        FIRST_CHANGED_LINE_CONTENT: If the commit changed the first changed line (with a + or -) in the hunk, give the content of that line as per the older version.
                    for example, if a line (+   x += foo();) was made (+   x += bar();) in the commit, give the old line (+   x += foo();) as the first changed line content.
        HUNK_LINES: Look at the lines of the patch hunk that were modified by the commit. Give the hunk lines for the older version, before the commit was made.
                    If some lines, in the hunk content were added / removed, give old lines as per the older version before the commit.

    If any of the above keys was NOT affected by the commit, its value is same as in ORIGINAL_HUNK_DATA.

    Give the data as Json List Object containing "question" and "answer" keys FOR EACH HUNK, where:
        - "question": A string containing the ORIGINAL_HUNK_DATA 
        - "answer": A string containing the BACKPORTED_HUNK_DATA, which is the patch for the version before the commit was made.
    
    Example format:
    [
    {{ "question": "
            ORIGINAL_HUNK_DATA:
                FILE_PATH: src/module/a/b/c.py
                HUNK_START_LINE_NUMBER: 120
                FUNCTION_SIGNATURE: def function_name(param1, param2):
                HUNK_START_LINE_CONTENT:     int x = 200;
                FIRST_CHANGED_LINE_NUMBER: 124
                FIRST_CHANGED_LINE_CONTENT:     x *= baz();
                HUNK_LINES:
                    int x = 200;
                    x -= foo();             // [for reference] - this was the line added in commit. Hence, old version hunk will not have this.
                    if (x > 100) {
                        x += bar();
                +       x *= baz();
                    }
                    return x;",
        "answer": "
            BACKPORTED_HUNK_DATA:
                FILE_PATH: src/module/a/b_old/c.py
                HUNK_START_LINE_NUMBER: 118
                FUNCTION_SIGNATURE: def old_function_name(old_param1, old_param2):
                HUNK_START_LINE_CONTENT:     int x = 200;
                FIRST_CHANGED_LINE_NUMBER: 121
                FIRST_CHANGED_LINE_CONTENT:     x *= baz();
                HUNK_LINES:
                    int x = 200;
                    if (x > 100) {
                        x += bar();
                +       x *= baz();
                    }
                    return x;",
    }},
    {{  "question": "..."
        "answer": "..."
    }},
    ]
    
    Ensure that hunk lines do not change the logic of the patch hunk. Only change the lines that were modified by the commit.
    The question-answer pairs should be very specific, they will be used to train a LLM model, so make sure they contain full context about the change as asked.
    Vague questions / answers are NOT allowed.
    
    If the commit did NOT affect the same file / lines of codes as the Patch Hunk, return ONLY an empty array [].

    ONLY OUTPUT valid JSON.
    DO NOT include any formatting tokens like ```json ... ```.

    Output
    <valid JSON array of objects with "question" and "answer" keys only, for EACH hunk in the Patch.>
"""

############################################ JSON ERROR PROMPT ############################################

json_error_prompt = """

    The previous output was not a valid JSON.
    Previous Error = {error}
    Do NOT include any formatting tokens like ```json ... ```. 
    If the output contains Quotes, Curly Braces etc, ensure they are escaped, to NOT interfere with JSON output.
    Please correct the mistakes and output a valid JSON array of objects with "question" and "answer" keys only.

"""

############################################ UTILITY CLASS ############################################
class FinetuningPrompts:
    def getPrompts(
            self,
            prompt_type,
            package_name=PACKAGE_NAME,
            commit_data=None,
            patch_hunk=None
        ):

            def get_commit_details_prompts():
                tpl = Template(COMMIT_DETAILS_USER_PROMPT.replace("{PACKAGE_NAME}", "$PACKAGE_NAME")
                                                        .replace("{COMMIT_DATA}", "$COMMIT_DATA")
                        )
                return (
                    COMMIT_DETAILS_SYSTEM_PROMPT,
                    tpl.substitute(
                        PACKAGE_NAME=package_name,
                        COMMIT_DATA=commit_data
                    ),
                )

            def get_commit_to_hunk_changes_prompts():
                tpl = Template(COMMIT_TO_HUNK_CHANGES_USER_PROMPT.replace("{PACKAGE_NAME}", "$PACKAGE_NAME")
                                                                .replace("{PATCH_HUNK}", "$PATCH_HUNK")
                                                                .replace("{COMMIT_DATA}", "$COMMIT_DATA")
                )
                return (
                    COMMIT_TO_HUNK_CHANGES_SYSTEM_PROMPT,
                    tpl.substitute (
                        PACKAGE_NAME=package_name,
                        PATCH_HUNK=patch_hunk,
                        COMMIT_DATA=commit_data
                    )
                )

            def get_patch_backport_prompts():
                tpl = Template(PATCH_BACKPORT_USER_PROMPT.replace("{PACKAGE_NAME}", "$PACKAGE_NAME")
                                                         .replace("{PATCH_HUNK}", "$PATCH_HUNK")
                                                         .replace("{COMMIT_DATA}", "$COMMIT_DATA")
                        )
                return (
                    PATCH_BACKPORT_SYSTEM_PROMPT,
                    tpl.substitute(
                        PACKAGE_NAME=package_name,
                        PATCH_HUNK=patch_hunk,
                        COMMIT_DATA=commit_data
                    ),
                )
            
            def get_json_error_prompt(error):
                tpl = Template(json_error_prompt.replace("{error}", "$error"))
                return (
                    tpl.substitute(error=error)
                )

            prompt_map = {
                "COMMIT_DETAILS"        : get_commit_details_prompts,
                "COMMIT_TO_HUNK_CHANGES": get_commit_to_hunk_changes_prompts,
                "PATCH_BACKPORT"        : get_patch_backport_prompts,
                "JSON_ERROR"            : get_json_error_prompt,
            }

            try:
                return prompt_map[prompt_type]()
            except KeyError:
                raise ValueError(f"Invalid Finetune prompt_type: {prompt_type}")
