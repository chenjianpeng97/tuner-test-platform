"""
CLI for BDD fixture management — seed or clean DB test identities.

Usage
-----
# Seed all identities defined in identity_registry.py:
  APP_ENV=local uv run --project fastapi-clean-example python scripts/uat/manage_fixtures.py seed

# Seed specific identities only:
  APP_ENV=local uv run --project fastapi-clean-example python scripts/uat/manage_fixtures.py seed --names Alice Charlie

# Clean all identities:
  APP_ENV=local uv run --project fastapi-clean-example python scripts/uat/manage_fixtures.py clean

# Clean specific identities:
  APP_ENV=local uv run --project fastapi-clean-example python scripts/uat/manage_fixtures.py clean --names Charlie

Identities are defined in:
  features/factories/identity_registry.py
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# ── Python path setup ─────────────────────────────────────────────────────────
_WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_ROOT = _WORKSPACE_ROOT / "fastapi-clean-example"
_BACKEND_SRC = _BACKEND_ROOT / "src"

for _p in (_WORKSPACE_ROOT, _BACKEND_ROOT, _BACKEND_SRC):
    _ps = str(_p)
    if _ps not in sys.path:
        sys.path.insert(0, _ps)

os.environ.setdefault("APP_ENV", "local")


def _print_identity_table(label: str, names: list[str]) -> None:
    from features.factories.identity_registry import get_identity  # noqa: PLC0415

    print(f"\n{'─' * 60}")
    print(f"  {label}")
    print(f"{'─' * 60}")
    print(f"  {'Name':<12} {'Username':<14} {'Role':<12} {'Active'}")
    print(f"  {'─' * 10} {'─' * 12} {'─' * 10} {'─' * 6}")
    for name in names:
        try:
            spec = get_identity(name)
            print(
                f"  {spec.name:<12} {spec.username:<14} {spec.role.value:<12} {spec.is_active}"
            )
        except KeyError as e:
            print(f"  ERROR: {e}")
    print(f"{'─' * 60}\n")


def cmd_seed(names: list[str]) -> int:
    from features.factories.seeding import ensure_identity  # noqa: PLC0415

    _print_identity_table("Seeding identities into DB", names)
    ok, fail = 0, 0
    for name in names:
        try:
            user = ensure_identity(name)
            print(
                f"  ✓  {user.username:<14}  role={user.role.value}  active={user.is_active}  id={user.id_[:8]}…"
            )
            ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗  {name:<14}  ERROR: {exc}")
            fail += 1
    print(f"\n  Seeded {ok}/{ok + fail} identities.\n")
    return 0 if fail == 0 else 1


def cmd_clean(names: list[str]) -> int:
    from features.factories.seeding import delete_identity  # noqa: PLC0415

    _print_identity_table("Cleaning identities from DB", names)
    ok, fail = 0, 0
    for name in names:
        try:
            delete_identity(name)
            print(f"  ✓  {name} deleted (or did not exist)")
            ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗  {name:<14}  ERROR: {exc}")
            fail += 1
    print(f"\n  Cleaned {ok}/{ok + fail} identities.\n")
    return 0 if fail == 0 else 1


def cmd_status(names: list[str]) -> int:
    from features.factories.seeding import get_user  # noqa: PLC0415

    _print_identity_table("Current DB state for identities", names)
    for name in names:
        try:
            user = get_user(name)
            if user is None:
                print(f"  ✗  {name:<12}  NOT IN DB")
            else:
                print(
                    f"  ✓  {user.username:<14}  role={user.role.value}  active={user.is_active}  id={user.id_[:8]}…"
                )
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗  {name:<12}  ERROR: {exc}")
    print()
    return 0


def main() -> int:
    from features.factories.identity_registry import IDENTITIES  # noqa: PLC0415

    all_names = sorted(IDENTITIES.keys())

    parser = argparse.ArgumentParser(
        description="Manage BDD test fixtures in the local DB.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Available identities: {', '.join(all_names)}",
    )
    parser.add_argument(
        "command",
        choices=["seed", "clean", "status"],
        help="seed: upsert identities | clean: delete identities | status: show DB state",
    )
    parser.add_argument(
        "--names",
        nargs="+",
        metavar="NAME",
        default=all_names,
        help=f"Identity names to operate on (default: all — {', '.join(all_names)})",
    )

    args = parser.parse_args()

    # Validate names
    unknown = [n for n in args.names if n not in IDENTITIES]
    if unknown:
        parser.error(
            f"Unknown identities: {', '.join(unknown)}. Available: {', '.join(all_names)}"
        )

    dispatch = {"seed": cmd_seed, "clean": cmd_clean, "status": cmd_status}
    return dispatch[args.command](args.names)


if __name__ == "__main__":
    sys.exit(main())
