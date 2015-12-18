#!/bin/bash
#
# Script to generate a template with the default values and
# after having started a Vagrant machine, configures a WSGI
# web application with a celery task connected to it.
set -o nounset
set -o errexit

function webuser_cmd() {
    ssh -i id_rsa_my_project \
        my_project@127.0.0.1 -p 2222 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no \
        "$@"
}

function webuser_scp_app() {
    scp -i id_rsa_my_project \
        -P 2222 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no \
        "$@" my_project@127.0.0.1:app/
}

# check if someone (vagrant) is already listening to post 2222
readonly TTTT="$(netstat -ltp 2>/dev/null | grep ':2222')"

test -n "${TTTT}" && {
    echo 'port 2222 already listening'
    exit 1
}

# http://stackoverflow.com/questions/59895/can-a-bash-script-tell-what-directory-its-stored-in
readonly DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

readonly COOKIECUTTER_DIR="$(readlink -f ${DIR}/..)"

# directory where we output the cookiecutter
readonly TEMP_DIR="$(mktemp -d)"

cd "${TEMP_DIR}"

virtualenv --no-site-packages .virtualenv
set +o nounset # https://github.com/pypa/virtualenv/issues/150
source .virtualenv/bin/activate
set -o nounset
pip install cookiecutter
cookiecutter --no-input "${COOKIECUTTER_DIR}"

cd provision
vagrant up --provider=virtualbox
# ansible doesn't play well with the virtualenv
set +o nounset # https://github.com/pypa/virtualenv/issues/150
deactivate
set -o nounset

ln -s ansible_deploy_variables ansible_vagrant_variables

./bin/ansible

# do a fake deploy
webuser_cmd virtualenv --no-site-packages .virtualenv
webuser_cmd "source .virtualenv/bin/activate && pip install uwsgi celery redis"
webuser_scp_app "${DIR}"/app/*
webuser_scp_app uwsgi.ini
webuser_cmd sudo /usr/bin/supervisorctl restart uwsgi_example

echo 'temporary directory at '${TEMP_DIR}/provision
echo go to https://192.168.33.10/


