import click
import os
import glob
import shutil
import subprocess
import imp

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
@click.option('--genonly', is_flag=True)
def submit(name, time, cpus, email, genonly):

    if not _checkproject():
        return

    template = _get_template('qsub.tpl')
    config = _conf()

    if template is None:
        return

    if email is None:
        email = _get_conf('email')

    if not config.has_section('qsub') and not all([time, cpus, name]):
        click.echo('ERROR: No qsub configuration found:')
        click.echo('Please provide options --time --cpus --name')
        return

    time = time if time is not None else config.get('qsub', 'time')
    name = name if name is not None else config.get('qsub', 'name')
    cpus = cpus if cpus is not None else config.get('qsub', 'cpus')

    render = template.format(name=name, time=time, cpus=cpus, email=email)
    with open('sub.pbs', 'w') as fd:
        fd.write(render)

    click.echo('WRITTEN: sub.pbs')
    click.echo('USING: time=%s | name=%s | cpus=%s' % (time, name, cpus))

    if not config.has_section('qsub'):
        config.add_section('qsub')

    config.set('qsub', 'time', time)
    config.set('qsub', 'name', name)
    config.set('qsub', 'cpus', cpus)

    if not genonly:
        ret = subprocess.check_output(['qsub', 'sub.pbs'])
        click.echo('INFO: Created job %s' % ret)
        config.set('qsub', 'job', ret)
    else:
        click.echo('INFO: Job not submitted')

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

@main.command()
@click.argument('path', required=False)
@click.option('--host', '-h')
@click.option('--user', '-u')
@click.option('--password', '-p')
def download(path, host, user, password):
    '''Download a GROMACS project via SSH'''
    from .ssh import SSHSession

    sub = True
    if path == None:
        sub = False
        if _checkproject(True):
            config = _conf()
            path = config.get('main', 'remote')
        else:
            click.echo('ERROR: path argument is required.')
            return


    # Connect
    host = host or _get_conf('host')
    u = user or _get_conf('user')
    p = password or _get_conf('password')

    sess = SSHSession(host, username=u, password=p)
    def cb(dir, file):
        click.echo('DOWNLOADING: %s' % file)

    outpath = '.' if sub else '..'
    sess.get_all(path, outpath, callback=cb)

    if sub:
        prev = os.getcwd()
        os.chdir(os.path.basename(path))

    config = _conf()
    if not config.has_section('main'):
        config.add_section('main')
    config.set('main', 'remote', path)
    config.write(open(config.filename, 'w'))

    click.echo('DONE')

    if sub:
        os.chdir(prev)

@main.command()
def status():
    from logfile import Logfile

    if not _checkproject():
        return

    # Read the logfile
    if not os.path.exists('md.log'):
        click.echo('No logfile found')
    else:
        lf = Logfile.parse('md.log')
        click.echo(repr(lf))

@main.command()
def shell():
    '''Open a shell in the remote directory'''
    if not _checkproject():
        return

    config = _conf()
    path = config.get('main', 'remote')
    host = _get_conf('host')
    u = _get_conf('user')
    p = _get_conf('password')

    if not all([host, u, p, path]):
        click.echo('ERROR: remote, host, user, password configurations required.')
        return
    os.system('ssh -t {}@{} "cd {} && bash"'.format(u, host, path))


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

@main.group()
def remote():
    pass

@remote.command()
@click.option('--host', '-h')
@click.option('--user', '-u')
@click.option('--password', '-p')
def qstat(host, user, password):
    '''Download a GROMACS project via SSH'''
    from .ssh import SSHSession
    import paramiko

    # Connect
    host = host or _get_conf('host')
    u = user or _get_conf('user')
    p = password or _get_conf('password')
    s = paramiko.SSHClient()
    s.load_system_host_keys()
    s.connect(host, 22, u, p)
    command = 'qstat -u %s' % u
    (stdin, stdout, stderr) = s.exec_command(command)
    for line in stdout.readlines():
        click.echo(click.style(line, bg='black'), nl=False)
    for line in stderr.readlines():
        click.echo(click.style(line, fg='yellow'), nl=False)
    click.echo('')
    s.close()


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

@main.command()
@click.argument('names', nargs=-1)
@click.option('-l', is_flag=True)
def script(names, l):
    """Run script"""

    fail = False
    funcs = []

    if l:
        for f in _find_avail_files('scripts'):
            if f.endswith('.py'):
                modname = os.path.splitext(os.path.basename(f))[0]
                click.echo(click.style('Module name: %s' % modname, fg='green'))
                _disp_commands(f)
        return

    for name in names:
        if ':' in name:
            mod, function = name.split(':')
        else:
            mod = name
            function = None

        path = _find_file_parent('scripts/%s.py' % mod)

        if path == None:
            return

        if function == None: # Run normally
            click.echo('Running the module %s' % mod)
            os.system('python %s' % path)
        else:
            module = imp.load_source(mod, path)
            # call function
            try:
                func = getattr(module, function)
                funcs.append(func)
            except AttributeError:
                click.echo(
                  click.style('Function "%s" not present in file %s' %
                              (function, path), fg='red'))
                _disp_commands(path)
                fail = True
    if not fail:
        [func() for func in funcs]

def _disp_commands(pyfile):
    mod = os.path.splitext(os.path.basename(pyfile))[0]
    module = imp.load_source(mod, pyfile)
    click.echo(click.style('Functions available', bold=True))
    if hasattr(module, '__all__'):
        [click.echo(click.style(fun, fg='yellow')) for fun in module.__all__]
    else:
        [click.echo(click.style(fun, fg='yellow'))
        for fun in dir(module)
        if not fun.startswith('_')]

@main.command()
@click.option('--deep', '-d', is_flag=True)
@click.option('--preview', '-p', is_flag=True)
def clean(deep, preview):
    patterns = ['#*']
    if deep:
        patterns.extend(['traj.xtc', 'traj.trr', 'topol.tpr', 'md.log', 'state*.cpt', 'state.trr'])

    torm = sum((glob.glob(pattern) for pattern in patterns), [])
    if preview:
        click.echo('INFO: The following files can be removed:')
        click.echo(' '.join(torm))
    else:
        click.echo('REMOVING: ' + ' '.join(torm))
    	[os.remove(file) for file in torm]

def _checkproject(mute=False):
    if not os.path.exists('.gpy'):
        if not mute:
            click.echo(click.style("ERROR: You are not in a gpy project.", fg='red'))
        return False
    return True

def _get_conf(key):
    configfile = os.path.expanduser('~/.gypconf')

    config = SafeConfigParser()
    config.read(configfile)

    return config.get('main', key)

def _find_file_parent(filename, path=None):
    '''Recurse up to find the filename'''
    prev = os.getcwd()
    if path != None:
       os.chdir(path)

    # Base case 1 -- found
    if os.path.exists(filename):
        path_abs = os.path.abspath(filename)
        click.echo(click.style('USING: File %s' % path_abs, fg='green'))
    # Base case 2 -- not found
    elif not _checkproject(mute=True) or isroot('.'):
        path_abs = None
        click.echo('ERROR: File not found. Search stopped at: %s' % prev)
    # Base case 3 -- recursive case
    else:
        path_abs = _find_file_parent(filename, '..')

    os.chdir(prev)
    return path_abs

def _find_avail_files(dirname, path=None):
    prev = os.getcwd()
    if path != None:
       os.chdir(path)

    # Base case 1 -- found
    if os.path.exists(dirname):
        paths = [os.path.abspath(os.path.join(dirname, f)) for f in os.listdir(dirname)]
        paths += _find_avail_files(dirname, '..')
    # Base case 2 -- not found
    elif not _checkproject(mute=True) or isroot('.'):
        paths = []
        click.echo('ERROR: File not found. Search stopped at: %s' % prev)
    # Base case 3 -- recursive case
    else:
        paths = _find_avail_files(dirname, '..')

    os.chdir(prev)
    return paths

def _conf():
    configfile = '.gpy'
    config = SafeConfigParser()
    config.read(configfile)

    config.filename = configfile
    return config


cli = main
if __name__ == '__main__':
    cli()
