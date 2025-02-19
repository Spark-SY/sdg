"""PoC code to demonstrate the usage of the data_operator package.
"""

from data_operator.operator import Operator, OperatorMeta
import data_operator
from dataset import Dataset, DataType
from task import Task, TaskType
import copy
import shutil
import pprint

registry = OperatorMeta.get_registry()


def get_operators(data_type, task_type) -> list[Operator]:
    operators: list[Operator] = []
    for clas_name, cls in registry.items():
        if cls.accept(data_type, task_type):
            operators.append(clas_name)
    return operators


def describe_operator(name):
    operator: Operator = registry[name]
    print('operator name: ', name)
    pprint.pprint(operator.get_config())
    print('\n')


if __name__ == '__main__':
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
    print('Evaludatin operator----------------------------------------------')
    evaluation_operators = get_operators(DataType.PYTHON, TaskType.EVALUATION)
    for operator_name in evaluation_operators:
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
                    '/Users/hongbin/Workspace/sdg/data/sample-preprocessing')

    preprocessing_task = Task([registry['PythonFormattingOperator']()],
                              TaskType.PREPROCESSING, DataType.PYTHON,
                              raw_dataset)
    preprocessing_task.run()
    if preprocessing_task.final_dataset is not None:
        shutil.move(preprocessing_task.final_dataset.base_path,
                    '/Users/hongbin/Workspace/sdg/data/preprocessing')

    dataset = Dataset('preprocessing', DataType.PYTHON)
    augmentation_task = Task([
        registry['PythonReorderOperator'](),
        registry['PythonDocstringInsertOperator']()
    ], TaskType.AUGMENTATION, DataType.PYTHON, dataset)
    augmentation_task.run()
    if augmentation_task.final_dataset is not None:
        shutil.move(augmentation_task.final_dataset.base_path,
                    '/Users/hongbin/Workspace/sdg/data/augmentation')

    dataset = Dataset('augmentation', DataType.PYTHON)
    evaluation_task = Task([registry['PythonValidationOperator']()],
                           TaskType.EVALUATION, DataType.PYTHON, dataset)
    evaluation_task.run()
