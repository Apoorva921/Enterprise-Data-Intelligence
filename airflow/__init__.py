"""
Airflow Module Compatibility Layer.
Exports DAG, operators, and airflow utilities.
"""
from typing import Any, List, Optional


class DAG:
    def __init__(self, dag_id: str, *args, **kwargs):
        self.dag_id = dag_id
        self.tasks = []
        self.default_args = kwargs.get("default_args", {})
        self.schedule_interval = kwargs.get("schedule_interval")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class BaseOperator:
    def __init__(self, task_id: str, *args, **kwargs):
        self.task_id = task_id
        self.downstream = []
        dag = kwargs.get("dag")
        if dag:
            dag.tasks.append(self)

    def __rshift__(self, other):
        if isinstance(other, list):
            for o in other:
                self.downstream.append(o)
        else:
            self.downstream.append(other)
        return other

    def __rrshift__(self, other):
        if isinstance(other, list):
            for o in other:
                o.downstream.append(self)
        else:
            other.downstream.append(self)
        return self


class PythonOperator(BaseOperator):
    def __init__(self, task_id: str, python_callable=None, *args, **kwargs):
        super().__init__(task_id, *args, **kwargs)
        self.python_callable = python_callable
        self.op_kwargs = kwargs.get("op_kwargs", {})

    def execute(self, context=None):
        if self.python_callable:
            return self.python_callable(**self.op_kwargs)


class EmptyOperator(BaseOperator):
    pass


class DummyOperator(EmptyOperator):
    pass


__all__ = ["DAG", "BaseOperator", "PythonOperator", "EmptyOperator", "DummyOperator"]
