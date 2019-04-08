""" Utilities to run CADET on a simualtion object.
"""
import logging

from app_common.traits.has_traits_utils import is_trait_event, \
    is_trait_property

from kromatography.model.chromatography_data import DataElement
from kromatography.utils.cadet_simulation_builder import build_cadet_input
from kromatography.utils.io_utils import write_to_h5
from kromatography.utils.string_definitions import SIM_SUBMITTED

logger = logging.getLogger(__name__)


def create_cadet_file_for_sim(sim):
    """ Create

    Parameters
    ----------
    sim : Simulation
        Simulation for which to create the CADET file.

    Returns
    -------
    str
        File path created for the simulation.
    """
    cadet_input = build_cadet_input(sim)
    output_file = sim.cadet_filepath
    write_to_h5(output_file, cadet_input, root='/input', overwrite=True)
    return output_file


def prepare_simulation_for_run(sim):
    """ Prepare a simulation for the CADET solver to be run.
    """
    walk_dataelement_editable(sim, False, skip_traits=['source_experiment'])
    output_file = create_cadet_file_for_sim(sim)
    sim.run_status = SIM_SUBMITTED
    return output_file


def walk_dataelement_editable(dataelement_obj, bool_val, skip_traits=None):
    """ Walks dataelement_obj recursively flipping editable flags to bool_val.

    Parameters
    ----------
    dataelement_obj : DataElement
        DataElement instance on which to walk and flip `editable` attr.

    bool_val : bool
        Value to switch `editable` to.

    skip_traits : None or list of str
        list of trait names to avoid flipping `editable` attr

    """
    # FIXME: some CADET related traits are not DataElements and so will be
    # missed by this walker.

    # flip its own editable flag
    dataelement_obj.editable = bool_val

    # walk its children, calling itself on all DataElement objects
    # Note, this assumes there will be no nested lists or dictionaries
    # involving DataElement objects
    for traitname in dataelement_obj.trait_names():

        # pass on specified traits (and don't walk them either)
        if skip_traits is not None and traitname in skip_traits:
            continue

        is_event_or_property = (is_trait_event(dataelement_obj, traitname) or
                                is_trait_property(dataelement_obj, traitname))
        if is_event_or_property:
            continue

        trait = getattr(dataelement_obj, traitname)

        if isinstance(trait, DataElement):
            walk_dataelement_editable(trait, bool_val, skip_traits=skip_traits)

        elif isinstance(trait, list) and len(trait) != 0:
            for item in trait:
                if isinstance(item, DataElement):
                    walk_dataelement_editable(item, bool_val,
                                              skip_traits=skip_traits)
                else:
                    break

        elif isinstance(trait, dict) and len(trait) != 0:
            for item in trait.values():
                if isinstance(item, DataElement):
                    walk_dataelement_editable(item, bool_val,
                                              skip_traits=skip_traits)
                else:
                    break
        else:
            # given trait wasn't DataElement or seq of DataElements, skipping
            pass
