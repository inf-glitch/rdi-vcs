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

Configuration lookup order:

1. `--config /path/to/repos.yaml` (overrides everything)
2. `RDI_VCS_CONFIG_LOCATION` (set by `rdi-vcs set-config ...`)

```sh
# e.g.
rdi-vcs set-config /path/to/meta_repo/repos.yaml
```

1. `./repos.yaml` in the current working directory

**rdi-vcs** *set-config* /path/to/repos.yaml - saves the location of your repos config and allows not to specify path afterwards  
to reset the config location just pass "reset" to set-config command: **rdi-vcs** *set-config* reset  

**rdi-vcs** *checkout-create* *your_branch_name* - checkouts all the configured repos to the specified branch or creates & checkouts it the branch does not exist  

**rdi-vcs** *push* - pushes your **staged** local changes to all repos to the branch the are currently in  

**rdi-vcs** *pull* - pulls to all repos  

**rdi-vcs** *commit* - stages all local changes and commits across all repos using one shared message   

**rdi-vcs** *commit -m "your message"* - stages and commits all repos with the provided shared message  

**rdi-vcs** *publish* - creates pull (merge) requests to the default branch for all repos  

If you run `rdi-vcs commit` without `-m/--message`, the tool generates one timestamp-based message and reuses it for every configured repository in that run.  
Message format: "rdi-vcs commit %Y-%m-%d %H:%M:%S"  

## Authentication

- **SSH is not supported**. Use HTTPS repo URLs like `https://github.com/owner/repo.git`.
- **Public repos** can be cloned over HTTPS without `GITHUB_TOKEN`.
- **Private repos** require `GITHUB_TOKEN` to be set in the environment.

## Uninstallation

From the clone directory (or anywhere if `~/.env.sh` still lists `RDI_VCS_INSTALLATION`):

```bash
cd rdi-vcs
chmod +x uninstall.sh
./uninstall.sh
```

This removes the Miniforge tree and downloaded installer under the install directory, the `rdi-vcs` conda environment (inside Miniforge), the `~/.local/rdi-vcs` launcher, the entire `~/.env.sh` file (installer and `rdi-vcs set-config` use this path), and the `export PATH=...~/.local` line added to `~/.bashrc` / `~/.zshrc` by `install.sh`.

Options:

- `./uninstall.sh --dry-run` — show what would be removed
- `./uninstall.sh -y` — skip the confirmation prompt (required if stdin is not a tty)
- `./uninstall.sh --install-dir /path/to/rdi-vcs` — if `~/.env.sh` is missing or wrong
- `./uninstall.sh --remove-rc-backups` — also delete `~/.bashrc.pre-rdi-vcs` and `~/.zshrc.pre-rdi-vcs` from the installer

Manual one-liner (equivalent core steps):

```bash
rm ~/.local/rdi-vcs
rm ~/.env.sh
cd rdi-vcs && rm -rf miniforge3 Miniforge3-$(uname)-$(uname -m).sh
```

