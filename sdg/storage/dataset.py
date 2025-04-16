from enum import Enum
from dataclasses import dataclass
import os
import shutil

from ..config import settings


class DataType(Enum):
    """Available data types."""
    PYTHON = 'python'
    IMAGE = 'image'
    AUDIO = 'audio'
    TEXT = 'text'
    VIDEO = 'video'
    TABLE = 'table'
    GRAPH = 'graph'


@dataclass
class DataEvaluation():
    # evaluation dimension key
    key: str
    # evaluation value
    value: str
    # evaluation result path
    detail_path: str
    # sub dimension evaluations
    children: list['DataEvaluation']


class Datadir:
    """A datadir is a collection of data files with the same type.

    Attributes:
        data_path (str): The path to the data dir.
        data_type (DataType): The type of the data files.
    """

    def __init__(self, data_path: str, data_type: DataType):
        self.relative_data_path = data_path
        self.data_path = settings.LOCAL_STORAGE_PATH + '/' + data_path
        self.data_type = data_type


class Dataset:
    """A dataset is a collection of datadirs.

    Note: The file format for the metadata is CSV, the header include data type(exists multi data-type if dataset 
    is multimodal data) and tags(split by |), join data_path in datadir and file name in metadata could touch the
    file.

    Examples:
    1. normal dataset
    code,tags
    1.py,tag1
    2.py,tag2|tag3
    2. multimodal dataset
    code,image,tags
    1.py,1.jpg,tag1
    1.py,2.jpg,tag1
    2.py,3.jpg,tag2
    
    
    Attributes:
        dirs (list[Datadir]): A list of datadirs.
        meta_path (str): The path to the metadata file, which connect mutlimodal data.
        evaluation (list[DataEvaluation]): A list of data evaluation result.
    """

    def __init__(self, dirs: list[Datadir], meta_path: str):
        self.dirs = dirs
        self.relative_meta_path = meta_path
        self.meta_path = settings.LOCAL_META_STORAGE_PATH + '/' + meta_path
        self.evaluation = []
    

def copy_dataset(src: Dataset, prefix: str):
    dirs: list[Datadir] = []
    for dir in src.dirs:
        relative_data_path = prefix + dir.relative_data_path
        data_type = dir.data_type
        target_dir = Datadir(relative_data_path, data_type)
        # os.mkdir(target_dir.data_path)
        shutil.copytree(dir.data_path, target_dir.data_path)
        dirs.append(target_dir)
    meta_path = prefix + src.relative_meta_path
    dataset: Dataset = Dataset(dirs, meta_path)
    shutil.copy(src.meta_path, dataset.meta_path)
    return dataset