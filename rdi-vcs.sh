#! /usr/bin/bash
ARGS="$@"
set --

# shellcheck source=/dev/null
. "${RDI_VCS_INSTALLATION}/miniforge3/bin/activate"
conda activate rdi-vcs

# TODO: add ssh key path passing

python "$RDI_VCS_INSTALLATION/rdi_cli.py" "$ARGS"
