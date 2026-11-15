import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def copy_files(source, output, *, dry_run=True):
    """Return a journal; by default inspect files without changing the filesystem."""
    source, output = Path(source).resolve(), Path(output).resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"Source directory does not exist: {source}")
    if output == source or source in output.parents or output in source.parents:
        raise ValueError("Source and output directories must not contain each other")
    categories = {".txt": "documents", ".md": "documents", ".csv": "tables"}
    paths = []

    def on_error(error):
        raise error

    for directory, dirs, files in os.walk(source, onerror=on_error, followlinks=False):
        for name in dirs[:]:
            path = Path(directory) / name
            if path.is_symlink():
                paths.append(path)
                dirs.remove(name)
        paths.extend(Path(directory) / name for name in files)

    journal, reserved = [], set()
    for path in sorted(paths):
        record = {
            "source": str(path),
            "target": None,
            "action": "skipped",
            "reason": "",
        }
        if path.is_symlink():
            record["reason"] = "symbolic link"
        elif path.suffix not in categories:
            record["reason"] = "unsupported extension"
        else:
            # Read all bytes in preview too, so unreadable input is not reported as OK.
            with path.open("rb") as stream:
                while stream.read(1024 * 1024):
                    pass
            target = output / categories[path.suffix] / path.name
            index = 2
            while target in reserved or os.path.lexists(target):
                target = (
                    output
                    / categories[path.suffix]
                    / (f"{path.stem}__{index}{path.suffix}")
                )
                index += 1
            if any(parent.is_symlink() for parent in target.parents):
                raise ValueError(f"Symbolic link in output path: {target}")
            reserved.add(target)
            record.update(
                target=str(target), action="would_copy" if dry_run else "copied"
            )
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                # Exclusive creation also protects against a concurrent name collision.
                with path.open("rb") as src, target.open("xb") as dst:
                    shutil.copyfileobj(src, dst)
        journal.append(record)
    return journal


def main():
    parser = argparse.ArgumentParser(description="Preview or copy files by category")
    parser.add_argument("source")
    parser.add_argument("output")
    parser.add_argument("--apply", action="store_true", help="Confirm copying")
    args = parser.parse_args()
    try:
        records = copy_files(args.source, args.output, dry_run=not args.apply)
    except (OSError, ValueError) as error:
        print(f"Copy failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(records, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
