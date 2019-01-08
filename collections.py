class Group:
    def __init__(self, name):
        self.name = name
        self.sprites = []

    def __repr__(self):
        n = self.name
        m = len(self.sprites)

        return "Group: {} ({} members)".format(n, m)

    def empty(self):
        self.sprites = []

    def add_member(self, member):
        if member not in self.sprites:
            self.sprites.append(member)

    def __getitem__(self, key):
        return self.sprites.__getitem__(key)

    def __len__(self):
        return len(self.sprites)

    def __setitem__(self, key, value):
        return self.sprites.__setitem__(key, value)

    def __delitem__(self, key):
        return self.sprites.__delitem__(key)

    def __iter__(self):
        return self.sprites.__iter__()

    def __contains__(self, item):
        return self.sprites.__contains__(item)


class CacheList(list):
    def __init__(self, size):
        super(CacheList, self).__init__()
        self._size = size

    def set_size(self):
        if len(self) > self._size:
            for i in range(len(self) - 1):
                self[i] = self[i + 1]
            self.pop()

    def append(self, p_object):
        super(CacheList, self).append(p_object)
        self.set_size()

    def __iadd__(self, other):
        for item in other:
            self.append(item)

        return self

    def average(self):
        if not self:
            return []

        if type(self[0]) in (int, float):
            return sum(self) / len(self)

        else:
            lhs = [i[0] for i in self]
            rhs = [i[1] for i in self]

            return (sum(lhs) / len(lhs)), (sum(rhs) / len(rhs))

    def changes(self, maximum):
        changes = []
        last = None
        for item in self:
            if item != last:
                last = item
                changes.append(item)

        if len(self) > maximum:
            return changes[-maximum:]

        else:
            return changes
