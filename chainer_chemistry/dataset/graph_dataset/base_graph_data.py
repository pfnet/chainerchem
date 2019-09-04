

class BaseGraphData(object):
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class PaddingGraphData(BaseGraphData):
    def __init__(self, x=None, adj=None, super_node=None, pos=None, y=None,
                 **kwargs):
        self.x = x
        self.adj = adj
        self.super_node = super_node
        self.pos = pos
        self.y = y
        super(PaddingGraphData, self).__init__(**kwargs)


class SparseGraphData(BaseGraphData):
    def __init__(self, x=None, edge_index=None, edge_attr=None,
                 pos=None, super_node=None, y=None, **kwargs):
        self.x = x
        self.edge_index = edge_index
        self.edge_attr = edge_attr
        self.pos = pos
        self.super_node = super_node
        self.y = y
        super(SparseGraphData, self).__init__()