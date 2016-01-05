import hashlib
import shlex
import subprocess
from fabric.contrib.files import is_link
from fabric.utils import abort
import os
from fabric.context_managers import show, settings, cd, prefix
from fabric.contrib import files
from fabric.operations import run, sudo, get, local, put, open_shell
from fabric.state import env
from fabric.api import task

REMOTE_REVISION = None
RELEASES_DIR = 'releases'

env.use_ssh_config = True

# https://gist.github.com/lost-theory/1831706
class CommandFailed(Exception):
    def __init__(self, message, result):
        Exception.__init__(self, message)
        self.result = result

def erun(*args, **kwargs):
    with settings(warn_only=True):
        result = run(*args, **kwargs)
    if result.failed:
        raise CommandFailed("args: %r, kwargs: %r, error code: %r" % (args, kwargs, result.return_code), result)
    return result

def esudo(*args, **kwargs):
    with settings(warn_only=True):
        result = sudo(*args, **kwargs)
    if result.failed:
        raise CommandFailed("args: %r, kwargs: %r, error code: %r" % (args, kwargs, result.return_code), result)
    return result


# http://docs.fabfile.org/en/latest/usage/execution.html#roles

def describe_revision(head='HEAD'):
    actual_tag = local('git describe --always %s' % head, capture=True)
    return actual_tag

def get_dump_filepath(user, prefix=u'backups'):
    return '%s/%s.sql' % (prefix, get_remote_revision(user))

def get_release_filename():
    return '%s.tar.gz' % describe_revision()

def get_release_filepath():
    return os.path.join(RELEASES_DIR, get_release_filename())

@task
def dump_db_snapshot(db_name, user):
    remote_tmp_file_path = '/tmp/dump_db.sql' # FIXME: use temporary file
    sudo('pg_dump %s > %s' % (db_name, remote_tmp_file_path), user='postgres')
    get(remote_path=remote_tmp_file_path, local_path= get_dump_filepath(user))

def reset_db():
    local('python manage.py reset_db')

@task
def load_db(user):
    local('cat %s | python manage.py dbshell' % get_dump_filepath(user))

@task
def load_db_snapshot(db_name, username):
    dump_db_snapshot(db_name, username)
    reset_db()
    load_db(username)

@task
def create_release_archive(head='HEAD'):
    local('mkdir -p %s' % RELEASES_DIR)
    local('git archive --worktree-attributes --format=tar.gz %s > %s' % (
        head,
        get_release_filepath()
    ))

def sync_virtualenv(virtualenv_path, requirements_path):
    if not files.exists(virtualenv_path):
        erun('virtualenv --no-site-packages %s' % virtualenv_path)

    erun('source %s/bin/activate && pip install -r %s' % (
        virtualenv_path,
        requirements_path,
    ))

def virtualenv(virtualenv_path, *args, **kwargs):
    prefix('source %s/bin/activate' % virtualenv_path)

def django_collectstatic(virtualenv_path):
    erun('source %s/bin/activate && honcho --env ../.env run ./manage.py collectstatic --noinput' % virtualenv_path)

def django_migrate(virtualenv_path):
    erun('source %s/bin/activate && honcho --env ../.env run ./manage.py migrate' % virtualenv_path)

def django_createcachetable(virtualenv_path):
    erun('source %s/bin/activate && honcho --env ../.env run ./manage.py createcachetable -v 3' % virtualenv_path)

def validate_steps(steps):
    '''
    >>> func1 = lambda x:x
    >>> steps = [func1, 'datetime.datetime']
    >>> validate_steps(steps)
    [func1, 'auaua']
    '''
    func_steps = []
    for step in steps:
        func_step = step
        # if is a string then import it
        if not callable(step) and isinstance(step, basestring):
            last_dot = step.rindex('.')
            module, func_name = step[:last_dot], step[last_dot + 1:]
            func_step = getattr(__import__(module), func_name)

        if not callable(func_step):
            raise ValueError('You must pass a function')

        func_steps.append(func_step)

    return func_steps

# https://stackoverflow.com/questions/3431825/generating-a-md5-checksum-of-a-file
def hashfile(afile, hasher, blocksize=65536):
    with open(afile, 'r') as f:
        buf = f.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(blocksize)

    return hasher.hexdigest()

@task
def _release(archive, revision=None, web_root=None, **kwargs):
    '''
    Main task

    its role is to decompress an archive to the web root into a directory
    named 'app-X' where X identifies the revision; by default the revision
    is calculated from the sha256 of the archive when not indicated.

    :param version:
    :param archive:
    :param web_root:
    :param kwargs:
    :return:
    '''
    previous_revision = None

    cwd = erun('pwd').stdout if not web_root else web_root

    if not os.path.exists(archive):
        raise CommandFailed('Archive \'%s\' doesn\'t exist' % archive)

    revision = revision or hashfile(archive, hashlib.sha256())
    remote_filepath = '%s-%s' % (archive, revision)

    app_dir = os.path.join(cwd, 'app-%s' % revision)
    app_symlink = os.path.join(cwd, 'app')

    put(local_path=archive, remote_path=remote_filepath)

    try:
        # if exists remove dir
        if files.exists(app_dir):
            erun('rm -vfr %s' % (
                app_dir,
            ))
        # create the remote dir
        erun('mkdir -p %s' % app_dir)
        erun('tar xf %s -C %s' % (
            remote_filepath,
            app_dir,
        ))
        # find the previous release and move/unlink it
        if files.exists(app_symlink) and is_link(app_symlink):
            # TODO: move old deploy in an 'archive' directory
            previous_deploy_path = erun('basename $(readlink -f %s)' % app_symlink).stdout
            idx = previous_deploy_path.index('-')
            previous_revision = previous_deploy_path[idx + 1:]

            if previous_revision != revision:
                erun('unlink %s' % app_symlink)
                erun('mkdir -p old && mv -f %s old/' % previous_deploy_path)

        elif files.exists(app_symlink):
            raise CommandFailed('app directory already exists and is not a symlink')

        erun('ln -s %s %s' % (app_dir, app_symlink))

    except CommandFailed as e:
        print 'An error occoured: %s' % e

    print '''

    %s --> %s

''' % (previous_revision or '?', revision)
    open_shell('cd %s' % (
        app_dir,
    ))

# TODO: factorize also steps related to python steps (e.g. virtualenv)
#       probably with pre-steps and post-steps
@task
def release(head='HEAD', web_root=None, requirements=u'requirements.txt', envpath='.env', steps=None):
    if not os.path.isfile(requirements):
        raise ValueError('%s does not exist' % requirements)

    steps = validate_steps(steps) if steps else []

    cwd = erun('pwd').stdout if not web_root else web_root

    abs_envpath = os.path.abspath(os.path.join(cwd, envpath))
    if not files.exists(abs_envpath):
        raise abort('%s doesn\'t exist, create it before release using configure_env task!!!' % abs_envpath)

    # locally we create the archive with the app code
    create_release_archive(head)
    release_filename = get_release_filename()

    actual_version = describe_revision(head)
    previous_version = None

    # and upload it to the server
    if not files.exists(release_filename):
        put(local_path=get_release_filepath())


    app_dir = os.path.abspath(os.path.join(cwd, 'app-%s' % describe_revision(head)))
    virtualenv_path = os.path.abspath(os.path.join(cwd, '.virtualenv'))

    try:
        # if exists remove dir
        if files.exists(app_dir):
            erun('rm -vfr %s' % (
                app_dir,
            ))
        # create the remote dir
        erun('mkdir -p %s' % app_dir)
        erun('tar xf %s -C %s' % (
            release_filename,
            app_dir,
        ))
        sync_virtualenv(virtualenv_path, '%s/%s' % (app_dir, requirements,))# parametrize
        with cd(app_dir):
            for step in steps:
                step(virtualenv_path)

        # find the previous release and move/unlink it
        if is_link('app'):
            # TODO: move old deploy in an 'archive' directory
            previous_deploy_path = erun('basename $(readlink -f app)').stdout
            idx = previous_deploy_path.index('-')
            previous_version = previous_deploy_path[idx + 1:]

            if previous_version != actual_version:
                erun('unlink app')
                erun('mkdir -p old && mv -f %s old/' % previous_deploy_path)

        erun('ln -s %s app' % app_dir)

    except CommandFailed as e:
        print 'An error occoured: %s' % e

    print '''

    %s --> %s

        Use 'honcho --env ../.env start' inside a screen session

    ''' % (previous_version, actual_version)
    open_shell('cd %s && source %s/bin/activate' % (
        app_dir,
        virtualenv_path,
    ))

@task
def shell(revision=None):
    '''Open a shell into an app's environment (the enabled one as default)'''
    cwd = erun('pwd').stdout

    virtualenv_path = os.path.abspath(os.path.join(cwd, '.virtualenv'))

    open_shell('cd %s && source %s/bin/activate' % (
        'app' if not revision else ('app-%s' % revision),
        virtualenv_path,
    ))

@task
def release_django(head='HEAD', web_root=None, requirements=u'requirements.txt', envpath='.env'):
    release(head, web_root, requirements, steps=[django_migrate, django_createcachetable, django_collectstatic,], envpath=envpath)

def get_remote_revision(user):
    global REMOTE_REVISION

    if not REMOTE_REVISION:
        current_app_dir = esudo('cd && basename $(readlink -f app)', user=user)
        try:
            _, REMOTE_REVISION = current_app_dir.split('-')
        except Exception as e:
            print e
            REMOTE_REVISION = 'unknown'

    return REMOTE_REVISION

@task
def configure_env(envpath='.env', local_copy_path='.remote.env', web_root=None):
    cwd = erun('pwd').stdout if not web_root else web_root

    envpath = os.path.abspath(os.path.join(cwd, envpath))
    # first of all, get the file remote side
    if files.exists(envpath):
        get(remote_path=envpath, local_path=local_copy_path)

    # just in case the remote file doesn't exist
    with open(local_copy_path, 'a+') as f:
        pass

    subprocess.call(shlex.split("vim %s" % local_copy_path))

    put(local_path=local_copy_path, remote_path=envpath)

    os.remove(local_copy_path)
