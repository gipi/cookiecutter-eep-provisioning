#!/bin/bash

find ./ -iname 'delete-*' | xargs rm -vfr
SECRET="$(cat /dev/urandom | LC_ALL=C tr -cd [a-zA-Z0-9] | head -c 12 )"

cat >> ansible_deploy_variables <<EOF
db_password: '${SECRET}'
EOF
