"""PoC code to demonstrate the usage of the data_operator package.
"""

import copy
import shutil
import pprint

from .data_operator.operator import Meta, Operator, OperatorMeta
from . import data_operator
from .storage.dataset import Dataset, DataType
from .task.task_type import TaskType
from .task.task import Task


registry = OperatorMeta.get_registry()


def get_operators(data_type, task_type) -> list[Operator]:
    operators: list[Operator] = []
    for clas_name, cls in registry.items():
        if cls.accept(data_type, task_type):
            operators.append(clas_name)
    return operators


def describe_operator(name):
    operator: Operator = registry[name]
    meta: Meta = operator.get_meta()
    print('operator name: ', meta.name)
    print('operator description: ', meta.description)
    pprint.pprint(operator.get_config())
    print('\n')


def poc():
    print('Preprocessing operator----------------------------------------------')
    preprocessing_operators = get_operators(DataType.PYTHON,
                                            TaskType.PREPROCESSING)
    for operator_name in preprocessing_operators:
        describe_operator(operator_name)
    print('Augmentation operator----------------------------------------------')
    augmentation_operators = get_operators(DataType.PYTHON,
                                           TaskType.AUGMENTATION)
    for operator_name in augmentation_operators:
        describe_operator(operator_name)
    print('----------------------------------------------')

    raw_dataset = Dataset('raw', DataType.PYTHON)

    sample_dataset: Dataset = copy.deepcopy(raw_dataset)
    sample_dataset.sample(1)
    sample_preprocessing_task = Task([registry['PythonFormattingOperator']()],
                                     TaskType.PREPROCESSING, DataType.PYTHON,
                                     sample_dataset)
    sample_preprocessing_task.run()
    if sample_preprocessing_task.final_dataset is not None:
        shutil.move(sample_preprocessing_task.final_dataset.base_path,
                    './data/sample-preprocessing')

    preprocessing_task = Task([registry['PythonFormattingOperator']()],
                              TaskType.PREPROCESSING, DataType.PYTHON,
                              raw_dataset)
    preprocessing_task.run()
    if preprocessing_task.final_dataset is not None:
        shutil.move(preprocessing_task.final_dataset.base_path,
                    './data/preprocessing')

    dataset = Dataset('preprocessing', DataType.PYTHON)
    augmentation_task = Task([
        registry['PythonReorderOperator'](),
        registry['PythonDocstringInsertOperator']()
    ], TaskType.AUGMENTATION, DataType.PYTHON, dataset)
    augmentation_task.run()
    if augmentation_task.final_dataset is not None:
        shutil.move(augmentation_task.final_dataset.base_path,
                    './data/augmentation')

if __name__ == '__main__':
    poc()