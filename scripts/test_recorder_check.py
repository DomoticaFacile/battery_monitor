import importlib.util
import unittest
from pathlib import Path


def _load_recorder_check_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "recorder_check.py"
    spec = importlib.util.spec_from_file_location("recorder_check", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecorderAttributesTests(unittest.TestCase):
    def test_list_attributes_are_not_recorded(self) -> None:
        module = _load_recorder_check_module()
        sensor_path = (
            Path(__file__).resolve().parents[1]
            / "custom_components"
            / "battery_monitor"
            / "sensor.py"
        )
        errors = module.validate_recorder_attributes(sensor_path)
        self.assertEqual(errors, [], msg="\n".join(errors))


if __name__ == "__main__":
    unittest.main()
