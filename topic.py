import hashlib
from topicset import TopicsSet


class Topic:
    def __init__(self, name):
        self.name = name.strip()
        self.children = TopicsSet()

    def __str__(self):
        str = self.name + '\n'
        for child in self.children:
            str += '\t%s\n' % child.name
        return str

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return int(hashlib.md5(self.name).hexdigest(), 16)

    def add_topic(self, name):
        self.children.add(Topic(name))

    def get_children_count(self):
        return len(self.children) + sum([item.get_children_count() for item in self.children])

