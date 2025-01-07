import os

def list_files(startpath):
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}├── {os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{subindent}├── {f}")

# 指定要检索的目录
startpath = '/home/xiaoxiao/Projects/ChemistryOS_DEMO/src'
list_files(startpath)