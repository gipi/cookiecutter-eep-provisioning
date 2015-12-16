# Cookiecutter template for provisioning

This is a strong opinionated template to use with cookiecutter
in order to provide a project with a provisioning directory.

## Getting started

Enter into the directory containing the project you need to add
provisioning and launch

    $ cookiecutter https://github.com/gipi/cookiecutter-eep-provisioning

(``cookiecutter`` can be installed using pip into a virtualenv).

You will be asked some question about your project name and stuffs.

## Variables

These are the defined variables

* ``project_name``: project for which is the provisioning
* ``repo_name``: like project name but slugified
* ``radix``: directory where place all the stuffs (default "provision")
* ``has_vagrant``
* ``has_git``
* ``has_supervisor``
* ``has_redis``
* ``site_domain``:
* ``site_name``:
* ``site_web_root``:
* ``webapp_username``:
* ``webapp_public_key``: ``ssh`` public key to use (if empty a new one will be generated)
* ``db_version``:
* ``db_name``:
* ``db_user``:

