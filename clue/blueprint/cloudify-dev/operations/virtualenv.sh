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

source ${virtualenvwrapper_path}

operation_mkvirtualenv()
{
    workon ${virtualenv_name} 2> /dev/null || mkvirtualenv ${virtualenv_name} || true
    local virtualenv_location=${VIRTUAL_ENV}
    deactivate
    ctx instance runtime-properties virtualenv_location ${virtualenv_location}
}

operation_${operation}
