""" Object and UI to check for and download any available update for the
current version and user.
"""
import sys
from logging import getLogger

from traits.api import Str

from app_common.apptools.update_downloader import UpdateDownloader as \
    BaseUpdateDownloader, version_str_to_version
import kromatography
from kromatography.utils.traitsui_utils import KromView
from kromatography.utils.app_utils import get_updater_folder, \
    initialize_updater_folder
from kromatography.ui.branding import APP_TITLE
from kromatography.utils.url_definitions import CHANGELOG_URL

logger = getLogger(__name__)

EGG_REPO_URL = "http://reveal.kbibiopharma.com/chromatography/eggs/{platform}/"

UPGRADE_URL = "https://www.kbibiopharma.com/download-reveal-chromatography"

EGG_REPO_URL = EGG_REPO_URL.format(platform=sys.platform)


class UpdateDownloader(BaseUpdateDownloader):
    """ Tool to check if a new release has been made.
    """
    #: URL to connect to to find new releases
    egg_repo_url = Str(EGG_REPO_URL)

    #: URL to the changelog (pointed to by help text)
    changelog_url = Str(CHANGELOG_URL)

    #: Application's title
    app_title = Str(APP_TITLE)

    #: View class to use for pop-up window:
    updater_view = KromView

    #: URL to point the user to for upgrade instructions
    upgrade_url = Str(UPGRADE_URL)

    def initialize(self):
        """ Initialize resources for downloader files. """
        initialize_updater_folder()

    # Traits initialization methods -------------------------------------------

    def _current_version_default(self):
        """ Convert the build number to an int if it's not a hash.
        """
        curr_v = version_str_to_version(kromatography.__version__)
        curr_b = kromatography.__build__

        # Since it is a real build and not a git hash, convert to an integer so
        # integer comparison works (for e.g. to avoid issues with 2 found more
        # recent than 10.)
        if len(curr_b) <= 2:
            curr_b = int(curr_b)

        return curr_v, curr_b

    def _local_updater_folder_default(self):
        return get_updater_folder()

    def _view_height_default(self):
        return 200

    def _adtl_bottom_view_groups_default(self):
        return []


if __name__ == "__main__":
    kromatography.__version__ = "0.6.0.dev0"
    tool = UpdateDownloader()
    tool.check_button = True
    tool.configure_traits()
