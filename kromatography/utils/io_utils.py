""" HDF5 utilities to write and read HDF5 files for CADET runs.
"""
import logging
import posixpath

import h5py
import numpy as np
from traits.api import HasStrictTraits, List

logger = logging.getLogger(__name__)


def get_sanitized_state(trait_obj):
    """ Build a dictionary describing the state of the trait_object to be
    stored in the CADET HDF5 input file.
    """
    if hasattr(trait_obj, "_cadet_input_keys"):
        cadet_inputs = getattr(trait_obj, "_cadet_input_keys")
        if isinstance(cadet_inputs, list):
            state = {key: getattr(trait_obj, key) for key in cadet_inputs}
        elif isinstance(cadet_inputs, dict):
            state = {cadet_name: getattr(trait_obj, trait_name)
                     for trait_name, cadet_name in cadet_inputs.items()}
        else:
            msg = "_cadet_input_keys is supposed to be a list or a dict but " \
                  "a {} was found.".format(type(cadet_inputs))
            logger.exception(msg)
            raise ValueError(msg)
    else:
        state = {key: val for key, val in trait_obj.__getstate__().items()
                 if not key.startswith('_')}

    # FIXME: depending on the inputs, we might have to do some sanitizing here
    # (e.g. unicode strings)
    return state


def get_dtype_sanitized_data(val):
    """ Return sanitized data for writing to H5.
    """
    # just handle the type that we care about for now and fail for the rest.
    if isinstance(val, int):
        val = np.int32(val)
    elif isinstance(val, float):
        val = np.float64(val)
    elif isinstance(val, str):
        pass
    elif isinstance(val, np.ndarray) and val.dtype.kind == 'i':
        val = val.astype(np.int32)
    elif isinstance(val, np.ndarray) and val.dtype.kind == 'f':
        val = val.astype(np.float64)
    elif isinstance(val, np.ndarray) and val.dtype.kind == 'S':
        pass
    else:
        msg = 'Unsupported data type to write to HDF5: {!r} (val = {})'
        msg = msg.format(type(val), val)
        logger.exception(msg)
        raise ValueError(msg)

    return val


def write_trait_obj(h5_grp, trait_obj):
    """ Write Traits object recursively in an HDF5 group.
    """
    state = get_sanitized_state(trait_obj)
    for key, val in state.items():
        if val is None:
            continue

        if isinstance(val, HasStrictTraits):
            new_grp = h5_grp.require_group(key)
            write_trait_obj(new_grp, val)
        elif (hasattr(val, 'trait') and
                isinstance(val.trait, List) and
                isinstance(val[0], HasStrictTraits)):
            # FIXME: HACK: Special case these node names for now.
            if key == 'section':
                key_fmt = "sec_{:03d}"
            else:
                msg = "Expected the key to be 'section' but found {}"
                msg = msg.format(key)
                logger.exception(msg)
                raise RuntimeError(msg)

            for ind, v in enumerate(val):
                new_grp = h5_grp.require_group(key_fmt.format(ind))
                write_trait_obj(new_grp, v)
        else:
            try:
                val = get_dtype_sanitized_data(val)
                h5_grp[key.upper()] = val
            except Exception as e:
                msg = 'Failed to write H5 data : {}({}). Error was {}.'
                msg = msg.format(val, type(val), e)
                logger.exception(msg)
                raise


def write_to_h5(filename, trait_obj, root='/', overwrite=False):
    """ Write a HasStrictTraits object into a H5 file.

    NOTE: This function is not meant to be full fledged serialization utility
    and does not try to preserve metadata/version/class information.

    Parameters
    ----------
    filename : file path
        The filename for the output h5 file.
    trait_obj : instance(HasStrictTraits)
        The traits object that needs to be written to the file.
    root : posix path
        The h5 group under which the attributes of `trait_obj` are written.

    FIXME: Move to ets_future?
    """
    if not isinstance(trait_obj, HasStrictTraits):
        msg = ('The argument `trait_obj` must be of type `HasStrictTraits`. '
               'Recevied type : {!r}').format(type(trait_obj))
        logger.exception(msg)
        raise ValueError(msg)

    mode = 'w' if overwrite else 'w-'
    with h5py.File(filename, mode) as h5:
        root_grp = h5.require_group(root)
        write_trait_obj(root_grp, trait_obj)


def read_from_h5(filename, root='/'):
    """ Read in all datasets from H5 file into a dictionary, mapping values to
    their node name.

    FIXME: create a hastraits object.
    FIXME: Move to ets_future?
    """
    results = {}

    def _read_data(name, obj):
        """ Reads in the data as native data type and store in global results.
        """
        if isinstance(obj, h5py.Dataset):
            path = posixpath.split(name)
            out = results
            for key in path[:-1]:
                # FIXME: there is prob. a cleaner way to do this
                if key == '' or '/':
                    continue
                out = out.setdefault(key, {})
            out[path[-1].lower()] = obj[()]

    with h5py.File(filename, 'r') as h5:
        root_grp = h5.get(root)
        if root_grp is None:
            msg = "Requested group {} not found in {}. Its content is: {}"
            content = get_hdf5_content(h5)
            msg = msg.format(root, filename, content)
            logger.error(msg)
        else:
            root_grp.visititems(_read_data)

    return results


def get_hdf5_content(h5file):
    """ Display nodes directly in root and list their content.
    """
    content = {}
    for key, val in h5file.items():
        content[key] = val.items()
    return content
