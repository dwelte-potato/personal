#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import os
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_EXCLUDES = [
    ".git",
    ".DS_Store",
    ".idea",
    ".vscode",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".terraform",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".coverage",
    ".cache",
    "scripts",
]


def _default_source_root(script_path: Path) -> Path:
    if script_path.parent.name == "scripts":
        return script_path.parent.parent
    return script_path.parent


def _is_excluded(rel_path: Path, patterns: list[str]) -> bool:
    rel_posix = rel_path.as_posix()
    for pattern in patterns:
        if "/" in pattern:
            if fnmatch.fnmatch(rel_posix, pattern):
                return True
            continue

        for part in rel_path.parts:
            if fnmatch.fnmatch(part, pattern):
                return True

    return False


def _symlink_points_to(target_path: Path, desired_source_abs: Path) -> bool:
    if not target_path.is_symlink():
        return False

    try:
        link_text = os.readlink(target_path)
    except OSError:
        return False

    link_path = Path(link_text)
    if not link_path.is_absolute():
        link_path = target_path.parent / link_path

    existing_abs = Path(os.path.abspath(link_path))
    return existing_abs == desired_source_abs


def _ensure_parent_dir(path: Path, *, dry_run: bool) -> None:
    parent = path.parent
    if parent.exists():
        if parent.is_dir():
            return
        raise RuntimeError(f"Target parent exists and is not a directory: {parent}")

    if not dry_run:
        parent.mkdir(parents=True, exist_ok=True)


@dataclass
class _Stats:
    created: int = 0
    updated: int = 0
    already_ok: int = 0
    skipped_excluded: int = 0
    conflicts: int = 0
    errors: int = 0


def _iter_top_level_dirs(
    source_root: Path,
    *,
    only_dirs: list[str] | None,
    include_dot_dirs: bool,
    exclude_patterns: list[str],
) -> list[Path]:
    if only_dirs:
        dirs = [source_root / d for d in only_dirs]
    else:
        dirs = [p for p in source_root.iterdir() if p.is_dir()]

    result: list[Path] = []
    for p in sorted(dirs, key=lambda x: x.name):
        if not include_dot_dirs and p.name.startswith("."):
            continue
        if _is_excluded(Path(p.name), exclude_patterns):
            continue
        result.append(p)
    return result


def _link_file(
    source_file: Path,
    target_file: Path,
    *,
    force: bool,
    dry_run: bool,
    stats: _Stats,
) -> None:
    desired_source_abs = Path(os.path.abspath(source_file))

    try:
        _ensure_parent_dir(target_file, dry_run=dry_run)
    except Exception as exc:
        stats.errors += 1
        print(f"ERROR  {target_file}: {exc}", file=sys.stderr)
        return

    if _symlink_points_to(target_file, desired_source_abs):
        stats.already_ok += 1
        return

    target_exists = target_file.exists() or target_file.is_symlink()
    if target_exists:
        if target_file.is_dir():
            stats.conflicts += 1
            print(f"SKIP   {target_file} (exists as directory)", file=sys.stderr)
            return

        if not force:
            stats.conflicts += 1
            print(f"SKIP   {target_file} (exists; use --force to replace)", file=sys.stderr)
            return

        if dry_run:
            print(f"UPDATE {target_file} -> {desired_source_abs}")
        else:
            target_file.unlink()
            rel = os.path.relpath(desired_source_abs, start=target_file.parent)
            target_file.symlink_to(rel)
        stats.updated += 1
        return

    if dry_run:
        print(f"CREATE {target_file} -> {desired_source_abs}")
    else:
        rel = os.path.relpath(desired_source_abs, start=target_file.parent)
        target_file.symlink_to(rel)
    stats.created += 1


def main() -> int:
    script_path = Path(__file__).resolve()
    default_source_root = _default_source_root(script_path)

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description=(
            "Symlink files from each top-level directory under <source-root> to the same "
            "relative location under <target-root> (default: ~/potato)."
        ),
        epilog=(
            "Examples:\n"
            "  python3 scripts/symlink_to_potato.py --dry-run\n"
            "  python3 scripts/symlink_to_potato.py\n"
            "  python3 scripts/symlink_to_potato.py simulation-infra --dry-run\n"
            "  python3 scripts/symlink_to_potato.py --force\n"
        ),
    )
    parser.add_argument(
        "dirs",
        nargs="*",
        help="Optional top-level directories under source-root to process (default: all).",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=default_source_root,
        help=f"Source root (default: {default_source_root}).",
    )
    parser.add_argument(
        "--target-root",
        type=Path,
        default=(Path.home() / "potato"),
        help="Target root (default: ~/potato).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change, but don't create/modify symlinks.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing files/symlinks at the target path (never deletes directories).",
    )
    parser.add_argument(
        "--include-dot-dirs",
        action="store_true",
        help="Also process top-level directories whose name starts with '.'.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help=(
            "Exclude pattern (repeatable). If pattern contains '/', it matches the "
            "posix-style relative path; otherwise it matches any path component."
        ),
    )
    args = parser.parse_args()

    source_root: Path = args.source_root.expanduser().resolve()
    target_root: Path = args.target_root.expanduser().resolve()
    exclude_patterns: list[str] = list(DEFAULT_EXCLUDES) + list(args.exclude)
    only_dirs: list[str] | None = args.dirs or None

    if not source_root.is_dir():
        print(f"ERROR: source-root is not a directory: {source_root}", file=sys.stderr)
        return 2

    top_level_dirs = _iter_top_level_dirs(
        source_root,
        only_dirs=only_dirs,
        include_dot_dirs=bool(args.include_dot_dirs),
        exclude_patterns=exclude_patterns,
    )
    if only_dirs:
        missing = [d for d in only_dirs if (source_root / d) not in top_level_dirs]
        for d in missing:
            if not (source_root / d).exists():
                print(f"ERROR: missing directory: {source_root / d}", file=sys.stderr)
            else:
                print(
                    f"ERROR: directory excluded by rules: {source_root / d}",
                    file=sys.stderr,
                )
        if missing:
            return 2

    stats = _Stats()
    for project_dir in top_level_dirs:
        for dirpath, dirnames, filenames in os.walk(project_dir, followlinks=False):
            current_dir = Path(dirpath)
            rel_dir = current_dir.relative_to(project_dir)

            pruned_dirnames: list[str] = []
            for d in dirnames:
                rel = rel_dir / d
                if _is_excluded(rel, exclude_patterns):
                    stats.skipped_excluded += 1
                    continue
                pruned_dirnames.append(d)
            dirnames[:] = pruned_dirnames

            for filename in filenames:
                rel = rel_dir / filename
                if _is_excluded(rel, exclude_patterns):
                    stats.skipped_excluded += 1
                    continue

                source_file = current_dir / filename
                if source_file.is_dir():
                    continue
                if not (source_file.is_file() or source_file.is_symlink()):
                    continue

                target_file = target_root / project_dir.name / rel
                _link_file(
                    source_file,
                    target_file,
                    force=bool(args.force),
                    dry_run=bool(args.dry_run),
                    stats=stats,
                )

    print(
        "Done:"
        f" created={stats.created}"
        f" updated={stats.updated}"
        f" ok={stats.already_ok}"
        f" excluded={stats.skipped_excluded}"
        f" conflicts={stats.conflicts}"
        f" errors={stats.errors}"
    )

    if stats.errors:
        return 2
    if stats.conflicts:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
