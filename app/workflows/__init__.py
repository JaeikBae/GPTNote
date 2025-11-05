"""Workflow management for MindDock."""

from __future__ import annotations

from .engine import Workflow, WorkflowContext, WorkflowEngine

workflow_engine = WorkflowEngine()
_initialized = False


def initialize_workflows() -> None:
    """Register default workflows once per process."""

    global _initialized
    if _initialized:
        return

    from .defaults import register_default_workflows

    register_default_workflows(workflow_engine)
    _initialized = True


__all__ = [
    "WorkflowEngine",
    "WorkflowContext",
    "Workflow",
    "workflow_engine",
    "initialize_workflows",
]

