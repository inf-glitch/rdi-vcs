# Installer for rdi-vcs tool

#! /usr/bin/bash

if [ $(echo $SHELL) = "/usr/bin/bash" ]; then
    echo "export PATH=$PATH:~/.local/" >> ~/.bashrc

else if [ $(echo $SHELL) = "/usr/bin/zsh" ]; then
    echo "export PATH=$PATH:~/.local/" >> ~/.zshrc
    echo ""
    echo $PATH
    echo ""

else
    echo "unsupported shell: $SHELL"
    exit 1
fi
fi

# ------------------------------------------------------

if ! ls | grep Miniforge3-$(uname)-$(uname -m).sh; then
   wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
fi

bash Miniforge3-$(uname)-$(uname -m).sh -b -p $PWD/miniforge3

. ./miniforge3/bin/activate
conda create -n rdi-vcs python=3.12 -y
conda activate rdi-vcs

pip install vcstool pygit2 argparse
pip install "setuptools==80"  # pkg_resources break on newer versions
pip install requests

conda deactivate  # rdi-vcs env
conda deactivate  # base env

ln -s $PWD/rdi-vcs.sh ~/.local/rdi-vcs

if [ $(echo $SHELL) = "/usr/bin/bash" ]; then
    cp ~/.bashrc ~/.bashrc.pre-rdi-vcs
    SHRC=".bashrc"

else if [ $(echo $SHELL) = "/usr/bin/zsh" ]; then
    cp ~/.zshrc ~/.zshrc.pre-rdi-vcs
    SHRC=".zshrc"
fi
fi

echo "export RDI_VCS_INSTALLATION=$PWD" > ~/.env.sh

echo ""
echo "====================================================="
echo "rdi-vcs installed. reload the shell to apply changes."
echo "current $SHRC saved to $SHRC.pre-rdi-vcs"
echo "====================================================="


