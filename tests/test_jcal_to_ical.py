import json
import unittest
from jCal.jCal import jcal_to_ical
import os

class JCalToICal(unittest.TestCase):
    maxDiff = None

    def test_conversion(self):
        for json_file in [f for f in os.listdir("tests/assets") if f.endswith(".json")]:
            ics_file = json_file.replace(".json", ".ics")
            if not os.path.exists(f"tests/assets/{ics_file}"):
                continue
            test_name = json_file.removesuffix(".json")
            with self.subTest(msg=test_name):
                print("Testing", test_name)
                with open(f"tests/assets/{json_file}", "r") as f:
                    jcal = json.load(f)
                    converted = jcal_to_ical(jcal)
                with open(f"tests/assets/{ics_file}", "r") as f:
                    reference = f.read().strip()
                converted_str = (
                    b"".join(c.to_ical() for c in converted)
                    if isinstance(converted, list)
                    else converted.to_ical()
                )
                converted_str = converted_str.replace(b"\r\n", b"\n").decode("utf-8").strip()
                print(f"Converted: {converted_str}")
                print(f"Reference: {reference}")
                self.assertEqual(converted_str, reference)
                #self.assertListEqual(jcal, from_ical(ical_1))
