
from traits.api import Button, Instance, Property, Str
from traitsui.api import EnumEditor, HGroup, Item, Label, ModelView, Spring, \
    VGroup, View

from kromatography.model.study import Study
from kromatography.io.study import load_exp_study_from_excel
from kromatography.model.product import BLANK_PRODUCT_NAME, make_blank_product
from kromatography.ui.menu_entry_names import \
    NEW_BLANK_PROJECT_MENU_NAME, NEW_PROJECT_FROM_EXPERIMENT_MENU_NAME, \
    OPEN_PROJECT_MENU_NAME

#: Limit in number of character for the path to the source experiment before
# truncation:
SOURCE_LIMIT_NUM_CHAR = 100


class StudyView(ModelView):
    """ View for a (modeling) Study model.
    """
    #: Model this view is about
    model = Instance(Study)

    #: Name of the product the model is about
    product_name = Property(depends_on="model.product.name")

    #: Button to create a new study from scratch on welcome screen
    new_study_button = Button(NEW_BLANK_PROJECT_MENU_NAME)

    #: Button to load a new study on welcome screen
    load_study_from_exp_button = Button(NEW_PROJECT_FROM_EXPERIMENT_MENU_NAME)

    #: Button to load an existing project
    open_project_button = Button(OPEN_PROJECT_MENU_NAME)

    #: Proxy for the model's experimental study filepath
    _exp_study_filepath = Property(Str, depends_on="model.exp_study_filepath")

    def default_traits_view(self):
        known_products = self.model.datasource.get_object_names_by_type(
            "products"
        )
        known_product_names = [BLANK_PRODUCT_NAME] + sorted(known_products)
        full_exp_path = self.model.exp_study_filepath

        view = View(
            VGroup(
                VGroup(
                    Item("model.name"),
                    Item("_exp_study_filepath", label="Source",
                         style="readonly", tooltip=full_exp_path),
                    Item("product_name",
                         editor=EnumEditor(values=known_product_names),
                         label="Product Name"),
                    Item("model.study_type"),
                    Item("model.study_purpose", style="custom"),
                    label="General Study Information:", show_border=True,
                    visible_when="not model.is_blank",
                ),
                VGroup(
                    Spring(),
                    VGroup(
                        HGroup(
                            Spring(),
                            Item("new_study_button", show_label=False),
                            Spring()
                        ),
                        HGroup(Spring(), Label("or"), Spring()),
                        HGroup(
                            Spring(),
                            Item("load_study_from_exp_button",
                                 show_label=False),
                            Spring()
                        ),
                        HGroup(Spring(), Label("or"), Spring()),
                        HGroup(
                            Spring(),
                            Item("open_project_button",
                                 show_label=False),
                            Spring()
                        ),
                    ),
                    Spring(),
                    visible_when="model.is_blank",
                    label="Create New Project", show_border=True,
                ),
            ),
        )

        return view

    def _get_product_name(self):
        if self.model and self.model.product:
            return self.model.product.name
        else:
            return ""

    def _set_product_name(self, product_name):
        if product_name == BLANK_PRODUCT_NAME:
            prod = make_blank_product()
        else:
            ds = self.model.datasource
            prod = ds.get_object_of_type("products", product_name)

        self.model.product = prod

    def _new_study_button_fired(self):
        self.model.is_blank = False

    def _load_study_from_exp_button_fired(self):
        from kromatography.utils.extra_file_dialogs import study_file_requester
        from app_common.pyface.monitored_actions import action_monitoring
        from kromatography.ui.menu_entry_names import \
            NEW_PROJECT_FROM_EXPERIMENT_MENU_NAME

        path = study_file_requester()
        if path is not None:
            with action_monitoring(NEW_PROJECT_FROM_EXPERIMENT_MENU_NAME):
                exp_study = load_exp_study_from_excel(
                    path, datasource=self.model.datasource
                )
                self.model.update_from_experimental_study(exp_study)

    def _open_project_button_fired(self):
        self._task._app.request_project_from_file()

    # Property getters/setters ------------------------------------------------

    def _get__exp_study_filepath(self):
        """ If the path to the source experiment is too long, truncate."""
        source = self.model.exp_study_filepath
        if len(source) > SOURCE_LIMIT_NUM_CHAR:
            source = (source[:int(SOURCE_LIMIT_NUM_CHAR/2)-2] + " ... " +
                      source[-int(SOURCE_LIMIT_NUM_CHAR/2):])
        return source
