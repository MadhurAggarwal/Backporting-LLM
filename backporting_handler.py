from constants import PR_CHANGELOG_FILE, UPSTREAM_PATCH_FILE, PACKAGE_NAME, PACKAGE_REPO, AZURELINUX_REPO_PATH, PATCH_TEST_FILE
from helper_functions import run_git_reset, apply_one_patch
import json
import re
import os
from collections import defaultdict

class BackportingHandler:
    def __init__(self):
        try:
            with open(UPSTREAM_PATCH_FILE, "r", encoding="utf-8") as f:
                self.upstream_data = json.load(f)

            with open(PR_CHANGELOG_FILE, "r", encoding="utf-8") as f:
                self.pr_data = json.load(f)
            
            spec_file_path = f"{AZURELINUX_REPO_PATH}/SPECS/{PACKAGE_NAME}/{PACKAGE_NAME}.spec"
            with open(spec_file_path, "r", encoding="utf-8") as f:
                self.spec_file_content = f.read()

        except (FileNotFoundError, json.JSONDecodeError):
            self.upstream_data = {}
            self.pr_data = {}

    def getUpstreamPatchForCVE(self, cve_number):
        if cve_number in self.upstream_data:
            patch = self.upstream_data[cve_number].get("upstream_patch", None)
            if patch is not None:
                return patch.encode("utf-8").decode("unicode_escape")
                # return json.dumps(patch, indent=2)
        return None
    
    def getCVEDescription(self, cve_number):
        if cve_number in self.upstream_data:
            description = self.upstream_data[cve_number].get("cve_description", None)
            if description is not None:
                return description.encode("utf-8").decode("unicode_escape")
                # return json.dumps(description, indent=2)
        return None

    def getPRNumberForCVE(self, cve_number):
        if cve_number in self.upstream_data:
            pr_numbers = self.upstream_data[cve_number].get("pr_number", None)
            return pr_numbers[-1]
        return None

    def getAzureLinuxPatch(self, cve_number):
        patch_location = f"{AZURELINUX_REPO_PATH}/SPECS/{PACKAGE_NAME}/{cve_number}.patch"
        if os.path.exists(patch_location):
            with open(patch_location, "r", encoding="utf-8") as f:
                return f.read()
        return None

        ## Fetching AzureLinux Patch from PR Changelog data
        # def normalize_patch(patch_text: str) -> str:
        #     lines = patch_text.splitlines()
        #     fixed_lines = []
        #     for line in lines:
        #         if line.startswith("+"):
        #             fixed_lines.append(line[1:])
        #         else:
        #             fixed_lines.append(line)

        #     return "\n".join(fixed_lines) + "\n"
        
        # pr_number = self.getPRNumberForCVE(cve_number)
        # file_name = f"SPECS/{PACKAGE_NAME}/{cve_number}.patch"
        # if pr_number in self.pr_data:
        #     all_files = self.pr_data[pr_number].get("code", [])
        #     for file in all_files:
        #         if file.get("filename", "") == file_name:
        #             patch = file.get("patch", None)
        #             return normalize_patch(patch) if patch else None
        # return None

    def getCVEDependencyList(self, cve_number):
        cves_list    = []
        target_found = False
        target_patch = f"{cve_number}.patch"

        for line in self.spec_file_content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            match = re.match(r'^(Patch\d+):\s*(\S+)$', line)
            if not match:
                continue

            patch_file = match.group(2)
            if patch_file == target_patch:
                target_found = True
                break

            cve_match = re.match(r'^(CVE-\d{4}-\d+)\.patch$', patch_file)
            if cve_match:
                cves_list.append(cve_match.group(1))

        if target_found:
            return cves_list
        return []

    def getChangedFileNames(self, patch):
        files = re.findall(r"diff --git a/(\S+) b/\S+", patch)
        return files
    
    def preparePackageRepo(self, cve_number):
        cve_dependency_list = self.getCVEDependencyList(cve_number)

        run_git_reset(PACKAGE_REPO)
        
        print(f"For {cve_number}, applying {len(cve_dependency_list)} Patches before fetching file codes")
        for dependent_cve in cve_dependency_list:
            dependent_cve_patch = self.getAzureLinuxPatch(dependent_cve)
            if dependent_cve_patch:
                print(f"Applying Patch {dependent_cve}.patch")
                apply_one_patch(PACKAGE_REPO, dependent_cve_patch)

    def getPackageFilesCode(self, cve_number):
        self.preparePackageRepo(cve_number)

        patch = self.getUpstreamPatchForCVE(cve_number)
        cleaner = CleanData()
        return cleaner.getRelevantSectionFromFileCodes(patch)

        # files = self.getChangedFileNames(patch)
        # file_code = {}

        # for file in files:
        #     file_location = PACKAGE_REPO.rstrip('/') + "/" + file

        #     if not os.path.exists(file_location):
        #         raise FileNotFoundError(f"File not found: {file_location}")

        #     with open(file_location, "r", encoding="utf-8") as f:
        #         filecontent = f.readlines()
        #         file_code[file] = [
        #             f"{i+1}: {line}" for i, line in enumerate(filecontent)
        #         ]
        # return file_code

    def testPatch(self, cve_number, patch):
        self.preparePackageRepo(cve_number)
        print(f"Testing Patch for {cve_number}")
        try:
            apply_one_patch(PACKAGE_REPO, patch)
        except RuntimeError as e:
            print(e)
            return False, e
        return True, None

    def getDataForOneCVE(self, cve_number):
        cve_description = self.getCVEDescription(cve_number)
        upstream_patch  = self.getUpstreamPatchForCVE(cve_number)
        file_codes      = self.getPackageFilesCode(cve_number)
        azurelinux_patch = self.getAzureLinuxPatch(cve_number)

        input  = (cve_number, cve_description, upstream_patch, file_codes)
        output = azurelinux_patch

        return input, output

    def getCVEList(self):
        return list(self.upstream_data.keys())

    def getData(self):
        all_cves = self.getCVEList()

        input  = []
        output = []

        for cve in all_cves:
            try:
                input_data, output_data = self.getDataForOneCVE(cve)
                input.append(input_data)
                output.append(output_data)
            except Exception as e:
                print(f"Error processing {cve}: {e}")
                continue

        return input, output
    
class CleanData:
    def breakPatchInSmallerPatches(self, patch):
        raise NotImplementedError
    
    def removeUnnecessaryDetailsFromPatch(self, patch):
        raise NotImplementedError

    def extractOutputFromGeneratedPatch(self, generatedOutput, inputPrompt):
        generatedOutput = generatedOutput.encode("utf-8").decode("unicode_escape")
        start_token = "<output>"
        end_token   = "</output>"
        
        start_idx = generatedOutput.find(start_token)
        end_idx   = generatedOutput.find(end_token)

        if start_idx == -1:
            start_idx = 0
        else:
            start_idx += len(start_token)

        if end_idx == -1:
            end_idx = len(generatedOutput)

        return generatedOutput[start_idx:end_idx].strip()

    def extract_patch_contexts(self, patch: str, extraLines=0):
        patch = patch.encode("utf-8").decode("unicode_escape")

        file_contexts = defaultdict(list)

        file_re = re.compile(r"^\s*diff --git a/(.+?) b/(.+)$")
        hunk_header_re = re.compile(r"^\s*@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)")

        current_file = None
        current_hunk_lines = []
        deletions = insertions = 0
        in_hunk = False
        hunk_done = False
        current_line_number = None

        print("Len: ", len(patch.splitlines()))

        for line in patch.splitlines():
            line = self.normalize_whitespace(line)
            m = file_re.match(line)
            if m:
                current_file = m.group(1)
                in_hunk = False
                hunk_done = False
                continue

            h = hunk_header_re.match(line)
            if h and current_file:
                if current_hunk_lines:
                    file_contexts[current_file].append({
                        "unchanged_code": "\n".join(current_hunk_lines).rstrip(),
                        "number_of_lines": deletions + insertions + extraLines,
                        "line_number": current_line_number
                    })

                current_hunk_lines = []
                deletions = int(h.group(2)) if h.group(2) else 1
                insertions = int(h.group(4)) if h.group(4) else 1
                current_line_number = int(h.group(3))

                trailing_context = h.group(5).strip()
                if trailing_context:
                    current_hunk_lines.append(trailing_context)

                in_hunk = True
                hunk_done = False
                continue

            if in_hunk and not hunk_done:
                if line.startswith("+") or line.startswith("-"):
                    if current_hunk_lines:
                        file_contexts[current_file].append({
                            "unchanged_code": "\n".join(current_hunk_lines).rstrip(),
                            "number_of_lines": deletions + insertions + extraLines,
                            "line_number": current_line_number
                        })
                    current_hunk_lines = []
                    hunk_done = True
                else:
                    current_hunk_lines.append(line.strip())

        if current_hunk_lines and current_file and not hunk_done:
            file_contexts[current_file].append({
                "unchanged_code": "\n".join(current_hunk_lines).rstrip(),
                "number_of_lines": deletions + insertions + extraLines,
                "line_number": current_line_number
            })

        return dict(file_contexts)

    def normalize_whitespace(self, s: str) -> str:
        return re.sub(r"\s+", " ", s.strip())
        # s = re.sub(r'(?:\s+|\\[nrtvf])+', ' ', s.strip())
        # return s.strip()

    def getRelevantSectionFromFileCodes(self, patch:str):
        file_contexts = self.extract_patch_contexts(patch)
        file_codes = {}
        for file_path, contexts in file_contexts.items():
            path = os.path.join(PACKAGE_REPO, file_path)
            with open(path, "r") as f:
                code_lines = f.readlines()
                n = len(code_lines)
                takeLine = [False] * n

                norm_code_lines = [self.normalize_whitespace(line) for line in code_lines]

                for context in contexts:
                    unchanged_code_lines = [
                        self.normalize_whitespace(l)
                        for l in context["unchanged_code"].splitlines()
                        if l.strip()
                    ]
                    line_number = context["line_number"]
                    number_of_lines = context["number_of_lines"]

                    matches = []
                    for uline in unchanged_code_lines:
                        for idx, nline in enumerate(norm_code_lines):
                            if uline and uline.strip() == nline.strip():
                                for x in range(idx-5,idx+5):
                                    if x != idx and x in matches:
                                        start = max(0, min(x,idx) - 5)
                                        end   = min(n, max(x,idx) + 5)
                                        takeLine[start:end] = [True] * (end - start)
                                matches.append(idx)

                    start = max(0, line_number)
                    end   = min(n, line_number + number_of_lines + 10)
                    takeLine[start:end] = [True] * (end - start)

                adjusted_code = [
                    f"{i+1}: {line}"
                    for i, line in enumerate(code_lines) if takeLine[i]
                ]
                file_codes[file_path] = adjusted_code

        return file_codes

def main():
    b = BackportingHandler()
    c = CleanData()

    cve_number = ""

    azpatch = b.getAzureLinuxPatch(cve_number)
    uspatch = b.getUpstreamPatchForCVE(cve_number)

    # patch = """
    # """

    # print("PATCH CONTEXT: ")
    # print(c.extract_patch_contexts(patch))
    # print()
    # print()

    # print("UPSTREAM PATCH")
    # upstream_patch = b.getUpstreamPatchForCVE("CVE-2025-32907")
    # print(upstream_patch)
    # print()
    # print()

    # print("PATCH CONTEXT: ")
    # print(c.extract_patch_contexts(upstream_patch))
    # print()
    # print()

    # print("FILE CODE")
    # code = b.getPackageFilesCode("CVE-2025-32907")
    # print(code)
    # print()
    # print()

    # upstream_patch = upstream_patch.encode("utf-8").decode("unicode_escape")
    # with open(PATCH_TEST_FILE, "w") as f:
    #     f.write(upstream_patch)

if __name__ == "__main__":
    main()