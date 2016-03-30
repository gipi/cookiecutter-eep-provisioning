#!/bin/bash
#
# Script to generate a template with the default values and
# after having started a Vagrant machine, configures a WSGI
# web application with a celery task connected to it.
#
# The user is not random generated, so if the test fail in
# an environment you have to delete it
set -o nounset
set -o errexit
set -o pipefail

function check_prog() {
    which $1 > /dev/null || {
        failure_msg "missing dependency: "$1
        exit 1
    }
}

# check that all the progs are installed and port are free
function check_environment() {
    check_prog ansible-playbook
}

function running_log() {
    echo -e "\e[32m\e[1m$1\e[0m"
}

function failure_msg() {
    echo -e "\e[31m\e[1m$1\e[0m"
}

function webuser_cmd() {
    ssh -i ${TEMP_DIR}/provision/id_rsa_my_project \
        my_project@127.0.0.1 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -oBatchMode=yes \
        "$@"
}

function webuser_scp_app() {
    scp -i ${TEMP_DIR}/provision/id_rsa_my_project \
        -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -oBatchMode=yes \
        "$@" my_project@127.0.0.1:app/
}

function cookiecutterme() {
    cd "${TEMP_DIR}" # just in case is recalled after the first time
    pip install cookiecutter
    python -c 'from cookiecutter.main import cookiecutter;cookiecutter("'${COOKIECUTTER_DIR}'", no_input=True, overwrite_if_exists=True, extra_context={"has_redis": "y", "site_web_root": "'${TEMP_WEB_ROOT}'"});'
    cd -
}

check_environment

# http://stackoverflow.com/questions/59895/can-a-bash-script-tell-what-directory-its-stored-in
readonly DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

readonly COOKIECUTTER_DIR="$(readlink -f ${DIR}/..)"

# directory where we output the cookiecutter
readonly TEMP_DIR="$(mktemp -d)"
readonly TEMP_WEB_ROOT=${TEMP_DIR}/webroot/


export TEMP_DIR
export COOKIECUTTER_DIR

running_log "creating temporary directory and entering it"
cd "${TEMP_DIR}"


running_log cookiecutter
cookiecutterme

test -f "${TEMP_DIR}/provision/id_rsa_my_project" || exit 1

( cd provision && ln -s ansible_deploy_variables ansible_vagrant_variables && cat ansible_vagrant_variables )

running_log provisioning
./provision/bin/configure_machines -l -s

running_log deploy
# do a fake deploy
#pip install fabric

#./bin/deploy -i id_rsa_my_project --user my_project -H 192.168.33.10
webuser_cmd virtualenv --no-site-packages .virtualenv
webuser_cmd "source .virtualenv/bin/activate && pip install uwsgi celery redis"
webuser_scp_app "${DIR}"/app/*
webuser_scp_app "${TEMP_DIR}/provision/"uwsgi.ini
# activate the celery daemon
webuser_cmd sed --in-place '"s/^\(# \)\(attach-daemon2\)/\2/"' app/uwsgi.ini
webuser_cmd sudo /usr/bin/supervisorctl restart uwsgi_example

echo 'temporary directory at '${TEMP_DIR}/provision
echo go to https://192.168.33.10/

function sshme() {
    ssh -i id_rsa_my_project my_project@127.0.0.1 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no
}

cat <<EOF

 now you are into the provisioning directory, you can use "sshme" to enter
 as the web application user.

 You can use "cookiecutterme" to update the generated cookiecutter template.

 At the end remember to destroy the vagrant instance with "destroy_provision".

EOF

# reactivate the virtualenv
set +o nounset # https://github.com/pypa/virtualenv/issues/150
source "${TEMP_DIR}/.virtualenv/bin/activate"
set -o nounset

export -f destroy_provision
export -f cookiecutterme
export -f sshme

/bin/bash 

