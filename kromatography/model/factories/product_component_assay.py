from kromatography.model.product_component_assay import ProductComponentAssay


def assay_names_from_instances(component_assay_list):
    """ Convert a list of ProductComponentAssays into a list of assay names.
    """
    return [assay.name for assay in component_assay_list]


def assay_instances_from_names(assay_names):
    """ List of instances of ProductComponentAssays from a list of assay names.
    """
    return [ProductComponentAssay(name=name) for name in assay_names]
