
class Topology(object):

    @classmethod
    def parse(cls, path):
        ret = cls()
        ret.path = path
        lines = open(path).readlines()


        #lines = [remove_comments(l, '') for l in lines]
        lines = [l.strip() for l in lines if l.strip()]

        # Remove empty lines
        lines = [l for l in lines if l != '']

        sections = []
        section = None
        for l in lines:

            if l.startswith('['):
                if section is not None:
                    sections.append(section)

                section = []

            if section is not None:
                section.append(l)
        if section not in sections:
            sections.append(section)

        ret.sections = sections
        return ret

    def write(self):
        with open(self.path, 'w') as fd:
            fd.write('\n\n'.join('\n'.join(line for line in section) for section in self.sections ))

    def copy_to(self, newpath):
        new = Topology()
        new.path = newpath
        new.sections = self.sections
        new.write()
        return new

    def __repr__(self):
        return 'Topology file (%s)' % self.path
