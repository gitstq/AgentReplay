"""Tests for AgentReplay core functionality"""

import json
import os
import tempfile
from datetime import datetime

import pytest

from agentreplay.core import (
    Trace,
    TraceEvent,
    TraceStep,
    TraceRecorder,
    TracePlayer,
    TraceAnalyzer,
    EventType,
    AgentFramework,
)


class TestTraceEvent:
    """Tests for TraceEvent"""
    
    def test_create_event(self):
        """Test creating a trace event"""
        event = TraceEvent(
            event_type=EventType.THINKING,
            timestamp=datetime.now(),
            content="Test thinking",
            tokens_used=10,
        )
        
        assert event.event_type == EventType.THINKING
        assert event.content == "Test thinking"
        assert event.tokens_used == 10
        assert event.event_id is not None
    
    def test_event_to_dict(self):
        """Test event serialization"""
        event = TraceEvent(
            event_type=EventType.TOOL_CALL,
            timestamp=datetime.now(),
            content="Calling tool",
            metadata={"tool_name": "Read"},
            duration_ms=50,
        )
        
        data = event.to_dict()
        
        assert data["event_type"] == "tool_call"
        assert data["content"] == "Calling tool"
        assert data["metadata"]["tool_name"] == "Read"
        assert data["duration_ms"] == 50
    
    def test_event_from_dict(self):
        """Test event deserialization"""
        data = {
            "event_id": "test123",
            "event_type": "message",
            "timestamp": datetime.now().isoformat(),
            "content": "Test message",
            "metadata": {"role": "user"},
        }
        
        event = TraceEvent.from_dict(data)
        
        assert event.event_id == "test123"
        assert event.event_type == EventType.MESSAGE
        assert event.content == "Test message"


class TestTraceStep:
    """Tests for TraceStep"""
    
    def test_create_step(self):
        """Test creating a trace step"""
        step = TraceStep(
            step_id="step_1",
            step_number=1,
            description="Test step",
        )
        
        assert step.step_id == "step_1"
        assert step.step_number == 1
        assert len(step.events) == 0
    
    def test_add_event(self):
        """Test adding events to a step"""
        step = TraceStep(step_id="step_1", step_number=1)
        event = TraceEvent(
            event_type=EventType.THINKING,
            timestamp=datetime.now(),
            content="Test",
        )
        
        step.add_event(event)
        
        assert len(step.events) == 1
        assert step.start_time is not None
        assert step.end_time is not None
    
    def test_step_duration(self):
        """Test step duration calculation"""
        step = TraceStep(step_id="step_1", step_number=1)
        
        event1 = TraceEvent(
            event_type=EventType.THINKING,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            content="Start",
        )
        event2 = TraceEvent(
            event_type=EventType.THINKING,
            timestamp=datetime(2024, 1, 1, 12, 0, 1),
            content="End",
        )
        
        step.add_event(event1)
        step.add_event(event2)
        
        assert step.duration_ms == 1000


class TestTrace:
    """Tests for Trace"""
    
    def test_create_trace(self):
        """Test creating a trace"""
        trace = Trace(
            trace_id="test123",
            agent_name="TestAgent",
            framework=AgentFramework.CLAUDE_CODE,
            task="Test task",
        )
        
        assert trace.trace_id == "test123"
        assert trace.agent_name == "TestAgent"
        assert trace.framework == AgentFramework.CLAUDE_CODE
        assert len(trace.steps) == 0
    
    def test_add_step(self):
        """Test adding steps to a trace"""
        trace = Trace(
            trace_id="test123",
            agent_name="TestAgent",
            framework=AgentFramework.GENERIC,
            task="Test",
        )
        
        step = TraceStep(step_id="step_1", step_number=1)
        step.add_event(TraceEvent(
            event_type=EventType.THINKING,
            timestamp=datetime.now(),
            content="Test",
        ))
        
        trace.add_step(step)
        
        assert len(trace.steps) == 1
        assert trace.total_events == 1
    
    def test_trace_serialization(self):
        """Test trace JSON serialization"""
        trace = Trace(
            trace_id="test123",
            agent_name="TestAgent",
            framework=AgentFramework.CLAUDE_CODE,
            task="Test task",
        )
        
        step = TraceStep(step_id="step_1", step_number=1, description="Test step")
        step.add_event(TraceEvent(
            event_type=EventType.THINKING,
            timestamp=datetime.now(),
            content="Test thinking",
            tokens_used=10,
        ))
        trace.add_step(step)
        
        json_str = trace.to_json()
        data = json.loads(json_str)
        
        assert data["trace_id"] == "test123"
        assert data["agent_name"] == "TestAgent"
        assert len(data["steps"]) == 1
    
    def test_trace_save_load(self):
        """Test saving and loading trace"""
        trace = Trace(
            trace_id="test123",
            agent_name="TestAgent",
            framework=AgentFramework.GENERIC,
            task="Test task",
        )
        
        step = TraceStep(step_id="step_1", step_number=1)
        step.add_event(TraceEvent(
            event_type=EventType.THINKING,
            timestamp=datetime.now(),
            content="Test",
        ))
        trace.add_step(step)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            trace.save(temp_path)
            loaded_trace = Trace.load(temp_path)
            
            assert loaded_trace.trace_id == trace.trace_id
            assert loaded_trace.agent_name == trace.agent_name
            assert len(loaded_trace.steps) == 1
        finally:
            os.unlink(temp_path)


class TestTraceRecorder:
    """Tests for TraceRecorder"""
    
    def test_start_end_trace(self):
        """Test starting and ending a trace"""
        recorder = TraceRecorder(auto_save=False)
        
        trace_id = recorder.start_trace("Test task")
        
        assert trace_id is not None
        assert recorder.is_recording
        
        trace = recorder.end_trace()
        
        assert trace is not None
        assert not recorder.is_recording
        assert trace.task == "Test task"
    
    def test_record_events(self):
        """Test recording various events"""
        recorder = TraceRecorder(auto_save=False)
        recorder.start_trace("Test task")
        recorder.start_step("Test step")
        
        recorder.record_thinking("Thinking...", tokens_used=10)
        recorder.record_tool_call("Read", {"file": "test.py"}, duration_ms=50)
        recorder.record_tool_result("Read", "file contents", success=True)
        recorder.record_message("user", "Hello")
        recorder.record_error("Test error", "TestError")
        
        trace = recorder.end_trace()
        
        assert trace is not None
        assert trace.total_events >= 5


class TestTracePlayer:
    """Tests for TracePlayer"""
    
    def create_sample_trace(self) -> Trace:
        """Create a sample trace for testing"""
        trace = Trace(
            trace_id="test123",
            agent_name="TestAgent",
            framework=AgentFramework.GENERIC,
            task="Test task",
        )
        
        step = TraceStep(step_id="step_1", step_number=1)
        step.add_event(TraceEvent(
            event_type=EventType.THINKING,
            timestamp=datetime.now(),
            content="Thinking 1",
        ))
        step.add_event(TraceEvent(
            event_type=EventType.TOOL_CALL,
            timestamp=datetime.now(),
            content="Tool call",
        ))
        trace.add_step(step)
        
        return trace
    
    def test_play_trace(self):
        """Test playing a trace"""
        trace = self.create_sample_trace()
        player = TracePlayer(trace)
        
        events = list(player.play(speed=0))
        
        assert len(events) == 2
    
    def test_step_navigation(self):
        """Test stepping forward and backward"""
        trace = self.create_sample_trace()
        player = TracePlayer(trace)
        
        # Step forward to first event
        event1 = player.step_forward()
        assert event1 is not None
        assert event1.content == "Thinking 1"
        
        # Step forward to second event
        event2 = player.step_forward()
        assert event2 is not None
        assert event2.content == "Tool call"
        
        # Step backward should return first event
        prev_event = player.step_backward()
        assert prev_event is not None
        assert prev_event.content == "Thinking 1"
    
    def test_get_progress(self):
        """Test getting playback progress"""
        trace = self.create_sample_trace()
        player = TracePlayer(trace)
        
        progress = player.get_progress()
        
        assert "total_steps" in progress
        assert "total_events" in progress
        assert "progress_percent" in progress


class TestTraceAnalyzer:
    """Tests for TraceAnalyzer"""
    
    def create_sample_trace(self) -> Trace:
        """Create a sample trace for testing"""
        trace = Trace(
            trace_id="test123",
            agent_name="TestAgent",
            framework=AgentFramework.GENERIC,
            task="Test task",
        )
        
        # Step 1
        step1 = TraceStep(step_id="step_1", step_number=1, description="Step 1")
        step1.add_event(TraceEvent(
            event_type=EventType.THINKING,
            timestamp=datetime.now(),
            content="Thinking",
            tokens_used=10,
            duration_ms=100,
        ))
        step1.add_event(TraceEvent(
            event_type=EventType.TOOL_CALL,
            timestamp=datetime.now(),
            content="Tool call",
            metadata={"tool_name": "Read"},
            duration_ms=50,
        ))
        step1.add_event(TraceEvent(
            event_type=EventType.TOOL_RESULT,
            timestamp=datetime.now(),
            content="Result",
            metadata={"tool_name": "Read", "success": True},
        ))
        trace.add_step(step1)
        
        # Step 2
        step2 = TraceStep(step_id="step_2", step_number=2, description="Step 2")
        step2.add_event(TraceEvent(
            event_type=EventType.ERROR,
            timestamp=datetime.now(),
            content="Test error",
            metadata={"error_type": "TestError"},
        ))
        step2.success = False
        step2.error_message = "Test error"
        trace.add_step(step2)
        
        return trace
    
    def test_analyze_trace(self):
        """Test analyzing a trace"""
        trace = self.create_sample_trace()
        analyzer = TraceAnalyzer(trace)
        
        result = analyzer.analyze()
        
        assert result.trace_id == "test123"
        assert result.total_steps == 2
        assert result.total_events >= 4
        assert result.error_count == 1
    
    def test_tool_analysis(self):
        """Test tool usage analysis"""
        trace = self.create_sample_trace()
        analyzer = TraceAnalyzer(trace)
        
        result = analyzer.analyze()
        
        assert "Read" in result.tool_stats
        assert result.tool_stats["Read"].call_count == 1
    
    def test_get_timeline(self):
        """Test getting timeline"""
        trace = self.create_sample_trace()
        analyzer = TraceAnalyzer(trace)
        
        timeline = analyzer.get_timeline()
        
        assert len(timeline) >= 4
        assert all("event_type" in t for t in timeline)
