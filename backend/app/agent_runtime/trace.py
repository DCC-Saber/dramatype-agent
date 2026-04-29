"""Execution trace recorder for the Agent runtime."""

from app.agent_runtime.schemas import AgentStep, ToolCall, AgentObservation


class TraceRecorder:
    """Collects AgentStep records during a run."""

    def __init__(self):
        self.steps: list[AgentStep] = []

    def record(
        self,
        phase: str,
        tool_name: str,
        arguments: dict | None = None,
        success: bool = True,
        data=None,
        error: str | None = None,
        decision_summary: str = "",
        status: str = "completed",
    ) -> AgentStep:
        step = AgentStep(
            step_index=len(self.steps) + 1,
            phase=phase,
            tool_call=ToolCall(
                tool_name=tool_name,
                arguments=arguments or {},
            ),
            observation=AgentObservation(
                success=success,
                data=data,
                error=error,
            ),
            decision_summary=decision_summary,
            status=status,
        )
        self.steps.append(step)
        return step

    def to_list(self) -> list[AgentStep]:
        return list(self.steps)
