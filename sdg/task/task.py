"""Task module.

Typical usage example:
    
    task = Task(operators, TaskType.PREPROCESSING, DataType.PYTHON, dataset)
    task.run()
    final_dataset = task.final_dataset
"""

from uuid import UUID, uuid4

from .task_type import TaskType
from ..storage.dataset import Dataset, DataType
from ..data_operator.operator import Operator


class Task:
    """Represents a task that processes a dataset through a series of operators.

    Attributes:
        operators: A list of operators to be applied to the dataset.
        task_type: The type of the task.
        data_type: The type of data being processed.
        in_dataset: The initial dataset to be processed.
        id: A unique identifier for the task.
        out_datasets: A dictionary mapping operator names to their
        output datasets.
        final_dataset: The final dataset after all operators have been 
        applied.

    """

    def __init__(self, operators: list[Operator], task_type: TaskType,
                 data_type: DataType, in_dataset: Dataset):
        """Initializes a task with the given operators, task type, data type
        and input dataset.

        Args:
            operators: A list of operators to be applied to the dataset.
            task_type: The type of the task.
            data_type: The type of data being processed.
            in_dataset: The initial dataset to be processed.
        """
        self.operators: list[Operator] = operators
        self.task_type: TaskType = task_type
        self.data_type: DataType = data_type
        self.in_dataset: Dataset = in_dataset
        self.id: UUID = uuid4()
        self.out_datasets: dict[str, Dataset] = {}
        self.final_dataset: Dataset | None = None

    def run(self) -> None:
        """Executes the task by applying the operators to the input dataset."""
        dataset: Dataset = self.in_dataset
        for operator in self.operators:
            out_dataset = Dataset(str(uuid4()), self.data_type)
            operator.execute(dataset, out_dataset)
            self.out_datasets[operator.__class__.__name__] = out_dataset
            dataset = out_dataset
        self.final_dataset = dataset
