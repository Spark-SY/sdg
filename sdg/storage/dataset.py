"""This module provides the Dataset class to manage the dataset.

Typical usage example:

    dataset = Dataset('path/to/dataset', DataType.PYTHON)
"""

import os
import random
from enum import Enum


class DataType(Enum):
    """Available data types."""
    PYTHON = 'python'


class Dataset:
    """A dataset is a collection of files.

    Attributes:
        base_path: A string representing the base path of the dataset.
        file_paths: A list of strings representing the paths of the files in 
        the dataset.
        type: A DataType representing the type of the dataset.
        _index: An integer representing the index of the current file.
    """

    root: str = './data'

    def __init__(self, path: str, data_type: DataType):
        """Initializes the dataset with the given path and type.

        Args:
            path: A string representing the path of the dataset.
            data_type: A DataType representing the type of the dataset
        """
        self.base_path = self.root + '/' + path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
        self.file_paths: list[str] = self._collect_file_paths(self.base_path)
        self.data_type: DataType = data_type
        self._index: int = 0

    def _collect_file_paths(self, path: str) -> list[str]:
        """Collects the paths of the files in the given path.
        
        Args:
            path: A string representing the path to collect the files.

        Returns:
            A list of strings representing the paths of the files in the given
             path.
        """
        file_paths: list[str] = []
        if os.path.isfile(path):
            file_paths.append(path)
        else:
            for root, _, files in os.walk(path):
                for file in files:
                    file_paths.append(os.path.join(root, file))
        return file_paths

    def __iter__(self):
        """Returns the iterator object."""
        self._index = 0
        return self

    def __next__(self) -> tuple[str, bytes]:
        """Returns the next file name and bytes data in the dataset."""
        if self._index < len(self.file_paths):
            file_path: str = self.file_paths[self._index]
            self._index += 1
            with open(file_path, 'rb') as f:
                return os.path.basename(file_path), f.read()
        raise StopIteration

    def __len__(self) -> int:
        """Returns the size of dataset."""
        return len(self.file_paths)

    def sample(self, size: int) -> None:
        """Samples the dataset with the given size.

        Would effect the current dataset.
        
        Args:
            size: An integer representing the size of the sample.
        """
        self.file_paths = random.sample(self.file_paths, size)

    def read(self, name: str) -> bytes:
        """Reads the file with the given name.

        Args:
            name: A string representing the name of the file to read.

        Returns:
            A bytes object representing the data of the file.
        """
        with open(self.base_path + '/' + name, 'rb') as f:
            return f.read()

    def write(self, name: str, data: bytes) -> None:
        """Writes the data to the file with the given name.
        
        Args:
            name: A string representing the name of the file to write.
            data: A bytes object representing the data to write.
        """
        with open(self.base_path + '/' + name, 'wb') as f:
            f.write(data)
        self.file_paths.append(self.base_path + '/' + name)
