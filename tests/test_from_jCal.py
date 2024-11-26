import json
import unittest
from jCal.jCal import from_ical

class TestFromJCal(unittest.TestCase):

    def test_valid(self):
        with open("tests/assets/rfc.json", "r") as f:
            jCal1 = json.load(f)
        with open("tests/assets/rfc.ics", "r") as f:
            jCal2 = from_ical(f.read())

        self.assertListEqual(jCal1, jCal2)