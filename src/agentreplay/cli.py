"""
CLI Interface for AgentReplay
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Optional

from .core import (
    Trace,
    TraceRecorder,
    TracePlayer,
    TraceAnalyzer,
    EventType,
    AgentFramework,
)
from .exporters import export_trace


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser"""
    parser = argparse.ArgumentParser(
        prog="agentreplay",
        description="🎬 AgentReplay - AI Agent Execution Trace Replay & Analysis Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a trace file
  agentreplay analyze trace.json
  
  # Export to different formats
  agentreplay export trace.json --format html --output report.html
  
  # Replay a trace
  agentreplay replay trace.json --speed 2.0
  
  # Create a demo trace
  agentreplay demo --output demo_trace.json
        """,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a trace file")
    analyze_parser.add_argument("trace_file", help="Path to trace JSON file")
    analyze_parser.add_argument("--format", "-f", choices=["json", "markdown", "html", "csv"], default="markdown", help="Output format")
    analyze_parser.add_argument("--output", "-o", help="Output file path")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export trace to different formats")
    export_parser.add_argument("trace_file", help="Path to trace JSON file")
    export_parser.add_argument("--format", "-f", choices=["json", "markdown", "html", "csv"], required=True, help="Export format")
    export_parser.add_argument("--output", "-o", help="Output file path")
    
    # Replay command
    replay_parser = subparsers.add_parser("replay", help="Replay a trace")
    replay_parser.add_argument("trace_file", help="Path to trace JSON file")
    replay_parser.add_argument("--speed", "-s", type=float, default=1.0, help="Playback speed (default: 1.0)")
    replay_parser.add_argument("--filter", "-F", nargs="+", help="Filter event types")
    replay_parser.add_argument("--step", type=int, default=0, help="Start from step number")
    
    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Create a demo trace")
    demo_parser.add_argument("--output", "-o", default="demo_trace.json", help="Output file path")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show trace info")
    info_parser.add_argument("trace_file", help="Path to trace JSON file")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two traces")
    compare_parser.add_argument("trace_file1", help="First trace file")
    compare_parser.add_argument("trace_file2", help="Second trace file")
    compare_parser.add_argument("--output", "-o", help="Output file path")
    
    return parser


def cmd_analyze(args: argparse.Namespace) -> int:
    """Handle analyze command"""
    if not os.path.exists(args.trace_file):
        print(f"❌ Error: File not found: {args.trace_file}")
        return 1
    
    try:
        trace = Trace.load(args.trace_file)
        analyzer = TraceAnalyzer(trace)
        analysis = analyzer.analyze()
        
        output = export_trace(trace, analysis, format=args.format, output_path=args.output)
        
        if not args.output:
            print(output)
        else:
            print(f"✅ Analysis saved to: {args.output}")
        
        return 0
    except Exception as e:
        print(f"❌ Error analyzing trace: {e}")
        return 1


def cmd_export(args: argparse.Namespace) -> int:
    """Handle export command"""
    if not os.path.exists(args.trace_file):
        print(f"❌ Error: File not found: {args.trace_file}")
        return 1
    
    try:
        trace = Trace.load(args.trace_file)
        analyzer = TraceAnalyzer(trace)
        analysis = analyzer.analyze()
        
        output = export_trace(trace, analysis, format=args.format, output_path=args.output)
        
        if args.output:
            print(f"✅ Exported to: {args.output}")
        else:
            print(output)
        
        return 0
    except Exception as e:
        print(f"❌ Error exporting trace: {e}")
        return 1


def cmd_replay(args: argparse.Namespace) -> int:
    """Handle replay command"""
    if not os.path.exists(args.trace_file):
        print(f"❌ Error: File not found: {args.trace_file}")
        return 1
    
    try:
        trace = Trace.load(args.trace_file)
        player = TracePlayer(trace)
        
        event_filter = None
        if args.filter:
            event_filter = [EventType(t) for t in args.filter]
        
        print(f"🎬 Replaying trace: {trace.trace_id}")
        print(f"📊 Steps: {len(trace.steps)}, Events: {trace.total_events}")
        print(f"⚡ Speed: {args.speed}x")
        print("-" * 50)
        
        for event in player.play(speed=args.speed, start_step=args.step, event_filter=event_filter):
            step = player.get_current_step()
            print(f"[Step {step.step_number if step else '?'}] {event.event_type.value}: {event.content[:80]}...")
        
        print("-" * 50)
        print("✅ Playback complete")
        
        return 0
    except Exception as e:
        print(f"❌ Error replaying trace: {e}")
        return 1


def cmd_demo(args: argparse.Namespace) -> int:
    """Handle demo command - create a sample trace"""
    try:
        recorder = TraceRecorder(
            agent_name="DemoAgent",
            framework=AgentFramework.CLAUDE_CODE,
            auto_save=False,
        )
        
        # Start trace
        trace_id = recorder.start_trace(
            task="Analyze Python code and suggest improvements",
            metadata={"version": "1.0", "demo": True},
        )
        
        # Step 1: Read file
        recorder.start_step("Read source file")
        recorder.record_thinking("I need to read the Python file first to understand its structure.", tokens_used=15)
        recorder.record_tool_call("Read", {"file_path": "example.py"}, duration_ms=50)
        recorder.record_tool_result("Read", "def hello():\n    print('Hello, World!')\n", duration_ms=10)
        recorder.end_step()
        
        # Step 2: Analyze code
        recorder.start_step("Analyze code structure")
        recorder.record_thinking("The code is simple. Let me check for potential improvements.", tokens_used=20)
        recorder.record_decision("Add type hints", "Python 3.5+ supports type hints for better code documentation")
        recorder.record_tool_call("Grep", {"pattern": "def ", "path": "."}, duration_ms=30)
        recorder.record_tool_result("Grep", "Found 1 function definition", duration_ms=5)
        recorder.end_step()
        
        # Step 3: Generate suggestions
        recorder.start_step("Generate improvement suggestions")
        recorder.record_thinking("Based on my analysis, I'll suggest improvements.", tokens_used=25)
        recorder.record_message("assistant", "Here are my suggestions:\n1. Add type hints\n2. Add docstring\n3. Use f-strings")
        recorder.record_checkpoint("suggestions_generated", {"count": 3})
        recorder.end_step()
        
        # Step 4: Write improved code (with an error for demo)
        recorder.start_step("Write improved code")
        recorder.record_tool_call("Write", {"file_path": "example_improved.py", "content": "..."}, duration_ms=100)
        recorder.record_error("Permission denied: example_improved.py", error_type="IOError")
        recorder.end_step(success=False, error_message="Failed to write file")
        
        # End trace
        trace = recorder.end_trace()
        
        if trace:
            trace.save(args.output)
            print(f"✅ Demo trace created: {args.output}")
            print(f"📊 Trace ID: {trace.trace_id}")
            print(f"📊 Steps: {len(trace.steps)}")
            print(f"📊 Events: {trace.total_events}")
            print(f"📊 Duration: {trace.duration_ms}ms")
            return 0
        else:
            print("❌ Failed to create demo trace")
            return 1
    
    except Exception as e:
        print(f"❌ Error creating demo: {e}")
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    """Handle info command"""
    if not os.path.exists(args.trace_file):
        print(f"❌ Error: File not found: {args.trace_file}")
        return 1
    
    try:
        trace = Trace.load(args.trace_file)
        
        print(f"🎬 Trace Information")
        print("=" * 50)
        print(f"📋 Trace ID:    {trace.trace_id}")
        print(f"🤖 Agent:       {trace.agent_name}")
        print(f"🔧 Framework:   {trace.framework.value}")
        print(f"📝 Task:        {trace.task}")
        print(f"⏱️  Duration:    {trace.duration_ms:,}ms")
        print(f"🔢 Tokens:      {trace.total_tokens:,}")
        print(f"📊 Steps:       {len(trace.steps)}")
        print(f"📋 Events:      {trace.total_events}")
        print(f"✅ Success:     {trace.success_rate:.1%}")
        
        if trace.start_time:
            print(f"🕐 Start:       {trace.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if trace.end_time:
            print(f"🕐 End:         {trace.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return 0
    except Exception as e:
        print(f"❌ Error reading trace: {e}")
        return 1


def cmd_compare(args: argparse.Namespace) -> int:
    """Handle compare command"""
    if not os.path.exists(args.trace_file1):
        print(f"❌ Error: File not found: {args.trace_file1}")
        return 1
    if not os.path.exists(args.trace_file2):
        print(f"❌ Error: File not found: {args.trace_file2}")
        return 1
    
    try:
        trace1 = Trace.load(args.trace_file1)
        trace2 = Trace.load(args.trace_file2)
        
        analyzer1 = TraceAnalyzer(trace1)
        comparison = analyzer1.compare(trace2)
        
        output = json.dumps(comparison, indent=2, ensure_ascii=False)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"✅ Comparison saved to: {args.output}")
        else:
            print(output)
        
        return 0
    except Exception as e:
        print(f"❌ Error comparing traces: {e}")
        return 1


def main() -> int:
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    commands = {
        "analyze": cmd_analyze,
        "export": cmd_export,
        "replay": cmd_replay,
        "demo": cmd_demo,
        "info": cmd_info,
        "compare": cmd_compare,
    }
    
    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
