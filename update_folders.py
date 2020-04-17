import sys
import re
import shutil
import os

# python update_folders.py source_file dest_file

# Itera sobre todos os elementos de dest_file e procura no arquivo source_file
# salva os que encontrou

# Source eh como tava antes
# Target eh o que queremos consertar

# A versao 5 antes englobava a 1.4.1 ---> source: 5.txt, target: commits-rel-1.4.txt
# A versao 6 englobava 1.5.1,1.5.2,1.5.3,1.5.4 ---> source: 6.txt, target: commits-rel-1.5.txt
# EX: python update_folders.py '5.txt' 'commits-rel-1.4.txt'


# recorta todos eles e poe na pasta de 6
dest_file = sys.argv[2]
source_file = sys.argv[1]

# This function receives a txt file with packages using . as separator
def generate_module_list(file, prefix=''):
    f = open(file, "r")
    lines = f.readlines()
    list = []
    for module in lines[2:]:
        if not "Package\n" in module:
            if prefix:
                list.append(prefix + "." + module.replace("\n", ""))
            else:
                list.append(module.replace("\n", ""))
    return list
    
# new_commits = generate_module_list(arquivo_novo)
source = generate_module_list(source_file)
source_hashes = [re.search(r'([^0-9\n]+)[a-z]?.*', s).group(0).replace('-','') for s in source]
dest = generate_module_list(dest_file)

# key: source
# value: dest
files = {}

# files = [f for f in dest if f in source]



for file in dest:
    hash_commit = re.search(r'([^0-9\n]+)[a-z]?.*', file).group(0).replace('-','')
    #print(hash_commit)
    if hash_commit in source_hashes:
        files.setdefault('version-'+source[source_hashes.index(hash_commit)],'version-'+file)
        #print('destino: ' + file)
        #print('origem: '+source[source_hashes.index(hash_commit)])

# print(files)

log = []


source = 'C:\\Users\\brasi\\Documents\\mining_my_repository\\compiled\\commits-rel-1.5\\jars'
dest1 = 'C:\\Users\\brasi\\Documents\\mining_my_repository\\compiled\\commits-rel-1.4\\jars'

files_dir = os.listdir(source)
files_dir = sorted(files_dir, key=lambda x: int(x.split('-')[1]))

replaced = []

for file in files_dir:
    if not os.path.isdir(os.path.join(source, file)):
        print('not directory')
        continue # Not a directory
    if os.path.exists(os.path.join(source, file)):
        # print(file)
        if file in files.keys():
            for jarfile in os.listdir(os.path.join(source, file)):
                if jarfile.endswith(".jar"):
                    os.rename(os.path.join(source+'\\'+file, jarfile), os.path.join(source+'\\'+file, files[file]+'.jar') )
            os.rename(os.path.join(source, file), os.path.join(source, files[file]))
            shutil.move(os.path.join(source, files[file]), os.path.join(dest1, files[file]))
            replaced.append('De: '+os.path.join(source, files[file])+' --> Para: '+os.path.join(dest1, files[file])+'\n')


f = open("replaced.txt","w")
f.write( str(replaced) )
f.close()
print('O resultado da operacao foi salvo na pasta onde esta este script com o nome \"replaced.txt\"')
# print(replaced)


# print(files2)


# for old in files.keys():
    #os.rename(old, files[old])
    #print("move de |"+old+"| to |"+files[old])
    # shutil.move(source+f, dest1)

