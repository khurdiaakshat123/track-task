from pydantic import BaseModel
from typing import Optional, Literal

PriorityType = Literal['low', 'medium', 'high']

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: PriorityType
    due_date: Optional[str] = None

class CreateTaskInput(TaskBase):
    pass

class UpdateTaskInput(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[PriorityType] = None
    due_date: Optional[str] = None
    is_completed: Optional[bool] = None
    completed_at: Optional[str] = None

class Task(TaskBase):
    id: str
    is_completed: bool
    created_at: str
    completed_at: Optional[str] = None
    user_id: Optional[str] = None

    class Config:
        from_attributes = True
