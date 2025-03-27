"""Operator base class definition.

Define supported functions for operators, and define metaclass for registering
operator classes.

Typical usage example:

    class NewOperator(Operator):
        @classmethod
        @override
        def accept(cls, data_type: DataType, task_type: TaskType) -> bool:
            return data_type == DataType.PYTHON and 
                task_type == TaskType.PREPROCESSING

        @classmethod
        @override
        def get_config(cls) -> list[Field]:
            return [
                Field('field1', Field.FieldType.STRING, 'Description of field1',
                    'default_value1'),
                Field('field2', Field.FieldType.NUMBER, 'Description of field2',
                    0),
            ]

        def __init__(self, field1: str, field2: int):
            self.field1 = field1
            self.field2 = field2

        @override
        def execute(self, in_dataset: Dataset, out_dataset: Dataset) -> None:
            # Do something with in_dataset and write to out_dataset
            pass
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..storage.dataset import Dataset, DataType
from ..task.task_type import TaskType


class OperatorMeta(type):
    """Metaclass for registering operator classes.
    """
    _registry = {}

    def __new__(mcs, name, bases, class_dict):
        new_class = super().__new__(mcs, name, bases, class_dict)
        if name != 'Operator':
            mcs._registry[name] = new_class
        return new_class

    @classmethod
    def get_registry(mcs):
        return mcs._registry


@dataclass
class Field():
    """Field metadata of the operator configuration.
    """

    class FieldType(Enum):
        STRING = 'string'
        NUMBER = 'number'
        BOOL = 'bool'
        FILE = 'file'

    # Unique name of the field.
    id: str
    # Type of the field.
    type: FieldType
    # Description of the field.
    description: str
    # Default value of the field.
    default: Any


@dataclass
class Meta():
    """Metadata of the operator.
    """

    # Name of the operator.
    name: str
    # Description of the operator.
    description: str


class Operator(metaclass=OperatorMeta):
    """Operator is the base class for all operators.
    """

    @classmethod
    def accept(cls, data_type: DataType, task_type: TaskType) -> bool:
        """Check if the operator can accept the data type and task type.

        Args:
            data_type (DataType): The data type.
            task_type (TaskType): The task type.

        Returns:
            True if the operator can accept the data type and task type.
        """
        raise NotImplementedError

    @classmethod
    def get_config(cls) -> list[Field]:
        """Get the metadata of configuration fields of the operator.

        Assist the user in constructing a dictionary with field.id as the key
        and the specified value as the value, which is used to initialize the
        operator instance.
        """
        raise NotImplementedError

    @classmethod
    def get_meta(cls) -> Meta:
        """Get the metadata of the operator.

        Returns:
            Meta: The metadata of the operator.
        """
        raise NotImplementedError


    def execute(self, in_dataset: Dataset, out_dataset: Dataset) -> None:
        """Execute the operator with the given input and output datasets.

        This method processes the input dataset and produces the output dataset
        with instance configuration.

        Args:
            in_dataset (Dataset): The input dataset.
            out_dataset (Dataset): The output dataset.
        """
        raise NotImplementedError
