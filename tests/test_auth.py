"""Test ui/auth.make_auth: accetta solo la coppia username/password esatta."""
from __future__ import annotations

import unittest

from ui.auth import make_auth


class MakeAuthTest(unittest.TestCase):
    def setUp(self):
        self.check = make_auth("admin", "s3gret!")

    def test_correct_credentials(self):
        self.assertTrue(self.check("admin", "s3gret!"))

    def test_wrong_password(self):
        self.assertFalse(self.check("admin", "wrong"))

    def test_wrong_username(self):
        self.assertFalse(self.check("root", "s3gret!"))

    def test_case_sensitive(self):
        self.assertFalse(self.check("Admin", "s3gret!"))

    def test_empty_or_none(self):
        self.assertFalse(self.check("", ""))
        self.assertFalse(self.check(None, None))

    def test_non_ascii(self):
        check = make_auth("utènte", "pàssword€")
        self.assertTrue(check("utènte", "pàssword€"))
        self.assertFalse(check("utente", "pàssword€"))


if __name__ == "__main__":
    unittest.main()
