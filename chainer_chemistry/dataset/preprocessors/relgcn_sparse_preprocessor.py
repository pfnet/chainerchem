import numpy
from chainer_chemistry.dataset.preprocessors.ggnn_preprocessor \
    import GGNNPreprocessor
from chainer_chemistry.dataset.graph_dataset.base_graph_data \
    import SparseGraphData
from chainer_chemistry.dataset.graph_dataset.base_graph_dataset \
    import SparseGraphDataset


class RelGCNSparsePreprocessor(GGNNPreprocessor):
    """RelGCNSParse Preprocessor

    Args:
        max_atoms (int): Max number of atoms for each molecule, if the
            number of atoms is more than this value, this data is simply
            ignored.
            Setting negative value indicates no limit for max atoms.
        out_size (int): It specifies the size of array returned by
            `get_input_features`.
            If the number of atoms in the molecule is less than this value,
            the returned arrays is padded to have fixed size.
            Setting negative value indicates do not pad returned array.
        add_Hs (bool): If True, implicit Hs are added.
        kekulize (bool): If True, Kekulizes the molecule.

    """

    def __init__(self, max_atoms=-1, out_size=-1, add_Hs=False,
                 kekulize=False):
        super(RelGCNSparsePreprocessor, self).__init__(
            max_atoms=max_atoms, out_size=out_size, add_Hs=add_Hs,
            kekulize=kekulize)

    def construct_sparse_data(self, x, adj, y):
        edge_index = [[], []]
        edge_attr = []
        label_num, n, _ = adj.shape
        for label in range(label_num):
            for i in range(n):
                for j in range(n):
                    if adj[label, i, j] != 0.:
                        edge_index[0].append(i)
                        edge_index[1].append(i)
                        edge_attr.append(label)
        return SparseGraphData(
            x=x,
            edge_index=numpy.array(edge_index, dtype=numpy.int),
            edge_attr=numpy.array(edge_attr, dtype=numpy.int),
            y=y
        )

    def create_dataset(self, *args, **kwargs):
        # args: (atom_array, adj_array, label_array)
        data_list = [
            self.construct_sparse_data(x, adj, y) for (x, adj, y) in zip(*args)
        ]
        return SparseGraphDataset(data_list)