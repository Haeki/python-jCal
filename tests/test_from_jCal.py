import json
import unittest
import icalendar
from jCal.jCal import from_jcal, from_ical
import os
from pprint import pprint


class TestFromJCal(unittest.TestCase):
    maxDiff = None

    def test_valid(self):
        for file in os.listdir("tests/assets"):
            if not file.endswith(".json"):
                continue
            file2 = file.replace(".json", ".ics")
            if not os.path.exists(f"tests/assets/{file2}"):
                continue
            with self.subTest(msg=file):
                print("Testing", file)
                with open(f"tests/assets/{file}", "r") as f:
                    jcal = json.load(f)
                    ical_1 = from_jcal(jcal)
                with open(f"tests/assets/{file2}", "r") as f:
                    ical_2 = f.read().strip()
                ical_1_str = (
                    b"".join(ic.to_ical() for ic in ical_1)
                    if isinstance(ical_1, list)
                    else ical_1.to_ical()
                )
                ical_1_str = ical_1_str.replace(b"\r\n", b"\n").decode("utf-8").strip()
                pprint(f"Converted: {ical_1_str}")
                pprint(f"Original: {ical_2}")
                self.assertEqual(ical_2, ical_1_str)
                self.assertListEqual(jcal, from_ical(ical_1))
