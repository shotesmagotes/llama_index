import uuid
from abc import ABC, abstractmethod
from collections import deque
from typing import Any, Deque, Dict, List, Optional

from pydantic import BaseModel, Field

from llama_index.memory.types import BaseMemory


class TaskStep(BaseModel):
    """ "Agent task step.

    Represents a single input step within the execution run ("Task") of an agent
    given a user input.

    The output is returned as a `TaskStepOutput`.

    """

    task_id: str = Field(..., diescription="Task ID")
    step_id: str = Field(..., description="Step ID")
    input: Optional[str] = Field(default=None, description="User input")
    memory: BaseMemory = Field(
        ..., type=BaseMemory, description="Conversational Memory"
    )
    step_state: Dict[str, Any] = Field(
        default_factory=dict, description="Additional state, carries over to next step."
    )

    def get_next_step(
        self,
        step_id: str,
        input: Optional[str] = None,
    ) -> "TaskStep":
        """Convenience function to get next step.

        Preserve task_id, memory, step_state.

        """
        return TaskStep(
            task_id=self.task_id,
            step_id=step_id,
            input=input,
            memory=self.memory,
            step_state=self.step_state,
        )


class TaskStepOutput(BaseModel):
    """Agent task step output."""

    output: Any = Field(..., description="Task step output")
    task_step: TaskStep = Field(..., description="Task step input")
    next_steps: List[TaskStep] = Field(..., description="Next steps to be executed.")
    is_last: bool = Field(default=False, description="Is this the last step?")

    def __str__(self) -> str:
        """String representation."""
        return str(self.output)


class Task(BaseModel):
    """Agent Task.

    Represents a "run" of an agent given a user input.

    """

    task_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), type=str, description="Task ID"
    )
    input: str = Field(..., type=str, description="User input")

    # NOTE: this is state that may be modified throughout the course of execution of the task
    memory: BaseMemory = Field(
        ..., type=BaseMemory, description="Conversational Memory"
    )

    step_queue: Deque[TaskStep] = Field(
        default_factory=deque, description="Task step queue."
    )
    completed_steps: List[TaskStepOutput] = Field(
        default_factory=list, description="Completed step outputs."
    )
    extra_state: Dict[str, Any] = Field(
        default_factory=dict, description="Additional state for task."
    )


class AgentState(BaseModel):
    """Agent state."""

    task_dict: Dict[str, Task] = Field(
        default_factory=dict, description="Task dictionary."
    )

    def get_task(self, task_id: str) -> Task:
        """Get task state."""
        return self.task_dict[task_id]

    def get_completed_steps(self, task_id: str) -> List[TaskStepOutput]:
        """Get completed steps."""
        return self.get_task(task_id).completed_steps

    def get_step_queue(self, task_id: str) -> Deque[TaskStep]:
        """Get step queue."""
        return self.get_task(task_id).step_queue


class BaseAgentStepEngine(ABC):
    """Base agent step engine."""

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    def initialize_step(self, task: Task, **kwargs: Any) -> TaskStep:
        """Initialize step from task."""

    @abstractmethod
    def run_step(self, step: TaskStep, task: Task, **kwargs: Any) -> TaskStepOutput:
        """Run step."""

    @abstractmethod
    async def arun_step(
        self, step: TaskStep, task: Task, **kwargs: Any
    ) -> TaskStepOutput:
        """Run step (async)."""
        raise NotImplementedError

    @abstractmethod
    def stream_step(self, step: TaskStep, task: Task, **kwargs: Any) -> TaskStepOutput:
        """Run step (stream)."""
        # TODO: figure out if we need a different type for TaskStepOutput
        raise NotImplementedError

    @abstractmethod
    async def astream_step(
        self, step: TaskStep, task: Task, **kwargs: Any
    ) -> TaskStepOutput:
        """Run step (async stream)."""
        raise NotImplementedError
