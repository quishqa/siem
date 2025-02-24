# siem/user.py
"""
Function for user output.

This modules have functions to user.

It allows the following functions:
    - `check_create_savedir(save_path)` - Create saving directory if does not exists.

"""

import os

def check_create_savedir(save_path: str) -> None:
    """
    Createa a directory to save if not exists.

    Parameters
    ----------
    save_path : str
        Directory to save output.

    Returns
    -------
        Create a new directory to save.
        

    """
    if not os.path.isdir(save_path):
        print('Missing directory, creating directory')
        os.makedirs(save_path)
    print(f'Saving in {save_path}')
    return None

