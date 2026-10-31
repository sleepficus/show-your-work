"""Command line interface for Show Your Work."""

import argparse
import json
import os
import sys

from .core import render_text, run_check


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="showyourwork",
        description="Check an agent's completion report against its evidence. "
                    "Deterministic; no model, no network.")
    sub = parser.add_subparsers(dest="command", required=True)
    chk = sub.add_parser("check", help="grade a report against evidence")
    chk.add_argument("report", help="path to the agent's report (text/markdown)")
    chk.add_argument("--evidence", required=True,
                     help="path to the evidence: a directory or a single file")
    chk.add_argument("--json", action="store_true",
                     help="emit the machine-readable report card (for agents)")
    args = parser.parse_args(argv)

    if args.command == "check":
        if not os.path.isfile(args.report):
            print(f"error: report not found: {args.report}", file=sys.stderr)
            return 2
        if not os.path.exists(args.evidence):
            print(f"error: evidence not found: {args.evidence}", file=sys.stderr)
            return 2
        try:
            result, exit_code = run_check(args.report, args.evidence)
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(render_text(result))
        return exit_code
    return 2


if __name__ == "__main__":
    sys.exit(main())
