""" Test script modifying the user datasource.
"""
import logging
from kromatography.model.product import Product

logger = logging.getLogger(__name__)

# Example of changing the content of the datasource by adding a new product
new_prod = Product(name="PROD", product_type="Mab")
user_datasource.set_object_of_type("products", new_prod)  # noqa

logger.warning("Opening new product {} in central pane...".format(new_prod))
