"""Minimal workflow engine to orchestrate domain events."""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, DefaultDict, List

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class WorkflowContext:
    """Context data passed to workflow steps."""

    session: Session
    payload: dict[str, Any]


WorkflowStep = Callable[[WorkflowContext], None]


@dataclass(slots=True)
class Workflow:
    """Represents a named workflow bound to a domain event."""

    name: str
    event: str
    steps: List[WorkflowStep]


class WorkflowEngine:
    """Registers workflows and executes them for incoming events."""

    def __init__(self) -> None:
        self._registry: DefaultDict[str, List[Workflow]] = defaultdict(list)

    def clear(self) -> None:
        """Remove all registered workflows (primarily for tests)."""

        self._registry.clear()

    def register(self, workflow: Workflow) -> None:
        """Register a workflow for its associated event."""

        self._registry[workflow.event].append(workflow)
        logger.info(
            "Registered workflow '%s' for event '%s' with %d steps",
            workflow.name,
            workflow.event,
            len(workflow.steps),
        )

    def trigger(
        self,
        event: str,
        *,
        session: Session,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Execute all workflows associated with an event."""

        workflows = self._registry.get(event)
        if not workflows:
            logger.debug("No workflows registered for event '%s'", event)
            return

        context = WorkflowContext(session=session, payload=payload or {})
        for workflow in workflows:
            logger.debug("Executing workflow '%s' for event '%s'", workflow.name, event)
            for step in workflow.steps:
                step_name = getattr(step, "__name__", repr(step))
                try:
                    step(context)
                except Exception as exc:  # noqa: BLE001
                    logger.exception(
                        "Workflow '%s' step '%s' failed: %s",
                        workflow.name,
                        step_name,
                        exc,
                    )

