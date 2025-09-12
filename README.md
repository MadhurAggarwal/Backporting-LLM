# Backporting-LLM
Designed for Team AzureLinux, Cloud+AI Microsoft  
<br>When a new bug/vulnerability is discovered in any package, fixes are generally available for the latest versions only. If you are using any older version, then Maintaining Your Version is a task that is left for developers to do manually, from understanding the fix and the latest package version to adapting it to the older version currently in use.  
<br>This manual work is what we try to reduce.  
<br>This LLM Framework has been designed for Backporting - taking Patches written for latest versions, view the context of an older version and update the Patch to apply cleanly to the older package version.

## Initial Workflow
<img width="1490" height="842" alt="image" src="https://github.com/user-attachments/assets/d579bb83-9d6b-4c42-bcc9-d7a3accf1507" />

## Approach
[To be Added]

## How To Run
Download the Following Outside this Repo, and update their Path in the Constants.py File:
```
1. Download [Azure Linux Repository](https://github.com/microsoft/azurelinux)
2. Download Libsoup 3.4.4 Version (Package Used for testing)
```

Install the Python Files in the requirements.py file  
[To be Added]

Download Any Model and update its path in Constants.py  
User Model: [Qwen-2.5-Coder-32B-Instruct](https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct)
```
git lfs install
git clone https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct
hf download Qwen/Qwen2.5-Coder-32B-Instruct
```

Now, just Run Main.py file!

## Additional
View [VM Setup](https://www.notion.so/VM-setup-2493774dee53802d8378ffbd953f1a0e?source=copy_link) used for running this framework
