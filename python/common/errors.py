"""Structured errors/warnings shared by the engine and the CLI (codes: DETAIL_DESIGN §9.7)."""

from __future__ import annotations


def issue(code: str, message: str, **details) -> dict:
    """A warning/error entry as it appears in the JSON results."""
    return {"code": code, "message": message, "details": details}


class EngineError(Exception):
    """Business error that stops the whole command (CLI exit code 1)."""

    def __init__(self, code: str, message: str, **details):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details

    def to_dict(self) -> dict:
        return issue(self.code, self.message, **self.details)
