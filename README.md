# rdi-vcs
A CLI tool to manage multiple repositories

## Installation
```bash
cd rdi-vcs
sudo chmod +x install.sh
./install.sh
```
The tool will now be available through rdi-vcs command

## Usage
After installation, first configure the repos file location:

**rdi-vcs** `set-config /path/to/repos.yaml` - saves the location of your repos config  
**rdi-vcs** `--config /path/to/repos.yaml` *clone* - set the config location explicitly (overrides the location of config if one was set via 'set-config')    
**rdi-vcs** *checkout-create* *\*your_branch_name\** - checkouts all the configured repos to the specified branch or creates & checkouts it the branch does not exist  
**rdi-vcs** *push* - pushes your **staged** local changes to all repos to the branch the are currently in  
**rdi-vcs** *pull* - pulls to all repos  
**rdi-vcs** *publish* - creates pull (merge) requests to the default branch for all repos  

## Authentication
- **SSH is not supported**. Use HTTPS repo URLs like `https://github.com/owner/repo.git`.
- **Public repos** can be cloned over HTTPS without `GITHUB_TOKEN`.
- **Private repos** require `GITHUB_TOKEN` to be set in the environment.

## Uninstallation
Uninstall the venv & wrappers:
(will be through uninstall.sh soon)
```bash
rm ~/.local/rdi-vcs
rm ~/.env.sh
cd rdi-vcs && rm -rf miniforge3 Miniforge3-$(uname)-$(uname -m).sh
```
