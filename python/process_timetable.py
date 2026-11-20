#!/usr/bin/env python3
"""CLI entrypoint called by Laravel via Symfony Process (DETAIL_DESIGN §8.3).

    python3 process_timetable.py <command> --job-dir <path>

Commands:
    check        Diagnostics: dependency versions + config validity, printed as JSON on stdout.
    list-weeks   -> <job-dir>/weeks.json
    analyze      -> <job-dir>/analysis.json   (reads request.json)
    generate     -> <job-dir>/generate.json + result.xlsx   (reads request.json, analysis.json)

Contract for job commands: results go to a JSON file in the job dir, never to stdout;
logs go to stderr as JSON lines. Exit codes: 0 ok, 1 business error (written to the
result file), 2 system/unexpected error.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

EXIT_OK, EXIT_BUSINESS_ERROR, EXIT_SYSTEM_ERROR = 0, 1, 2

RESULT_FILES = {
    "list-weeks": "weeks.json",
    "analyze": "analysis.json",
    "generate": "generate.json",
}


def log(event: str, **fields) -> None:
    print(json.dumps({"event": event, **fields}, ensure_ascii=False), file=sys.stderr)


def write_result(job_dir: Path, command: str, payload: dict) -> None:
    (job_dir / RESULT_FILES[command]).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def cmd_check() -> int:
    import lxml.etree
    import openpyxl

    from common.config import load_config

    config = load_config()
    print(json.dumps({
        "status": "ok",
        "python": sys.version.split()[0],
        "openpyxl": openpyxl.__version__,
        "lxml": lxml.etree.__version__,
        "profile_id": config.profile["profile_id"],
        "slots_per_week": len(config.slot_rows()),
    }, ensure_ascii=False))
    return EXIT_OK


def cmd_job(command: str, job_dir: Path) -> int:
    from common import jobs
    from common.errors import EngineError

    if not job_dir.is_dir():
        log("job_dir_missing", command=command)
        return EXIT_SYSTEM_ERROR

    handler = {"list-weeks": jobs.list_weeks, "analyze": jobs.analyze, "generate": jobs.generate}[command]
    started = time.monotonic()
    try:
        payload = handler(job_dir)
    except EngineError as exc:
        write_result(job_dir, command, {"success": False, "error": exc.to_dict()})
        log("business_error", command=command, code=exc.code, duration_ms=_ms(started))
        return EXIT_BUSINESS_ERROR

    if command != "analyze":  # analyze writes analysis.json itself (generate re-reads it)
        write_result(job_dir, command, payload)
    log("done", command=command, duration_ms=_ms(started))
    return EXIT_OK


def _ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Teacher Workspace timetable engine")
    parser.add_argument("command", choices=["check", *RESULT_FILES])
    parser.add_argument("--job-dir", type=Path)
    args = parser.parse_args(argv)

    try:
        if args.command == "check":
            return cmd_check()
        if args.job_dir is None:
            parser.error("--job-dir is required for job commands")
        return cmd_job(args.command, args.job_dir)
    except Exception as exc:  # noqa: BLE001 — last-resort guard; Laravel maps exit 2 to a system error
        log("unhandled_error", command=args.command, error=type(exc).__name__, detail=str(exc))
        return EXIT_SYSTEM_ERROR


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.exit(main())
