#! /bin/bash -e
########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
############

print_git_branch_state()
{
    GIT_PS1_SHOWCOLORHINTS=true
    GIT_PS1_SHOWDIRTYSTATE=true
    GIT_PS1_SHOWSTASHSTATE=true
    GIT_PS1_SHOWUNTRACKEDFILES=true
    GIT_PS1_SHOWUPSTREAM=auto
    source {{git_prompt_path}}
    cd {{repo_location}}
    __git_ps1 "" "" "%s" || true
    export PS1
    export __git_ps1_branch_name
    program='''
import os
import sys
output = os.environ["PS1"]
output = output.replace("\\[", "")
output = output.replace("\\]", "")
branch_name = os.environ.get("__git_ps1_branch_name")
if branch_name:
    output = output.replace("${__git_ps1_branch_name}", branch_name)
sys.stdout.write(output)
'''
    output=$(python -c "$program")
    echo -e "${output}"
}

print_git_branch_state
