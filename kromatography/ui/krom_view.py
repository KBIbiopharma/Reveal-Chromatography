from traits.api import Bool
from traitsui.api import View
from .image_resources import reveal_chrom_icon


class KromView(View):
    """ Common view which sets arguments that are common to all app views.
    """
    resizable = Bool(True)
    icon = reveal_chrom_icon
