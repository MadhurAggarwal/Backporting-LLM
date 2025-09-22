# Testing the Finetuned LLM in SWE Agent

## Test-1: Filepath & Linenumber changes

In the 'Libsoup' Package, Apply Custom Commits using the following commands:
```
git checkout master
git reset --hard b3df7199959e8661d6cf9d65ffbfb94692982b3a

git am libsoup_custom_changes_for_swe_test/patches/0001-Renamed-Files-Moved-file-paths.patch
git am libsoup_custom_changes_for_swe_test/patches/0002-Added-Random-Lines-to-sb-output-stream.c.patch
git am libsoup_custom_changes_for_swe_test/patches/0003-Added-More-Random-Lines-to-sb-output-stream.c.patch
```

These Commits change the:
- 0001: Change Filenames of some files  
- 0002, 0003: Add new lines to a function (to change the line numbers)

Now, apply the test patch:
```
patch -p1 < libsoup_custom_changes_for_swe_test/test_patches/test-1-filename-and-linenumber-changes.patch
git add .
git commit -m "Test-patch-1"
```

Get the Latest Commit ID. This is your `cid`, that the SWE-Agent will try to backport onto some older version.
```
git show HEAD
```

On the libsoup folder, run:
```
git checkout 3.4.4
```

This is the old version to which SWE-Agent will backport the cid patch to.

Now, Run [SWE-AGENT](https://dev.azure.com/mariner-org/mariner/_git/AllSpark) with either the Base or Finetuned Model  
For running with the Finetuned Model, use 
- export LITELLM_LOCAL_MODEL_COST_MAP=True
- Add details about finetuned model (name, tokens, etc) in the .venv/lib/python3.13/site-packages/litellm/model_prices_and_context_window_backup.json file
- Add the .env in SWE Agent to include AZURE_API_KEY and AZURE_API_BASE

Then use SWE Agent to Backport latest local HEAD to tag: 3.4.4

Test-1 tests how well can the Base/Finetuned Models in the SWE Agent backport changes to filenames and linenumbers.

---
Results

## Test-2: Filepath & Function-name Changes

Prepare Libsoup as before
``` 
git checkout master
git reset --hard b3df7199959e8661d6cf9d65ffbfb94692982b3a

git am /home/sumsharma/madhur/backporting-llm/training_llm/libsoup_custom_changes_for_swe_test/patches/*.patch
```

Now Apply the second test patch:
```
patch -p1 < /home/sumsharma/madhur/backporting-llm/training_llm/libsoup_custom_changes_for_swe_test/test_patches/test-2-function-location-and-filepath-change.patch

git add .
git commit -m "Test-patch-2"
```

## Test 3

```
git checkout master
git reset --hard b3df7199959e8661d6cf9d65ffbfb94692982b3a

git am /home/sumsharma/madhur/backporting-llm/training_llm/libsoup_custom_changes_for_swe_test/patches/0001-Renamed-Files-Moved-file-paths.patch
git am /home/sumsharma/madhur/backporting-llm/training_llm/libsoup_custom_changes_for_swe_test/patches/0002-Added-Random-Lines-to-sb-output-stream.c.patch
git am /home/sumsharma/madhur/backporting-llm/training_llm/libsoup_custom_changes_for_swe_test/patches/0003-Added-More-Random-Lines-to-sb-output-stream.c.patch
git am /home/sumsharma/madhur/backporting-llm/training_llm/libsoup_custom_changes_for_swe_test/patches/0004-Refactored-function-into-multiple-different-function.patch
```