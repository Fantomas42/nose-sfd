"""
Nose plugin for easy testing of django projects and apps. Sets up a test
database (or schema) and installs apps from test settings file before tests
are run, and tears the test database (or schema) down after all tests are run.
"""
import os
import re
import sys

from nose.plugins import Plugin
import nose.case

# Force settings.py pointer
# search the current working directory and all parent directories to find
# the settings file
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
NT_ROOT = re.compile(r"^[a-zA-Z]:\\$")


def get_SETTINGS_PATH():
    '''
    Hunt down the settings.py module by going up the FS path
    '''
    cwd = os.getcwd()
    while cwd:
        if 'settings.py' in os.listdir(cwd):
            break
        cwd = os.path.split(cwd)[0]
        if os.name == 'nt' and NT_ROOT.match(cwd):
            return None
        elif cwd == '/':
            return None
    return cwd

SETTINGS_PATH = get_SETTINGS_PATH()


class SimpleFastDjango(Plugin):
    """
    Enable to set up django test environment before running all tests, and
    tear it down after all tests. If the django database engine in use is not
    sqlite3, one or both of --django-test-db or django-test-schema must be
    specified.

    Note that your django project must be on PYTHONPATH for the settings file
    to be loaded. The plugin will help out by placing the nose working dir
    into sys.path if it isn't already there, unless the -P
    (--no-path-adjustment) argument is set.
    """
    name = 'sfd'

    def configure(self, options, conf):
        Plugin.configure(self, options, conf)
        self.verbosity = conf.verbosity

    def begin(self):
        """Create the test database and schema, if needed, and switch the
        connection over to that database. Then call install() to install
        all apps listed in the loaded settings module.
        """
        # use dynamical import: we not necessary use settings.py
        __import__(os.environ['DJANGO_SETTINGS_MODULE'])
        settings = sys.modules[os.environ['DJANGO_SETTINGS_MODULE']]

        # Some Django code paths evaluate differently
        # between DEBUG and not DEBUG.  Example of this include the url
        # dispatcher when 404's are hit.  Django's own test runner forces DEBUG
        # to be off.
        settings.DEBUG = False

        from django.core import mail
        self.mail = mail
        from django.conf import settings
        from django.test.utils import setup_test_environment
        from django.db import connection

        try:
            self.old_db = settings.DATABASE_NAME
        except AttributeError:
            self.old_db = settings.DATABASES['default']['NAME']

        # setup the test env for each test case
        setup_test_environment()
        connection.creation.create_test_db(verbosity=self.verbosity)

        # exit the setup phase and let nose do it's thing

    def beforeTest(self, test):

        if not SETTINGS_PATH:
            # short circuit if no settings file can be found
            return

        # This is a distinctive difference between the NoseDjango
        # test runner compared to the plain Django test runner.
        # Django uses the standard unittest framework and resets the
        # database between each test *suite*.  That usually resolves
        # into a test module.
        #
        # The NoseDjango test runner will reset the database between *every*
        # test case.  This is more in the spirit of unittesting where there is
        # no state information passed between individual tests.

        from django.core.management import call_command
        from django.core.urlresolvers import clear_url_caches
        from django.conf import settings
        call_command('flush', verbosity=0, interactive=False)

        if isinstance(test, nose.case.Test) and \
            isinstance(test.test, nose.case.MethodTestCase) and \
            hasattr(test.context, 'fixtures'):
                # We have to use this slightly awkward syntax due to the fact
                # that we're using *args and **kwargs together.
                call_command('loaddata', *test.context.fixtures,
                             **{'verbosity': 0})

        if isinstance(test, nose.case.Test) and \
            isinstance(test.test, nose.case.MethodTestCase) and \
            hasattr(test.context, 'urls'):
                # We have to use this slightly awkward syntax due to the fact
                # that we're using *args and **kwargs together.
                self.old_urlconf = settings.ROOT_URLCONF
                settings.ROOT_URLCONF = self.urls
                clear_url_caches()

        self.mail.outbox = []

    def finalize(self, result=None):
        """
        Clean up any created database and schema.
        """
        if not SETTINGS_PATH:
            # short circuit if no settings file can be found
            return

        from django.test.utils import teardown_test_environment
        from django.db import connection
        from django.conf import settings
        from django.core.urlresolvers import clear_url_caches
        connection.creation.destroy_test_db(
            self.old_db, verbosity=self.verbosity)
        teardown_test_environment()

        if hasattr(self, 'old_urlconf'):
            settings.ROOT_URLCONF = self.old_urlconf
            clear_url_caches()
