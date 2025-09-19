# Testing the Finetuned LLM in SWE Agent

## Test-1: Filepath & Linenumber changes

Apply Custom Commits:
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

Now, Run [SWE-AGENT](https://dev.azure.com/mariner-org/mariner/_git/AllSpark) with either the Base or Finetuned Model  
For running with the Finetuned Model, use 
- export LITELLM_LOCAL_MODEL_COST_MAP=True
- Add details about finetuned model (name, tokens, etc) in the model_prices_and_context_window_backup.json file

Then use SWE Agent to Backport latest local HEAD to tag: 3.4.4

Test-1 tests how well can the Base/Finetuned Models in the SWE Agent backport changes to filenames and linenumbers.

---
Results
