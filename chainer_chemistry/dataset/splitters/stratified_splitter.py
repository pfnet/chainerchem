import numpy
import pandas

from chainer_chemistry.dataset.splitters.base_splitter import BaseSplitter
from chainer_chemistry.datasets.numpy_tuple_dataset import NumpyTupleDataset


def _approximate_mode(class_counts, n_draws):
    n_class = len(class_counts)
    continuous = class_counts * n_draws / class_counts.sum()
    floored = numpy.floor(continuous)
    assert n_draws // n_class == floored.sum() // n_class
    n_remainder = int(n_draws - floored.sum())
    remainder = continuous - floored
    inds = numpy.argsort(remainder)[::-1]
    inds = inds[:n_remainder]
    floored[inds] += 1
    assert n_draws == floored.sum()
    return floored.astype(numpy.int)


class StratifiedSplitter(BaseSplitter):
    """Class for doing stratified data splits."""

    def _split(self, dataset, frac_train=0.8, frac_valid=0.1, frac_test=0.1,
               labels=None, **kwargs):
        numpy.testing.assert_almost_equal(frac_train + frac_valid + frac_test,
                                          1.)

        seed = kwargs.get('seed', None)
        label_axis = kwargs.get('label_axis', -1)
        task_index = kwargs.get('task_index', 0)
        n_bin = kwargs.get('n_bin', 10)
        task_type = kwargs.get('task_type', 'infer')
        if task_type not in ['classification', 'regression', 'infer']:
            raise ValueError("{} is invalid. Please use 'classification',"
                             "'regression' or 'infer'".format(task_type))

        rng = numpy.random.RandomState(seed)

        if labels is None:
            if not isinstance(dataset, NumpyTupleDataset):
                raise ValueError("Please assign label dataset.")
            labels = dataset.features[:, label_axis]

        if len(labels.shape) == 1:
            labels = labels
        else:
            labels = labels[:, task_index]

        if task_type == 'infer':
            if labels.dtype.kind == 'i':
                task_type = 'classification'
            elif labels.dtype.kind == 'f':
                task_type = 'regression'
            else:
                raise ValueError

        if task_type == 'classification':
            classes, labels = numpy.unique(labels, return_inverse=True)
        elif task_type == 'regression':
            classes = numpy.arange(n_bin)
            labels = pandas.qcut(labels, n_bin, labels=False)
        else:
            raise ValueError

        n_classes = classes.shape[0]
        n_total_valid = int(numpy.floor(frac_valid * len(dataset)))
        n_total_test = int(numpy.floor(frac_test * len(dataset)))

        class_counts = numpy.bincount(labels)
        class_indices = numpy.split(numpy.argsort(labels,
                                                  kind='mergesort'),
                                    numpy.cumsum(class_counts)[:-1])

        n_valid_samples = _approximate_mode(class_counts, n_total_valid)
        class_counts = class_counts - n_valid_samples
        n_test_samples = _approximate_mode(class_counts, n_total_test)

        train_index = []
        valid_index = []
        test_index = []

        for i in range(n_classes):
            n_valid = n_valid_samples[i]
            n_test = n_test_samples[i]

            perm = rng.permutation(len(class_indices[i]))
            class_perm_index = class_indices[i][perm]

            class_valid_index = class_perm_index[:n_valid]
            class_test_index = class_perm_index[n_valid:n_valid+n_test]
            class_train_index = class_perm_index[n_valid+n_test:]

            train_index.extend(class_train_index)
            valid_index.extend(class_valid_index)
            test_index.extend(class_test_index)

        assert n_total_valid == len(valid_index)
        assert n_total_test == len(test_index)

        return rng.permutation(train_index),\
            rng.permutation(valid_index),\
            rng.permutation(test_index),

    def train_valid_test_split(self, dataset, labels=None, label_axis=-1,
                               task_index=0, frac_train=0.8, frac_valid=0.1,
                               frac_test=0.1, converter=None,
                               return_index=True, seed=None, task_type='infer',
                               n_bin=10, **kwargs):
        """Generate indices by stratified splittting dataset into train, valid
        and test set.

        Args:
            dataset(NumpyTupleDataset, numpy.ndarray):
                Dataset.
            labels_feature_id(int):
                Dataset feature ID in NumpyTupleDataset.
            task_id(int):
                Target task number for stratification.
            seed (int):
                Random seed.
            frac_train(float):
                Fraction of dataset put into training data.
            frac_valid(float):
                Fraction of dataset put into validation data.
            converter(callable):
            return_index(bool):
                If `True`, this function returns only indexes. If `False`, this
                function returns splitted dataset.

        Returns:
            SplittedDataset(tuple):
                splitted dataset or indexes

        .. admonition:: Example
            >>> from chainer_chemistry.datasets import NumpyTupleDataset
            >>> from chainer_chemistry.dataset.splitters \
            >>>                                 import StratifiedSplitter
            >>> a = numpy.random.random((10, 10))
            >>> b = numpy.random.random((10, 8))
            >>> c = numpy.random.random((10, 1))
            >>> d = NumpyTupleDataset(a, b, c)
            >>> splitter = StratifiedSplitter()
            >>> splitter.train_valid_test_split()
            >>> train, valid, test =
                splitter.train_valid_test_split(dataset, return_index=False)
            >>> print(len(train), len(valid))
            8, 1, 1
        """

        return super(StratifiedSplitter, self)\
            .train_valid_test_split(dataset, frac_train, frac_valid, frac_test,
                                    converter, return_index, seed=seed,
                                    label_axis=label_axis, task_type=task_type,
                                    task_index=task_index, n_bin=n_bin,
                                    labels=labels, **kwargs)

    def train_valid_split(self, dataset, labels=None, label_axis=-1,
                          task_index=0, frac_train=0.9, frac_valid=0.1,
                          converter=None, return_index=True, seed=None,
                          task_type='infer', n_bin=10, **kwargs):
        """Generate indices by stratified splittting dataset into train and
        valid set.

        Args:
            dataset(NumpyTupleDataset, numpy.ndarray):
                Dataset.
            labels_feature_id(int):
                Dataset feature ID in NumpyTupleDataset.
            task_id(int):
                Target task number for stratification.
            seed (int):
                Random seed.
            frac_train(float):
                Fraction of dataset put into training data.
            frac_valid(float):
                Fraction of dataset put into validation data.
            converter(callable):
            return_index(bool):
                If `True`, this function returns only indexes. If `False`, this
                function returns splitted dataset.

        Returns:
            SplittedDataset(tuple):
                splitted dataset or indexes

        .. admonition:: Example
            >>> from chainer_chemistry.datasets import NumpyTupleDataset
            >>> from chainer_chemistry.dataset.splitters \
            >>>                                 import StratifiedSplitter
            >>> a = numpy.random.random((10, 10))
            >>> b = numpy.random.random((10, 8))
            >>> c = numpy.random.random((10, 1))
            >>> d = NumpyTupleDataset(a, b, c)
            >>> splitter = StratifiedSplitter()
            >>> splitter.train_valid_split()
            >>> train, valid =
                    splitter.train_valid_split(dataset, return_index=False)
            >>> print(len(train), len(valid))
            9, 1
        """

        return super(StratifiedSplitter, self)\
            .train_valid_split(dataset, frac_train, frac_valid, converter,
                               return_index, seed=seed, label_axis=label_axis,
                               task_type=task_type, task_index=task_index,
                               n_bin=n_bin, labels=labels, **kwargs)