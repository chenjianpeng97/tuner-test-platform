from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[2]
    features_root = workspace_root / "features"

    errors: list[str] = []
    for subfeature_file in sorted(features_root.glob("*/*.feature")):
        # Skip standalone Behave suites that manage their own namespace
        if (subfeature_file.parent / "environment.py").is_file():
            continue
        parent_name = subfeature_file.parent.name
        expected_prefix = f"{parent_name}_"
        if not subfeature_file.name.startswith(expected_prefix):
            errors.append(
                "Subfeature name must follow 主功能_子功能.feature: "
                f"{subfeature_file.relative_to(workspace_root)}"
            )

    if errors:
        print("Subfeature naming check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Subfeature naming check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())