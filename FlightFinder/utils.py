import sys
from os.path import join, dirname, realpath


def data_filepath(data_file):
    """
    Gets the file path of a data file
    :param data_file: data file path
    :return: file path to data file
    """
    if hasattr(sys, 'frozen'):
        dir = dirname(sys.executable)
    else:
        dir = join(dirname(realpath(__file__)), '..')

    return join(dir, 'data', data_file)
