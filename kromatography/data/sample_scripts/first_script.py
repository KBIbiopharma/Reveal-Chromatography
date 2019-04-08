""" Example script changing attributes of the application: study, user data,
....

Note: This script is overly simple. What happens if you try and open the newly
created simulation? See second_script.py for a little more realistic objects.
"""
from kromatography.model.api import Product, Simulation

# Example of changing the content of the datasource by adding a new product
new_prod = Product(name="PROD002", product_type="Mab")
user_datasource.set_object_of_type("products", new_prod)

print("Current Study contains {} simulations".format(len(study.simulations)))

# Create a new simulation and add it to the study:
new_sim = Simulation(name="new")
study.add_simulations(new_sim)

# Open the new product in the central pane:
task.edit_object_in_central_pane(new_prod)
