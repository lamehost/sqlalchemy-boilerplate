"""
Automated tests for the package
"""

import os
import unittest

from sqlalchemy_boilerplate import Boilerplate, AsyncBoilerplate


class TestBoilerplate(unittest.TestCase):
    """
    Automated tests for the Boilerplate class
    """
    def setUp(self):
        """
        Define context for the methods below
        """
        # Get variable from ENV
        no_maxdiff = os.getenv('NO_MAXDIFF', None)
        if no_maxdiff:
            self.maxDiff = None  # pylint: disable=invalid-name

    def test_call_method(self):
        """
        Test if class can be used as a method
        """
        database = Boilerplate(
           url="sqlite://",
           echo=False,
           create_tables=True
        )
        database = database()
        self.assertIsInstance(database, Boilerplate)

        for row in database.execute("SELECT date('1982-10-26');"):
            self.assertEqual(row, ('1982-10-26', ))

    def test_with_context(self):
        """
        Test if class can be used within context
        """
        with Boilerplate(
           url="sqlite://",
           echo=False,
           create_tables=True
        ) as database:
            self.assertIsInstance(database, Boilerplate)

        for row in database.execute("SELECT date('1982-10-26');"):
            self.assertEqual(row, ('1982-10-26', ))


class TestAsyncBoilerplate(unittest.IsolatedAsyncioTestCase):
    """
    Automated tests for the AsyncBoilerplate class
    """
    def setUp(self):
        """
        Define context for the methods below
        """
        # Get variable from ENV
        no_maxdiff = os.getenv('NO_MAXDIFF', None)
        if no_maxdiff:
            self.maxDiff = None  # pylint: disable=invalid-name

    async def test_call_method(self):
        """
        Test if class can be used as a method
        """
        database = AsyncBoilerplate(
           url="sqlite://",
           echo=False,
           create_tables=True
        )
        database = await database()
        self.assertIsInstance(database, AsyncBoilerplate)

        async for row in database.execute("SELECT date('1982-10-26');"):
            self.assertEqual(row, ('1982-10-26', ))

    async def test_with_context(self):
        """
        Test if class can be used within context
        """
        async with AsyncBoilerplate(
           url="sqlite://",
           echo=False,
           create_tables=True
        ) as database:
            self.assertIsInstance(database, AsyncBoilerplate)

            async for row in database.execute("SELECT date('1982-10-26');"):
                self.assertEqual(row, ('1982-10-26', ))


if __name__ == '__main__':
    unittest.main(verbosity=2)
