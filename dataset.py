import os
import pandas as pd
from tqdm import tqdm
import torch
from torchvision import transforms
from torch.utils.data import DataLoader, Dataset
from torchvision.datasets.folder import pil_loader
import re
from common import *
from utils import *
import numpy as np


class MURA_Dataset(Dataset):
    def _select_study(self, study_name):
        studydf = self._fulldf[
            list(map(lambda x: self._fulldf.path.at[x].split('/')[2] == study_name, range(self._fulldf.path.size)))
        ]
        return studydf

    def _gen_tot_cnt(self):
        self.nt = {}
        self.at = {}
        self.wt1 = {}
        self.wt0 = {}
        for name in study_names:
            studydf = self._select_study(name)
            nt = studydf.label.value_counts().iloc[0]
            at = studydf.label.value_counts().iloc[1]
            self.nt[name] = nt
            self.at[name] = at
            self.wt1[name] = (nt / (nt + at)).astype(np.float32)
            self.wt0[name] = (at / (nt + at)).astype(np.float32)

    def __init__(self, phase, study_name=None, data_dir='MURA-v1.0', transform=None):
        assert phase in phases
        if study_name:
            assert study_name in study_names

        self._fulldf = pd.read_csv(data_dir + '/' + phase + '.csv', names=['path', 'label'])
        self._fulldf.transform({'path': lambda x: x.str.replace(r'^[\w\-.\d_]+(?=/)', data_dir), 'label': lambda x: x})
        if study_name:
            self.df = self._select_study(study_name)
        else:
            self.df = self._fulldf
        self._gen_tot_cnt()
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, item):
        imgPath = self.df.iloc[item, 0]
        image = pil_loader(imgPath)
        label = self.df.iloc[item, 1]
        if self.transform:
            image = self.transform(image)
        study_name = imgPath.split('/')[2]
        metadata = {
            'study_name': study_name,
            'nt': self.nt[study_name],
            'at': self.at[study_name],
            'wt1': self.wt1[study_name],
            'wt0': self.wt0[study_name]
        }
        if label == 1:
            metadata['wt'] = metadata['wt1']
        else:
            metadata['wt'] = metadata['wt0']
        sample = {'image': image, 'label': label, 'metadata': metadata}
        return sample


def get_dataloaders(study_name=None, data_dir='MURA-v1.0', batch_size=8, shuffle=True):
    data_transforms = {
        'train': transforms.Compose([
            transforms.Resize((320, 320)),
            transforms.RandomResizedCrop(224),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(20),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ]),
        'valid': transforms.Compose([
            transforms.Resize((320, 320)),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ]),
    }
    image_datasets = {x: MURA_Dataset(x, study_name, data_dir, data_transforms[x]) for x in phases}
    dataloader = \
        {x: DataLoader(image_datasets[x], batch_size=batch_size, shuffle=shuffle, num_workers=32) for x in phases}
    dataset_sizes = {x: len(image_datasets[x]) for x in phases}
    return dataloader, dataset_sizes


def main():
    dataloaders, _ = get_dataloaders(None, batch_size=8)
    for i, data in enumerate(tqdm(dataloaders['train'])):
        j = 0


if __name__ == '__main__':
    main()