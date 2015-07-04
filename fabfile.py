from fabric.api import sudo, cd, env

code_dir = '/var/praekelt/bellman'

env.hosts = ['kraken.praekelt.com']


def deploy():
    with cd(code_dir):
        sudo('git pull', user='ubuntu')
        sudo('pip install -e .')
        sudo('./manage.py collectstatic --noinput', user='ubuntu')
        sudo('supervisorctl restart bellman')
