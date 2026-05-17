"""
AgentReplay - AI Agent Execution Trace Replay & Analysis Engine
Example Usage
"""

from datetime import datetime
import sys
import os

# Add src to path for local development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

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
from agentreplay.exporters import export_trace


def create_demo_trace():
    """Create a demo trace showing typical agent execution"""
    print("🎬 Creating demo trace...")
    
    recorder = TraceRecorder(
        agent_name="ClaudeCode",
        framework=AgentFramework.CLAUDE_CODE,
        auto_save=False,
    )
    
    # Start recording
    trace_id = recorder.start_trace(
        task="Analyze Python code and suggest improvements",
        metadata={"version": "1.0", "demo": True},
    )
    print(f"   Trace ID: {trace_id}")
    
    # Step 1: Read file
    print("   Step 1: Reading source file...")
    recorder.start_step("Read source file")
    recorder.record_thinking(
        "I need to read the Python file first to understand its structure.",
        tokens_used=15
    )
    recorder.record_tool_call(
        "Read",
        {"file_path": "example.py"},
        duration_ms=50
    )
    recorder.record_tool_result(
        "Read",
        "def hello():\n    print('Hello, World!')\n",
        success=True,
        duration_ms=10
    )
    recorder.end_step()
    
    # Step 2: Analyze code
    print("   Step 2: Analyzing code...")
    recorder.start_step("Analyze code structure")
    recorder.record_thinking(
        "The code is simple. Let me check for potential improvements.",
        tokens_used=20
    )
    recorder.record_decision(
        "Add type hints",
        "Python 3.5+ supports type hints for better code documentation"
    )
    recorder.record_tool_call(
        "Grep",
        {"pattern": "def ", "path": "."},
        duration_ms=30
    )
    recorder.record_tool_result(
        "Grep",
        "Found 1 function definition",
        success=True,
        duration_ms=5
    )
    recorder.end_step()
    
    # Step 3: Generate suggestions
    print("   Step 3: Generating suggestions...")
    recorder.start_step("Generate improvement suggestions")
    recorder.record_thinking(
        "Based on my analysis, I'll suggest improvements.",
        tokens_used=25
    )
    recorder.record_message(
        "assistant",
        "Here are my suggestions:\n1. Add type hints\n2. Add docstring\n3. Use f-strings"
    )
    recorder.record_checkpoint(
        "suggestions_generated",
        {"count": 3}
    )
    recorder.end_step()
    
    # Step 4: Write improved code (with error for demo)
    print("   Step 4: Writing improved code...")
    recorder.start_step("Write improved code")
    recorder.record_tool_call(
        "Write",
        {"file_path": "example_improved.py", "content": "..."},
        duration_ms=100
    )
    recorder.record_error(
        "Permission denied: example_improved.py",
        error_type="IOError"
    )
    recorder.end_step(success=False, error_message="Failed to write file")
    
    # End recording
    trace = recorder.end_trace()
    print(f"✅ Trace created with {trace.total_events} events")
    
    return trace


def demo_replay(trace: Trace):
    """Demo trace replay functionality"""
    print("\n📼 Replaying trace...")
    
    player = TracePlayer(trace)
    
    # Set up callbacks
    def on_event(event: TraceEvent):
        print(f"   [{event.event_type.value}] {event.content[:60]}...")
    
    player.set_callbacks(on_event=on_event)
    
    # Play at fast speed
    for event in player.play(speed=0):  # speed=0 for instant playback
        pass
    
    print("✅ Playback complete")


def demo_analysis(trace: Trace):
    """Demo trace analysis functionality"""
    print("\n📊 Analyzing trace...")
    
    analyzer = TraceAnalyzer(trace)
    result = analyzer.analyze()
    
    print(f"   Total Duration: {result.total_duration_ms}ms")
    print(f"   Total Tokens: {result.total_tokens}")
    print(f"   Total Steps: {result.total_steps}")
    print(f"   Success Rate: {result.success_rate:.1%}")
    print(f"   Error Count: {result.error_count}")
    
    if result.recommendations:
        print("\n💡 Recommendations:")
        for rec in result.recommendations:
            print(f"   - {rec}")
    
    print("✅ Analysis complete")
    
    return result


def demo_export(trace: Trace, analysis):
    """Demo export functionality"""
    print("\n📤 Exporting to different formats...")
    
    # Export to JSON
    json_output = export_trace(trace, analysis, format="json")
    print(f"   JSON: {len(json_output)} characters")
    
    # Export to Markdown
    md_output = export_trace(trace, analysis, format="markdown")
    print(f"   Markdown: {len(md_output)} characters")
    
    # Export to HTML
    html_output = export_trace(trace, analysis, format="html")
    print(f"   HTML: {len(html_output)} characters")
    
    # Export to CSV
    csv_output = export_trace(trace, analysis, format="csv")
    print(f"   CSV: {len(csv_output)} characters")
    
    print("✅ Export complete")


def main():
    """Run all demos"""
    print("=" * 60)
    print("🎬 AgentReplay Demo")
    print("=" * 60)
    
    # Create demo trace
    trace = create_demo_trace()
    
    # Demo replay
    demo_replay(trace)
    
    # Demo analysis
    analysis = demo_analysis(trace)
    
    # Demo export
    demo_export(trace, analysis)
    
    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
