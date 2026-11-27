"""Run the project's gate command once, and write its result for the scorecard and the reviewers.

The command is the project's own (`make -k test`, say): the flow never runs a linter or a type
checker of its own, so CI checks exactly what the project checks locally. The output goes to the
job log as it comes, so a tool that prints GitHub annotations (Ruff with RUFF_OUTPUT_FORMAT=github)
marks its findings on the PR's lines.
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

TAIL_LINES = 60
FAILED_TARGET = re.compile(r"make(?:\[\d+\])?: \*\*\* \[(?:[^\]]*?:\d+: )?([^\]]+)\] Error")


def failed_targets(output: str) -> list[str]:
    """The make targets that failed, in order, once each."""
    return list(dict.fromkeys(FAILED_TARGET.findall(output)))


def result(command: str, code: int, output: str, seconds: float) -> dict[str, str]:
    """The gate's result in the scorecard's format."""
    if code == 0:
        return {"check": "gate", "state": "pass", "headline": f"`{command}` passed in {seconds:.0f} s", "details": ""}
    targets = failed_targets(output)
    where = f": {', '.join(targets)}" if targets else ""
    tail = "\n".join(output.rstrip().splitlines()[-TAIL_LINES:])
    return {
        "check": "gate",
        "state": "fail",
        "headline": f"`{command}` failed (exit {code}) in {seconds:.0f} s{where}",
        "details": f"The last {TAIL_LINES} lines of the output:\n\n```\n{tail}\n```",
    }


def run(command: str) -> tuple[int, str]:
    """Run the command in bash, echoing its output as it comes, and return its exit code and output."""
    lines: list[str] = []
    with subprocess.Popen(["bash", "-c", command], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as process:
        assert process.stdout is not None
        for line in process.stdout:
            sys.stdout.write(line)
            lines.append(line)
    return process.returncode, "".join(lines)


def main() -> int:
    """Run the gate and write the result; the job's own verdict reads it."""
    args = _arguments()
    started = time.monotonic()
    code, output = run(args.command)
    gate = result(args.command, code, output, time.monotonic() - started)
    Path(args.result).parent.mkdir(parents=True, exist_ok=True)
    Path(args.result).write_text(json.dumps(gate))
    print(f"gate: {gate['state']}: {gate['headline']}")
    return 0


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", required=True)
    parser.add_argument("--result", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
