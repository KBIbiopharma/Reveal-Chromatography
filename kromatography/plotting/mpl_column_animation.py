import matplotlib.pyplot as plt
import numpy as np
from matplotlib import animation

from kromatography.plotting.animation_data import \
    _build_animation_data_from_sim


def column_animation(sim):
    """ Make an animation for each product component contained in the
    simulation.
    """
    for comp_idx in range(len(sim.product.product_component_names)):
        column_animation_for_comp(sim, comp_idx)


def column_animation_for_comp(sim, component_idx):
    """ Build a Matplotlib animation displaying the evolution of a product
    component concentration over time.

    Parameters
    ----------
    sim : Simulation
        Simulation object that contains particle data as part of its results.

    component_idx : int
        Index of the component to display the animated time evolution.
    """
    anim_data = _build_animation_data_from_sim(sim, component_idx)

    ax1, ax2, ax3, fig = initialize_animation_figs(sim.name, anim_data)

    def animate(mframe):

        step_start_times = anim_data.step_start_times
        times = anim_data.times
        nframe = mframe * 20

        for i in range(0, len(step_start_times)):
            test = (times[nframe] >= step_start_times[i] and
                    times[nframe] < step_start_times[i+1])
            if test:
                step = anim_data.step_names[i]

        # Plot the liquid phase concentration in the column
        x, y = anim_data.columnliqX, anim_data.columnliqY
        z = anim_data.columnliqZ[:, :, nframe]
        ax1.cla()
        ax1.contourf(x, y, z, levels=anim_data.levelsliq)
        label = "Step = {}\nTime (min) = {:4.1f}".format(step, times[nframe])
        ax1.set_xlabel(label, fontsize=14)

        # Plot the liquid phase concentration in the bead
        x, y = anim_data.beadX, anim_data.beadY
        z = anim_data.beadliqZ[:, :, nframe]
        ax2.cla()
        ax2.contourf(x, y, z, levels=anim_data.levelsliq)

        # Plot the bound phase concentration in the bead
        x, y = anim_data.beadX, anim_data.beadY
        z = anim_data.beadboundZ[:, :, nframe]
        ax3.cla()
        ax3.contourf(x, y, z, levels=anim_data.levelsbound)

    animation.FuncAnimation(fig, animate,
                            frames=len(anim_data.times), interval=1,
                            blit=False, repeat=True)
    plt.show()


def initialize_animation_figs(sim_name, anim_data):
    # Set the overall size of the plot and subplots
    fig = plt.figure(figsize=(16, 8), facecolor='white')
    fig.suptitle(sim_name + ' Animation for ' + anim_data.component_name,
                 fontsize=20)

    ax1 = plt.subplot(1, 3, 1)
    ax1.set_xticklabels([])
    ax1.set_xticks([])
    plt.title('Column Liquid Phase', fontsize=14)
    plt.ylabel('Column Position (cm)', fontsize=14)
    # Initialize the axis plot with the first timestamp
    x, y = anim_data.columnliqX, anim_data.columnliqY
    z = anim_data.columnliqZ[:, :, 0]
    ax1.contourf(x, y, z, levels=anim_data.levelsliq)

    ax2 = plt.subplot(1, 3, 2)
    plt.title('Bead Pores Liquid Phase', fontsize=14)
    ax2.set_xlabel("Bead Position (um)", fontsize=14)
    ax2.set_xticks(np.linspace(0, anim_data.beaddiam_um, 10))
    ax2.yaxis.set_visible(False)
    x, y, z = anim_data.beadX, anim_data.beadY, anim_data.beadliqZ[:, :, 0]
    plt.contourf(x, y, z, levels=anim_data.levelsliq)
    plt.colorbar(label="Liquid Concentration (g/L)", format='%0.1f')

    ax3 = plt.subplot(1, 3, 3)
    plt.title('Bead Pores Bound Phase', fontsize=14)
    ax3.set_xlabel("Bead Position (um)", fontsize=14)
    ax3.set_xticks(np.linspace(0, anim_data.beaddiam_um, 10))
    ax3.yaxis.set_visible(False)
    x, y, z = anim_data.beadX, anim_data.beadY, anim_data.beadboundZ[:, :, 0]
    plt.contourf(x, y, z, levels=anim_data.levelsbound)
    plt.colorbar(label="Bound Concentration (g/L)", format='%0.1f')

    return ax1, ax2, ax3, fig


if __name__ == '__main__':

    from kromatography.utils.testing_utils import \
        load_default_experiment_simulation

    _, sim = load_default_experiment_simulation()
    column_animation_for_comp(sim, 0)
