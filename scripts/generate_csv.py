import os
import subprocess
import sys
from pathlib import Path

# python generate_csv.py 'C:\Users\brasi\Documents\mining_my_repository\compiled\apache-hadoop\commits-release-0.20.203.0\jars'

path = Path(sys.argv[1]).expanduser().resolve(strict=True)
if not path.is_dir():
    raise NotADirectoryError(path)

arr = os.listdir(path)
sorted_files = sorted(arr, key=lambda x: int(x.split('-')[1]))
for folder in sorted_files:
    print(path / folder)
    folder = (path / folder).resolve(strict=True)
    if not folder.is_dir() or path not in folder.parents:
        continue
    print('===================================\n')
    if folder.exists():
        for filename in os.listdir(folder):
            print(filename)
            if "PM.csv" not in os.listdir(folder) and filename.endswith(".jar"):
                print(folder)
                try:
                    subprocess.run(
                        [
                            "java",
                            "-jar",
                            "Arcan-1.2.1-SNAPSHOT.jar",
                            "-p",
                            str(folder),
                            "-out",
                            str(folder),
                            "-pm",
                            "-folderOfJars",
                        ],
                        check=False,
                    )
                except Exception as er:
                    print(er)
            else:
                continue
