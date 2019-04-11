from unittest import TestCase
from os.path import dirname, isdir, isfile, join, splitext
import os
import shutil
from StringIO import StringIO
import json

from app_updater.utils import DEFAULT_HIST_FILENAME
from app_common.apptools.testing_utils import temp_bringup_ui_for
from app_common.apptools.update_downloader import download_version, \
    NO_RELEASE, RELEASE_LIST_FNAME, retrieve_file_from_url, \
    version_str_to_version

import kromatography
from kromatography.tools.update_downloader import EGG_REPO_URL, \
    UpdateDownloader
from kromatography.utils.app_utils import get_updater_folder

HERE = dirname(__file__)

NEWEST_CONTENT_FNAME = 'content_0.7.2_3.json'

FIRST_RELEASE_ENTRY = {u'release_filenames': [NEWEST_CONTENT_FNAME],
                       u'target_versions': u'0.6..+',
                       u'target_builds': u'.+',
                       u'target_users': u'all'}


class TestUpdateDownloader(TestCase):
    def setUp(self):
        self.updater = UpdateDownloader()

    def tearDown(self):
        hist_file = join(HERE, DEFAULT_HIST_FILENAME)
        if isfile(hist_file):
            os.remove(hist_file)

    def test_bringup(self):
        with temp_bringup_ui_for(self.updater):
            pass

    def test_default_release_data(self):
        updater = self.updater
        self.assertEqual(updater.release_data, [])
        self.assertEqual(updater.new_release_list, [])
        self.assertEqual(updater.newest_release, "")

        updater.release_data_file = join(HERE, "release_list.json")
        self.assertIn(FIRST_RELEASE_ENTRY, updater.release_data)

    def test_current_version(self):
        version, build = self.updater.current_version
        self.assertIsInstance(version, tuple)
        self.assertEqual(version,
                         version_str_to_version(kromatography.__version__))
        if len(kromatography.__build__) > 2:
            self.assertEqual(build, kromatography.__build__)
        else:
            self.assertEqual(build, int(kromatography.__build__))

        self.assertIsInstance(self.updater.current_version_msg, str)

    def test_download_release_data(self):
        local_egg_repo = get_updater_folder()
        release_list_file = join(local_egg_repo, RELEASE_LIST_FNAME)
        if isfile(release_list_file):
            os.remove(release_list_file)

        self.updater.update_release_data_file()
        try:
            self.assertTrue(isfile(release_list_file))
        finally:
            os.remove(release_list_file)

        # Information propagates to the release_data attribute
        self.assertIn(FIRST_RELEASE_ENTRY, self.updater.release_data)

    def test_download_release_data_using_button(self):
        local_egg_repo = get_updater_folder()
        release_list_file = join(local_egg_repo, RELEASE_LIST_FNAME)
        if isfile(release_list_file):
            os.remove(release_list_file)

        self.updater.check_button = True
        try:
            self.assertTrue(isfile(release_list_file))
        finally:
            os.remove(release_list_file)

        # Information propagates to the release_data attribute
        self.assertIn(FIRST_RELEASE_ENTRY, self.updater.release_data)

    def test_new_releases_previous_minor_version(self):
        # Fake to be in an old version state for the specified release to be
        # considered eligible.
        updater = UpdateDownloader(current_version=((0, 6, 1), 4))
        updater.release_data_file = join(HERE, "release_list.json")
        self.assertIn(NEWEST_CONTENT_FNAME, updater.new_release_list)
        self.assertEqual(updater.newest_release, NEWEST_CONTENT_FNAME)

    def test_new_releases_previous_minor_version_str(self):
        # Fake to be in an old version state for the specified release to be
        # considered eligible.
        updater = UpdateDownloader(current_version=("0.6.1", 4))
        updater.release_data_file = join(HERE, "release_list.json")
        self.assertIn(NEWEST_CONTENT_FNAME, updater.new_release_list)
        self.assertEqual(updater.newest_release, NEWEST_CONTENT_FNAME)

    def test_new_releases_previous_bug_fix_release(self):
        # Slightly older version (and build)
        updater = UpdateDownloader(current_version=("0.7.1", 2))
        updater.release_data_file = join(HERE, "release_list.json")
        self.assertIn(NEWEST_CONTENT_FNAME, updater.new_release_list)
        self.assertEqual(updater.newest_release, NEWEST_CONTENT_FNAME)

    def test_new_releases_previous_bug_fix_release_but_larger_build(self):
        # slightly order version but larger build number
        updater = UpdateDownloader(current_version=("0.7.1", 4))
        updater.release_data_file = join(HERE, "release_list.json")
        self.assertIn(NEWEST_CONTENT_FNAME, updater.new_release_list)
        self.assertEqual(updater.newest_release, NEWEST_CONTENT_FNAME)

    def test_new_releases_previous_minor_version_09_010(self):
        """ Test that 0.10 is treated as newer than 0.9."""
        updater = UpdateDownloader(current_version=("0.9.2", 1))
        updater.release_data_file = join(HERE, "release_list2.json")
        self.assertIn('content_0.10.0_0.json', updater.new_release_list)
        self.assertEqual(updater.newest_release, 'content_0.10.0_0.json')

    def test_new_releases_previous_build_number(self):
        # Fake to be the same version but a previous build number for the
        # specified release to be considered eligible.
        updater = UpdateDownloader(current_version=("0.7.2", 2))
        updater.release_data_file = join(HERE, "release_list.json")
        self.assertIn(NEWEST_CONTENT_FNAME, updater.new_release_list)
        self.assertEqual(updater.newest_release, NEWEST_CONTENT_FNAME)

    def test_no_new_releases_future_version(self):
        # Larger major version number:
        updater = UpdateDownloader(current_version=("1.4", 1))
        updater.release_data_file = join(HERE, "release_list.json")
        self.assert_no_release_found(updater)

    def test_no_new_releases_same_version(self):
        # Fake to be in a futuristic version
        updater = UpdateDownloader(current_version=("0.7.2", 3))
        updater.release_data_file = join(HERE, "release_list.json")
        self.assert_no_release_found(updater)

    def test_download_data_to_existing_folder(self):
        self.assert_can_download_update_to(HERE)

    def test_download_data_to_existing_folder_using_button(self):
        updater = UpdateDownloader(local_egg_repo=HERE, allow_dlg=False,
                                   current_version=("0.6.1", 4))
        updater.release_data_file = join(HERE, "release_list.json")
        updater.download_button = True
        self.assert_files_downloaded_to(HERE)

    def test_fail_download_data_bad_release_file(self):
        updater = UpdateDownloader(local_egg_repo=HERE, allow_dlg=False,
                                   current_version=("0.6.1", 4))
        updater.release_data_file = join(HERE, "BAD_release_list.json")
        updater.download_button = True
        # There is not content file downloaded or no egg
        for fname in os.listdir(HERE):
            self.assertNotIn("content", fname)
            ext = splitext(fname)[1]
            self.assertNotEqual(ext, ".egg")

    def test_download_data_to_new_folder(self):
        local_egg_repo = join(HERE, "new folder")
        self.assertFalse(isdir(local_egg_repo))
        try:
            self.assert_can_download_update_to(local_egg_repo)
        finally:
            shutil.rmtree(local_egg_repo)

    def test_download_utility(self):
        download_version(NEWEST_CONTENT_FNAME, egg_repo_url=EGG_REPO_URL,
                         local_egg_repo=HERE)
        self.assert_files_downloaded_to(HERE)

    def test_download_utility_with_bitly_link(self):
        self.skipTest("bitly not yet in use")
        download_version("content_v0.10.4_1.json", egg_repo_url=EGG_REPO_URL,
                         local_egg_repo=HERE)
        filenames = ["content_v0.10.4_1.json", 'kromatography-0.10.4-1.egg']
        self.assert_files_downloaded_to(HERE, filenames=filenames)

    # Helper methods ----------------------------------------------------------

    def assert_no_release_found(self, updater):
        self.assertEqual(updater.new_release_list, [])
        self.assertEqual(updater.newest_release, NO_RELEASE)
        self.assertIsInstance(updater.newest_release_msg, str)

    def assert_can_download_update_to(self, local_egg_repo):
        updater = UpdateDownloader(local_egg_repo=local_egg_repo,
                                   current_version=("0.6.1", 4))
        updater.release_data_file = join(HERE, "release_list.json")
        self.assertEqual(updater.newest_release, NEWEST_CONTENT_FNAME)
        success = updater.download_newest_version()

        self.assertTrue(success)
        self.assert_files_downloaded_to(local_egg_repo)

    def assert_files_downloaded_to(self, local_egg_repo, filenames=None):
        if filenames is None:
            filenames = [NEWEST_CONTENT_FNAME, 'kromatography-0.7.2-3.egg']

        for fname in filenames:
            try:
                self.assertIn(fname, os.listdir(local_egg_repo))
            finally:
                filepath = join(local_egg_repo, fname)
                if isfile(filepath):
                    os.remove(filepath)


class TestFileDownloadUtility(TestCase):

    def tearDown(self):
        if isfile(self.tgt_file):
            os.remove(self.tgt_file)

    def test_retrieve_text_file(self):
        self.tgt_file = join(HERE, "new_file.txt")
        if isfile(self.tgt_file):
            os.remove(self.tgt_file)

        retrieve_file_from_url(EGG_REPO_URL+RELEASE_LIST_FNAME, self.tgt_file)
        self.assertTrue(isfile(self.tgt_file))
        content = open(self.tgt_file, "r").read().strip()
        loaded_content = json.load(StringIO(content))
        self.assertIn(FIRST_RELEASE_ENTRY, loaded_content)
