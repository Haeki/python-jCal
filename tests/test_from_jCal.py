import json
import unittest
from jCal.jCal import from_ical
import os

class TestFromJCal(unittest.TestCase):

    def test_valid(self):
        for file in os.listdir("tests/assets"):
            if not file.endswith(".ics"):
                continue
            file2 = file.replace(".ics", ".json")
            if not os.path.exists(f"tests/assets/{file2}"):
                continue
            print("Testing", file)
            with open(f"tests/assets/{file}", "r") as f:
                jCal1 = from_ical(f.read())
            with open(f"tests/assets/{file2}", "r") as f:
                jCal2 = json.load(f)
            print(jCal1)
            self.assertListEqual(jCal2, jCal1)