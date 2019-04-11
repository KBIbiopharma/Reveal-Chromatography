"""
Load product data from any datasource file into the active one user datasource
"""
# Script inputs ---------------------------------------------------------------

EXTERNAL_DATASOURCE_FILEPATH = r"<FILE PATH HERE>"

PRODUCT_TO_IMPORT = "<YOUR PRODUCT NAME HERE>"

# Script ----------------------------------------------------------------------

import logging
from kromatography.io.reader_writer import load_object

logger = logging.getLogger(__name__)

logger.warning("Loading external datasource...")
ds = load_object(EXTERNAL_DATASOURCE_FILEPATH)

new_prod_comps = ds.get_objects_by_type(
    "product_components", filter_by={"target_product": PRODUCT_TO_IMPORT})
msg = "Adding {} components into active datasource..."
msg = msg.format(len(new_prod_comps))
logger.warning(msg)
for new_comp in new_prod_comps:
    user_datasource.set_object_of_type("product_components", new_comp)

logger.warning("Adding new product into active datasource...")
new_prod = ds.get_object_of_type("products", PRODUCT_TO_IMPORT)
user_datasource.set_object_of_type("products", new_prod)

task.edit_object_in_central_pane(new_prod)

# End of script ---------------------------------------------------------------
