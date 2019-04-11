""" Central pane view for the animation plot.
"""
from traits.api import Instance, on_trait_change, Str
from traitsui.api import EnumEditor, HGroup, Item, ModelView, RangeEditor, \
    Spring, UItem, VGroup, View

from enable.api import ComponentEditor

from kromatography.plotting.animation_plot import AnimationPlot


class AnimationPlotView(ModelView):
    """ The view class for a AnimationPlot model.
    """
    #: AnimationPlot model containing the Chaco plot container and data
    model = Instance(AnimationPlot)

    #: Description of the selected time slot
    time_description = Str

    def default_traits_view(self):
        prod_comp_names = self.model.all_data.keys()
        time_slice_max = self.model.active_anim_data.columnliqZ.shape[2] - 1

        return View(
            VGroup(
                HGroup(
                    Item('model.product_component', label='Component',
                         editor=EnumEditor(values=prod_comp_names)),
                    Spring(),
                    Item("time_description", style="readonly",
                         show_label=False),
                    Spring(),
                    Item("model.simulation_name", style="readonly",
                         label="Simulation"),
                ),
                Item('model.time_slice', label='Time slice',
                     editor=RangeEditor(low=0, high=time_slice_max,
                                        mode='slider')),
                HGroup(
                    UItem('model.plot', editor=ComponentEditor(),
                          show_label=False),
                ),
                show_border=True,
            ),
            resizable=True,
            title="Animation Plot",
            width=1000,
            height=800,
        )

    @on_trait_change("model.time_slice")
    def update_plot_title(self):
        step, tot_time = self.model.get_current_step_time()
        desc = 'Step = {}, Time (min) = {:4.1f}'
        self.time_description = desc.format(step, tot_time)


if __name__ == '__main__':

    from kromatography.plotting.animation_plot import \
        _build_animation_data_from_sim
    from kromatography.utils.testing_utils import \
        load_default_experiment_simulation

    _, sim = load_default_experiment_simulation()

    prod_comps = sim.product.product_component_names

    all_data = {prod_comps[i]: _build_animation_data_from_sim(sim, i)
                for i in range(len(prod_comps))}

    aplot = AnimationPlot(all_data=all_data)

    view = AnimationPlotView(model=aplot)

    view.configure_traits()
