# Provisioning

You can use the files contained in this directory to provision
your machine in order to make the project working.

To start quickly edit the ``ansible_deploy_inventory`` and ``ansible_deploy_variables``
files following your taste and then

    $ cd {{ cookiecutter.radix }}/
    $ bin/ansible -i ansible_deploy_inventory -v ansible_deploy_variables

{% if cookiecutter.has_supervisor == "y" %}## Supervisor

To manage the running state of ``uwsgi`` we are using a [supervisor](https://supervisord.readthedocs.org/en/latest/)
configuration script in ``/etc/supervisor/{{ cookiecutter.site_name }}.conf``.

It's possible to restart the app thanks to a ``sudo`` configuration that allows
certain commands on ``supervisorctl``.

    $ sudo /usr/bin/supervisorctl restart uwsgi_{{ cookiecutter.site_name }}

{% endif %}

## Ansible

Use the 2.0+ version.

{% if cookiecutter.has_vagrant == "y" %}## Vagrant

Out of the box is available a Debian8 virtualbox configuration, you have
to do a simple

    $ vagrant up --provider virtualbox

{% endif %}

## Nginx

The web server listen only ``HTTPS`` (un-encrypted requests are redirect to encrypted ones).

It's configured to use self-signed certificate, the real one must be generated and certificate
and private key be in the correct places (look at ``/etc/nginx/site-available/{{ cookiecutter.site_name }}``).
