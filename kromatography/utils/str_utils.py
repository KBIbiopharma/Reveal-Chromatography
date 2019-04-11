""" Utilities to manipulate strings, convert them, identify them, ...
"""


def is_string_valid_variable_name(name, bad_char="", bad_values=()):
    """ Returns whether :arg:`name` is a valid variable name.

    Parameters
    ----------
    name : str
        Name to be tested.

    bad_char : str or iterable of str
        Iterable of characters to be treated as bad characters. If name
        contains any of them, it will be deemed invalid.

    bad_values : Iterable of strings
        List of string values that name shouldn't be in to be deemed valid.

    Returns
    -------
    bool
        Whether the name is valid.
    """
    # A component can be bad because it contains certain characters though they
    # wouldn't prevent the compilation of the code below...
    for char in list(bad_char):
        if char in name:
            return False

    # ... or be in a list of bad values...
    if name in bad_values:
        return False

    # ... or don't lead to compile-able code when trying to assign it a value.
    # Note that it's safer to use compile than exec, so that the python parser
    # is used, but no code is run
    try:
        compile("{} = 0".format(name), '<name>', 'single')
        return True
    except SyntaxError:
        return False


def get_dtype(data):
    """ Return the type (str or float) for input string `data`.
    """
    try:
        float(data)
    except ValueError:
        return "str"
    else:
        return "float"


def str_list_mostly_float(str_list, limit=None):
    """ Are most of the fields (half or more) floating point values?
    """
    if limit is None:
        limit = len(str_list)/2.

    types_are_float = [get_dtype(field) == "float" for field in str_list]
    return sum(types_are_float) >= limit


def strip_decode_strings(str_list):
    return [s.decode('ascii', 'ignore').strip() for s in str_list]


def sanitize_str_list(str_list):
    """ Truncate the provided list removing all empty strings at its end.
    """
    while True:
        if str_list[-1] == "":
            str_list.pop(-1)
        else:
            break
