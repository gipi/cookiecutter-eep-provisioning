#!/bin/bash
#
# Script to generate a template with the default values and
# after having started a Vagrant machine, configures a WSGI
# web application with a celery task connected to it.
set -o nounset
set -o errexit

function running_log() {
    echo -e "\e[32m\e[1m$1\e[0m"
}

function failure_msg() {
    echo -e "\e[31m\e[1m$1\e[0m"
}

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
    failure_msg 'port 2222 already listening'
    exit 1
}

# http://stackoverflow.com/questions/59895/can-a-bash-script-tell-what-directory-its-stored-in
readonly DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

readonly COOKIECUTTER_DIR="$(readlink -f ${DIR}/..)"

# directory where we output the cookiecutter
readonly TEMP_DIR="$(mktemp -d)"

running_log "creating temporary directory and entering it"
cd "${TEMP_DIR}"


running_log "virtualenv"
virtualenv --no-site-packages .virtualenv
set +o nounset # https://github.com/pypa/virtualenv/issues/150
source .virtualenv/bin/activate
set -o nounset

running_log cookiecutter
(
pip install cookiecutter
# use the programmatic way in order to change some defaults
python -c 'from cookiecutter.main import cookiecutter;cookiecutter("'${COOKIECUTTER_DIR}'", no_input=True, extra_context={"has_redis": "y"});'
) | sed 's/^/    /' 
cd provision
running_log vagrant
(
vagrant up --provider=virtualbox
) | sed 's/^/    /' 
# ansible doesn't play well with the virtualenv
set +o nounset # https://github.com/pypa/virtualenv/issues/150
deactivate
set -o nounset

ln -s ansible_deploy_variables ansible_vagrant_variables

running_log provisioning
(
./bin/ansible
) | sed 's/^/    /' 

running_log deploy
(
# do a fake deploy
webuser_cmd virtualenv --no-site-packages .virtualenv
webuser_cmd "source .virtualenv/bin/activate && pip install uwsgi celery redis"
webuser_scp_app "${DIR}"/app/*
webuser_scp_app uwsgi.ini
# activate the celery daemon
webuser_cmd sed --in-place '"s/^\(# \)\(attach-daemon2\)/\2/"' app/uwsgi.ini
webuser_cmd sudo /usr/bin/supervisorctl restart uwsgi_example
) | sed 's/^/    /'

echo 'temporary directory at '${TEMP_DIR}/provision
echo go to https://192.168.33.10/

function destroy_provision() {
    vagrant destroy --force
}

export -f destroy_provision

