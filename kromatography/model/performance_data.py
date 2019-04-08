import logging

from traits.api import Constant, Instance, on_trait_change, Str
from scimath.units.unit_scalar import UnitScalar

from kromatography.model.chromatography_data import ChromatographyData
from kromatography.model.solution_with_product import SolutionWithProduct

logger = logging.getLogger(__name__)


class PerformanceData(ChromatographyData):
    """ Container to hold performance data from simulation or experiment
    """

    #: The time that start collect was initiated/should start
    start_collect_time = Instance(UnitScalar)

    #: The time that collection was stopped/should stop
    stop_collect_time = Instance(UnitScalar)

    #: Volume of Product Pool resulting from chromatography process in CVs
    pool_volume = Instance(UnitScalar)

    #: Pool created by selected start and stop times
    pool = Instance(SolutionWithProduct)

    #: Percent of product yielded by process (product in pool/product in load)
    step_yield = Instance(UnitScalar)

    #: Concentration of all product components in the pool
    pool_concentration = Instance(UnitScalar)

    #: String representation of all component purities
    pool_purities = Str

    # -------------------------------------------------------------------------
    # ChromatographyData traits
    # -------------------------------------------------------------------------

    #: The type-id for this class.
    type_id = Constant('Performance Data')

    @on_trait_change("pool.product_component_purities")
    def update_pool_purities(self):
        pool = self.pool

        if pool is None or pool.product_component_purities is None:
            return ""

        comp_names = pool.product.product_component_names
        purities = pool.product_component_purities
        unit = purities.units.label
        entries = [
            "{name}: {val:.3f}{unit}".format(name=name, val=val, unit=unit)
            for name, val in zip(comp_names, purities.tolist())]
        self.pool_purities = ", ".join(entries)
