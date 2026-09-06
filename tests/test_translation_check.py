import importlib.util
import unittest
from pathlib import Path


def _load_translation_check_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "translation_check.py"
    spec = importlib.util.spec_from_file_location("translation_check", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TranslationCheckTests(unittest.TestCase):
    def test_all_translation_files_match_base_keys(self) -> None:
        module = _load_translation_check_module()
        base_dir = Path(__file__).resolve().parents[1] / "custom_components" / "battery_monitor"
        errors = module.validate_translation_files(base_dir)
        self.assertEqual(errors, [], msg="\n".join(errors))


if __name__ == "__main__":
    unittest.main()
