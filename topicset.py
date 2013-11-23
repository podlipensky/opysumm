class TopicsSet(set):
    def getelement(self, item):
        for i in self:
            if i == item: return i

    def get_count(self):
        return len(self) + sum([item.get_children_count() for item in self])

