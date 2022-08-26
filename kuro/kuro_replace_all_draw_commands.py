# Script to replace all draw commands with manual drawindexedinstanced
# commands, as Kuro no Kiseki's engine does not use drawindexed commands
# so the 'drawindexed = auto' command can fail to draw meshes if the
# primitives are instanced.
# GitHub eArmada8/vbuffer_merge_split

import glob, os

# Define as a global variable the size of index buffer chunks (in bytes).
# Kuro no Kiseki uses R32_UINT format for index buffers, which is a 32-bit
# unsigned integer, therefore 4 bytes in size.
ib_format_size = 4 

# We cannot know the instance count for each call unfortunately, the way
# that 3DMigoto is current written.  But numbers that are too high do not
# seem to cause a problem, so we default to 3. (Higher than 3 seems to be
# problematic)
instance_count = 3

def retrieve_ini_files():
    # Make a list of all ini in the current folder recursively
    return glob.glob('**/*.ini',recursive=True)

def process_ini_file(ini_file):
    # Open the file
    with open(ini_file, 'rb') as f:
        ini_filedata = f.read()

    # Determine if there is an IB file listed, and if so, determine its index count using filesize
    ini_file_has_ib = False
    current_offset = ini_filedata.find(b'\x0afilename')
    while current_offset > 0:
        if ini_filedata[ini_filedata.find(b'\x0d\x0a',current_offset)-2:][0:2] == b'ib':
            line_end = ini_filedata.find(b'\x0d\x0a',current_offset)
            ib_filename = ini_filedata[current_offset+12:line_end].decode("utf-8")
            ib_filename_withpath = '\\'.join([os.path.dirname(os.path.abspath(ini_file)), ib_filename])
            ib_indexcount = int(os.stat(ib_filename_withpath).st_size / ib_format_size)
            ini_file_has_ib = True # IB File was found, indicating this ini file should be processed
        current_offset = ini_filedata.find(b'\x0afilename', current_offset+1)

    # Further Processing should proceed only if IB file was found
    processed = False
    if (ini_file_has_ib):
        current_offset = ini_filedata.find(b'\x0adraw')
        if current_offset > 0:
            line_end = ini_filedata.find(b'\x0d\x0a',current_offset)
            with open(ini_file, 'wb') as f:
                f.write(ini_filedata[:current_offset] + b'\x0adrawindexedinstanced = ' \
                + str(ib_indexcount).encode() + b', ' + str(instance_count).encode() \
                + b', 0, 0, 0' + ini_filedata[line_end:])
            processed = True

    # Not really needed
    return(processed)

if __name__ == "__main__":
    # Set current directory
    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    # Retrieve ini files to process
    ini_files = retrieve_ini_files()

    # Open each file, look for IB, and replace the draw command
    for i in range(len(ini_files)):
        process_ini_file(ini_files[i])