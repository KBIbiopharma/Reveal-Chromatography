import numpy as np

from traits.api import Array, HasStrictTraits, Int, Instance, Property, Str

from kromatography.model.product import Product
from kromatography.model.column import Column


class AnimationData(HasStrictTraits):
    """ Data storage for building animation plots of the particle data
    evolution over time during a simulation.
    """
    # Setup description -------------------------------------------------------

    #: Name of the simulation the data was extracted from
    simulation_name = Str

    #: Column the animation data is about
    column = Instance(Column)

    #: Product the animation is about
    product = Instance(Product)

    #: Index of the component the data is about
    component_idx = Int

    #: Component the animation is about
    component_name = Property(depends_on="product, component_idx")

    #: Column bed height
    bedheight_cm = Property(depends_on="column")

    #: Bead diameter in packed column
    beaddiam_um = Property(depends_on="column")

    # Process method description ----------------------------------------------

    #: Method step start times during animation
    step_start_times = Array

    #: Method step names
    step_names = Array

    # Plot description --------------------------------------------------------

    #: levels for liquid contour plots
    levelsliq = Array

    #: levels for bound contour plot
    levelsbound = Array

    #: Axis arrays
    beadX = Array

    beadY = Array

    #: Boundaries of X values for the column liquid phase data
    columnliqX = Property(Array, depends_on="column")

    columnliqY = Array

    #: Array of timestamps
    times = Array

    #: Data in the liquid phase in the bead
    beadliqZ = Array

    #: Data in the bound phase in the bead
    beadboundZ = Array

    #: Data in the liquid phase in the bead
    columnliqZ = Array

    # Property getters/setters ------------------------------------------------

    def _get_component_name(self):
        return self.product.product_component_names[self.component_idx]

    def _get_bedheight_cm(self):
        return self.column.bed_height_actual.tolist()  # in cm

    def _get_beaddiam_um(self):
        return self.column.resin.average_bead_diameter.tolist()  # in um

    def _get_columnliqX(self):
        col_radius = float(self.column.column_type.diameter) / 2.
        return np.array([0, col_radius])


def _build_animation_data_from_sim(sim, component_idx):
    """ AnimationData factory for a given component from a simulation object.

    FIXME: Need to read units off of simulation object rather than assuming
    them.
    """
    # Set product parameters
    product = sim.product
    results = sim.output
    comp = product.product_components[component_idx]
    component_name = comp.name
    extcoef = comp.extinction_coefficient[()]
    bedheight_cm = sim.column.bed_height_actual.tolist()  # in cm
    beaddiam_um = sim.column.resin.average_bead_diameter.tolist()  # in um

    # Load column tags
    tagname = 'Section_Tags_Sim'
    step_start_times = results.continuous_data[tagname].x_data / 60.0
    step_names = results.continuous_data[tagname].y_data

    # Transform column data for plot
    colname = component_name + '_Column_Sim'
    times = results.continuous_data[colname].x_data / 60.0
    N_times = len(times)
    column = results.continuous_data[colname].y_data / extcoef

    # Transform particle liquid data for plot
    partliqname = component_name + '_Particle_Liq_Sim'
    particleliq = results.continuous_data[partliqname].y_data / extcoef

    # Transform particle bound data for plot
    partboundname = component_name + '_Particle_Bound_Sim'
    particlebound = results.continuous_data[partboundname].y_data / extcoef

    levelsliq = np.linspace(0, np.amax(column[:, :]), 100)
    levelsbound = np.linspace(0, np.amax(particlebound[:, :, :]), 100)

    # Prepare the column liquid phase data
    columnliqY = np.linspace(0, bedheight_cm, len(column[0, :]))

    Z = []
    for i in range(0, N_times):
        z = np.array([column[i, :], column[i, :]])
        z1 = z.transpose()
        Z.append(np.flipud(z1))

    columnliqZ = np.dstack([Z[i] for i in range(0, N_times)])

    # Prepare the bead liquid and bound phase data
    beadX = np.linspace(beaddiam_um/2, 0, len(particleliq[0, 0, :]))
    beadY = np.linspace(0, bedheight_cm, len(particleliq[0, :, 0]))

    Z1 = []
    for i in range(0, N_times):
        z = particleliq[i, :, :]
        z1 = np.fliplr(z)
        Z1.append(np.flipud(z1))
    beadliqZ = np.dstack([Z1[i] for i in range(0, N_times)])

    Z2 = []
    for i in range(0, N_times):
        z = particlebound[i, :, :]
        z1 = np.fliplr(z)
        Z2.append(np.flipud(z1))
    beadboundZ = np.dstack([Z2[i] for i in range(0, N_times)])

    return AnimationData(
        column=sim.column, product=sim.product, component_idx=component_idx,
        levelsliq=levelsliq, levelsbound=levelsbound,
        columnliqY=columnliqY, beadX=beadX, beadY=beadY,
        columnliqZ=columnliqZ, beadliqZ=beadliqZ, beadboundZ=beadboundZ,
        times=times,
        step_start_times=step_start_times, step_names=step_names,
        simulation_name=sim.name
    )
