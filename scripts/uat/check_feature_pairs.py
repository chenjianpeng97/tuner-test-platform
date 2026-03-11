from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[2]
    features_root = workspace_root / "features"

    errors: list[str] = []
    for child_dir in sorted(path for path in features_root.iterdir() if path.is_dir()):
        if not any(child_dir.rglob("*.feature")):
            continue

        # Skip subdirectories that are standalone Behave suites (have their own
        # environment.py); these are independent runners, not sub-suites of the
        # main features/*.feature hierarchy.
        if (child_dir / "environment.py").is_file():
            continue

        main_feature = features_root / f"{child_dir.name}.feature"
        if not main_feature.is_file():
            errors.append(
                "Missing main feature for subfeature directory: "
                f"{child_dir.relative_to(workspace_root)}"
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