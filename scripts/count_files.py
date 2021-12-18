import os
import sys

'''
    Script para calcular o tamanho de todos os jars dentro de um repositorio
    O algoritmo para ordenar os arquivos deve ser revisto de acordo com o padrao 
    de nomenclatura de arquivos adotado.
    
    Esse script eh usado para descobrir se todos os jars gerados foram gerados
    corretamente (faz isso comparando com o limite_inf.
    
'''
# python count_files.py 'compiled/commits-rel-1.7.0/jars' limite_inf (bytes)
os.system('cls' if os.name == 'nt' else 'clear')
os.system('cls')

directory = sys.argv[1]
limite_inf = int(sys.argv[2])


def humanbytes(b):
    'Return the given bytes as a human friendly KB, MB, GB, or TB string'
    b = float(b)
    KB = float(1024)
    MB = float(KB ** 2)  # 1,048,576
    GB = float(KB ** 3)  # 1,073,741,824
    TB = float(KB ** 4)  # 1,099,511,627,776

    if b < KB:
        return '{0} {1}'.format(b, 'Bytes' if 0 == b > 1 else 'Byte')
    elif KB <= b < MB:
        return '{0:.2f} KB'.format(b / KB)
    elif MB <= b < GB:
        return '{0:.2f} MB'.format(b / MB)
    elif GB <= b < TB:
        return '{0:.2f} GB'.format(b / GB)
    elif TB <= b:
        return '{0:.2f} TB'.format(b / TB)


def file_size(file_path):
    """
    this function will return the file size
    """
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return humanbytes(file_info.st_size)


TRED = '\033[1;31;40m '
TGREEN = '\033[32m'  # Green Text
ENDC = '\033[m'  # reset to the defaults
TBLUE = "\033[1;34m"
TCYAN = "\033[1;36m"
TGREEN = "\033[0;32m"
RESET = "\033[0;0m"
BOLD = "\033[;1m"
REVERSE = "\033[;7m"

average = 0
number_of_files = 0
minor_file = ''
minimo = sys.maxsize
maximo = -1
if directory:
    if os.path.exists(directory):
        arr = os.listdir(directory)
        sorted_files = sorted(arr, key=lambda x: int(x.split('-')[1]))
        for subdirectory in sorted_files:
            version = subdirectory
            subdirectory = os.path.join(directory, subdirectory)
            # print("\n" + subdirectory +)
            print("\n----------------------\n")
            hasJar = False
            for filename in [f for f in os.listdir(subdirectory)]:
                if filename.endswith(".jar"):
                    file = os.path.join(subdirectory, filename)
                    hasJar = True
                    number_of_files += 1
                    average += os.stat(file).st_size
                    if os.stat(file).st_size >= maximo:
                        maximo = os.stat(file).st_size
                    if os.stat(file).st_size <= minimo:
                        minimo = os.stat(file).st_size
                        minor_file = filename
                    if limite_inf and os.stat(file).st_size > limite_inf:
                        print(filename + ' - ' + TGREEN + str(file_size(file)) + ENDC)
                    else:
                        print(filename + ' - ' + TRED + str(file_size(file)) + ENDC)
                    break

            if not hasJar:
                print(REVERSE + 'SEM JAR' + ENDC)

    print("\n----------------------\n")
    average = average / number_of_files
    print("Media do tamanho de arquivos: " + BOLD + humanbytes(average) + ENDC + '\n')
    print("Minimo: " + BOLD + humanbytes(minimo) + ENDC + ' (' + minor_file + ')\n')
    print("Maximo: " + BOLD + humanbytes(maximo) + ENDC + '\n')

else:
    print("Processo encerrado\nTempo de execucao:")
