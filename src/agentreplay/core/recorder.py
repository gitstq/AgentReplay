"""
Trace Recorder - Records agent execution traces in real-time
"""

import json
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
import hashlib

from .trace import Trace, TraceEvent, TraceStep, EventType, AgentFramework


class TraceRecorder:
    """
    Records agent execution traces in real-time.
    
    Supports multiple agent frameworks and provides hooks for instrumentation.
    """
    
    def __init__(
        self,
        agent_name: str = "unknown",
        framework: AgentFramework = AgentFramework.GENERIC,
        output_dir: str = "./traces",
        auto_save: bool = True,
    ):
        self.agent_name = agent_name
        self.framework = framework
        self.output_dir = output_dir
        self.auto_save = auto_save
        
        # Current recording state
        self._current_trace: Optional[Trace] = None
        self._current_step: Optional[TraceStep] = None
        self._step_counter: int = 0
        self._event_hooks: List[Callable[[TraceEvent], None]] = []
        
        # Ensure output directory exists
        if auto_save:
            os.makedirs(output_dir, exist_ok=True)
    
    def start_trace(self, task: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start recording a new trace.
        
        Args:
            task: Description of the task being executed
            metadata: Optional metadata for the trace
            
        Returns:
            Trace ID
        """
        trace_id = hashlib.md5(
            f"{task}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        self._current_trace = Trace(
            trace_id=trace_id,
            agent_name=self.agent_name,
            framework=self.framework,
            task=task,
            start_time=datetime.now(),
            metadata=metadata or {},
        )
        self._step_counter = 0
        
        return trace_id
    
    def start_step(self, description: str = "") -> str:
        """
        Start a new step in the current trace.
        
        Args:
            description: Description of the step
            
        Returns:
            Step ID
        """
        if self._current_trace is None:
            raise RuntimeError("No active trace. Call start_trace() first.")
        
        # End previous step if exists
        if self._current_step is not None:
            self._end_current_step()
        
        self._step_counter += 1
        step_id = f"step_{self._step_counter}"
        
        self._current_step = TraceStep(
            step_id=step_id,
            step_number=self._step_counter,
            description=description,
            start_time=datetime.now(),
        )
        
        return step_id
    
    def record_event(
        self,
        event_type: EventType,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
    ) -> str:
        """
        Record an event in the current step.
        
        Args:
            event_type: Type of the event
            content: Content of the event
            metadata: Optional metadata
            duration_ms: Duration in milliseconds
            tokens_used: Tokens consumed
            
        Returns:
            Event ID
        """
        if self._current_trace is None:
            raise RuntimeError("No active trace. Call start_trace() first.")
        
        if self._current_step is None:
            # Auto-create a step if none exists
            self.start_step("Auto-created step")
        
        event = TraceEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            content=content,
            metadata=metadata or {},
            duration_ms=duration_ms,
            tokens_used=tokens_used,
        )
        
        self._current_step.add_event(event)
        
        # Call event hooks
        for hook in self._event_hooks:
            hook(event)
        
        return event.event_id
    
    def record_thinking(self, content: str, tokens_used: Optional[int] = None) -> str:
        """Record a thinking/reasoning event"""
        return self.record_event(
            EventType.THINKING,
            content,
            tokens_used=tokens_used,
        )
    
    def record_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        duration_ms: Optional[int] = None,
    ) -> str:
        """Record a tool call event"""
        return self.record_event(
            EventType.TOOL_CALL,
            f"Calling tool: {tool_name}",
            metadata={"tool_name": tool_name, "arguments": arguments},
            duration_ms=duration_ms,
        )
    
    def record_tool_result(
        self,
        tool_name: str,
        result: Any,
        success: bool = True,
        duration_ms: Optional[int] = None,
    ) -> str:
        """Record a tool result event"""
        result_str = str(result)[:1000] if result else ""
        return self.record_event(
            EventType.TOOL_RESULT,
            f"Tool result: {tool_name}",
            metadata={
                "tool_name": tool_name,
                "result": result_str,
                "success": success,
            },
            duration_ms=duration_ms,
        )
    
    def record_message(self, role: str, content: str) -> str:
        """Record a message event"""
        return self.record_event(
            EventType.MESSAGE,
            content,
            metadata={"role": role},
        )
    
    def record_error(self, error_message: str, error_type: str = "unknown") -> str:
        """Record an error event"""
        if self._current_step:
            self._current_step.success = False
            self._current_step.error_message = error_message
        
        return self.record_event(
            EventType.ERROR,
            error_message,
            metadata={"error_type": error_type},
        )
    
    def record_decision(self, decision: str, reasoning: str = "") -> str:
        """Record a decision event"""
        return self.record_event(
            EventType.DECISION,
            decision,
            metadata={"reasoning": reasoning},
        )
    
    def record_checkpoint(self, name: str, state: Dict[str, Any]) -> str:
        """Record a checkpoint event"""
        return self.record_event(
            EventType.CHECKPOINT,
            f"Checkpoint: {name}",
            metadata={"checkpoint_name": name, "state": state},
        )
    
    def end_step(self, success: bool = True, error_message: Optional[str] = None) -> None:
        """End the current step"""
        if self._current_step:
            self._current_step.success = success
            if error_message:
                self._current_step.error_message = error_message
            self._end_current_step()
    
    def _end_current_step(self) -> None:
        """Internal method to end current step and add to trace"""
        if self._current_step and self._current_trace:
            self._current_step.end_time = datetime.now()
            self._current_trace.add_step(self._current_step)
            self._current_step = None
    
    def end_trace(self) -> Optional[Trace]:
        """
        End the current trace recording.
        
        Returns:
            The completed trace, or None if no trace was active
        """
        if self._current_trace is None:
            return None
        
        # End current step if any
        if self._current_step is not None:
            self._end_current_step()
        
        self._current_trace.end_time = datetime.now()
        
        trace = self._current_trace
        self._current_trace = None
        
        # Auto-save if enabled
        if self.auto_save:
            filepath = os.path.join(
                self.output_dir,
                f"trace_{trace.trace_id}.json"
            )
            trace.save(filepath)
        
        return trace
    
    def add_event_hook(self, hook: Callable[[TraceEvent], None]) -> None:
        """Add a hook to be called on each event"""
        self._event_hooks.append(hook)
    
    def remove_event_hook(self, hook: Callable[[TraceEvent], None]) -> None:
        """Remove an event hook"""
        if hook in self._event_hooks:
            self._event_hooks.remove(hook)
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording a trace"""
        return self._current_trace is not None
    
    @property
    def current_trace(self) -> Optional[Trace]:
        """Get the current trace being recorded"""
        return self._current_trace
