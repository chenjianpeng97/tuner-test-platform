from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[2]
    features_root = workspace_root / "features"
    db_root = features_root / "db"

    errors: list[str] = []
    if not (db_root / "base").is_dir():
        errors.append("Missing shared base data directory: features/db/base")

    for feature_file in sorted(features_root.glob("*.feature")):
        mapped_dir = db_root / feature_file.stem
        if not mapped_dir.is_dir():
            errors.append(
                f"Missing data directory for main feature: {mapped_dir.relative_to(workspace_root)}"
            )

    if errors:
        print("Feature-to-db mapping check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Feature-to-db mapping check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())