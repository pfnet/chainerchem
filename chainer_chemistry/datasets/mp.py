import os
import json
import pickle
import ast
import numpy as np
import pandas as pd


import chainer
import h5py
from tqdm import tqdm
from pymatgen.core.structure import Structure


class MPDataset(chainer.dataset.DatasetMixin):
    """
    """

    def __init__(self):
        """
        """
        self.id_prop_data = None
        self.data = None
        self.mpid = []


    def __len__(self):
        """
        """
        return len(self.data)


    def save_pickle(self, path):
        """
        """
        print("saving dataset into {}".format(path))
        with open(path, "wb") as file_:
            pickle.dump(self.data, file_)


    def load_pickle(self, path):
        """
        """
        print("loading dataset from {}".format(path))
        if os.path.exists(path) is False:
            print("Fail.")
            return False
        with open(path, "rb") as file_:
            self.data = pickle.load(file_)

        return True


    def _load_data_list(self, data_dir, target_list, is_stable=True):
        """Collect the label
        """
        # TODO: data_dirは今後はURLを指すようになる
        # load csv
        id_prop_data = pd.read_csv(os.path.join(data_dir, "property_data.csv"), index_col=0)
        stability_data = pd.read_csv(os.path.join(data_dir, "stability_data.csv"),
                                     index_col=0, converters={3: ast.literal_eval})

        id_prop_data = id_prop_data.merge(stability_data, on="material_id")
        # drop data which has warnings
        if is_stable:
            n_warns = np.array([len(d) for d in id_prop_data["warnings"]])
            mask = n_warns == 0
            id_prop_data = id_prop_data[mask]

        # TODO: why??
        # drop data which doesn't have fermi energy data
        id_prop_data = id_prop_data[~np.isnan(id_prop_data["efermi"].values)]

        if "band_gap" in target_list:
            id_prop_data = id_prop_data[id_prop_data["band_gap"].values > 0]

        if "K_VRH" in target_list or "G_VRH" in target_list or "poisson_ratio" in target_list:
            # TODO: why more than 1 ??
            id_prop_data = id_prop_data[id_prop_data["K_VRH"] >= 1]
            id_prop_data = id_prop_data[id_prop_data["G_VRH"] >= 1]

        self.id_prop_data = id_prop_data


    def get_mp(self, data_dir, target_list, preprocessor=None, num_data=None, is_stable=True):
        """Downloads, caches and preprocesses Material Project dataset.
     
         Args:
             preprocessor (BasePreprocessor): 
             labels (str or list): List of target labels.
             return_mpid (bool): If set to ``True``,
                 mp-id array is also returned.
     
         Returns:
             dataset, which is composed of `features`, which depends on
             `preprocess_method`.
     
        """
        print("loading mp dataset from {}".format(data_dir))
        # TODO: is_stableは外で受け取る
        self._load_data_list(data_dir, target_list, is_stable)
    
        # TODO: data_dirはURLを指すようにする
        cif_data = h5py.File(os.path.join(data_dir, "cif_data.h5"), "r")
    
        data = self.id_prop_data
        if num_data is not None and num_data >=0:
            data = data[0:num_data]
    
    
        self.data = list()
        data_length = len(data)
        for i in tqdm(range(data_length)):
            # get crystal object from CIF
            properties = self.id_prop_data.iloc[i]
            cif_id = properties["material_id"] + ".cif"
            if cif_id not in cif_data:
                continue
            crystal = Structure.from_str(cif_data[cif_id].value, "yaml")
    
            # prepare lebel
            target = properties[target_list].astype(np.float32)
            if np.isnan(target).any():
                continue
            # convert unit into /atom
            if "energy" in target:
                n_atom = crystal.num_sites
                target["energy"] = target["energy"] / n_atom
            # convert to log10
            if "K_VRH" in target:
                target["K_VRH"] = np.log10(target["K_VRH"])
            # convert to log10
            if "G_VRH" in target:
                target["G_VRH"] = np.log10(target["G_VRH"])
    
            # get input feature from crystal object
            features = preprocessor.get_input_feature(crystal)
            self.data.append((*features, target))
            self.mpid.append(properties["material_id"])

        return True


    def get_example(self, i):
        atom_feat = self.data[i][0]
        nbr_feat = self.data[i][1]
        global_feat = self.data[i][2]
        atom_num = self.data[i][3]
        bond_num = self.data[i][4]
        bond_idx = self.data[i][5]
        target = self.data[i][6]
        return atom_feat, nbr_feat, global_feat, atom_num, bond_num, bond_idx, target
        # return *data
