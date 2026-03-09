from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[2]
    features_root = workspace_root / "features"

    errors: list[str] = []
    for feature_file in sorted(features_root.glob("*.feature")):
        sibling_dir = features_root / feature_file.stem
        if not sibling_dir.is_dir():
            errors.append(
                f"Missing paired directory for main feature: {feature_file.relative_to(workspace_root)}"
            )

    if errors:
        print("Feature pair check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Feature pair check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())