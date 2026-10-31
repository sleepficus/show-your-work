import io
import unittest

from exporter import export


class ExportTests(unittest.TestCase):
    def test_writes_rows(self):
        buf = io.StringIO()
        n = export([["a", "b"]], buf)
        self.assertEqual(n, 1)
        self.assertIn("a,b", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
