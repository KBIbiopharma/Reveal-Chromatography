import logging

from traits.api import adapt, Enum, HasStrictTraits, Instance, List, Property,\
    Str
from traitsui.api import Handler, HGroup, InstanceEditor, Item, ModelView, \
    OKButton, OKCancelButtons, Spring, VGroup

from kromatography.utils.traitsui_utils import KromView
from kromatography.model.binding_model import BINDING_MODEL_TYPES, \
    BindingModel, ExternalLangmuir, Langmuir, LANGMUIR_BINDING_MODEL, \
    PH_STERIC_BINDING_MODEL, PhDependentStericMassAction, \
    STERIC_BINDING_MODEL, StericMassAction, PH_LANGMUIR_BINDING_MODEL
from kromatography.model.factories.binding_model import create_binding_model

logger = logging.getLogger(__name__)


class BindingModelBuilderHandler(Handler):
    def close(self, info, is_ok):
        return info.object.active_model_view.close(info, is_ok)


class BindingModelBuilder(HasStrictTraits):
    """ UI to select and build a new binding model.
    """
    # BindingModelBuilder interface -------------------------------------------

    #: Target model type selector
    binding_model_type = Enum(BINDING_MODEL_TYPES)

    #: Selected binding model
    model = Property(Instance(BindingModel), depends_on="binding_model_type")

    #: Currently active model view
    active_model_view = Property(Instance(ModelView),
                                 depends_on="binding_model_type")

    #: Name of the product the binding model is built for
    target_product = Str

    # BindingModelBuilder private interface -----------------------------------

    #: Actual model when binding_model_type is STERIC_BINDING_MODEL
    _sma_model = Instance(StericMassAction)

    #: Actual model when binding_model_type is PH_STERIC_BINDING_MODEL
    _ph_sma_model = Instance(PhDependentStericMassAction)

    #: Actual model when binding_model_type is LANGMUIR_BINDING_MODEL
    _langmuir_model = Instance(Langmuir)

    #: Actual model when binding_model_type is PH_LANGMUIR_BINDING_MODEL
    _ext_langmuir_model = Instance(ExternalLangmuir)

    #: View for _sma_model
    _sma_model_view = Instance(ModelView)

    #: View for _ph_sma_model
    _ph_sma_model_view = Instance(ModelView)

    #: View for _langmuir_model
    _langmuir_model_view = Instance(ModelView)

    #: View for _ext_langmuir_model
    _ext_langmuir_model_view = Instance(ModelView)

    # Names of the product components to model
    _target_component_names = List(Str)

    def traits_view(self):
        visible_when_sma = "binding_model_type == '{}'".format(
            STERIC_BINDING_MODEL
        )
        visible_when_ph_sma = "binding_model_type == '{}'".format(
            PH_STERIC_BINDING_MODEL
        )
        visible_when_langmuir = "binding_model_type == '{}'".format(
            LANGMUIR_BINDING_MODEL
        )
        visible_when_extern_langmuir = "binding_model_type == '{}'".format(
            PH_LANGMUIR_BINDING_MODEL
        )
        view = KromView(
            VGroup(
                HGroup(
                    Spring(),
                    Item("binding_model_type"),
                    Spring()
                ),
                HGroup(
                    Item('_sma_model_view', editor=InstanceEditor(),
                         show_label=False, style="custom",
                         visible_when=visible_when_sma),
                    Item('_ph_sma_model_view', editor=InstanceEditor(),
                         show_label=False, style="custom",
                         visible_when=visible_when_ph_sma),
                    Item('_langmuir_model_view', editor=InstanceEditor(),
                         show_label=False, style="custom",
                         visible_when=visible_when_langmuir),
                    Item('_ext_langmuir_model_view', editor=InstanceEditor(),
                         show_label=False, style="custom",
                         visible_when=visible_when_extern_langmuir),
                    show_border=True, label="Model parameters"
                ),
            ),
            buttons=OKCancelButtons, default_button=OKButton,
            handler=BindingModelBuilderHandler(),
            title="Configure new binding model"
        )
        return view

    def create_new_binding_model(self, bind_type):
        """ Create a binding model object to display.
        """
        names = {STERIC_BINDING_MODEL: "New SMA model",
                 PH_STERIC_BINDING_MODEL: "New pH-dependent SMA model",
                 LANGMUIR_BINDING_MODEL: "New Langmuir model",
                 PH_LANGMUIR_BINDING_MODEL: "New pH-dep. Langmuir model"}

        component_names = self._target_component_names
        if bind_type in [STERIC_BINDING_MODEL, PH_STERIC_BINDING_MODEL]:
            component_names = ["Cation"] + component_names

        model = create_binding_model(
            len(component_names), model_type=bind_type, name=names[bind_type],
            component_names=component_names, target_product=self.target_product
        )
        return model

    # Traits property getters/setters methods ---------------------------------

    def _get_model(self):
        models = {STERIC_BINDING_MODEL: self._sma_model,
                  PH_STERIC_BINDING_MODEL: self._ph_sma_model,
                  LANGMUIR_BINDING_MODEL: self._langmuir_model,
                  PH_LANGMUIR_BINDING_MODEL: self._ext_langmuir_model}
        return models[self.binding_model_type]

    def _get_active_model_view(self):
        views = {STERIC_BINDING_MODEL: self._sma_model_view,
                 PH_STERIC_BINDING_MODEL: self._ph_sma_model_view,
                 LANGMUIR_BINDING_MODEL: self._langmuir_model_view,
                 PH_LANGMUIR_BINDING_MODEL: self._ext_langmuir_model_view}
        return views[self.binding_model_type]

    # Traits initialization methods -------------------------------------------

    def __sma_model_view_default(self):
        view = adapt(self._sma_model, ModelView)
        return view

    def __sma_model_default(self):
        return self.create_new_binding_model(STERIC_BINDING_MODEL)

    def __ph_sma_model_view_default(self):
        view = adapt(self._ph_sma_model, ModelView)
        return view

    def __ph_sma_model_default(self):
        return self.create_new_binding_model(PH_STERIC_BINDING_MODEL)

    def __langmuir_model_default(self):
        return self.create_new_binding_model(LANGMUIR_BINDING_MODEL)

    def __langmuir_model_view_default(self):
        view = adapt(self._langmuir_model, ModelView)
        return view

    def __ext_langmuir_model_default(self):
        return self.create_new_binding_model(PH_LANGMUIR_BINDING_MODEL)

    def __ext_langmuir_model_view_default(self):
        view = adapt(self._ext_langmuir_model, ModelView)
        return view
