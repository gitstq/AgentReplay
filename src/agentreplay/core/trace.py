"""
Core data structures for AgentReplay
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import json
import hashlib


class EventType(Enum):
    """Event types in agent execution trace"""
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    MESSAGE = "message"
    ERROR = "error"
    DECISION = "decision"
    STATE_CHANGE = "state_change"
    CHECKPOINT = "checkpoint"


class AgentFramework(Enum):
    """Supported agent frameworks"""
    CLAUDE_CODE = "claude_code"
    CURSOR = "cursor"
    CODEX = "codex"
    WINDSURF = "windsurf"
    COPILOT = "copilot"
    GENERIC = "generic"


@dataclass
class TraceEvent:
    """Single event in agent execution trace"""
    event_type: EventType
    timestamp: datetime
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    parent_id: Optional[str] = None
    event_id: str = field(default_factory=lambda: hashlib.md5(
        str(datetime.now().timestamp()).encode()
    ).hexdigest()[:8])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
            "metadata": self.metadata,
            "duration_ms": self.duration_ms,
            "tokens_used": self.tokens_used,
            "parent_id": self.parent_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraceEvent":
        """Create from dictionary"""
        return cls(
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            content=data["content"],
            metadata=data.get("metadata", {}),
            duration_ms=data.get("duration_ms"),
            tokens_used=data.get("tokens_used"),
            parent_id=data.get("parent_id"),
            event_id=data.get("event_id", hashlib.md5(
                str(datetime.now().timestamp()).encode()
            ).hexdigest()[:8]),
        )


@dataclass
class TraceStep:
    """A step in agent execution (contains multiple events)"""
    step_id: str
    step_number: int
    events: List[TraceEvent] = field(default_factory=list)
    description: str = ""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def add_event(self, event: TraceEvent) -> None:
        """Add an event to this step"""
        self.events.append(event)
        if self.start_time is None or event.timestamp < self.start_time:
            self.start_time = event.timestamp
        if self.end_time is None or event.timestamp > self.end_time:
            self.end_time = event.timestamp
    
    @property
    def duration_ms(self) -> int:
        """Calculate step duration in milliseconds"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() * 1000)
        return 0
    
    @property
    def total_tokens(self) -> int:
        """Calculate total tokens used in this step"""
        return sum(e.tokens_used or 0 for e in self.events)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "step_id": self.step_id,
            "step_number": self.step_number,
            "events": [e.to_dict() for e in self.events],
            "description": self.description,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "success": self.success,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "total_tokens": self.total_tokens,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraceStep":
        """Create from dictionary"""
        step = cls(
            step_id=data["step_id"],
            step_number=data["step_number"],
            description=data.get("description", ""),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            success=data.get("success", True),
            error_message=data.get("error_message"),
        )
        for event_data in data.get("events", []):
            step.events.append(TraceEvent.from_dict(event_data))
        return step


@dataclass
class Trace:
    """Complete agent execution trace"""
    trace_id: str
    agent_name: str
    framework: AgentFramework
    task: str
    steps: List[TraceStep] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, step: TraceStep) -> None:
        """Add a step to this trace"""
        self.steps.append(step)
        if self.start_time is None or (step.start_time and step.start_time < self.start_time):
            self.start_time = step.start_time
        if self.end_time is None or (step.end_time and step.end_time > self.end_time):
            self.end_time = step.end_time
    
    @property
    def duration_ms(self) -> int:
        """Calculate total trace duration"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() * 1000)
        return 0
    
    @property
    def total_tokens(self) -> int:
        """Calculate total tokens used"""
        return sum(step.total_tokens for step in self.steps)
    
    @property
    def total_events(self) -> int:
        """Count total events"""
        return sum(len(step.events) for step in self.steps)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of steps"""
        if not self.steps:
            return 0.0
        successful = sum(1 for s in self.steps if s.success)
        return successful / len(self.steps)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "trace_id": self.trace_id,
            "agent_name": self.agent_name,
            "framework": self.framework.value,
            "task": self.task,
            "steps": [s.to_dict() for s in self.steps],
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "metadata": self.metadata,
            "statistics": {
                "duration_ms": self.duration_ms,
                "total_tokens": self.total_tokens,
                "total_steps": len(self.steps),
                "total_events": self.total_events,
                "success_rate": self.success_rate,
            }
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Trace":
        """Create from dictionary"""
        trace = cls(
            trace_id=data["trace_id"],
            agent_name=data["agent_name"],
            framework=AgentFramework(data.get("framework", "generic")),
            task=data["task"],
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            metadata=data.get("metadata", {}),
        )
        for step_data in data.get("steps", []):
            trace.steps.append(TraceStep.from_dict(step_data))
        return trace
    
    @classmethod
    def from_json(cls, json_str: str) -> "Trace":
        """Create from JSON string"""
        return cls.from_dict(json.loads(json_str))
    
    def save(self, filepath: str) -> None:
        """Save trace to file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    @classmethod
    def load(cls, filepath: str) -> "Trace":
        """Load trace from file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())
