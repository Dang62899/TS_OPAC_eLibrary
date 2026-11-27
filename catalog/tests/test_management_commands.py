from io import StringIO

from django.core.management import call_command
from django.db import connection
from django.test import TestCase


class DatabaseOptimizationCommandTests(TestCase):
    def test_create_indices_uses_current_notification_schema(self):
        output = StringIO()

        call_command("optimize_database", create_indices=True, stdout=output)

        self.assertIn("9 created, 0 warnings", output.getvalue())
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor, "circulation_notification"
            )
        self.assertIn("idx_notification_borrower", constraints)

    def test_analysis_uses_database_introspection(self):
        output = StringIO()

        call_command("optimize_database", analyze=True, stdout=output)

        self.assertIn("Table Sizes:", output.getvalue())
        self.assertIn("Missing Indices:", output.getvalue())