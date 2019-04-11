
from app_common.apptools.io.reader_writer import LocalFileReader, \
    LocalFileWriter

from .serializer import serialize
from .deserializer import deserialize


def save_object(filepath, object_to_save):
    """ Stores any object into a project file (.chrom).

    Parameters
    ----------
    filepath : str
        Absolute or relative path to the file to load.

    object_to_save : any
        Object to save. It is expected to be a subclass of HasTraits.
    """
    writer = LocalFileWriter(filepath=filepath, serialize=serialize)
    writer.save(object_to_save)


def load_object(filepath):
    """ Load object from project file (.chrom).

    Parameters
    ----------
    filepath : str
        Absolute or relative path to the file to load.

    Returns
    -------
    any, bool
        The object found in the file, and whether or not at least 1 legacy
        deserializer was used.
    """
    reader = LocalFileReader(filepath=filepath, deserialize=deserialize)
    return reader.load()
