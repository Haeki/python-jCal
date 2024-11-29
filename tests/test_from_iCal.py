import json
import unittest
from jCal.jCal import from_ical
import os
from pprint import pprint

class TestFromJCal(unittest.TestCase):
    maxDiff = None

    def test_valid(self):
        for file in os.listdir("tests/assets"):
            if not file.endswith(".ics"):
                continue
            file2 = file.replace(".ics", ".json")
            if not os.path.exists(f"tests/assets/{file2}"):
                continue
            with self.subTest(msg=file):
                print("Testing", file)
                with open(f"tests/assets/{file}", "r") as f:
                    jCal1 = from_ical(f.read())
                with open(f"tests/assets/{file2}", "r") as f:
                    jCal2 = json.load(f)
                pprint(f"Converted: {jCal1}")
                pprint(f"Original: {jCal2}")
                #self.assertEqual(json.dumps(jCal1, sort_keys=True), json.dumps(jCal2, sort_keys=True))
                self.assertListEqual(jCal2, jCal1)
