import click
import os
import glob
import shutil
import subprocess

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
    conffile = os.path.join(path, '.gpy')
    if not os.path.exists(conffile):
        # create
        os.system('touch %s' % conffile)
    else:
        click.echo('INFO: already a repository')

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

@main.command()
@click.option('--name', '-n')
@click.option('--time', '-t')
@click.option('--cpus', '-c')
@click.option('--email', '-e')
@click.option('--yes', is_flag=True)
@click.option('--no', is_flag=True)
def qsub(name, time, cpus, email, yes, no):
    
    if not _checkproject():
        return

    template = _get_template('qsub.tpl')
    config = _conf()
    
    if template is None:
        return

    if email is None:
        email = _get_conf('email')
    
    time = time if time is not None else config.get('qsub', 'time')
    name = name if name is not None else config.get('qsub', 'name')
    cpus = cpus if cpus is not None else config.get('qsub', 'cpus')
    
    render = template.format(name=name, time=time, cpus=cpus, email=email)
    with open('sub.pbs', 'w') as fd:
        fd.write(render)
    
    click.echo('WRITTEN: sub.pbs')
    ret = subprocess.check_output(['qsub', 'sub.pbs'])
    click.echo('INFO: Created job %s' % ret)

    if not config.has_section('qsub'):
        config.add_section('qsub')
    
    config.set('qsub', 'job', ret)

    if no:
        pass
    elif yes or click.confirm('Do you want to save the settings for next time?'):
        config.set('qsub', 'name', name)
        config.set('qsub', 'cpus', cpus)
        config.set('qsub', 'time', time)
        click.echo('WRITTEN: default settings')
    
    with open(config.filename, 'w') as fd:
        config.write(fd)

@main.command()
def qdel():
    config = _conf()
    job = config.get('qsub', 'job')
    config.remove_option('qsub', 'job')
    exitcode = os.system('qdel %s' % job)
    if exitcode == 0:
        click.echo(click.style('SUCCESS: Job %s successfully removed.' % job, fg='green'))
    
def isroot(dir):
    return os.path.abspath(dir) == os.path.abspath(os.path.join(dir, '..'))

def _get_template(tplname, path='.'):
    prev = os.getcwd()
    if path != None:
       os.chdir(path)

    tplpath = os.path.join('templates', tplname)

    # Base case 1 -- found
    if os.path.exists(tplpath):
       click.echo(click.style('USING: Template %s' % os.path.abspath(tplpath), fg='green'))
       template = open(tplpath).read()
    # Base case 2 -- not found
    elif not _checkproject() or isroot('.'):
       template = None
       click.echo('ERROR: Template not found.')
    # Base case 3 -- recursive case
    else:
       template = _get_template(tplname, '..')

    os.chdir(prev)
    return template

@main.command()
def minimize():
    pass

@main.command()
def compile():
    # TODO
    # Just run the command
    cmd = 'grompp_mpi_d -f eq.mdp -c start.gro -p topol.top'
    os.system(cmd)

@main.command()
def run():
    #TODO
    os.system('mdrun_mpi_d -v')

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

def _conf():
    configfile = '.gpy'
    config = SafeConfigParser()
    config.read(configfile)
    
    config.filename = configfile
    return config

    

if __name__ == '__main__':
    main()
