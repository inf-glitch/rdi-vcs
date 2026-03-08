#! /usr/bin/bash

. ~/.env.sh
. $RDI_VCS_INSTALLATION/miniforge3/bin/activate

conda activate rdi-vcs
python $RDI_VCS_INSTALLATION/rdi-vcs.py
