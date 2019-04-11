""" CADET input class that gets automatically translated into HDF5 input file.

Consequently, the class names, attribute names and units that contained in this
class and its children are set by the specs of the version of CADET using the
generated input file.
"""
from traits.api import HasStrictTraits, Instance, Str

from kromatography.model.cadet_model import CADETModel
from kromatography.model.solver import Solver
from kromatography.model.discretization import Discretization
from kromatography.model.sensitivity import Sensitivity
from kromatography.model.transport_model import GRM_TRANSPORT_MODEL


class CADETInput(HasStrictTraits):
    """  The class that models the CADET input h5 group (i.e. `/input`). The
    attributes of the class are H5 nodes under the input group.
    """

    #: The type of the chromatography model used in simulation.
    chromatography_type = Str(GRM_TRANSPORT_MODEL)

    #: The instance containing discretization parameters.
    discretization = Instance(Discretization, ())

    #: The instance containing CADET model parameters.
    model = Instance(CADETModel)

    #: The instance containing sensitivity parameters.
    sensitivity = Instance(Sensitivity, args=())

    #: The instance containing solver parameters.
    solver = Instance(Solver, args=())
