def hasextension(path, ext):
    return os.path.splitext(path)[-1] == ext


def most_recent(path, ext, penalize=None):
    files = os.listdir(path)
    extfiles = [f for f in files if hasextension(f, ext)]


    if len(extfiles) == 0:
        raise ValueError('No files with extension ' + ext)
    else:
        candidates = sorted(extfiles, key=lambda x: os.path.getctime(os.path.join(path, x)))
        candidates = deque(candidates)


        if candidates[0] == penalize:
            candidates.rotate(-1)
        # print("Multiple files with the %s extension. Getting the most recent %s" % (ext, recent))
        return candidates[0]

def indent(lines, amount, ch=' '):
    padding = amount * ch
    return padding + ('\n'+padding).join(lines.split('\n'))

def remove_comments(string, delimiter):
    return re.sub(delimiter + '.*$', '', string)
