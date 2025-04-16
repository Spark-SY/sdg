""" Operators for Python code processing.
"""

import black
import ast
import random
from typing import override
import os
import pandas as pd

from .operator import Meta
from .operator import Operator, Field
from ..storage.dataset import DataType, Dataset
from ..task.task_type import TaskType


class PythonFormattingOperator(Operator):
    """PythonFormattingOperator is an operator that formats Python code using
    the Black code formatter. 
    
    It can be used for both preprocessing andaugmentation tasks.

    Attributes:
        line_length: How many characters per line to allow.
        string_normalization: Whether to normalize string quotes or prefixes.
        magic_trailing_comma: Whether to use trailing commas.
    """

    def __init__(self, **kwargs):
        self.line_length: int = kwargs.get('line-length', 88)
        self.string_normalization: bool = not kwargs.get(
            'skip-string-normalization', False)
        self.magic_trailing_comma: bool = not kwargs.get(
            'skip-magic-trailing-comma', False)

    @classmethod
    @override
    def accept(cls, data_type, task_type) -> bool:
        if data_type == DataType.PYTHON and (
                task_type == TaskType.PREPROCESSING or
                task_type == TaskType.AUGMENTATION):
            return True
        return False

    @classmethod
    @override
    def get_config(cls) -> list[Field]:
        return [
            Field('line-length', Field.FieldType.NUMBER,
                  'How many characters per line to allow.', 88),
            Field('skip-string-normalization', Field.FieldType.BOOL,
                  'Don’t normalize string quotes or prefixes.', False),
            Field('skip-magic-trailing-comma', Field.FieldType.BOOL,
                  'Don’t use trailing commas.', False)
        ]

    @classmethod
    @override
    def get_meta(cls) -> Meta:
        return Meta(
            name='PythonFormattingOperator',
            description='Formats Python code using the Black code formatter.'
        )

    @override
    def execute(self, dataset: Dataset) -> None:
        df = pd.read_csv(dataset.meta_path)
        dir = [dir for dir in dataset.dirs if dir.data_type == DataType.PYTHON][0]
        files = df[DataType.PYTHON.value].tolist()
        for file in files:
            file_path = os.path.join(dir.data_path, file)
            with open(file_path, 'rb+') as f:
                code = f.read().decode('utf-8')
                code = self._inner_execute(code)
                f.seek(0)
                f.write(code.encode('utf-8'))
    
    def _inner_execute(self, code: str):
        code = black.format_str(
            code,
            mode=black.FileMode(
                line_length=self.line_length,
                string_normalization=self.string_normalization,
                magic_trailing_comma=self.magic_trailing_comma))
        return code


class PythonReorderOperator(Operator):
    """PythonReorderOperator is an operator that reorders the definitions of
    functions, imports, and classes in Python code. It can be used for code
    augmentation tasks.

    Attributes:
        reorder_functions: Whether to reorder function definitions.
        reorder_imports: Whether to reorder import statements.
        reorder_classes: Whether to reorder class definitions
    """

    def __init__(self, **kwargs):
        self.reorder_functions: bool = kwargs.get('reorder-functions', True)
        self.reorder_imports: bool = kwargs.get('reorder-imports', True)
        self.reorder_classes: bool = kwargs.get('reorder-classes', True)

    @classmethod
    @override
    def accept(cls, data_type, task_type) -> bool:
        if data_type == DataType.PYTHON and task_type == TaskType.AUGMENTATION:
            return True
        return False

    @classmethod
    @override
    def get_config(cls) -> list[Field]:
        return [
            Field('reorder-functions', Field.FieldType.BOOL,
                  'Reorder functions in the code.', True),
            Field('reorder-imports', Field.FieldType.BOOL,
                  'Reorder imports in the code.', True),
            Field('reorder-classes', Field.FieldType.BOOL,
                  'Reorder classes in the code.', True)
        ]

    @classmethod
    @override
    def get_meta(cls) -> Meta:
        return Meta(
            name='PythonReorderOperator',
            description='Reorders the definitions of functions, imports, and '
            'classes in Python code.'
        )

    @override
    def execute(self, dataset: Dataset) -> None:
        df = pd.read_csv(dataset.meta_path)
        dir = [dir for dir in dataset.dirs if dir.data_type == DataType.PYTHON][0]
        files = df[DataType.PYTHON.value].tolist()
        for file in files:
            file_path = os.path.join(dir.data_path, file)
            with open(file_path, 'rb+') as f:
                code = f.read().decode('utf-8')
                code = self._inner_execute(code)
                f.seek(0)
                f.write(code)

    
    def _inner_execute(self, code: str):
        tree: ast.Module = ast.parse(code)
        if self.reorder_functions:
            reorderer = FunctionReorderer()
            tree = reorderer.visit(tree)
        if self.reorder_imports:
            reorderer = ImportReorderer()
            tree = reorderer.visit(tree)
        if self.reorder_classes:
            reorderer = ClassReorderer()
            tree = reorderer.visit(tree)
        code = ast.unparse(tree)
        return code.encode('utf-8')


class FunctionReorderer(ast.NodeTransformer):
    """FunctionReorderer is an AST (Abstract Syntax Tree) transformer that
    reorders function definitions in a module or class.
    """

    @override
    def visit_Module(self, node: ast.Module) -> ast.Module:
        """Visits a module node and reorders the top-level function definitions.
        Functions that are only called after their definition (or not called at
        the top level) are shuffled, while others retain their original order.
        """
        self.generic_visit(node)
        calls_positions = {}
        func_positions = {}

        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.FunctionDef):
                func_positions[stmt.name] = i
            else:
                for call_name in self._collect_top_calls(stmt):
                    calls_positions.setdefault(call_name, []).append(i)

        function_defs = []
        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.FunctionDef):
                fn_name = stmt.name
                safe_to_move = True
                if fn_name in calls_positions:
                    for call_i in calls_positions[fn_name]:
                        if call_i < i:
                            safe_to_move = False
                            break
                function_defs.append((stmt, safe_to_move))

        other_nodes = [
            stmt for stmt in node.body if not isinstance(stmt, ast.FunctionDef)
        ]

        safe_functions = [f for f, safe in function_defs if safe]
        unsafe_functions = [f for f, safe in function_defs if not safe]

        random.shuffle(safe_functions)

        new_body = other_nodes + unsafe_functions + safe_functions

        node.body = new_body
        return node

    @override
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Visits a class definition node and shuffles the order of method 
        definitions within the class.
        """
        method_defs = [
            stmt for stmt in node.body if isinstance(stmt, ast.FunctionDef)
        ]
        other_nodes = [
            stmt for stmt in node.body if not isinstance(stmt, ast.FunctionDef)
        ]

        random.shuffle(method_defs)

        node.body = other_nodes + method_defs
        return node

    def _collect_top_calls(self, stmt):
        """Collects the names of functions called at the top level within a 
        given statement. This method only analyzes direct call scenarios and 
        does not handle nested or complex cases.
        """
        calls = []
        for child in ast.walk(stmt):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
        return calls


class ImportReorderer(ast.NodeTransformer):
    """Reorders import statements in a module.
    """

    @override
    def visit_Module(self, node: ast.Module) -> ast.Module:
        import_nodes = [
            n for n in node.body if isinstance(n, (ast.Import, ast.ImportFrom))
        ]
        other_nodes = [
            n for n in node.body
            if not isinstance(n, (ast.Import, ast.ImportFrom))
        ]

        random.shuffle(import_nodes)

        node.body = import_nodes + other_nodes
        return node


class ClassReorderer(ast.NodeTransformer):
    """Reorders class definitions in a module or class.
    """

    @override
    def visit_Module(self, node: ast.Module) -> ast.Module:
        class_defs = [
            stmt for stmt in node.body if isinstance(stmt, ast.ClassDef)
        ]
        other_nodes = [
            stmt for stmt in node.body if not isinstance(stmt, ast.ClassDef)
        ]

        random.shuffle(class_defs)

        node.body = other_nodes + class_defs
        return node


class PythonDocstringInsertOperator(Operator):
    """Operator that inserts docstrings into Python code if they are missing.

    Attributes:
        insert_class_doc: Whether to insert docstring if class doc is missing.
        insert_function_doc: Whether to insert docstring if function doc is 
        missing
    """

    def __init__(self, **kwargs):
        self.insert_class_doc = kwargs.get('class', True)
        self.insert_function_doc = kwargs.get('function', True)

    @classmethod
    @override
    def accept(cls, data_type, task_type):
        if data_type == DataType.PYTHON and task_type == TaskType.AUGMENTATION:
            return True
        return False

    @classmethod
    @override
    def get_config(cls) -> list[Field]:
        return [
            Field('class', Field.FieldType.BOOL,
                  'Insert docstring if class doc is missing.', True),
            Field('function', Field.FieldType.BOOL,
                  'Insert docstring if function doc is missing.', True)
        ]

    @classmethod
    @override
    def get_meta(cls) -> Meta:
        return Meta(
            name='PythonDocstringInsertOperator',
            description='Inserts docstrings into Python code if they are '
            'missing.'
        )

    @override
    def execute(self, dataset: Dataset):
        df = pd.read_csv(dataset.meta_path)
        dir = [dir for dir in dataset.dirs if dir.data_type == DataType.PYTHON][0]
        files = df[DataType.PYTHON.value].tolist()
        for file in files:
            file_path = os.path.join(dir.data_path, file)
            with open(file_path, 'rb+') as f:
                code = f.read().decode('utf-8')
                code = self._inner_execute(code)
                f.seek(0)
                f.write(code.encode('utf-8'))
    
    def _inner_execute(self, code: str):
        tree = ast.parse(code)
        inserter = DocstringInserter(self.insert_class_doc,
                                     self.insert_function_doc)
        tree = inserter.visit(tree)
        code = ast.unparse(tree)
        return code


class DocstringInserter(ast.NodeTransformer):
    """AST transformer that inserts docstrings into Python code if they are
    missing.
    """

    def __init__(
        self,
        insert_class_docstring: bool = True,
        insert_function_docstring: bool = True,
    ):
        """Initializes the transformer with the specified settings.

        Args:
            insert_class_docstring: Whether to insert docstrings for classes.
            insert_function_docstring: Whether to insert docstrings for 
            functions.
        """
        super().__init__()
        self.insert_class_docstring = insert_class_docstring
        self.insert_function_docstring = insert_function_docstring

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.generic_visit(node)
        if (self.insert_function_docstring and
            (len(node.body) == 0 or not isinstance(node.body[0], ast.Expr) or
             not isinstance(node.body[0].value, ast.Constant) or
             not isinstance(node.body[0].value.value, str))):
            docstring = f"Docstring for function '{node.name}'."
            doc_expr = ast.Expr(value=ast.Constant(value=docstring))
            node.body.insert(0, doc_expr)
        return node

    @override
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        self.generic_visit(node)
        if (self.insert_class_docstring and
            (len(node.body) == 0 or not isinstance(node.body[0], ast.Expr) or
             not isinstance(node.body[0].value, ast.Constant) or
             not isinstance(node.body[0].value.value, str))):
            docstring = f"Docstring for class '{node.name}'."
            doc_expr = ast.Expr(value=ast.Constant(value=docstring))
            node.body.insert(0, doc_expr)
        return node
