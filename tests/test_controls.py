import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'src' / 'pwnagotchi_hgsec' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

buttons = load('buttons')
actions = load('actions')

class HoldTests(unittest.TestCase):
    def test_hold_fires_once_and_requires_release(self):
        detector = buttons.HoldDetector()
        self.assertFalse(detector.update(20, True, 0))
        self.assertFalse(detector.update(20, True, 1.99))
        self.assertTrue(detector.update(20, True, 2))
        self.assertFalse(detector.update(20, True, 5))
        self.assertFalse(detector.update(20, False, 5.1))
        self.assertFalse(detector.update(20, True, 6))
        self.assertTrue(detector.update(20, True, 8))

    def test_releasing_early_resets_hold(self):
        detector = buttons.HoldDetector()
        detector.update(16, True, 0)
        detector.update(16, False, 1.9)
        self.assertFalse(detector.update(16, True, 2))
        self.assertFalse(detector.update(16, True, 3.9))
        self.assertTrue(detector.update(16, True, 4))

class ToggleTests(unittest.TestCase):
    def test_toggle_preserves_other_configuration_and_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'config.toml'
            config.write_text('personality.deauth = false # research\nui.fps = 1\n')
            config.chmod(0o640)
            self.assertTrue(actions.toggle_config(config))
            self.assertEqual(config.read_text(), 'personality.deauth = true # research\nui.fps = 1\n')
            self.assertEqual(config.stat().st_mode & 0o777, 0o640)
            self.assertFalse(actions.toggle_config(config))
            self.assertIn('personality.deauth = false', config.read_text())

    def test_refuses_missing_or_ambiguous_config_without_modification(self):
        for content in ('ui.fps = 1\n', '[personality]\ndeauth = false\n', 'personality.deauth = true\npersonality.deauth = false\n'):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                config = Path(directory) / 'config.toml'
                config.write_text(content)
                with self.assertRaises(ValueError):
                    actions.toggle_config(config)
                self.assertEqual(config.read_text(), content)

if __name__ == '__main__':
    unittest.main()
