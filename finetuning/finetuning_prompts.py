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
                       Old Path: a_old/c.py
                       New Path: a/b/c.py"
        }},
        {{  "question": "The linenumber 125 is 'foo = bar()' in function 'baz(str, *sniff)' of the file 'a/b/c.py'.
                         What was the previous function name to which this line belonged before refactoring?",
            "answer": "5 Lines were added above foo = bar() of function 'baz(str, *sniff)' in the file a/b/c.py.
                        The lines added (in the commit), above line 125 were:
                            x += 10
                            if foo:
                                foo += 1
                            else:
                                foo = 0
                        Before the commit, The Line 'foo = bar()' was at linenumber 120, in Function baz of Signature baz(str, *sniff). in the file a/b/c.py"
        }},
        ...
        ]
    
    Keep Answers to the point.
    MAKE SURE:
    Generate ATLEAST 10 question-answer pairs, upto a maximum of 25 pairs.

    The question-answer pair will be used to train an LLM model, so make sure they contain full context about the change.
    The goal of Training is to make sure MODEL CAN MAP THE POSITIONS & CONTENT of code lines from new version to old version. 
    GENERATE DATASET ACCORDINGLY.
    Questions like given new path or location, give the old path or location are very important.
    Make sure questions are given new version -> answer the old version, NOT the other way round.

    Vague questions / answers are NOT allowed.
    do NOT mention commit hash or author name or date in the questions or answers. Give proper description of the change, and its location instead.

    Do NOT generate generic questions that do not depend on the commit details or questions that have NO_CHANGE or SAME_AS_BEFORE as answer.
    In case of no significant changes in the commit, return an empty array [].

    ONLY OUTPUT valid JSON.
    DO NOT include any formatting tokens like ```json ... ```.

    DO NOT ASK questions about plain text, like comments or readme files or Metadata like changelog email-id and changelog timestamps.

    IMPORTANT:
    MAKE SURE that changes to FILE PATHS, FILE NAMES, FUNCTION NAMES, are ALWAYS INCLUDED, since they are important for mapping code lines from new version to old version.
    For the question-answers, focus less on english grammar / sentences, and more on CODE and CODE CONTEXT (location, filename, functionname, line numbers etc). The answers will train a code-search / code-map model from new version to old version.
    
    Focus more on name changes (like file paths, function names etc) and less on simple line number changes.
    IF adding a linenumber change, try to include function-signature, file names to give proper context about the line number change.
    
    Give PROPER CODE-BLOCKS in the answers wherever possible, containing complete line content, and CONTEXT about the location of code block, instead of just plain text.
    For the code-blocks, give both old and new version codeblocks, highlighting the difference.

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

    Make Sure that CHANGES OF COMMIT that affect the Patch are asked about in the questions.
    DO NOT ask about / make chages based on the PATCH.

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
                        x += foo();         // [for reference] - this was the line added in COMMIT. Hence, old version hunk will not have this. Remove effect of commit.
                        x -= bar();         // [for reference] - this was the line added in the COMMIT. Remove effect of commit in the answer.
                    +   if (x > 0) {        // [for reference] - this line was added in the PATCH. Only effect of commit needs to be removed in the answer.
                    +       return x;       // [for reference] - this line was added in the PATCH. do NOT remove this in the answer.
                    +   }                   // [for reference] - this line was added in the PATCH.

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
                    +    foo = bar()            // [For reference] - line added in the COMMIT, not PATCH. Hence, old patch = remove effect of this line.
                    +    if foo:                // [For reference] - line added in the COMMIT, not PATCH.
                    +        return None        // [For reference] - line added in the COMMIT, not PATCH.
                    were added above line 257 in the file utils/network.py. 
                So line number for 'long_response = requests.get(url, timeout=10)' should be 254 in the patch for older version."
    }}
    ...
    ]

    The [for reference] comments in the questions are just for your understanding, do NOT include them in the output.

    Generate only high quality training-dataset that are very specific to the commit details provided.
    You are allowed to generate multiple questions about the same change, but the questions must be VERY SPECIFIC and DIFFERENT.

    Ensure that the questions are VERY SPECIFIC - they contain proper information about the linenumber and content / variable / function / filename or path etc.
    The answers will be used to train a LLM model, so make sure they contain full context about the change. 

    The goal of Training is to make sure MODEL CAN MAP THE POSITIONS & CONTENT of code lines from new version to old version. GENERATE DATASET ACCORDINGLY.

    do NOT mention commit hash or author name or date in the questions or answers. Give proper description of the change, and its location instead.
    Vague questions / answers are NOT allowed.

    If the Commit did NOT affect the same file / lines of codes as the Patch Hunk,
    Return ONLY an empty array [].

    ONLY OUTPUT valid JSON.
    Make sure that any {{}} or quotes "" in the output JSON is properly escaped to not interfere with JSON formatting.
    DO NOT include any formatting tokens like ```json ... ```.
    
    MAKE SURE:
    if the commit DOES affect the patch files, hunk and lines, generate ATLEAST 10 question-answer pairs, and maximum 20 pairs.

    IMPORTANT:
    The answers will train a backporting model to port Patch from new version to old version, help the model find out where the code lines are in older version and what content they have.
    For the question-answers, focus less on english grammar / sentences, and more on CODE and CODE CONTEXT (location, filename, functionname etc). 
    Try to give code-blocks in the answers wherever possible, with proper context about the location of code block.
    For the code-blocks, try to give both old and new version codeblocks, highlighting the difference.

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
                    Note that, Lines Added / removed by the PATCH are NOT to be removed / added. The patch content stays as it is, with the effect of the COMMIT removed.

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
                    x -= foo();             // [for reference] - this was the line added in commit. Hence, old version hunk will not have this. Remove effect of commit. 
                    if (x > 100) {
                        x += bar();
                +       x *= baz();         // [for reference] - this line was added in the PATCH. DO NOT remove it. only effect of commit needs to be removed in the answer.
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
    {{  "question": "
                ORIGINAL_HUNK_DATA:
                ..."
        "answer": "
                BACKPORTED_HUNK_DATA:
                ..."
    }},
    ]
    
    Note that for each HUNK, the question-answer pair are separate JSON objects in the array.
    The [for reference] comments in the questions are just for your understanding, do NOT include them in the output.
    Make sure that any {{}} or quotes "" in the output JSON is properly escaped to not interfere with JSON formatting.

    Ensure that hunk lines do not change the logic of the patch hunk. Only change the lines that were modified by the commit.
    The question-answer pairs should be very specific, they will be used to train a LLM model, so make sure they contain full context about the change as asked.

    The goal of Training is to make sure MODEL CAN MAP THE POSITIONS & CONTENT of code lines from new version to old version. GENERATE DATASET ACCORDINGLY.

    Vague questions / answers are NOT allowed. I want the question-answer pairs to give proper context about the change.
    
    If the commit did NOT affect the same file / lines of codes as the Patch Hunk, return ONLY an empty array [].
    DO NOT return anything if the ORIGINAL_HUNK_DATA and the BACKPORTED_HUNK_DATA are EXACTLY same. if there is atleast one difference, only then return the question-answer pair for that hunk.

    ONLY OUTPUT valid JSON.
    DO NOT include any formatting tokens like ```json ... ```.

    Output
    <valid JSON array of objects with "question" and "answer" keys only, for EACH hunk in the Patch with changes between ORIGINAL AND BACKPORTED data.>
"""

############################################ JSON ERROR PROMPT ############################################

JSON_ERROR_SYSTEM_PROMPT = """

    The previous output was not a valid JSON.
    Do NOT include any formatting tokens like ```json ... ```. 
    If the output contains Quotes, Curly Braces etc, ensure they are escaped, to NOT interfere with JSON output.
    Please correct the mistakes and output a valid JSON array of objects with "question" and "answer" keys only.

"""

JSON_ERROR_USER_PROMPT = """

    The output for above prompt was not a valid JSON.
    Previous Output: {output}

    Previous Error = {error}
    Fix the output to not have any JSON errors.
    
"""

############################################ UTILITY CLASS ############################################
class FinetuningPrompts:
    def getPrompts(
            self,
            prompt_type,
            package_name=PACKAGE_NAME,
            commit_data=None,
            patch_hunk=None,
            error=None,
            output=None
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
            
            def get_json_error_prompt():
                tpl = Template(JSON_ERROR_USER_PROMPT.replace("{output}", "$OUTPUT")
                                                     .replace("{error}", "$ERROR")
                    )
                return (
                    JSON_ERROR_SYSTEM_PROMPT,
                    tpl.substitute(
                        OUTPUT=output,
                        ERROR=error
                    ),
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
