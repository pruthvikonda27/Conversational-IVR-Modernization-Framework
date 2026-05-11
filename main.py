"""
Root ASGI entrypoint.

This wrapper lets you run:
  uvicorn main:app --reload

from the repository root.
"""

from __future__ import annotations

from Milestone2.backend import app

