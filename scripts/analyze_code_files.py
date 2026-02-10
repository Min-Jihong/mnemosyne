#!/usr/bin/env python3
"""
Code size analysis script.

Analyzes Python files for lines of code and complexity,
failing CI if any file exceeds the threshold.

Usage:
    python scripts/analyze_code_files.py --threshold 500 --strict
"""

import argparse
import sys
from pathlib import Path


def count_lines(file_path: Path) -> tuple[int, int, int]:
    """Count total lines, code lines, and comment lines in a file."""
    total = 0
    code = 0
    comments = 0
    in_docstring = False
    docstring_char = None

    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0, 0, 0

    for line in content.splitlines():
        total += 1
        stripped = line.strip()

        if not stripped:
            continue

        if in_docstring:
            comments += 1
            if docstring_char and docstring_char in stripped:
                in_docstring = False
                docstring_char = None
            continue

        if stripped.startswith('"""') or stripped.startswith("'''"):
            docstring_char = stripped[:3]
            comments += 1
            if stripped.count(docstring_char) >= 2 and len(stripped) > 3:
                continue
            in_docstring = True
            continue

        if stripped.startswith("#"):
            comments += 1
            continue

        code += 1

    return total, code, comments


def analyze_directory(
    directory: Path,
    threshold: int,
    strict: bool = False,
) -> list[dict]:
    """Analyze all Python files in directory."""
    results = []
    violations = []

    python_files = list(directory.rglob("*.py"))
    python_files = [f for f in python_files if "__pycache__" not in str(f)]

    for file_path in sorted(python_files):
        total, code, comments = count_lines(file_path)

        relative_path = file_path.relative_to(directory)
        result = {
            "file": str(relative_path),
            "total_lines": total,
            "code_lines": code,
            "comment_lines": comments,
            "exceeds_threshold": code > threshold,
        }
        results.append(result)

        if code > threshold:
            violations.append(result)

    return results, violations


def print_report(results: list[dict], threshold: int):
    """Print analysis report."""
    print("\n" + "=" * 70)
    print("CODE SIZE ANALYSIS REPORT")
    print("=" * 70)
    print(f"\nThreshold: {threshold} lines of code\n")

    print(f"{'File':<50} {'Code':<8} {'Total':<8} {'Status'}")
    print("-" * 70)

    for r in sorted(results, key=lambda x: x["code_lines"], reverse=True)[:20]:
        status = "EXCEEDS" if r["exceeds_threshold"] else "OK"
        print(f"{r['file']:<50} {r['code_lines']:<8} {r['total_lines']:<8} {status}")

    total_files = len(results)
    total_code = sum(r["code_lines"] for r in results)
    violations = sum(1 for r in results if r["exceeds_threshold"])

    print("\n" + "-" * 70)
    print(f"Total files: {total_files}")
    print(f"Total code lines: {total_code}")
    print(f"Average lines per file: {total_code // total_files if total_files else 0}")
    print(f"Files exceeding threshold: {violations}")


def main():
    parser = argparse.ArgumentParser(description="Analyze code file sizes")
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path("mnemosyne"),
        help="Directory to analyze",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=500,
        help="Maximum lines of code per file",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if any file exceeds threshold",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of table",
    )

    args = parser.parse_args()

    if not args.directory.exists():
        print(f"Error: Directory {args.directory} does not exist")
        sys.exit(1)

    results, violations = analyze_directory(
        args.directory,
        args.threshold,
        args.strict,
    )

    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        print_report(results, args.threshold)

    if args.strict and violations:
        print(f"\nERROR: {len(violations)} file(s) exceed the threshold!")
        for v in violations:
            print(f"  - {v['file']}: {v['code_lines']} lines")
        sys.exit(1)

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
