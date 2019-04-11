import logging

from app_common.traitsui.adapters.trait_object_to_tree_node import \
    TraitListObjectToTreeNode as BaseTraitListObjectToTreeNode

logger = logging.getLogger(__name__)


class TraitListObjectToTreeNode(BaseTraitListObjectToTreeNode):
    """ Adapts a list of objects to an ITreeNode.

    This class implements the ITreeNodeAdapter interface thus allowing the use
    of TreeEditor for viewing any TraitList.
    """
    def _prepare_to_append(self, obj):
        """ Prepare to append to a list.

        Parameters
        ----------
        obj : any
            Object to review and optionally modify to prepare it to be appended
            to current list.

        Returns
        -------
        Any
            Object to paste, if any.
        """
        from kromatography.model.api import Experiment, Product, Simulation, \
            BindingModel, TransportModel, LazyLoadingSimulation
        from kromatography.utils.traitsui_utils import prompt_for_new_name

        types_with_uniq_names = (Experiment, Simulation, Product, BindingModel,
                                 TransportModel)
        # Avoid trying to paste LazyLoading sims since they freeze the app
        # on Windows
        if isinstance(obj, LazyLoadingSimulation):
            obj = obj.to_simulation()

        if isinstance(obj, types_with_uniq_names):
            existing_obj_names = {element.name for element in self.adaptee}
            if obj.name in existing_obj_names:
                msg = "Names of {}s should be unique: please enter a new " \
                      "name for {}.".format(type(obj).__name__, obj.name)
                new_name = prompt_for_new_name(obj, msg=msg)
                if new_name:
                    obj.name = new_name

            if obj.name not in existing_obj_names:
                return obj
        else:
            return obj
