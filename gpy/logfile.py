import datetime
import bisect

class Logfile(object):

    @classmethod
    def parse(cls, path):
        ret = Logfile()
        lines = open(path).readlines()

        steps = []
        times = []
        timestamps = []

        for i, l in enumerate(lines):
            if 'Step' in l and 'Time' in l:
                try:
                    s, t, lamb = lines[i + 1].split()
                    steps.append(int(s))
                    times.append(float(t))
                except ValueError: # A parsing mistake
                    print 'SKIP: Parsing line "%s"' % lines[i + 1].rstrip()

            if l.startswith('Writing checkpoint'):
                splitted = l.split()
                step = int(splitted[splitted.index('step') + 1])
                datestr = l.split(' at ')[1].strip()
                ts = datetime.datetime.strptime(datestr, '%a %b %d %X %Y')
                timestamps.append((step, ts))

        ret.path = path
        ret.steps = steps
        ret.times = times
        ret.timestamps = timestamps
        return ret

    def __repr__(self):
        if len(self.timestamps) < 10:
            return 'Log file (%s)\n'
        
        t2_ix = bisect.bisect(self.steps, self.timestamps[-1][0])
        t2 = self.times[t2_ix - 1]
        t1_ix = bisect.bisect(self.steps, self.timestamps[-10][0])
        t1 = self.times[t1_ix - 1]

        seconds = (self.timestamps[-1][1] - self.timestamps[-10][1]).total_seconds()
        speed = ((t2 - t1)/1000) / (seconds / 86400.0)
        return ('Log file (%s) \n' % self.path +
                '  Calculation run for %.2f ns\n  Current speed %.2f ns/day\n' % (self.times[-1]/1000, speed))
