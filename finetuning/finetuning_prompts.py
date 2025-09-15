############################################ CODEBASE UNDERSTANDING PROMPTS ############################################

############################################ COMMIT DETAILS PROMPTS ############################################
COMMIT_DETAILS_SYSTEM_PROMPT = """
    You are an expert software developer. Generate a high-quality training data for finetuning an assistant with good knowledge of commit history of a codebase.
"""

COMMIT_DETAILS_USER_PROMPT = """
    Commit Details for the {PACKAGE_NAME} Package are:
{COMMIT_DATA}

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

    Example format:
        [
        {{
            "question": "The variable 'x' of type 'long' in function 'y' had what type in the old version?",
            "answer": "int"
        }},
        {{
            "question": "What was the old path of the file 'a/b/c.py'?",
            "answer": "a/b_old/c.py"
        }},
        {{  "question": "The line 'foo = bar()' in function 'baz' belonged to which function in the old version?",
            "answer": "qux"
        }},
        ...
        ]
    
    Generate only high quality training-dataset that are very specific to the commit details provided.

    Do NOT generate generic questions that do not depend on the commit details or questions that have NO_CHANGE or SAME_AS_BEFORE as answer.
    In case of no significant changes in the commit, return an empty array [].
    Generate atmost 30 question-answer pairs.

    OUTPUT:
    <valid JSON array of objects with "question" and "answer" keys only.>
"""

############################################ PATCH HUNKS SEPARATE PROMPTS ############################################

# HUNK_EXTRACT -> Can Make it deterministic (regex on --diff)

############################################ HUNK CHANGES PROMPTS ############################################

COMMIT_TO_HUNK_CHANGES_USER_PROMPT = """
    Look at this hunk from a Patch for {PACKAGE_NAME} package:
{PATCH_HUNK}

    For the following git commit, check if the commit affected same file of this patch hunk.
{COMMIT_DATA}

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
    {{ "question": "The hunk header in Patch is @@ -10,7 +10,8 @@ soup_select(self, selector, dict) for the latest version. What should be the backported hunk header for the older version, before the commit changed the function signature?",
        "answer": " New Function Name: 'soup_select(self, selector, dict)'
                    Old Function Name: 'soup_old_select(selector, old_dict)'
                    Old Hunk Header: @@ -10,7 +10,8 @@ soup_old_select(selector, old_dict)"
    }},
    {{"question": "The hunk content from the latest patch is:
                        int x = get_value();
                        x += foo();
                        x -= bar();
                    +   if (x > 0) {
                    +       return x;
                    +   }

                        return x+1
                    
                    What were the lines in the hunk content for the older version, before the commit added extra lines?",
        "answer": "2 Extra Lines: 'x += foo();' and 'x -= bar();' were added in the commit, 
                    the hunk content for the older version should be:

                        int x = get_value();
                    +   if (x > 0) {
                    +       return x;
                    +   }

                        return x+1"
    }},
    {{"question": "The hunk 
                    @@ -257,5 +257,5 @@ def fetch_data(url): 
                        long_response = requests.get(url, timeout=10)
                        return long_response.json()

                    indicates that line number for 'long_response = requests.get(url, timeout=10)' is 257. 
                    What was the line number for this line before the commit added lines above 257?",
        "answer": "3 Lines:
                    +    foo = bar()
                    +    if foo:
                    +        return None
                    are added above line 257 in the commit. So line number for 'long_response = requests.get(url, timeout=10)' should be 254 in the patch for older version."
    }}
    ...
    ]

    Generate only high quality training-dataset that are very specific to the commit details provided.
    Generate atmost 15 question-answer pairs.

    If the Commit did NOT affect the same file / lines of codes as the Patch Hunk,
    Return ONLY an empty array [].

    OUTPUT:
    <valid JSON array of objects with "question" and "answer" keys only.>
"""

############################################ PATCH UPDATE PROMPTS ############################################

PATCH_BACKPORT_USER_PROMPT = """
    Look at this hunk from a Patch for {PACKAGE_NAME} package:
{PATCH_HUNK}

    This Patch is for the latest version of the package.
    You need to backport this patch hunk for an older version of the package, before a specific commit was made.
    The commit details are:
{COMMIT_DATA}

    Here, Answer the following Questions:
        1. Is the file name or path of the hunk file changed in the commit?
            if YES, what should be the old file name or path, before the commit?
        2. Look at the start line number for the hunk in the hunk header of the patch.
           Based on the commit data, are there any lines added or removed above the hunk start line in the commit?
           if YES, what should be the starting line number, before the commit?
        3. Look at the function signature mentioned in the hunk header.
           Does the commit change the function signature or function name? 
           if Yes, what was the old function signature before the commit was made?
        4. Are there some lines added or removed in the hunk content, due to the commit?
              if YES, what should be the hunk content for the older version, before the commit was made?
        5. Are there changes to variables or datatypes in the hunk content, due to the commit?
        
    Output the data as:
    FILE_PATH                : <file path before commit changes or original as per patch hunk if not changed>
    HUNK_START_LINE_NUMBER   : <line number before the commit added / removed of lines above the hunk. Original line number as per patch if not affected by the commit.>
    FUNCTION_SIGNATURE       : <function signature before commit or original if not changed>
    HUNK_LINES_BEFORE_COMMIT : <hunk lines, after removing any extra lines due to commit, or adding removed lines due to commit. Also take care of variable name / datatype changes due to commit.>
"""