class Shelf(object):

    def __init__(self, path):
        '''Accepts a directory name to store the settings'''
        self.path = path

        if not os.path.exists(path):
            os.mkdir(path)

        self.supported_extensions = ['.npy', '.json']

    def __setitem__(self, key, value):
        basefile = os.path.join(self.path, key)

        if isinstance(value, np.ndarray):
            np.save(basefile, value)

        if isinstance(value, pd.DataFrame):
            value.to_json(basefile + '.json')

    def __getitem__(self, key):
        match = self._map_key_file(key)

        if match.endswith('.npy'):
            return np.load(os.path.join(self.path, match))

        if match.endswith('.json'):
            return pd.read_json(os.path.join(self.path, match))

    def _map_key_file(self, key):
        basefile = os.path.join(self.path, key)
        if not key in self.keys():
            raise KeyError()

        basename = os.path.basename
        splitext = os.path.splitext

        matches = [f for f in self.stored_files()
                     if splitext(basename(f))[0].endswith(key)]
        match = matches[0]
        return match

    def stored_files(self):
        return [f for f in os.listdir(self.path)
                   if f.endswith(tuple(self.supported_extensions))]
    def keys(self):
        files = self.stored_files()
        bn = os.path.basename
        sp = os.path.splitext
        return [sp(bn(f))[0] for f in files]

    def __repr__(self):
        return ('Extra data stored:\n  ' +
                '\n  '.join(self.keys()))
