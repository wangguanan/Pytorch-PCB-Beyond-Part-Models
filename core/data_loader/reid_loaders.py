import sys
sys.path.append('../')

from .dataset import *
from .loader import *

import torchvision.transforms as transforms
from tools import *


class ReIDLoaders:

    def __init__(self, config):

        # loaders
        transform_train = [
            MisAlgnAug(crop_prob=0.5, ratio=config.mis_align_ratio),
            transforms.Resize(config.image_size, interpolation=3),
            transforms.RandomHorizontalFlip(),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])]
        if config.use_rea:
            transform_train.append(RandomErasing(probability=0.5, mean=[0.485, 0.456, 0.406]))
        self.transform_train = transforms.Compose(transform_train)

        self.transform_test = transforms.Compose([
            transforms.Resize(config.image_size, interpolation=3),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])])


        self.datasets = ['market', 'duke']

        # dataset
        self.market_path = config.market_path
        self.duke_path = config.duke_path
        self.train_dataset = config.train_dataset
        self.test_dataset = config.test_dataset
        assert self.train_dataset in self.datasets

        # batch size
        self.p = config.p
        self.k = config.k

        # dataset paths
        self.samples_path = {
            'market_train': os.path.join(self.market_path, 'bounding_box_train/'),
            'duke_train': os.path.join(self.duke_path, 'bounding_box_train/'),
            'market_test_query': os.path.join(self.market_path, 'query/'),
            'market_test_gallery': os.path.join(self.market_path, 'bounding_box_test/'),
            'duke_test_query': os.path.join(self.duke_path, 'query/'),
            'duke_test_gallery': os.path.join(self.duke_path, 'bounding_box_test/')}

        # load
        self._load()


    def _load(self):

        '''init train dataset'''
        train_samples = self._get_train_samples(self.train_dataset+'_train')
        self.train_iter = self._get_uniform_iter(train_samples, self.transform_train, self.p, self.k)

        '''init test dataset'''
        if self.test_dataset == 'market':
            self.market_query_samples, self.market_gallery_samples = self._get_test_samples('market_test')
            self.market_query_loader = self._get_loader(self.market_query_samples, self.transform_test, 128)
            self.market_gallery_loader = self._get_loader(self.market_gallery_samples, self.transform_test, 128)
        elif self.test_dataset == 'duke':
            self.duke_query_samples, self.duke_gallery_samples = self._get_test_samples('duke_test')
            self.duke_query_loader = self._get_loader(self.duke_query_samples, self.transform_test, 128)
            self.duke_gallery_loader = self._get_loader(self.duke_gallery_samples, self.transform_test, 128)


    def _get_train_samples(self, train_dataset):

        train_samples_path = self.samples_path[train_dataset]
        if train_dataset == 'market_train':
            samples = Samples4Market(train_samples_path)
        elif train_dataset == 'duke_train':
            samples = Samples4Duke(train_samples_path)

        return samples


    def _get_test_samples(self, test_dataset):

        query_data_path = self.samples_path[test_dataset + '_query']
        gallery_data_path = self.samples_path[test_dataset + '_gallery']

        if test_dataset == 'market_test':
            query_samples = Samples4Market(query_data_path, reorder=False)
            gallery_samples = Samples4Market(gallery_data_path, reorder=False)
        elif test_dataset == 'duke_test':
            query_samples = Samples4Duke(query_data_path, reorder=False)
            gallery_samples = Samples4Duke(gallery_data_path, reorder=False)

        return query_samples, gallery_samples


    def _get_uniform_iter(self, samples, transform, p, k):
        '''
        load person reid data_loader from images_folder
        and uniformly sample according to class
        :param images_folder_path:
        :param transform:
        :param p:
        :param k:
        :return:
        '''
        dataset = PersonReIDDataSet(samples.samples, transform=transform)
        loader = data.DataLoader(dataset, batch_size=p * k, num_workers=8, drop_last=False, sampler=ClassUniformlySampler(dataset, class_position=1, k=k))
        iters = IterLoader(loader)

        return iters


    def _get_random_iter(self, samples, transform, batch_size):

        dataset = PersonReIDDataSet(samples.samples, transform=transform)
        loader = data.DataLoader(dataset, batch_size=batch_size, num_workers=8, drop_last=False, shuffle=True)
        iters = IterLoader(loader)

        return iters


    def _get_random_loader(self, samples, transform, batch_size):

        dataset = PersonReIDDataSet(samples.samples, transform=transform)
        loader = data.DataLoader(dataset, batch_size=batch_size, num_workers=8, drop_last=False, shuffle=True)
        return loader


    def _get_loader(self, samples, transform, batch_size):

        dataset = PersonReIDDataSet(samples.samples, transform=transform)
        loader = data.DataLoader(dataset, batch_size=batch_size, num_workers=8, drop_last=False, shuffle=False)
        return loader

