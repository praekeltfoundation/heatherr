from fabric.api import sudo, cd

code_dir = '/var/praekelt/bellman'


def deploy():
    with cd(code_dir):
        sudo('git pull', user='ubuntu')
        sudo('pip install -e .')
        sudo('./manage.py collectstatic --noinput', user='ubuntu')
