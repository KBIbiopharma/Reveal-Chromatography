from app_common.pyface.ui.extra_file_dialogs import generate_file_requester
from kromatography.ui.tasks.kromatography_task import KROM_EXTENSION


desc = "Experimental Study Excel"
ext = "*xlsx"
study_file_requester = generate_file_requester(desc, ext)


desc = "CSV data"
ext = "*csv"
to_csv_file_requester = generate_file_requester(desc, ext, action="save as")


desc = "Project"
project_file_requester = generate_file_requester(desc, KROM_EXTENSION)
