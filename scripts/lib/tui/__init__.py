"""Guarded operator console for ez-comfy-stack.

A single curses front end over the operator CLI. The package is a dispatcher:
it describes every ``manage.sh`` verb and every unmanaged utility as data, reads
the machine through the scripts that already own those answers, and refuses
anything the safety layer would refuse. See :mod:`tui.contract` for the shared
vocabulary and :mod:`tui.cli` for the entry point.
"""

from __future__ import annotations
