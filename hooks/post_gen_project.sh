#!/bin/bash

find ./ -iname 'delete-*' | xargs rm -vfr
SECRET="$(cat /dev/urandom | LC_ALL=C tr -cd [a-zA-Z0-9] | head -c 12 )"

# generate on fly the password for the db
cat >> ansible_deploy_variables <<EOF
db_password: '${SECRET}'
EOF

# generate ssh key for the deploy with empty passphrase
{% if cookiecutter.webapp_public_key == "" %}
KEYNAME="id_rsa_{{ cookiecutter.repo_name }}"

# do not overwrite existing key
test -f "${KEYNAME}" || {
    ssh-keygen -f "${KEYNAME}" -N ""
    cat >> ansible_deploy_variables <<EOF
webapp_public_key: '${KEYNAME}.pub'
EOF
}
{% endif %}
