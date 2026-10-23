"""Checks for the production start command."""

import unittest
from pathlib import Path

from server import app, create_app


ROOT = Path(__file__).resolve().parents[1]


class DeployConfigTests(unittest.TestCase):
    def test_blueprint_starts_one_worker_on_port(self):
        blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        start = "gunicorn --bind 0.0.0.0:$PORT --workers 1 server:app"

        self.assertIn(start, blueprint)
        self.assertIn(start, readme)
        self.assertIn("pip install -r requirements.txt", blueprint)
        self.assertIn("plan: free", blueprint)
        self.assertEqual(blueprint.count("type: web"), 1)

    def test_imported_app_is_not_in_debug_mode(self):
        self.assertFalse(app.debug)
        self.assertFalse(create_app().debug)


if __name__ == "__main__":
    unittest.main()
