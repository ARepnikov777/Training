"""Copy the E01 fixture with Python 3.10+ standard library only."""
import argparse
from pathlib import Path
import shutil

CATEGORIES = {
    '.txt': 'documents', '.md': 'documents', '.json': 'documents',
    '.pdf': 'documents', '.png': 'images', '.csv': 'tables',
}


def copy_files(source: Path, destination: Path) -> None:
    """Copy flat input files into a new, separate destination directory."""
    source = source.resolve()
    destination = destination.resolve()
    if destination == source or source in destination.parents:
        raise ValueError('Destination must be outside the source directory')
    files = sorted(source.iterdir())
    # Resolve every category before creating output, so unsupported inputs fail.
    targets = [(file, CATEGORIES[file.suffix]) for file in files]
    destination.mkdir(parents=True)
    for file, category in targets:
        target = destination / category / file.name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(file, target)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Input files directory')
    parser.add_argument('destination', type=Path, help='New output directory')
    args = parser.parse_args()
    copy_files(args.source, args.destination)
    print(f'Copied {len(list(args.source.iterdir()))} files to {args.destination}')
