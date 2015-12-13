# Provisioning

You can use the files contained in this directory to provision
your machine in order to make the project working.

To start quickly edit the ``ansible_deploy_inventory`` and ``ansible_deploy_variables``
files following your taste and then

    $ cd {{ cookiecutter.radix }}/
    $ bin/ansible -i ansible_deploy_inventory -v ansible_deploy_variables

## Ansible

Use the 2.0+ version.

## Vagrant

Out of the box is available a Debian8 virtualbox configuration, you have
to do a simple

    $ vagrant up --provider virtualbox

