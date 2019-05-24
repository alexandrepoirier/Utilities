#!/usr/bin/env python
# encoding: utf-8
import os, os.path, time, shutil, sys, console, pickle
from send2trash import send2trash

__doc__ ="""
Merge Copy - mcopy.py
copyright : Alexandre Poirier 2015-2017
last modified : 3 february 2017
Modifications: transitioned the code to Python 3.5, added getMsgTimeStamp for clearer debug info, added the time duration at the end.
    
Copies the content of the source directory to the target, recursively. If files have the same name,
the last modified version is copied in the target directory.

syntax  : mcopy.py [options] [extensions] [source] [target]
example : mcopy.py -k -e wav,aif,mp3 /Users/xxxx/Desktop/music /Users/xxxx/Desktop/playlist

options : -c : copies files and directories in both ways (form 'source' to 'target', and vice versa)
          -k : If files have the same name, the earlier version is kept, but the suffix "-old"
               is added to the end of the file name.
          -d : copies files from 'source' to 'target', then deletes anything in 'target' that is not in
               'source'. Therefore, making 'target' the same as 'source'.
          -i : inclusive mode. Only copies files with the given extensions.
          -e : exclusive mode. Copies all files except the ones with the extentions listed.
               If using this option, extensions must follow directly after. Separate extensions using commas.
"""

def getMsgTimeStamp(level=0):
    if level==0:
        tag = "INFO"
    elif level==1:
        tag = "WARNING"
    elif level==2:
        tag = "ERROR"
    return "[%s][%s] " % (time.strftime("%H:%M:%S"), tag)

if len(sys.argv) < 3:
    print(__doc__)
    sys.exit()

# --------------------------
# Variables Globales
# --------------------------
log_name = '_mcopy.log'
start_time = time.time()
width, height = console.getTerminalSize()
opt = None
mode = None
ext = []
overwrite = True
dir2 = sys.argv.pop(-1)
dir1 = sys.argv.pop(-1)

if not os.path.exists(dir1):
    raise IOError("source path does not exist.")
    
if not os.path.exists(dir2):
    print(console.colour(getMsgTimeStamp(0)+"created root target path : "+dir2,"orange"))
    os.mkdir(dir2)

trgt_log = [] #lists all the files copied from source to target
src_log = [] #lists all the files copied from target to source (case -c)

if os.path.exists(os.path.join(dir1,log_name)):
    with open(os.path.join(dir1,log_name), 'rb') as f:
        src_log = pickle.load(f)

if os.path.exists(os.path.join(dir2,log_name)):
    with open(os.path.join(dir2,log_name), 'rb') as f:
        trgt_log = pickle.load(f)

#sets the overwrite flag
if '-k' in sys.argv:
    sys.argv.pop(sys.argv.index('-k'))
    overwrite = False
    
#sets the extensions
if '-e' in sys.argv:
    index = sys.argv.index('-e')
    sys.argv.pop(index)
    ext = sys.argv.pop(index).split(',')
    mode = 'e'
elif '-i' in sys.argv:
    index = sys.argv.index('-i')
    sys.argv.pop(index)
    ext = sys.argv.pop(index).split(',')
    mode = 'i'

#if two elements are present at this stage, we have an option!
if len(sys.argv) == 2:
    opt = sys.argv[1]

def printMessage(message, colour=None):
    """
    Affiche un message au terminal en s'assurant qu'il occupe toute la largeur
    pour effacer le barre de prograssion en dessous.
    Ensuite, affche la barre de progression.
    """
    global pbar, width
    
    if len(message) < width:
        spaces = width-len(message)
        message += " "*spaces+'\n'
    else:
        message += '\n'
    
    if colour != None:
        message = console.colour(message, colour)
    
    sys.stdout.write('\r'+message)
    sys.stdout.write(console.colour(str(pbar), "green"))
    sys.stdout.flush()
    
def evalFile_mtime(file, target_file, log):
    """
    Evalue si un fichier doit etre copie ou non en se basant sur
    le moment de la derniere modification.
    """
    if len(log) > 0:
        i = inLog(file, log)
        if i != -1:
            if os.path.getmtime(file) > log[i][1]:
                return 1
            if not os.path.exists(target_file):
                return 1
            return 0
    if os.path.exists(target_file):
        if os.path.getmtime(file) > os.path.getmtime(target_file):
            return 1
    else:
        return 1
    return 0
    
def evalFile_ctime(file, target_file, log):
    """
    Evalue si un fichier doit etre copie ou non en se basant sur
    le moment de sa creation.
    """
    if len(log) > 0:
        i = inLog(file, log)
        if i != -1:
            if os.path.getmtime(file) > log[i][1]:
                return 1
            if not os.path.exists(target_file):
                return 1
            return 0
    if os.path.exists(target_file):
        if os.path.getctime(file) > os.path.getctime(target_file):
            return 1
    else:
        return 1
    return 0

def getNumFilesToCopy(source, target, src_log):
    """
    Retourne le nombre de fichier a copier.
    """
    global ext
    count = 0
    for root, dirs, files in os.walk(source):
        rel_source = os.path.relpath(root,source)
        if rel_source == ".":rel_source=""
        
        if len(files)>0:
            if files[0].find("DS_Store") != -1: del files[0]
            try:
                del files[files.index(log_name)]
            except:
                pass
        
        for file in files:
            target_path = os.path.join(target,rel_source,file)
            source_path = os.path.join(root,file)
            src_name, src_ext = source_path.rsplit(".", 1)
            
            if mode == 'e':
                if not src_ext in ext:
                    count += evalFile_mtime(source_path, target_path, src_log)
            elif mode == 'i':
                if src_ext in ext:
                    count += evalFile_mtime(source_path, target_path, src_log)
            else:
                count += evalFile_mtime(source_path, target_path, src_log)
    return count
    
def doCopyFile(source_file, target_file, file_name, src_log):
    """
    Verifie si le fichier passe en parametre doit etre copie et, le cas echeant, procede a la copie.
    """
    global mode, ext, overwrite
    src_name, src_ext = source_file.rsplit(".", 1)
    
    if mode == 'e':
        if src_ext in ext:
            return 0
    if mode == 'i':
        if not src_ext in ext:
            return 0
    
    i = inLog(source_file, src_log)
    if i != -1:
        if os.path.getmtime(source_file) > src_log[i][1]:
            del src_log[i]
            if overwrite:
                printMessage(getMsgTimeStamp(0)+"overwriting file : "+file_name, "red")
                shutil.copy(source_file,target_file)
            else:
                printMessage(getMsgTimeStamp(0)+"copying new file (old version kept) : "+file_name, "cyan")
                name,ext = target_file.rsplit(".", 1)
                old = name+"-old."+ext
                shutil.move(target_file,old)
                shutil.copy(source_file,target_file)
            return 1
        if os.path.exists(target_file):
            return 0
    
    if os.path.exists(target_file):
        if os.path.getmtime(source_file) > os.path.getmtime(target_file):
            if overwrite:
                printMessage(getMsgTimeStamp(0)+"overwriting file : "+file_name, "red")
                shutil.copy(source_file,target_file)
            else:
                printMessage(getMsgTimeStamp(0)+"copying new file (old version kept) : "+file_name, "cyan")
                name,ext = target_file.rsplit(".", 1)
                old = name+"-old."+ext
                shutil.move(target_file,old)
                shutil.copy(source_file,target_file)
            return 1
    else:
        printMessage(getMsgTimeStamp(0)+"copying file : "+file_name, "cyan")
        shutil.copy(source_file,target_file)
        return 1
    return 0

def recursiveCopy(source, target, src_log, trgt_log, dcount_offset=0, fcount_offset=0):
    """
    Traverse tous les dossiers et sous dossiers de la source et recre l'arborescence dans le dossier cible.
    """
    global pbar
    
    dcount = dcount_offset
    fcount = fcount_offset
    for root, dirs, files in os.walk(source):
        printMessage(getMsgTimeStamp(0)+"scanning "+root)
        rel_source = os.path.relpath(root,source)
        if rel_source == ".":rel_source=""
        
        for dir in dirs:
            target_path = os.path.join(target,rel_source,dir)
            if not os.path.exists(target_path):
                printMessage(getMsgTimeStamp(0)+"created target path : "+target_path)
                os.mkdir(target_path)
                dcount += 1
        
        if len(files)>0:
            if files[0].find("DS_Store") != -1: del files[0]
            try:
                del files[files.index(log_name)]
            except:
                pass
        
        for file in files:
            target_path = os.path.join(target,rel_source,file)
            source_path = os.path.join(root,file)
            if doCopyFile(source_path, target_path, file, src_log):
                fcount += 1
                trgt_log.append([target_path,time.time()])
            pbar.update(fcount)
        
    return (dcount,fcount)
                
def cleanTargetDir(source,target):
    """
    Enleve tout ce qui se trouve dans le dossier cible et
    qui n'est pas dans le dossier source.
    """
    dcount = 0
    fcount = 0
    for root, dirs, files in os.walk(target):
        rel_target = os.path.relpath(root,target)
        if rel_target == ".":rel_target=""
        for dir in dirs:
            curpath = os.path.join(source,rel_target,dir)
            if not os.path.exists(curpath):
                print(getMsgTimeStamp(0)+"moving directory to trash : ", dir)
                send2trash(os.path.join(root,dir))
                dcount += 1
        for file in files:
            curpath = os.path.join(source,rel_target,file)
            if not os.path.exists(curpath):
                print(getMsgTimeStamp(0)+"moving file to trash : ", file)
                send2trash(os.path.join(root,file))
                fcount += 1
    return (dir_count, files_count)
  
def inLog(file, log):
    """
    Verifie la presence d'un fichier dans l'historique et retourne son index.
    Retourne -1 en cas d'échec.
    """
    for i, item in enumerate(log):
        if file == item[0]:
            return i
    return -1

def writeLogsToDisk():
    """
    Ecrit les fichiers d'historique sur le disque.
    """
    global src_log, trgt_log, dir1, dir2
    
    if len(src_log) > 0:
        with open(os.path.join(dir1,log_name), 'wb') as f:
            pickle.dump(src_log, f)
    else:
        if os.path.exists(os.path.join(dir1,log_name)):
            os.remove(os.path.join(dir1,log_name))
            
    if len(trgt_log) > 0:
        with open(os.path.join(dir2,log_name), 'wb') as f:
            pickle.dump(trgt_log, f)
    else:
        if os.path.exists(os.path.join(dir2,log_name)):
            os.remove(os.path.join(dir2,log_name))
            
def cleanLogs():
    """
    Enleve tout fichier de l'historique qui n'est plus dans l'arborescence concourante.
    Supprimer l'historique du disque si vide.
    """
    global src_log, trgt_log
    to_del = []
    if len(src_log) > 0:
        for i, item in enumerate(src_log):
            if not os.path.exists(item[0]):
                to_del.append(i)
                #sys.stdout.write(console.colour("deleting log entry : "+src_log[i][0]+'\n', "orange"))
        while len(to_del)>0:
            del src_log[to_del.pop()]
                
    if len(trgt_log) > 0:
        for i, item in enumerate(trgt_log):
            if not os.path.exists(item[0]):
                to_del.append(i)
                #sys.stdout.write(console.colour("deleting log entry : "+trgt_log[i][0]+'\n', "orange"))
        while len(to_del) > 0:
            del trgt_log[to_del.pop()]

def main():
    global pbar
    
    ftocp_SRC = getNumFilesToCopy(dir1, dir2, src_log)
    ftocp_TRGT = 0
    if opt == '-c':
        ftocp_TRGT = getNumFilesToCopy(dir2, dir1, trgt_log)
    num_files_to_copy = ftocp_SRC+ftocp_TRGT
    
    if num_files_to_copy == 0:
        print(console.colour("\n"+getMsgTimeStamp(0)+"--- no files to copy ---\n", "red"))
        return 0
    else:
        pbar = console.ProgressBar(0, num_files_to_copy, width)
    
    if opt == None:
        #no options specified
        printMessage(getMsgTimeStamp(0)+"--- copying files from source ---")
        cdir, cfiles = recursiveCopy(dir1, dir2, src_log, trgt_log)
    elif opt == "-c":
        #copying files from both sides
        printMessage(getMsgTimeStamp(0)+"--- copying files from dir1 -> dir2 ---")
        cdir, cfiles = recursiveCopy(dir1, dir2, src_log, trgt_log)
        if ftocp_TRGT > 0:
            printMessage(getMsgTimeStamp(0)+"--- copying files from dir2 -> dir1 ---")
            cdir, cfiles = recursiveCopy(dir2, dir1, trgt_log, src_log, cdir, cfiles)
    elif opt == "-d":
        #copying files from source and then cleaning target
        printMessage(getMsgTimeStamp(0)+"--- copying files from source ---")
        cdir, cfiles = recursiveCopy(dir1, dir2, src_log, trgt_log)
        printMessage(getMsgTimeStamp(0)+"--- cleaning target directory ---")
        ddir, dfiles = cleanTargetDir(dir1,dir2)

    sys.stdout.write('\r'+console.colour(str(pbar), "green"))
    print(console.colour("\n"+getMsgTimeStamp(0)+"*** DONE ***", "orange"))
    runtime = time.time()-start_time
    print(console.colour(getMsgTimeStamp(0)+"it took %.3fs to copy all files" % runtime, "orange"))
    print(console.colour(getMsgTimeStamp(0)+"Directories created : "+str(cdir), "orange"))
    if 'ddir' in locals():
        print(console.colour(getMsgTimeStamp(0)+"Directories deleted : "+str(ddir), "orange"))
    print(console.colour(getMsgTimeStamp(0)+"Files copied : "+str(cfiles), "orange"))
    if 'dfiles' in locals():
        print(console.colour(getMsgTimeStamp(0)+"Files deleted : "+str(dfiles), "orange"))
    print("")
        
        
if __name__ == "__main__":
    cleanLogs()
    main()
    writeLogsToDisk()
