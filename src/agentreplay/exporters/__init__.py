"""
Exporters - Export trace analysis to various formats
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import asdict

from ..core.trace import Trace
from ..core.analyzer import TraceAnalysisResult


class BaseExporter:
    """Base class for exporters"""
    
    def __init__(self, output_path: Optional[str] = None):
        self.output_path = output_path
    
    def export(self, trace: Trace, analysis: TraceAnalysisResult) -> str:
        """Export trace and analysis - to be implemented by subclasses"""
        raise NotImplementedError


class JSONExporter(BaseExporter):
    """Export to JSON format"""
    
    def export(self, trace: Trace, analysis: TraceAnalysisResult) -> str:
        """Export to JSON"""
        result = {
            "trace": trace.to_dict(),
            "analysis": self._analysis_to_dict(analysis),
            "exported_at": datetime.now().isoformat(),
        }
        
        output = json.dumps(result, indent=2, ensure_ascii=False)
        
        if self.output_path:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(output)
        
        return output
    
    def _analysis_to_dict(self, analysis: TraceAnalysisResult) -> Dict[str, Any]:
        """Convert analysis result to dictionary"""
        result = asdict(analysis)
        
        # Convert tool stats
        tool_stats_dict = {}
        for name, stats in analysis.tool_stats.items():
            tool_stats_dict[name] = asdict(stats)
        result["tool_stats"] = tool_stats_dict
        
        return result


class MarkdownExporter(BaseExporter):
    """Export to Markdown format"""
    
    def export(self, trace: Trace, analysis: TraceAnalysisResult) -> str:
        """Export to Markdown"""
        lines = []
        
        # Header
        lines.append(f"# Agent Execution Trace Report")
        lines.append("")
        lines.append(f"**Trace ID**: `{trace.trace_id}`")
        lines.append(f"**Agent**: {trace.agent_name}")
        lines.append(f"**Task**: {trace.task}")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Summary
        lines.append("## 📊 Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Duration | {analysis.total_duration_ms:,}ms |")
        lines.append(f"| Total Tokens | {analysis.total_tokens:,} |")
        lines.append(f"| Total Steps | {analysis.total_steps} |")
        lines.append(f"| Total Events | {analysis.total_events} |")
        lines.append(f"| Success Rate | {analysis.success_rate:.1%} |")
        lines.append(f"| Error Count | {analysis.error_count} |")
        lines.append("")
        
        # Step Statistics
        lines.append("## 📈 Step Statistics")
        lines.append("")
        lines.append(f"- **Average Step Duration**: {analysis.avg_step_duration_ms:.1f}ms")
        lines.append(f"- **Max Step Duration**: {analysis.max_step_duration_ms:,}ms")
        lines.append(f"- **Min Step Duration**: {analysis.min_step_duration_ms:,}ms")
        lines.append(f"- **Average Tokens per Step**: {analysis.avg_tokens_per_step:.1f}")
        lines.append("")
        
        # Event Distribution
        if analysis.events_by_type:
            lines.append("## 📋 Event Distribution")
            lines.append("")
            lines.append("| Event Type | Count |")
            lines.append("|------------|-------|")
            for event_type, count in sorted(analysis.events_by_type.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"| {event_type} | {count} |")
            lines.append("")
        
        # Tool Usage
        if analysis.tool_stats:
            lines.append("## 🔧 Tool Usage")
            lines.append("")
            lines.append("| Tool | Calls | Success | Failures | Avg Duration |")
            lines.append("|------|-------|---------|----------|--------------|")
            for tool_name, stats in sorted(analysis.tool_stats.items(), key=lambda x: x[1].call_count, reverse=True):
                lines.append(f"| {tool_name} | {stats.call_count} | {stats.success_count} | {stats.failure_count} | {stats.avg_duration_ms:.1f}ms |")
            lines.append("")
        
        # Errors
        if analysis.errors:
            lines.append("## ❌ Errors")
            lines.append("")
            for error in analysis.errors:
                lines.append(f"### Step {error['step_number']}")
                lines.append(f"- **Type**: {error['error_type']}")
                lines.append(f"- **Message**: {error['error_message']}")
                lines.append("")
        
        # Bottlenecks
        if analysis.bottlenecks:
            lines.append("## ⚠️ Bottlenecks")
            lines.append("")
            for bottleneck in analysis.bottlenecks:
                lines.append(f"- {bottleneck['message']}")
            lines.append("")
        
        # Recommendations
        if analysis.recommendations:
            lines.append("## 💡 Recommendations")
            lines.append("")
            for i, rec in enumerate(analysis.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        
        # Step Details
        lines.append("## 📝 Step Details")
        lines.append("")
        for step_analysis in analysis.step_analyses:
            status = "✅" if step_analysis.success else "❌"
            lines.append(f"### {status} Step {step_analysis.step_number}")
            lines.append(f"- **Duration**: {step_analysis.duration_ms}ms")
            lines.append(f"- **Tokens**: {step_analysis.tokens_used}")
            lines.append(f"- **Events**: {step_analysis.event_count}")
            if step_analysis.tool_calls:
                lines.append(f"- **Tools Used**: {', '.join(step_analysis.tool_calls)}")
            if step_analysis.error_message:
                lines.append(f"- **Error**: {step_analysis.error_message}")
            lines.append("")
        
        output = "\n".join(lines)
        
        if self.output_path:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(output)
        
        return output


class HTMLExporter(BaseExporter):
    """Export to HTML format with interactive visualization"""
    
    def export(self, trace: Trace, analysis: TraceAnalysisResult) -> str:
        """Export to HTML"""
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Trace Report - {trace.trace_id}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #22d3ee; margin-bottom: 20px; }}
        h2 {{ color: #a78bfa; margin: 20px 0 10px; border-bottom: 1px solid #334155; padding-bottom: 10px; }}
        .header {{ background: linear-gradient(135deg, #1e293b, #0f172a); padding: 20px; border-radius: 12px; margin-bottom: 20px; }}
        .header p {{ margin: 5px 0; color: #94a3b8; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: #1e293b; padding: 20px; border-radius: 12px; text-align: center; }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #22d3ee; }}
        .stat-label {{ color: #94a3b8; font-size: 0.9em; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #334155; }}
        th {{ background: #1e293b; color: #a78bfa; }}
        tr:hover {{ background: #1e293b; }}
        .success {{ color: #22c55e; }}
        .error {{ color: #ef4444; }}
        .warning {{ color: #f59e0b; }}
        .recommendation {{ background: #1e293b; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #22d3ee; }}
        .bottleneck {{ background: #1e293b; padding: 15px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #f59e0b; }}
        .step {{ background: #1e293b; padding: 15px; border-radius: 8px; margin: 10px 0; }}
        .step-header {{ display: flex; justify-content: space-between; align-items: center; }}
        .step-status {{ font-size: 1.2em; }}
        .progress-bar {{ height: 8px; background: #334155; border-radius: 4px; overflow: hidden; margin: 10px 0; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #22d3ee, #a78bfa); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 Agent Execution Trace Report</h1>
            <p><strong>Trace ID:</strong> {trace.trace_id}</p>
            <p><strong>Agent:</strong> {trace.agent_name}</p>
            <p><strong>Task:</strong> {trace.task}</p>
            <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{analysis.total_duration_ms:,}ms</div>
                <div class="stat-label">Total Duration</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{analysis.total_tokens:,}</div>
                <div class="stat-label">Total Tokens</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{analysis.total_steps}</div>
                <div class="stat-label">Total Steps</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{analysis.success_rate:.1%}</div>
                <div class="stat-label">Success Rate</div>
            </div>
        </div>
        
        <h2>📊 Event Distribution</h2>
        <table>
            <tr><th>Event Type</th><th>Count</th></tr>
            {self._render_event_rows(analysis)}
        </table>
        
        <h2>🔧 Tool Usage</h2>
        <table>
            <tr><th>Tool</th><th>Calls</th><th>Success</th><th>Failures</th><th>Avg Duration</th></tr>
            {self._render_tool_rows(analysis)}
        </table>
        
        {self._render_errors_section(analysis)}
        {self._render_bottlenecks_section(analysis)}
        {self._render_recommendations_section(analysis)}
    </div>
</body>
</html>'''
        
        if self.output_path:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(html)
        
        return html
    
    def _render_event_rows(self, analysis: TraceAnalysisResult) -> str:
        rows = []
        for event_type, count in sorted(analysis.events_by_type.items(), key=lambda x: x[1], reverse=True):
            rows.append(f"<tr><td>{event_type}</td><td>{count}</td></tr>")
        return "\n".join(rows)
    
    def _render_tool_rows(self, analysis: TraceAnalysisResult) -> str:
        rows = []
        for tool_name, stats in sorted(analysis.tool_stats.items(), key=lambda x: x[1].call_count, reverse=True):
            rows.append(f"<tr><td>{tool_name}</td><td>{stats.call_count}</td><td class='success'>{stats.success_count}</td><td class='error'>{stats.failure_count}</td><td>{stats.avg_duration_ms:.1f}ms</td></tr>")
        return "\n".join(rows)
    
    def _render_errors_section(self, analysis: TraceAnalysisResult) -> str:
        if not analysis.errors:
            return ""
        rows = []
        for error in analysis.errors:
            rows.append(f"<div class='step'><strong>Step {error['step_number']}</strong>: {error['error_message']}</div>")
        return f"<h2>❌ Errors</h2>" + "\n".join(rows)
    
    def _render_bottlenecks_section(self, analysis: TraceAnalysisResult) -> str:
        if not analysis.bottlenecks:
            return ""
        items = [f"<div class='bottleneck'>⚠️ {b['message']}</div>" for b in analysis.bottlenecks]
        return f"<h2>⚠️ Bottlenecks</h2>" + "\n".join(items)
    
    def _render_recommendations_section(self, analysis: TraceAnalysisResult) -> str:
        if not analysis.recommendations:
            return ""
        items = [f"<div class='recommendation'>💡 {r}</div>" for r in analysis.recommendations]
        return f"<h2>💡 Recommendations</h2>" + "\n".join(items)


class CSVExporter(BaseExporter):
    """Export to CSV format"""
    
    def export(self, trace: Trace, analysis: TraceAnalysisResult) -> str:
        """Export to CSV"""
        lines = []
        
        # Header
        lines.append("step_number,event_type,content,duration_ms,tokens_used,timestamp")
        
        # Data rows
        for step in trace.steps:
            for event in step.events:
                content = event.content.replace('"', '""')[:100]
                lines.append(f'{step.step_number},{event.event_type.value},"{content}",{event.duration_ms or 0},{event.tokens_used or 0},{event.timestamp.isoformat()}')
        
        output = "\n".join(lines)
        
        if self.output_path:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                f.write(output)
        
        return output


def export_trace(
    trace: Trace,
    analysis: TraceAnalysisResult,
    format: str = "json",
    output_path: Optional[str] = None,
) -> str:
    """
    Export trace to specified format.
    
    Args:
        trace: The trace to export
        analysis: The analysis result
        format: Export format (json, markdown, html, csv)
        output_path: Optional file path to save output
        
    Returns:
        Exported content as string
    """
    exporters = {
        "json": JSONExporter,
        "markdown": MarkdownExporter,
        "md": MarkdownExporter,
        "html": HTMLExporter,
        "csv": CSVExporter,
    }
    
    exporter_class = exporters.get(format.lower())
    if not exporter_class:
        raise ValueError(f"Unsupported format: {format}. Supported: {list(exporters.keys())}")
    
    exporter = exporter_class(output_path)
    return exporter.export(trace, analysis)
