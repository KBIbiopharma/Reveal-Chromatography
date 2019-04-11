# coding=utf-8
""" A module for all branding text content.
"""
import datetime

from kromatography import __build__, __version__

curr_year = datetime.datetime.now().year

APP_FAMILY = "REVEAL"

APP_TITLE = "Chromatography"

#: UUID for this application (constant over time). Generated using:
# >>> uuid5(NAMESPACE_DNS, 'kromatography')
APP_UUID = '4808dfa2-1b67-58e2-b6a9-5053dd613995'

# Duration for the splash screen with the KBI logo to be displayed upon launch
DEFAULT_SPLASH_DURATION = 3

# Same duration for the DEBUG mode so DEBUG launched runs still display the
# splash screen with the KBI logo
DEBUG_SPLASH_DURATION = 3

SPLASH_CONTENT = (u'Copyright Reveal Software © 2016-{} KBI Biopharma Inc, '
                  u'Durham, NC, USA\n'
                  u'Copyright CADET Software © 2015 Forschungszentrum Jülich '
                  u'GmbH, IBG-1, created by Joel \nAndersson, Sebastian '
                  u'Schnittert, Andreas Püttman, Samuel Leweke and Eric von '
                  u'Lieres.'.format(curr_year))

ABOUT_HTML = '''
<html>
  <body>
    <center>
      <table width="100%%" cellspacing="4" cellpadding="0" border="0">
        <tr>
          <td align="center">
          <p>
            <img src="%s" alt="">
          </td>
        </tr>
      </table>

      <p>
      %s<br>
      </p>
  </center>
  </body>
</html>
'''

ABOUT_MSG = ["{} {}-%s version {} build {}. <br><br>".format(
    APP_FAMILY, APP_TITLE, __version__, __build__)]

text = "Copyright {} {} &copy; 2016-{} KBI Biopharma, Inc., Durham NC, USA." \
       "<br> Created by Tim Fattor, Steve Hunt, Trent Larsen, Jonathan " \
       "Rocher and Robert Todd".format(APP_FAMILY, APP_TITLE, curr_year)
ABOUT_MSG += [text]

ABOUT_MSG += ["Copyright CADET software &copy; 2015-{} Forschungszentrum "
              "J&uuml;lich GmbH, IBG-1. <br>Created by Joel Andersson, "
              "Sebastian Schnittert, Andreas P&uuml;ttman, Samuel Leweke and "
              "Eric Von Lieres.".format(curr_year)]


SUPPORT_EMAIL_ADDRESS = "reveal-support@kbibiopharma.com"


BUG_REPORT_CONTENT_TEMPLATE = """
<!DOCTYPE html>
<html>
    <body>
    Thanks for your report and for helping us to improve {app_family} {app_name}!
    <p>
    To report an issue or send feedback, please contact us at
    <a href="mailto:{email}?Subject={subject}" target="_top">{email}</a>. When
    reporting an issue, please include the following in your email:
    <ol>
        <li>A description as precise as possible of what you were doing
        when the issue occurred.</li>
        <li>The version ({version}) and build number ({build}) of the
        version you are running.</li>
        <li>The log file at the time of the issue. All log files are in
        <a href="file://{log_dir}">{log_dir}</a>. (The one currently in
        use is <a href="file://{log_dir}">{log_file}</a>.)</li>
        <li>The project file. To create one, select
        <p><font face="Courier New">File > Save Project</font>.</p></li>
        {ds_item}
    </ol>
    <br><br>
    </p>
    We will get back to you quickly.
    </body>
</html>
"""  # noqa
