"""
Nose plugin for easy testing of django projects and apps. Sets up a test
database and installs apps from test settings file before tests are run.
"""
from nose.plugins import Plugin


class SimpleFastDjango(Plugin):
    """
    Enable to set up Django test environment
    before running all tests in a quick way.
    """
    name = 'sfd'

    def configure(self, options, conf):
        Plugin.configure(self, options, conf)
        self.verbosity = 0

    def begin(self):
        """
        Initialize the test environment then create the test database
        and switch the connection over to that database.
        """
        from django.conf import settings
        from django.db import connection
        from django.test.utils import setup_test_environment

        try:
            self.original_db_name = settings.DATABASE_NAME
        except AttributeError:  # Django > 1.2
            self.original_db_name = settings.DATABASES['default']['NAME']

        setup_test_environment()
        from south.hacks import hacks
        from django.core import management
        management.get_commands()
        hacks.patch_flush_during_test_db_creation()


        connection.creation.create_test_db(self.verbosity)

        if 'south' in settings.INSTALLED_APPS:
            from south import migration

            for app in migration.all_migrations():
                migration.migrate_app(app, verbosity=self.verbosity)

    def finalize(self, result):
        """
        Teardown the test environment and destroy the test database.
        """
        from django.db import connection
        from django.test.utils import teardown_test_environment

        connection.creation.destroy_test_db(self.original_db_name,
                                            self.verbosity)
        teardown_test_environment()
