from enum import Enum

class TaskType(Enum):
    """Represents the type of task to be executed.
    """
    PREPROCESSING = 'preprocessing'
    AUGMENTATION = 'augmentation'