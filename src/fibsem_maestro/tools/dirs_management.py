import glob
import logging
import os
import re


def make_dirs(dirs):
    """
    :param dirs: A dictionary containing the directories to be created. The key 'dirs' should have a list of directory paths as its value.
    :return: None

    This method creates directories that do not already exist. It logs the creation of each directory using the logging module.

    Example usage:
        make_dirs(dirs=['/path/to/dir1', '/path/to/dir2'])
    """
    for d in dirs:
        new_dir = dirs[d]
        if not os.path.isdir(new_dir):
            logging.info(f"{new_dir} created.")
            os.makedirs(new_dir)


def findfile(data_dir):
    """
    Find the file with highest slice_number
    """
    max_slice = 0
    image_filename = None
    list_files = glob.glob(f"{data_dir}\\*.tif")
    # Iterate through each string in the list
    for s in list_files:
        # Use re.search to find the match in the string
        match = re.search(r'slice_(\d+)', s)

        # Extract the numbers from the match groups
        if match:
            slice_number = int(match.group(1))
            if slice_number > max_slice:
                max_slice = slice_number
                image_filename = s

    return max_slice, image_filename
