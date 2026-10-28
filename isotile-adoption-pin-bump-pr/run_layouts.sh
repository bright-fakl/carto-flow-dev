#!/bin/bash
# Layout runs for the pin bump. Environments: venv_old (isotile 392484c), venv_new (isotile a4625b7).
# main_src: archive of carto-flow main at 0ef643c (src/); branch_src: the branch of the pull request.
# Runs one after the other with nothing else running; wall times are single runs.
set -e
SP=/tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad
D=/home/fakl/carto-flow-dev/isotile-adoption-pin-bump-pr
W=/home/fakl/carto-flow/.claude/worktrees/agent-aa4901a28886b4ddd
cd /tmp
PYTHONPATH=$SP/mainsrc/src $SP/venv_old/bin/python $D/layout_cases.py run oldpin $SP/L_old.pkl > $D/layouts_oldpin.log 2>&1
PYTHONPATH=$SP/mainsrc/src $SP/venv_new/bin/python $D/layout_cases.py run newpin $SP/L_new.pkl > $D/layouts_newpin.log 2>&1
PYTHONPATH=$W/src $SP/venv_new/bin/python $D/layout_cases.py run branch $SP/L_branch.pkl > $D/layouts_branch.log 2>&1
PYTHONPATH=$SP/mainsrc/src $SP/venv_old/bin/python $D/layout_cases.py phase oldpin $SP/P_old.json > $D/phase_oldpin.log 2>&1
PYTHONPATH=$SP/mainsrc/src $SP/venv_new/bin/python $D/layout_cases.py phase newpin $SP/P_new.json > $D/phase_newpin.log 2>&1
echo done
