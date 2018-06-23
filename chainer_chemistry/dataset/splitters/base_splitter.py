from chainer_chemistry.datasets import NumpyTupleDataset


class BaseSplitter(object):
    def k_fold_split(self, dataset, k):
        raise NotImplementedError

    def _split(self, dataset):
        raise NotImplementedError

    def train_valid_test_split(self, dataset, frac_train=.8, frac_valid=.1,
                               frac_test=.1, seed=None, return_index=True):
        train_inds, valid_inds, test_inds = self._split(dataset,
                                                        frac_train=frac_train,
                                                        frac_valid=frac_valid,
                                                        frac_test=frac_test)
        if return_index:
            return train_inds, valid_inds, test_inds
        else:
            if type(dataset) == NumpyTupleDataset:
                train = NumpyTupleDataset(*dataset[train_inds])
                valid = NumpyTupleDataset(*dataset[valid_inds])
                test = NumpyTupleDataset(*dataset[test_inds])
                return train, valid, test
            else:
                return dataset[train_inds], dataset[valid_inds],\
                    dataset[test_inds]

    def train_valid_split(self, dataset, frac_train=.9, frac_valid=.1,
                          seed=None, return_index=True):
        train_inds, valid_inds, test_inds = self._split(dataset,
                                                        frac_train=frac_train,
                                                        frac_valid=frac_valid,
                                                        frac_test=0)
        assert len(test_inds) == 0
        if return_index:
            return train_inds, valid_inds
        else:
            if type(dataset) == NumpyTupleDataset:
                train = NumpyTupleDataset(*dataset[train_inds])
                valid = NumpyTupleDataset(*dataset[valid_inds])
                return train, valid,
            else:
                return dataset[train_inds], dataset[valid_inds]