import asyncio
import logging
import uuid

from taskforce.storage.redis_client import get_redis

logger = logging.getLogger(__name__)

APPROVAL_TIMEOUT = 300  # 5 minutes
APPROVAL_KEY_PREFIX = "approval:"


async def create_approval_request(
    task_id: str,
    chat_id: int,
    action_description: str,
    risk_level: str,
) -> str:
    """Create a pending approval request in Redis. Returns the approval ID."""
    approval_id = str(uuid.uuid4())
    r = await get_redis()

    await r.hset(
        f"{APPROVAL_KEY_PREFIX}{approval_id}",
        mapping={
            "task_id": task_id,
            "chat_id": str(chat_id),
            "action": action_description,
            "risk_level": risk_level,
            "status": "pending",
        },
    )
    await r.expire(f"{APPROVAL_KEY_PREFIX}{approval_id}", APPROVAL_TIMEOUT)

    return approval_id


async def wait_for_decision(approval_id: str, timeout: int = APPROVAL_TIMEOUT) -> str:
    """Wait for user to approve or deny. Returns 'approved', 'denied', or 'timeout'."""
    r = await get_redis()
    decision_key = f"{APPROVAL_KEY_PREFIX}{approval_id}:decision"

    result = await r.blpop(decision_key, timeout=timeout)
    if result is None:
        return "timeout"

    return result[1]  # "approved" or "denied"


async def submit_decision(approval_id: str, decision: str) -> bool:
    """Submit a decision (approved/denied) for a pending approval."""
    r = await get_redis()
    key = f"{APPROVAL_KEY_PREFIX}{approval_id}"

    exists = await r.exists(key)
    if not exists:
        return False

    await r.hset(key, "status", decision)
    await r.lpush(f"{key}:decision", decision)

    return True


async def get_approval_info(approval_id: str) -> dict | None:
    """Get approval request info."""
    r = await get_redis()
    data = await r.hgetall(f"{APPROVAL_KEY_PREFIX}{approval_id}")
    return data if data else None
