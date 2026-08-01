"""Modelos Pydantic do protocolo A2A (Google Agent2Agent).

Subset mínimo suficiente para POC: text parts, message/send síncrono, tasks/get.
Baseado em https://google.github.io/A2A/ (JSON-RPC 2.0).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"


class TextPart(BaseModel):
    kind: Literal["text"] = "text"
    text: str


Part = Union[TextPart]


class Message(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: Literal["user", "agent"]
    parts: list[Part]
    message_id: str = Field(default_factory=lambda: str(uuid4()), alias="messageId")
    task_id: Optional[str] = Field(default=None, alias="taskId")
    context_id: Optional[str] = Field(default=None, alias="contextId")


class TaskStatus(BaseModel):
    state: TaskState
    message: Optional[Message] = None
    timestamp: datetime = Field(default_factory=_now)


class Artifact(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    artifact_id: str = Field(default_factory=lambda: str(uuid4()), alias="artifactId")
    name: Optional[str] = None
    parts: list[Part]


class Task(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    context_id: str = Field(default_factory=lambda: str(uuid4()), alias="contextId")
    status: TaskStatus
    history: list[Message] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    kind: Literal["task"] = "task"


class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class AgentCapabilities(BaseModel):
    streaming: bool = False
    push_notifications: bool = Field(default=False, alias="pushNotifications")
    state_transition_history: bool = Field(default=True, alias="stateTransitionHistory")

    model_config = ConfigDict(populate_by_name=True)


class AgentCard(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    default_input_modes: list[str] = Field(default=["text/plain"], alias="defaultInputModes")
    default_output_modes: list[str] = Field(default=["text/plain"], alias="defaultOutputModes")
    skills: list[AgentSkill]


class MessageSendParams(BaseModel):
    message: Message
    configuration: Optional[dict[str, Any]] = None


class TaskQueryParams(BaseModel):
    id: str
    history_length: Optional[int] = Field(default=None, alias="historyLength")

    model_config = ConfigDict(populate_by_name=True)
