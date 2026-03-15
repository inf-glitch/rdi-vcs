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
**rdi-vcs** *clone* - cloning all repositories mentioned in meta_repo/repos.yaml to the directory the tool is called in
**rdi-vcs** *checkout-create* *\*your_branch_name\** - checkouts all the configured repos to the specified branch or creates & checkouts it the branch does not exist
**rdi-vcs** *push* - pushes your **staged** local changes to all repos to the branch the are currently in
**rdi-vcs** *pull* - pulls to all repos
**rdi-vcs** *publish* - creates pull (merge) requests to the default branch for all repos

## Uninstallation
Uninstall the venv & wrappers:
(will be through uninstall.sh soon)
```bash
rm ~/.local/rdi-vcs
rm ~/.env.sh
cd rdi-vcs && rm -rf miniforge3 Miniforge3-$(uname)-$(uname -m).sh
```
