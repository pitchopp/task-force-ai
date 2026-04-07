from typing import Literal

RiskLevel = Literal["low", "medium", "high", "critical"]
RiskAction = Literal["auto", "review", "approve"]

# (risk_level, tool_pattern) -> action
# More specific rules take precedence
_RISK_RULES: list[tuple[RiskLevel, str, RiskAction]] = [
    ("low", "*", "auto"),
    ("medium", "Read", "auto"),
    ("medium", "Glob", "auto"),
    ("medium", "Grep", "auto"),
    ("medium", "Write", "review"),
    ("medium", "Edit", "review"),
    ("medium", "Bash", "approve"),
    ("high", "Read", "auto"),
    ("high", "Glob", "auto"),
    ("high", "Grep", "auto"),
    ("high", "*", "approve"),
    ("critical", "*", "approve"),
]


def assess_risk(agent_risk_level: RiskLevel, tool_name: str) -> RiskAction:
    """Determine whether a tool call needs approval based on agent risk level."""
    result: RiskAction = "auto"
    for level, pattern, action in _RISK_RULES:
        if level != agent_risk_level:
            continue
        if pattern == "*" or pattern == tool_name:
            result = action
    return result


def needs_approval(agent_risk_level: RiskLevel, tool_name: str) -> bool:
    return assess_risk(agent_risk_level, tool_name) == "approve"
