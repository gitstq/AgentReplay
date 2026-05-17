"""
Trace Player - Replay agent execution traces
"""

import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Generator
from dataclasses import dataclass

from .trace import Trace, TraceEvent, TraceStep, EventType


class PlaybackMode(Enum):
    """Playback speed modes"""
    REALTIME = 1.0
    FAST = 2.0
    FASTER = 5.0
    FASTEST = 10.0
    STEP_BY_STEP = 0.0  # Manual stepping


@dataclass
class PlaybackState:
    """Current playback state"""
    is_playing: bool = False
    is_paused: bool = False
    current_step_index: int = 0
    current_event_index: int = 0
    speed: float = 1.0
    elapsed_ms: int = 0


class TracePlayer:
    """
    Replay agent execution traces with various playback modes.
    
    Supports real-time playback, fast-forward, step-by-step debugging,
    and event filtering.
    """
    
    def __init__(self, trace: Trace):
        self.trace = trace
        self.state = PlaybackState()
        
        # Event callbacks
        self._on_step_start: Optional[Callable[[TraceStep], None]] = None
        self._on_step_end: Optional[Callable[[TraceStep], None]] = None
        self._on_event: Optional[Callable[[TraceEvent], None]] = None
        self._on_playback_end: Optional[Callable[[], None]] = None
        
        # Breakpoints
        self._breakpoints: Dict[str, List[int]] = {}  # step_id -> event indices
    
    def set_callbacks(
        self,
        on_step_start: Optional[Callable[[TraceStep], None]] = None,
        on_step_end: Optional[Callable[[TraceStep], None]] = None,
        on_event: Optional[Callable[[TraceEvent], None]] = None,
        on_playback_end: Optional[Callable[[], None]] = None,
    ) -> None:
        """Set callback functions for playback events"""
        self._on_step_start = on_step_start
        self._on_step_end = on_step_end
        self._on_event = on_event
        self._on_playback_end = on_playback_end
    
    def add_breakpoint(self, step_id: str, event_index: Optional[int] = None) -> None:
        """Add a breakpoint at a step or specific event"""
        if step_id not in self._breakpoints:
            self._breakpoints[step_id] = []
        if event_index is not None:
            self._breakpoints[step_id].append(event_index)
    
    def remove_breakpoint(self, step_id: str, event_index: Optional[int] = None) -> None:
        """Remove a breakpoint"""
        if step_id in self._breakpoints:
            if event_index is None:
                del self._breakpoints[step_id]
            elif event_index in self._breakpoints[step_id]:
                self._breakpoints[step_id].remove(event_index)
    
    def play(
        self,
        speed: float = 1.0,
        start_step: int = 0,
        event_filter: Optional[List[EventType]] = None,
    ) -> Generator[TraceEvent, None, None]:
        """
        Play the trace and yield events.
        
        Args:
            speed: Playback speed (1.0 = real-time, 0.0 = step-by-step)
            start_step: Step index to start from
            event_filter: Only yield events of these types
            
        Yields:
            TraceEvent objects
        """
        self.state.is_playing = True
        self.state.is_paused = False
        self.state.speed = speed
        self.state.current_step_index = start_step
        
        for step_idx, step in enumerate(self.trace.steps[start_step:], start=start_step):
            if not self.state.is_playing:
                break
            
            self.state.current_step_index = step_idx
            
            # Call step start callback
            if self._on_step_start:
                self._on_step_start(step)
            
            for event_idx, event in enumerate(step.events):
                if not self.state.is_playing:
                    break
                
                # Check event filter
                if event_filter and event.event_type not in event_filter:
                    continue
                
                self.state.current_event_index = event_idx
                
                # Check breakpoint
                if step.step_id in self._breakpoints:
                    if event_idx in self._breakpoints[step.step_id]:
                        self.state.is_paused = True
                        # Wait for resume
                        while self.state.is_paused and self.state.is_playing:
                            time.sleep(0.1)
                
                # Call event callback
                if self._on_event:
                    self._on_event(event)
                
                # Yield event
                yield event
                
                # Timing
                if speed > 0 and event.duration_ms:
                    sleep_time = event.duration_ms / 1000.0 / speed
                    time.sleep(sleep_time)
            
            # Call step end callback
            if self._on_step_end:
                self._on_step_end(step)
        
        self.state.is_playing = False
        
        if self._on_playback_end:
            self._on_playback_end()
    
    def play_async(
        self,
        speed: float = 1.0,
        start_step: int = 0,
        event_filter: Optional[List[EventType]] = None,
    ) -> None:
        """Start asynchronous playback (non-blocking)"""
        import threading
        
        def _play_thread():
            for _ in self.play(speed, start_step, event_filter):
                pass
        
        thread = threading.Thread(target=_play_thread, daemon=True)
        thread.start()
    
    def pause(self) -> None:
        """Pause playback"""
        self.state.is_paused = True
    
    def resume(self) -> None:
        """Resume paused playback"""
        self.state.is_paused = False
    
    def stop(self) -> None:
        """Stop playback"""
        self.state.is_playing = False
        self.state.is_paused = False
    
    def step_forward(self) -> Optional[TraceEvent]:
        """
        Step forward one event (for step-by-step mode).
        
        Returns:
            The next event, or None if at end
        """
        if not self.trace.steps:
            return None
        
        step = self.trace.steps[self.state.current_step_index]
        
        # Try to get current event first
        if self.state.current_event_index < len(step.events):
            event = step.events[self.state.current_event_index]
            self.state.current_event_index += 1
            if self._on_event:
                self._on_event(event)
            return event
        
        # Move to next step if current step is exhausted
        self.state.current_step_index += 1
        self.state.current_event_index = 0
        
        while self.state.current_step_index < len(self.trace.steps):
            step = self.trace.steps[self.state.current_step_index]
            if self.state.current_event_index < len(step.events):
                event = step.events[self.state.current_event_index]
                self.state.current_event_index += 1
                if self._on_event:
                    self._on_event(event)
                return event
            self.state.current_step_index += 1
        
        return None
    
    def step_backward(self) -> Optional[TraceEvent]:
        """
        Step backward one event.
        
        Returns:
            The previous event, or None if at beginning
        """
        if not self.trace.steps:
            return None
        
        # Need to go back 2 positions because step_forward increments after returning
        # So after two step_forwards, index is at 2 (pointing to next event)
        # To get the previous event (index 0), we need to go back 2
        self.state.current_event_index -= 2
        
        # Move to previous step if needed
        while self.state.current_event_index < 0:
            self.state.current_step_index -= 1
            
            if self.state.current_step_index < 0:
                self.state.current_step_index = 0
                self.state.current_event_index = 0
                return None
            
            step = self.trace.steps[self.state.current_step_index]
            self.state.current_event_index = len(step.events) + self.state.current_event_index
        
        step = self.trace.steps[self.state.current_step_index]
        if 0 <= self.state.current_event_index < len(step.events):
            event = step.events[self.state.current_event_index]
            if self._on_event:
                self._on_event(event)
            return event
        
        return None
    
    def seek_to_step(self, step_index: int) -> None:
        """Jump to a specific step"""
        if 0 <= step_index < len(self.trace.steps):
            self.state.current_step_index = step_index
            self.state.current_event_index = 0
    
    def seek_to_event(self, step_index: int, event_index: int) -> None:
        """Jump to a specific event"""
        if 0 <= step_index < len(self.trace.steps):
            step = self.trace.steps[step_index]
            if 0 <= event_index < len(step.events):
                self.state.current_step_index = step_index
                self.state.current_event_index = event_index
    
    def get_current_step(self) -> Optional[TraceStep]:
        """Get the current step"""
        if 0 <= self.state.current_step_index < len(self.trace.steps):
            return self.trace.steps[self.state.current_step_index]
        return None
    
    def get_current_event(self) -> Optional[TraceEvent]:
        """Get the current event"""
        step = self.get_current_step()
        if step and 0 <= self.state.current_event_index < len(step.events):
            return step.events[self.state.current_event_index]
        return None
    
    def get_progress(self) -> Dict[str, Any]:
        """Get playback progress information"""
        total_events = self.trace.total_events
        current_event = (
            sum(len(self.trace.steps[i].events) for i in range(self.state.current_step_index)) +
            self.state.current_event_index
        )
        
        return {
            "current_step": self.state.current_step_index,
            "total_steps": len(self.trace.steps),
            "current_event": self.state.current_event_index,
            "total_events": total_events,
            "progress_percent": (current_event / total_events * 100) if total_events > 0 else 0,
            "is_playing": self.state.is_playing,
            "is_paused": self.state.is_paused,
            "speed": self.state.speed,
        }
