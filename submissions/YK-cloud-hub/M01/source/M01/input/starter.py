from pathlib import Path
import shutil

def copy_files(source, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for p in Path(source).iterdir():
        if p.is_file():
            shutil.copy2(p, output / p.name)
