import json
import unittest
from jCal.jCal import ical_to_jcal
import os
from pprint import pprint

class ICalToJCal(unittest.TestCase):
    maxDiff = None

    def test_conversion(self):
        for ics_file in [f for f in os.listdir("tests/assets") if f.endswith(".ics")]:
            json_file = ics_file.replace(".ics", ".json")
            if not os.path.exists(f"tests/assets/{ics_file}"):
                continue
            test_name = ics_file.removesuffix(".ics")
            with self.subTest(msg=test_name):
                print("Testing", test_name)
                with open(f"tests/assets/{json_file}", "r") as f:
                    reference = json.load(f)
                with open(f"tests/assets/{ics_file}", "r") as f:
                    ical = f.read().strip()
                    converted = ical_to_jcal(ical)
                pprint(f"Converted: {converted}")
                pprint(f"Reference: {reference}")
                self.assertListEqual(converted, reference)
