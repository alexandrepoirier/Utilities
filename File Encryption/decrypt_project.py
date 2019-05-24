from filedecrypt import decryptFile
import os
import shutil
import getpass

keypath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "private_key.bin")
ERRORS = False

def copyFile(src, dest):
    print("Copying file '{}' to '{}'".format(src, dest))
    shutil.copy(src, dest)


def decryptProject(path, outputpath=None):
    global ERRORS

    assert os.path.exists(path), "Path doesn't exist"
    assert os.path.isdir(path), "Path is not a directory"

    passphrase = getpass.getpass()

    if not outputpath:
        suffix = "_decrypted"
        outputpath = path[:-1] + suffix if path[-1] == '/' else path + suffix

    if not os.path.exists(outputpath):
        os.mkdir(outputpath)

    for root, folders, files in os.walk(path):
        newpath = os.path.join(outputpath, os.path.relpath(root, path))
        if not os.path.exists(newpath):
            os.mkdir(newpath)

        for file in files:
            filepath = os.path.join(root, file)
            try:
                if file.split('.')[1] == 'bin':
                    try:
                        print("Decrypting file '{}' to '{}'".format(filepath, newpath))
                        decryptFile(filepath, keypath, passphrase, newpath)
                    except ValueError:
                        ERRORS = True
                        print("[Warning] File '{}' is corrupted and can't be decoded".format(filepath))
                else:
                    copyFile(filepath, newpath)
            except IndexError:
                copyFile(filepath, newpath)

    return outputpath

if __name__ == "__main__":
    import sys

    assert len(sys.argv) == 2 or len(sys.argv) == 3

    decryptProject(*sys.argv[1:])

    if ERRORS:
        print("*Finished with errors*")
    else:
        print("Done")
