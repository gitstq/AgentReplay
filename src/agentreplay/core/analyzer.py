"""
Trace Analyzer - Analyze agent execution traces
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import statistics

from .trace import Trace, TraceEvent, TraceStep, EventType


@dataclass
class ToolUsageStats:
    """Statistics for tool usage"""
    tool_name: str
    call_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_duration_ms: int = 0
    avg_duration_ms: float = 0.0
    min_duration_ms: int = 0
    max_duration_ms: int = 0


@dataclass
class StepAnalysis:
    """Analysis results for a single step"""
    step_id: str
    step_number: int
    duration_ms: int
    tokens_used: int
    event_count: int
    success: bool
    error_message: Optional[str]
    tool_calls: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)


@dataclass
class TraceAnalysisResult:
    """Complete analysis result for a trace"""
    trace_id: str
    agent_name: str
    task: str
    
    # Time statistics
    total_duration_ms: int = 0
    avg_step_duration_ms: float = 0.0
    max_step_duration_ms: int = 0
    min_step_duration_ms: int = 0
    
    # Token statistics
    total_tokens: int = 0
    avg_tokens_per_step: float = 0.0
    tokens_by_event_type: Dict[str, int] = field(default_factory=dict)
    
    # Step statistics
    total_steps: int = 0
    successful_steps: int = 0
    failed_steps: int = 0
    success_rate: float = 0.0
    
    # Event statistics
    total_events: int = 0
    events_by_type: Dict[str, int] = field(default_factory=dict)
    
    # Tool statistics
    tool_stats: Dict[str, ToolUsageStats] = field(default_factory=dict)
    most_used_tools: List[str] = field(default_factory=list)
    
    # Error analysis
    error_count: int = 0
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    # Decision analysis
    decision_count: int = 0
    decisions: List[str] = field(default_factory=list)
    
    # Performance insights
    bottlenecks: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Step-by-step analysis
    step_analyses: List[StepAnalysis] = field(default_factory=list)


class TraceAnalyzer:
    """
    Analyze agent execution traces for insights and optimization.
    
    Provides comprehensive analysis including:
    - Performance metrics
    - Tool usage patterns
    - Error patterns
    - Decision analysis
    - Optimization recommendations
    """
    
    def __init__(self, trace: Trace):
        self.trace = trace
    
    def analyze(self) -> TraceAnalysisResult:
        """
        Perform comprehensive analysis of the trace.
        
        Returns:
            Complete analysis result
        """
        result = TraceAnalysisResult(
            trace_id=self.trace.trace_id,
            agent_name=self.trace.agent_name,
            task=self.trace.task,
        )
        
        # Basic statistics
        result.total_steps = len(self.trace.steps)
        result.total_events = self.trace.total_events
        result.total_duration_ms = self.trace.duration_ms
        result.total_tokens = self.trace.total_tokens
        
        # Analyze each step
        step_durations = []
        step_tokens = []
        
        for step in self.trace.steps:
            step_analysis = self._analyze_step(step)
            result.step_analyses.append(step_analysis)
            
            step_durations.append(step.duration_ms)
            step_tokens.append(step.total_tokens)
            
            if step.success:
                result.successful_steps += 1
            else:
                result.failed_steps += 1
        
        # Calculate step statistics
        if step_durations:
            result.avg_step_duration_ms = statistics.mean(step_durations)
            result.max_step_duration_ms = max(step_durations)
            result.min_step_duration_ms = min(step_durations)
        
        if step_tokens:
            result.avg_tokens_per_step = statistics.mean(step_tokens)
        
        result.success_rate = (
            result.successful_steps / result.total_steps 
            if result.total_steps > 0 else 0.0
        )
        
        # Analyze events
        self._analyze_events(result)
        
        # Analyze tools
        self._analyze_tools(result)
        
        # Analyze errors
        self._analyze_errors(result)
        
        # Analyze decisions
        self._analyze_decisions(result)
        
        # Find bottlenecks
        self._find_bottlenecks(result)
        
        # Generate recommendations
        self._generate_recommendations(result)
        
        return result
    
    def _analyze_step(self, step: TraceStep) -> StepAnalysis:
        """Analyze a single step"""
        analysis = StepAnalysis(
            step_id=step.step_id,
            step_number=step.step_number,
            duration_ms=step.duration_ms,
            tokens_used=step.total_tokens,
            event_count=len(step.events),
            success=step.success,
            error_message=step.error_message,
        )
        
        for event in step.events:
            if event.event_type == EventType.TOOL_CALL:
                tool_name = event.metadata.get("tool_name", "unknown")
                analysis.tool_calls.append(tool_name)
            elif event.event_type == EventType.DECISION:
                analysis.decisions.append(event.content)
        
        return analysis
    
    def _analyze_events(self, result: TraceAnalysisResult) -> None:
        """Analyze event distribution"""
        events_by_type: Dict[str, int] = defaultdict(int)
        tokens_by_type: Dict[str, int] = defaultdict(int)
        
        for step in self.trace.steps:
            for event in step.events:
                event_type = event.event_type.value
                events_by_type[event_type] += 1
                
                if event.tokens_used:
                    tokens_by_type[event_type] += event.tokens_used
        
        result.events_by_type = dict(events_by_type)
        result.tokens_by_event_type = dict(tokens_by_type)
    
    def _analyze_tools(self, result: TraceAnalysisResult) -> None:
        """Analyze tool usage patterns"""
        tool_stats: Dict[str, ToolUsageStats] = {}
        tool_durations: Dict[str, List[int]] = defaultdict(list)
        
        for step in self.trace.steps:
            for event in step.events:
                if event.event_type == EventType.TOOL_CALL:
                    tool_name = event.metadata.get("tool_name", "unknown")
                    
                    if tool_name not in tool_stats:
                        tool_stats[tool_name] = ToolUsageStats(tool_name=tool_name)
                    
                    tool_stats[tool_name].call_count += 1
                    
                    if event.duration_ms:
                        tool_durations[tool_name].append(event.duration_ms)
                        tool_stats[tool_name].total_duration_ms += event.duration_ms
                
                elif event.event_type == EventType.TOOL_RESULT:
                    tool_name = event.metadata.get("tool_name", "unknown")
                    
                    if tool_name in tool_stats:
                        if event.metadata.get("success", True):
                            tool_stats[tool_name].success_count += 1
                        else:
                            tool_stats[tool_name].failure_count += 1
        
        # Calculate averages
        for tool_name, stats in tool_stats.items():
            if tool_durations[tool_name]:
                stats.avg_duration_ms = statistics.mean(tool_durations[tool_name])
                stats.min_duration_ms = min(tool_durations[tool_name])
                stats.max_duration_ms = max(tool_durations[tool_name])
        
        result.tool_stats = tool_stats
        
        # Find most used tools
        sorted_tools = sorted(
            tool_stats.items(),
            key=lambda x: x[1].call_count,
            reverse=True
        )
        result.most_used_tools = [name for name, _ in sorted_tools[:5]]
    
    def _analyze_errors(self, result: TraceAnalysisResult) -> None:
        """Analyze error patterns"""
        errors = []
        
        for step in self.trace.steps:
            for event in step.events:
                if event.event_type == EventType.ERROR:
                    errors.append({
                        "step_id": step.step_id,
                        "step_number": step.step_number,
                        "error_message": event.content,
                        "error_type": event.metadata.get("error_type", "unknown"),
                        "timestamp": event.timestamp.isoformat(),
                    })
        
        result.errors = errors
        result.error_count = len(errors)
    
    def _analyze_decisions(self, result: TraceAnalysisResult) -> None:
        """Analyze decision patterns"""
        decisions = []
        
        for step in self.trace.steps:
            for event in step.events:
                if event.event_type == EventType.DECISION:
                    decisions.append(event.content)
        
        result.decisions = decisions
        result.decision_count = len(decisions)
    
    def _find_bottlenecks(self, result: TraceAnalysisResult) -> None:
        """Identify performance bottlenecks"""
        bottlenecks = []
        
        # Find slow steps (above average + 1 std dev)
        if result.step_analyses:
            durations = [s.duration_ms for s in result.step_analyses]
            if len(durations) > 1:
                avg = statistics.mean(durations)
                std = statistics.stdev(durations)
                threshold = avg + std
                
                for step_analysis in result.step_analyses:
                    if step_analysis.duration_ms > threshold:
                        bottlenecks.append({
                            "type": "slow_step",
                            "step_number": step_analysis.step_number,
                            "duration_ms": step_analysis.duration_ms,
                            "threshold_ms": threshold,
                            "message": f"Step {step_analysis.step_number} took {step_analysis.duration_ms}ms (threshold: {threshold:.0f}ms)",
                        })
        
        # Find tools with high failure rates
        for tool_name, stats in result.tool_stats.items():
            if stats.call_count > 0:
                failure_rate = stats.failure_count / stats.call_count
                if failure_rate > 0.2:  # More than 20% failure rate
                    bottlenecks.append({
                        "type": "high_failure_tool",
                        "tool_name": tool_name,
                        "failure_rate": failure_rate,
                        "message": f"Tool '{tool_name}' has {failure_rate:.1%} failure rate",
                    })
        
        result.bottlenecks = bottlenecks
    
    def _generate_recommendations(self, result: TraceAnalysisResult) -> None:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Token optimization
        if result.total_tokens > 10000:
            recommendations.append(
                "Consider implementing context compression to reduce token usage"
            )
        
        # Step optimization
        if result.avg_step_duration_ms > 5000:
            recommendations.append(
                "Average step duration is high - consider parallelizing tool calls"
            )
        
        # Error handling
        if result.error_count > 0:
            error_rate = result.error_count / result.total_events if result.total_events > 0 else 0
            if error_rate > 0.05:
                recommendations.append(
                    f"Error rate is {error_rate:.1%} - improve error handling and retry logic"
                )
        
        # Tool usage optimization
        if len(result.most_used_tools) > 0:
            top_tool = result.most_used_tools[0]
            if top_tool in result.tool_stats:
                stats = result.tool_stats[top_tool]
                if stats.avg_duration_ms > 1000:
                    recommendations.append(
                        f"Most used tool '{top_tool}' has high average duration ({stats.avg_duration_ms:.0f}ms) - consider caching or optimization"
                    )
        
        # Success rate
        if result.success_rate < 0.9:
            recommendations.append(
                f"Success rate is {result.success_rate:.1%} - investigate failed steps"
            )
        
        result.recommendations = recommendations
    
    def compare(self, other_trace: Trace) -> Dict[str, Any]:
        """
        Compare this trace with another trace.
        
        Args:
            other_trace: Another trace to compare with
            
        Returns:
            Comparison results
        """
        other_analyzer = TraceAnalyzer(other_trace)
        other_result = other_analyzer.analyze()
        self_result = self.analyze()
        
        return {
            "trace_1": {
                "id": self_result.trace_id,
                "duration_ms": self_result.total_duration_ms,
                "tokens": self_result.total_tokens,
                "steps": self_result.total_steps,
                "success_rate": self_result.success_rate,
            },
            "trace_2": {
                "id": other_result.trace_id,
                "duration_ms": other_result.total_duration_ms,
                "tokens": other_result.total_tokens,
                "steps": other_result.total_steps,
                "success_rate": other_result.success_rate,
            },
            "differences": {
                "duration_diff_ms": self_result.total_duration_ms - other_result.total_duration_ms,
                "tokens_diff": self_result.total_tokens - other_result.total_tokens,
                "success_rate_diff": self_result.success_rate - other_result.success_rate,
            },
            "tool_usage_diff": self._compare_tool_usage(self_result, other_result),
        }
    
    def _compare_tool_usage(
        self,
        result1: TraceAnalysisResult,
        result2: TraceAnalysisResult
    ) -> Dict[str, Any]:
        """Compare tool usage between two traces"""
        tools1 = set(result1.tool_stats.keys())
        tools2 = set(result2.tool_stats.keys())
        
        return {
            "only_in_trace_1": list(tools1 - tools2),
            "only_in_trace_2": list(tools2 - tools1),
            "common_tools": list(tools1 & tools2),
        }
    
    def get_timeline(self) -> List[Dict[str, Any]]:
        """
        Get a timeline view of the trace.
        
        Returns:
            List of timeline events
        """
        timeline = []
        
        for step in self.trace.steps:
            for event in step.events:
                timeline.append({
                    "timestamp": event.timestamp.isoformat(),
                    "step_number": step.step_number,
                    "event_type": event.event_type.value,
                    "content": event.content[:100] + "..." if len(event.content) > 100 else event.content,
                    "duration_ms": event.duration_ms,
                    "tokens_used": event.tokens_used,
                })
        
        return timeline
