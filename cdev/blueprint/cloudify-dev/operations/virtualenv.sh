#! /bin/bash -e

source ${virtualenvwrapper_path}

operation_mkvirtualenv()
{
    workon ${virtualenv_name} 2> /dev/null || mkvirtualenv ${virtualenv_name} || true
    local virtualenv_location=${VIRTUAL_ENV}
    deactivate
    ctx instance runtime-properties virtualenv_location ${virtualenv_location}
}

operation_${operation}
