#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# SIMPLE GIT-LIKE VERSION CONTROL PROGRAM
#
# AUTHOR: MATEUSZ BIEGAŃSKI
# EMAIL:  BIEGANSKI.M@WP.PL
#


import filecmp
import os
import sys
import uuid
from distutils.dir_util import copy_tree
from os.path import exists, isdir, normpath, join, dirname, relpath, basename
from shutil import copy2

REPO_DIR = ".simplegit"

# files in 'REPO_DIR':
HEAD = 'HEAD'  # file that remembers last commit in actual state
TO_COMMIT = 'TO_COMMIT'  # tracked files list

# in each commit directory (named with commit hash) there are following files:
TRACKED_LIST = 'TRACKED_LIST'  # list of all files tracked by this commit
PREV_COMMIT = 'PREV_COMMIT'  # keeps hash of previous commit, empty if none
COMMIT_DIR = 'COMMIT_DIR'  # directory containing all commit-files


def allFiles(path):
    """Given !absolute path returns list of absolute paths
    of all visible, non-directory files in 'path' location.
    For usage with relative path, i.e. '.' <if not f[0] == '.'>
    needst to be changed not to throw out proper '.' dir.
    """
    retFiles = []
    for root, dirs, files in os.walk(path):
        # ignore hidden files
        files = [f for f in files if not f[0] == '.']
        dirs[:] = [d for d in dirs if not d[0] == '.']
        for file in files:
            retFiles.append(normpath(join(root, file)))
    return retFiles


def fatalError(msg):
    # associated with user activity, i.e bad command usage
    print(msg)
    sys.exit()


def changePathsRef(initAbsolutePath, destAbsolutePath, files):
    """Given init absolute path and list of file paths, relative to init path
    it returns that list, but with paths now relating to 'destAbsolutePath'.
    """
    fileAbsolutePaths = [normpath(join(initAbsolutePath, f)) for f in files]
    return [relpath(f, destAbsolutePath) for f in fileAbsolutePaths]


def nearestRepo(absolutePath):
    """Given a absolute path it returns closest repository associated with it,
    i.e. first folder containing 'REPO_DIR' directory on it's path to
    root directory and None if none exists.
    """
    tmpPath = normpath(absolutePath)
    while tmpPath:
        possibleRepo = normpath(join(tmpPath, REPO_DIR))
        if exists(possibleRepo) and isdir(possibleRepo):
            return dirname(possibleRepo)
        if tmpPath == '/':
            return None
        tmpPath = dirname(tmpPath)
    return None


def lastCommitHash(repoPath):
    with open(normpath(join(repoPath, REPO_DIR, HEAD)), 'r') as headFile:
        return headFile.readline().strip()


def init(path):
    path = normpath(join(path, REPO_DIR))
    if not os.path.exists(path):
        os.mkdir(path)
    else:
        fatalError("Repository in this directory already exists!")
    os.mknod(normpath(join(path, HEAD)))
    os.mknod(normpath(join(path, TO_COMMIT)))


def toCommitList(repoPath):
    with open(normpath(join(repoPath, REPO_DIR, TO_COMMIT)), 'r') as toCommit:
        return toCommit.read().splitlines()


def add(repoPath, files):
    """Stashes given list of files to be commited.
    Files might be dirs also, then it calls itself recursively
    ASSERTION: 'files' paths are relative to 'repoPath'
    """
    dirs = []
    toCommitAsList = toCommitList(repoPath)
    toCommit = open(normpath(join(repoPath, REPO_DIR, TO_COMMIT)), 'a+')
    for file in files:
        filePath = normpath(join(repoPath, file))
        if not exists(filePath):
            print("ERROR: " + filePath + " doesn't exist!")
            continue
        if isdir(filePath):
            dirs.append(file)
        elif file not in toCommitAsList:
            toCommit.write(file + '\n')
            toCommitAsList.append(file)
    toCommit.close()
    # files from subdirectories handling
    for dir in dirs:
        filesInSubdir = os.listdir(normpath(join(repoPath, dir)))
        add(repoPath, [normpath(join(dir, f)) for f in filesInSubdir])


def generateDirTree(repoPath, files):
    """Generates whole directory in HEAD-commit from 'files' list.
    """
    assert lastCommitHash(repoPath)  # it had to be made earlier
    dstPath = normpath(join(repoPath, REPO_DIR,
                            lastCommitHash(repoPath), COMMIT_DIR))
    for f in files:
        srcPath = normpath(join(repoPath, f))
        newFilePath = normpath(join(dstPath, f))
        if not os.path.isdir(dirname(newFilePath)):
            os.makedirs(newFilePath)
        copy2(srcPath, newFilePath)


def commit(repoPath):
    newCommitHash = uuid.uuid4().hex
    newPath = normpath(join(repoPath, REPO_DIR, newCommitHash))

    toCommit = normpath(join(repoPath, REPO_DIR, TO_COMMIT))
    commitDir = normpath(join(newPath, COMMIT_DIR))
    tracked = normpath(join(newPath, TRACKED_LIST))
    prev = normpath(join(newPath, PREV_COMMIT))

    assert not os.path.exists(newPath)

    os.mkdir(newPath)
    os.mkdir(commitDir)
    os.mknod(tracked)
    os.mknod(prev)

    # set previous commit
    lastCommitName = lastCommitHash(repoPath)  # empty if I'm first commit
    if lastCommitName:
        with open(prev, 'w') as prev:
            prev.write(lastCommitName)

    # set new HEAD value
    with open(normpath(join(repoPath, REPO_DIR, HEAD)), 'w') as head:
        head.truncate()
        head.write(newCommitHash)

    # copy 'toCommit' content to  'TRACKED_LIST' file
    with open(tracked, 'w') as tracked, open(toCommit, 'r') as toCommit:
        tracked.writelines(l for l in toCommit)

    # copy whole directory with tracked files
    generateDirTree(repoPath, toCommitList(repoPath))


def wasCommited(repoPath, file):
    comm = lastCommitHash(repoPath)
    tracked = normpath(join(repoPath, REPO_DIR, comm, TRACKED_LIST))
    if not comm:
        return False
    with open(tracked) as commited:
        return file in commited.read().splitlines()


def wasAdded(repoPath, file):
    added = normpath(join(repoPath, REPO_DIR, TO_COMMIT))
    with open(added) as added:
        return file in added.read().splitlines()


def status(repoPath):
    # need to use relative instead of absolute paths
    files = changePathsRef('/', repoPath, allFiles(repoPath))
    for f in files:
        if not wasCommited(repoPath, f):
            if not wasAdded(repoPath, f):
                print(f + " (new file)")
            else:
                print(f + " (added and waiting to commit)")
        else:
            # print nothing
            pass


def help():
    msg = str("simplegit - Usage:\n" +
        "- simplegit init - creates repository in actual directory\n" +
        "- simplegit add * - adds all files to commit\n" +
        "- simplegit add file_path - adds single file to commit\n" +
        "- simplegit commit  - commits all tracked files\n" +
        "- simplegit status - shows files tracking status")
    print(msg)
    sys.exit()


def main():
    if len(sys.argv) < 2:
        help()

    currentDir = os.getcwd()
    currentRepo = nearestRepo(currentDir)

    # special case, we don't pass repository path, can't throw
    if sys.argv[1] == "init":
        if currentRepo:
            fatalError("Repository already exists!")
        if len(sys.argv) != 2:
            print(len(sys.argv))
            help()
        init(currentDir)
        sys.exit()

    if currentRepo is None:
        fatalError("No repository found! " +
                   "Create new one using 'simplegit init'")

    try:
        if sys.argv[1] == "add":
            if len(sys.argv) == 2:
                help()
            files = sys.argv[2:]  # simplegit add args..
            # need to change relativity point
            filesRepoPath = changePathsRef(currentDir, currentRepo, files)
            add(currentRepo, filesRepoPath)
        elif sys.argv[1] == "commit":
            if len(sys.argv) != 2:
                help()
            commit(currentRepo)
        elif sys.argv[1] == "status":
            if len(sys.argv) != 2:
                help()
            status(currentRepo)
        else:
            help()
    except EnvironmentError:
        fatalError("FATAL ERROR: Repository broken")

