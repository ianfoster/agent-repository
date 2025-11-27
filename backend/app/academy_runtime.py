# backend/app/academy_runtime.py

from __future__ import annotations

import asyncio
import importlib
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor

from academy.exchange import LocalExchangeFactory
from academy.manager import Manager
from .models import AgentImplementation


@dataclass
class RuntimeEnv:
  ctx: Any  # the context manager returned by from_exchange_factory
  manager: Manager
  handles: Dict[str, Any] = field(default_factory=dict)

_env: Optional[RuntimeEnv] = None

async def get_or_create_manager() -> RuntimeEnv:
  """
  Lazily create a single Manager using LocalExchangeFactory and reuse it.

  We use Manager.from_exchange_factory(...) as per Academy docs.
  """
  global _env
  if _env is not None:
    return _env

  # Create an async context manager that will yield a Manager
  ctx = await Manager.from_exchange_factory(
    factory=LocalExchangeFactory(),
    executors=ThreadPoolExecutor(),
  )
  # Enter the context to get the Manager instance
  manager = await ctx.__aenter__()

  _env = RuntimeEnv(ctx=ctx, manager=manager)
  return _env


async def start_academy_instance(agent_impl: AgentImplementation) -> str:
    """
    Launch an Academy-based agent instance from an AgentImplementation and return an instance_id.

    For now, we only support local thread-based execution.
    """
    env = await get_or_create_manager()

    if not agent_impl.entrypoint:
        raise RuntimeError("Agent has no entrypoint configured")

    if ":" not in agent_impl.entrypoint:
        raise RuntimeError(f"Invalid entrypoint {agent_impl.entrypoint!r}, expected 'module:Class'")

    module_path, class_name = agent_impl.entrypoint.split(":", 1)
    module = importlib.import_module(module_path)
    agent_cls = getattr(module, class_name)

    # Instantiate behavior and launch via Manager
    behavior = agent_cls()
    handle = env.manager.launch(behavior)

    instance_id = str(uuid.uuid4())
    env.handles[instance_id] = handle
    return instance_id


async def call_instance_action(instance_id: str, action: str, payload: Dict[str, Any]) -> Any:
    """
    Call a named action on a running instance by ID.

    This is a first sketch; you'd want better error handling and type checking later.
    """
    env = await get_or_create_manager()
    handle = env.handles.get(instance_id)
    if handle is None:
        raise RuntimeError(f"No instance with id {instance_id!r}")

    # For now, assume the action exists and returns an awaitable
    method = getattr(handle, action)
    result = await method(**payload)
    return result


async def stop_instance(instance_id: str) -> None:
    """
    Stop a running instance and forget its handle.
    """
    env = await get_or_create_manager()
    handle = env.handles.pop(instance_id, None)
    if handle is None:
        return

    # In a full implementation, you'd use env.manager.shutdown(handle)
    # Here we just drop the reference and rely on process shutdown
    # for the simple thread-based example.
