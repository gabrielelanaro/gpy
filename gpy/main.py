import click
import os
import glob
import shutil
from ConfigParser import SafeConfigParser, DuplicateSectionError

from fabric.api import *

@click.group()
def main():
    pass


@main.command()
@click.argument('path', required=False)
def init(path=None):
    '''Initialize a calculation repository.'''
    # All we do is creating boilerplate inside the directory

    path = path if path else '.'
    with cd('path'):
        conffile = os.path.join(path, '.gpy')
        if not os.path.exists(conffile):
            # create
            os.system('touch %s' % conffile)

@main.command('list')
@click.argument('path', required=False)
def list_(path=None):
    '''List calculations.'''
    # Check recursively
    path = path if path else '.'

    os.chdir(path)
    if not _checkproject():
        return

    for root, dirs, files in os.walk('.'):
        if '.gpy' in files:
            click.echo(root)

@main.command()
@click.argument('source', required=True)
@click.argument('dest', required=True)
def copy(source, dest):
    # Stuff to copy .mdp .gro .pdb table.xvg .ndx
    click.echo('CREATE directory %s' %(dest))
    os.mkdir(dest)

    prev = os.getcwd()
    os.chdir(source)
    tocopy = sum((glob.glob(ext) for ext in
                  ['*.mdp', '*.gro', 'table.xvg', '*.top', '*.ndx']), [])
    click.echo('COPYING files')
    os.chdir(prev)
    [shutil.copy(os.path.join(source, f), dest) for f in tocopy]
    click.echo('INIT repo')
    init([dest])

@main.command()
@click.argument('source', required=True)
@click.argument('dest', required=True)
def upload(source, dest):
    from .ssh import SSHSession
    # Connect
    host = _get_conf('host')
    u = _get_conf('user')
    p = _get_conf('password')

    sess = SSHSession(host, username=u, password=p)
    print sess.put('setup.py', 'setup.py')



    # Stuff to copy .mdp .gro .pdb table.xvg .ndx
    # click.echo('CREATE directory %s' %(dest))
    # os.mkdir(dest)
    #
    # prev = os.getcwd()
    # os.chdir(source)
    # tocopy = sum((glob.glob(ext) for ext in
    #               ['*.mdp', '*.gro', 'table.xvg', '*.top', '*.ndx']), [])
    # click.echo('COPYING files')
    # os.chdir(prev)
    # [shutil.copy(os.path.join(source, f), dest) for f in tocopy]
    # click.echo('INIT repo')
    # init([dest])

@main.command()
@click.argument('key')
@click.argument('value')
def config(key, value):
    configfile = os.path.expanduser('~/.gypconf')

    config = SafeConfigParser()
    config.read(configfile)

    try:
        config.add_section('main')
    except DuplicateSectionError:
        pass

    click.echo('UPDATE configuration %s' % key)
    config.set('main', key, value)

    with open(configfile, 'w') as f:
        config.write(f)


def _checkproject():
    if not os.path.exists('.gpy'):
        click.echo(click.style("ERROR: You are not in a gpy project.", fg='red'))
        return False
    return True

def _get_conf(key):
    configfile = os.path.expanduser('~/.gypconf')

    config = SafeConfigParser()
    config.read(configfile)

    return config.get('main', key)

if __name__ == '__main__':
    main()
