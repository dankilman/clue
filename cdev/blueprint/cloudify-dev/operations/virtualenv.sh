#! /bin/bash -e

source $virtualenvwrapper_path

operation_mkvirtualenv()
{
    local name=$virtualenv_name
    workon $name || mkvirtualenv $name
    local virtualenv_location=$VIRTUAL_ENV
    deactivate
    ctx instance runtime-properties virtualenv_location $virtualenv_location
}

operation_$operation
