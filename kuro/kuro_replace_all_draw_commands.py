# Script to replace all draw commands with drawindexedinstanced = auto
# commands.  This version of my script REQUIRES the custom build of
# 3DMigoto that has drawindexedinstanced = auto implemented.
# GitHub eArmada8/vbuffer_merge_split

import glob, os

def retrieve_ini_files():
    # Make a list of all ini in the current folder recursively
    return glob.glob('**/*.ini',recursive=True)

def process_ini_file(ini_file):
    # Open the file
    with open(ini_file, 'rb') as f:
        ini_filedata = f.read()

    # Replace all the drawindexed* commands
    changes_made = False
    current_offset = ini_filedata.find(b'\x0adrawindexed')
    while current_offset > 0:
        line_end = ini_filedata.find(b'\x0d\x0a',current_offset)
        ini_filedata = ini_filedata[:current_offset] + b'\x0adrawindexedinstanced = auto' + ini_filedata[line_end:]
        current_offset = ini_filedata.find(b'\x0adrawindexed', current_offset + 1)
        changes_made = True

    # If any changes were made, write the new file
    if changes_made == True:
        with open(ini_file, 'wb') as f:
            f.write(ini_filedata)

    return(changes_made)

if __name__ == "__main__":
    # Set current directory
    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    # Retrieve ini files to process
    ini_files = retrieve_ini_files()

    # Open each file, look for IB, and replace the draw command
    for i in range(len(ini_files)):
        process_ini_file(ini_files[i])
