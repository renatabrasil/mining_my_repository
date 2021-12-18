import os
import sys

# python generate_csv.py 'C:\Users\brasi\Documents\mining_my_repository\compiled\apache-hadoop\commits-release-0.20.203.0\jars'

path = sys.argv[1]

arr = os.listdir(path)
sorted_files = sorted(arr, key=lambda x: int(x.split('-')[1]))
for folder in sorted_files:
    print(os.path.join(path, folder))
    folder = os.path.join(path, folder)
    print('===================================\n')
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            print(filename)
            if "PM.csv" not in os.listdir(folder) and filename.endswith(".jar"):
                print(folder)
                try:
                    rc = os.system(
                        'java -jar Arcan-1.2.1-SNAPSHOT.jar -p ' + '"' + folder + '"' + ' -out ' + '"' + folder + '"' + ' -pm -folderOfJars')
                except Exception as er:
                    print(er)
            else:
                continue
