class Parameters(OrderedDict):

    @classmethod
    def parse(cls, path):
        lines = open(path).readlines()

        items = []
        for l in lines:
            # Remove comments
            l = remove_comments(l, ';')
            if '=' not in l:
                continue

            values = l.strip().split('=')
            values = (values[0].strip(), values[1].strip())
            items.append(values)

        ret = cls()
        ret.nowrite = True
        ret.update(items)
        ret.nowrite = False
        ret.path = path

        ret.has_xvg = 'table.xvg' in os.listdir(os.path.dirname(path))



        return ret

    def __repr__(self):
        integrator = self['integrator']
        nsteps = self['nsteps']
        dt = self['dt']

        temperature = self['ref_t']
        pressure = self['ref_p']

        retstr = ('Parameter file (%s):\n' % self.path +
                  '  Simulation using -%s- integrator\n' % integrator +
                  '  %s steps (%s fs). Total: %.2f ns\n' % (nsteps, dt, int(nsteps)*float(dt)/1000) +
                  '  T = %s K\n' % temperature +
                  '  P = %s bar\n' % pressure)

        return retstr

    def copy_to(self, newpath):
        newinst = Parameters()
        newinst.nowrite = True
        newinst.update(self)
        newinst.nowrite = False
        newinst.path = newpath
        newinst.write()

        src_dir = os.path.dirname(self.path)
        dst_dir = os.path.dirname(newpath)

        jn = os.path.join
        if self.has_xvg:
            shutil.copy(jn(src_dir, 'table.xvg'), jn(dst_dir, 'table.xvg'))

        return newinst

    def write(self):
        with open(self.path, 'w') as fd:
            fd.write('\n'.join(' = '.join(pair) for pair in self.items()))

    def __setitem__(self, name, value):
        super(Parameters, self).__setitem__(name, str(value))
        if not self.nowrite:
            self.write()

    def set_time(self, time, timestep, unit='ps'):
        self['dt'] = str(timestep)
        self['nsteps'] = int(time / timestep)
