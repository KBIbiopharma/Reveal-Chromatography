""" Utility functions related to plotting.

NOTE
----
The utility functions returning properties for a family / curve can be
moved to a separate module with the hardcoded values being instead loaded
# from a CSV/JSON file.
"""
import logging
from collections import Mapping
from posixpath import join
import itertools

from enable.api import marker_names

from kromatography.utils.string_definitions import LOG_FAMILY_UV, \
    LOG_FAMILY_CATION, LOG_FAMILY_PH

COLORS = ('blue green black purple red brown gray cyan orange darkblue tan '
          'darkgray darkviolet deeppink mediumpurple firebrick darkcyan lime '
          'lightblue lightgreen yellow silver').split()

LINESTYLES = ['dash', 'dot', 'dot dash', 'long dash']

MARKER_SIZE = 5

LINE_WIDTH = 2

logger = logging.getLogger(__name__)


class ColorCycler(object):
    """ Class used to cycle colors based on the experiment / sim name
    """
    #: Iterator to select the next color available
    _colors = itertools.cycle(COLORS)

    known_collections = {}

    def __call__(self, collection_source):
        if collection_source in self.known_collections:
            return self.known_collections[collection_source]
        else:
            color = next(self._colors)
            self.known_collections[collection_source] = color
            return color


COLOR_CYCLER = ColorCycler()
MARKERS = list(marker_names)
MARKERS.remove('pixel')
MARKER_CYCLER = itertools.cycle(MARKERS)
LINESTYLE_CYCLER = itertools.cycle(LINESTYLES)


def get_base_properties_for_family(family_name):
    """ Return properties associated with the given `family_name`.
    """
    # FIXME: Treat these data as data and move to a CSV / JSON / module.
    props = {
        'name': family_name,
        'time_label': 'Time',
        'time_unit_label': 'minutes',
    }
    if family_name == LOG_FAMILY_UV:
        props.update({
            'data_label': 'Absorbance',
            'data_unit_label': 'AU/cm',
            'description': ('Protein Concentration Data from Experiment or '
                            'Simulation')
        })
    elif family_name == LOG_FAMILY_CATION:
        props.update({
            'data_label': 'Conc or Cond',
            'data_unit_label': 'mM or mS/cm',
            'description': ('Chemical Component Concentration Data from '
                            'Experiment or Simulation')
        })
    elif family_name == LOG_FAMILY_PH:
        props.update({
            'data_label': 'pH',
            'data_unit_label': '',
            'description': 'pH Data from Experiment or Simulation'
        })
    else:
        msg = 'Unknown family name : {!r}'.format(family_name)
        logger.exception(msg)
        raise ValueError(msg)

    return props


def get_plot_container_properties_for_family(family_name):
    """ Return properties for the Plot object containing the renderers
    for a given family.
    """

    # FIXME: Treat these data as data and move to a CSV / JSON / module.
    prop = {
        'legend': {
            'padding': 10,
        },
        'axes_factory': {
            'orientation': 'normal',
            'vtitle_fmt': '{data_label} ({data_unit_label})',
        },
        'plot_context': {},
    }

    # FIXME: we could also pass in the constraint/layout information for the
    # container
    if family_name == LOG_FAMILY_UV:
        prop['legend'].update({'visible': True, 'align': 'ul'})
        prop['axes_factory'].update({'htitle_fmt': 'Time ({time_unit_label})'})

    elif family_name == LOG_FAMILY_PH:
        prop['legend'].update({'visible': False, 'align': 'ul'})
        prop['axes_factory'].update({'htitle_fmt': 'Time ({time_unit_label})',
                                     'orientation': 'normal',
                                     'vtitle_fmt': '{data_label}'})

    elif family_name == LOG_FAMILY_CATION:
        prop['legend'].update({'visible': False, 'align': 'ul'})
        prop['axes_factory'].update({'htitle_fmt': 'Time ({time_unit_label})'})

    else:
        prop['legend'].update({'visible': False, 'align': 'ur'})

    return prop


def get_renderer_properties(collection_source, family, source_type):
    """ Return properties for plotting a log for the given family and source.

    The returned properties are passed when creating a renderer using
    `Plot.plot`.
    """
    # FIXME: Treat these data as data and move to a CSV / JSON / module.

    # FIXME: perhaps we should instead return a callable for each
    # key in the dicts below, that the caller can then use to create
    # multiple instances of plots for a particular family.

    # FIXME: This prob. has to be a function of ChromeLog and not just family
    # as we need diff. prop for each curve in a family.

    plot_prop = {
        'origin': 'bottom left',
        'index_scale': 'linear',
        'value_scale': 'linear',
    }
    color = COLOR_CYCLER(collection_source)
    if source_type == 'fraction':
        marker = next(MARKER_CYCLER)
        plot_prop.update({
            'type': 'scatter',
            'color': color,
            'marker': marker,
            'marker_size': MARKER_SIZE,
        })
    elif source_type == 'experiment':
        plot_prop.update({
            'type': 'line',
            'color': color,
            'line_style': 'solid',
            'line_width': LINE_WIDTH,
        })
    elif source_type == 'simulation':
        linestyle = next(LINESTYLE_CYCLER)
        plot_prop.update({
            'type': 'line',
            'color': color,
            'line_style': linestyle,
            'line_width': LINE_WIDTH,
        })
    else:
        msg = 'Invalid family source: {!r}'.format(source_type)
        logger.exception(msg)
        raise ValueError(msg)

    return plot_prop


def flatten_nested_mapping(data_dict, root=None):
    """ Flatten a nested dictionary to construct a flat dictionary where the
    keys are POSIX paths indicating the relative position of the values in the
    original dictionary.
    i.e. {'a': {'b': 10}, 'c':20} --> {'a/b': 10, 'c':20}
    """
    flat_dict = {}
    for key, value in data_dict.items():
        if not isinstance(key, basestring):
            msg = "Keys must be of string type. Got {!r}"
            logger.exception(msg)
            raise TypeError(msg.format(key))
        if isinstance(value, Mapping):
            nested_flat_dict = flatten_nested_mapping(value)
            flat_dict.update(
                {join(key, flat_key): flat_val
                 for flat_key, flat_val in nested_flat_dict.items()}
            )
        else:
            flat_dict[key] = value

    if root is not None:
        return {join(root, key.strip('/')): value
                for key, value in flat_dict.items()}
    else:
        return flat_dict


def interpolate_properties(properties, namespace=None):
    """ Interpolate any fmt strings in `properties`.

    The basic idea is to allow some keys to be named as `<attr_name>_fmt` with
    a value being a format string. The format string would be passed a namspace
    containing the normal keys. This allows us to store plot properties
    that depend on others properties.

    If `namespace` is explicitly passed, then it is used when interpolating
    the strings.

    Here is an example (note `g_fmt` contains the format string in input and
    gets converted to `g` in the output):

        In [16]: aa = {'a':10, 'b': {'c': 'sfsdsfdsf'}, 'g_fmt': "{a}_{b/c}"}
        In [17]: chaco_chromatogram.interpolate_properties(aa)
        Out[17]: {'a': 10, 'b': {'c': 'sfsdsfdsf'}, 'g': '10_sfsdsfdsf'}
    """
    if not isinstance(properties, dict):
        msg = 'Argument `properties` must be a dict'
        logger.exception(msg)
        raise ValueError(msg)

    # if namespace is not passed, created a namespace where where the keys
    # are essentially posix paths by flattening the input dict.
    if namespace is None:
        namespace = {
            k: v for k, v in flatten_nested_mapping(properties).items()
            if not k.endswith('_fmt')
        }

    norm_props = {}
    for key, val in properties.items():
        if isinstance(key, basestring) and key.endswith('_fmt'):
            attr_name = key.rsplit('_', 1)[0]
            norm_props[attr_name] = val.format(**namespace)
        elif isinstance(val, Mapping):
            norm_props[key] = interpolate_properties(val, namespace=namespace)
        else:
            norm_props[key] = val

    return norm_props
