from fileencrypt import encryptFile
import os
import shutil

ERRORS = False
keypath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public_key.bin")

# files to encrypt
ext_whitelist = ['py', 'txt', 'rtf', 'plist', 'h', 'cpp', 'c', 'sh', 'spec']

# files we don't want to copy
ext_blacklist = ['pyc', 'jpg', 'jpeg', 'tiff', 'png', 'psd', 'icns', 'pages', 'wav', 'wave', 'aif', 'aiff']


def copyFile(src, dest, ext=None):
    if ext not in ext_blacklist:
        path, name = os.path.split(src)
        if os.path.isfile(src) and name[0] != '.':
            print("Copying file '{}' to '{}'".format(src, dest))
            shutil.copy(src, dest)


def encryptProject(path, outputpath=None):
    global ERRORS

    assert os.path.exists(path), "Path doesn't exist."
    assert os.path.isdir(path), "Path isn't a directory"

    if not outputpath:
        suffix = "_encrypted"
        outputpath = path[:-1] + suffix if path[-1] == '/' else path + suffix

    if not os.path.exists(outputpath):
        os.mkdir(outputpath)

    for root, folders, files in os.walk(path):
        if root == path or '.' not in os.path.relpath(root, path):
            newpath = os.path.join(outputpath, os.path.relpath(root, path))
            if not os.path.exists(newpath):
                os.mkdir(newpath)

            for file in files:
                filepath = os.path.join(root, file)
                try:
                    ext = file.rsplit('.', 1)[1]
                    if ext in ext_whitelist:
                        print("Encrypting file '{}' to '{}'".format(filepath, newpath))
                        ret = encryptFile(filepath, keypath, newpath)
                        if ret:
                            ERRORS = True
                            os.remove(ret)
                    else:
                        copyFile(filepath, newpath, ext)
                except IndexError:
                    copyFile(filepath, newpath)

    return outputpath


def cleanDirectory(path):
    to_del = []
    for root, folders, files in os.walk(path):
        if not files and not folders: to_del.append(root)
    [os.rmdir(dir) for dir in to_del]

if __name__ == "__main__":
    import sys

    assert len(sys.argv) == 2 or len(sys.argv) == 3
    cleanDirectory(encryptProject(*sys.argv[1:]))

    if ERRORS:
        print("*Finished with errors*")
    else:
        print("Done")
