import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INVALIDATED_ARTIFACTS = (
    "page.html",
    "id",
    "data.json",
    "ics",
    "image",
    "date",
    "categories",
    "circuits",
    "organizer",
    "slug",
    "title",
    "event-url",
)

FAKE_REQUESTS = '''
import json
import os
from pathlib import Path


class Response:
    def __init__(self, data):
        self.data = data
        self.content = json.dumps(data).encode()

    def raise_for_status(self):
        pass

    def json(self):
        return self.data


def record(method, url, timeout, data=None):
    path = Path(os.environ["REQUEST_RECORD"])
    with path.open("a") as f:
        f.write(json.dumps({"method": method, "url": url, "timeout": timeout, "data": data}) + "\\n")


def get(url, timeout):
    record("GET", url, timeout)
    return Response({
        "results": [{
            "geometry": {"location": {"lat": 38.72, "lng": -9.14}},
            "address_components": [
                {"types": ["country"], "long_name": "Portugal"},
                {"types": ["administrative_area_level_1"], "long_name": "Lisboa"},
            ],
        }]
    })


def post(url, headers, data, timeout):
    record("POST", url, timeout, data)
    return Response({"choices": [{"message": {"content": "Resumo atualizado"}}]})
'''


class ScrapeCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.event_dir = self.root / "events" / "example-event"
        self.event_dir.mkdir(parents=True)
        self.fake_modules = self.root / "fake-modules"
        self.fake_modules.mkdir()
        (self.fake_modules / "requests.py").write_text(FAKE_REQUESTS)
        self.request_record = self.root / "requests.jsonl"

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_script(self, script, *args, env=None):
        script_env = os.environ.copy()
        script_env.update(
            {
                "PYTHONPATH": str(self.fake_modules),
                "REQUEST_RECORD": str(self.request_record),
                "GOOGLE_MAPS_API_KEY": "unused",
                "OPENROUTER_KEY": "unused",
            }
        )
        if env:
            script_env.update(env)
        return subprocess.run(
            [sys.executable, str(REPO_ROOT / script), *args],
            cwd=self.root,
            env=script_env,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def recorded_requests(self):
        if not self.request_record.exists():
            return []
        return [json.loads(line) for line in self.request_record.read_text().splitlines()]

    def test_sitemap_change_preserves_expensive_artifacts(self):
        (self.root / "sitemap.xml").write_text(
            """<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.portugalrunning.com/eventos/example-event/</loc>
    <lastmod>2026-09-02T12:00:00+00:00</lastmod>
  </url>
</urlset>
"""
        )
        (self.event_dir / "lastmod").write_text("2026-08-01T12:00:00+00:00")
        for artifact in INVALIDATED_ARTIFACTS:
            (self.event_dir / artifact).write_text("stale")
        preserved = {
            "location": "location data",
            "location-input": "location hash",
            "oneline-description": "summary data",
            "oneline-description-input": "summary hash",
        }
        for artifact, value in preserved.items():
            (self.event_dir / artifact).write_text(value)

        self.run_script("setup-directories")

        for artifact in INVALIDATED_ARTIFACTS:
            self.assertFalse((self.event_dir / artifact).exists(), artifact)
        for artifact, value in preserved.items():
            self.assertEqual((self.event_dir / artifact).read_text(), value)
        self.assertEqual(
            (self.event_dir / "lastmod").read_text(),
            "2026-09-02T12:00:00+00:00",
        )

    def test_location_cache_tracks_cleaned_ics_location(self):
        (self.event_dir / "ics").write_text(
            "LOCATION:Porto\\, Portugal Porto\\, Portugal\n"
        )
        original_location = {
            "name": "Porto, Portugal Porto, Portugal",
            "country": "Portugal",
            "locality": "Porto",
        }
        (self.event_dir / "location").write_text(json.dumps(original_location))

        self.run_script("fetch-location", "example-event")

        self.assertEqual(self.recorded_requests(), [])
        first_input = (self.event_dir / "location-input").read_text()
        self.assertEqual(
            json.loads((self.event_dir / "location").read_text()), original_location
        )

        self.run_script("fetch-location", "example-event")
        self.assertEqual(self.recorded_requests(), [])
        self.assertEqual((self.event_dir / "location-input").read_text(), first_input)

        (self.event_dir / "ics").write_text(
            "LOCATION:Lisboa\\, Portugal Lisboa\\, Portugal\n"
        )
        self.run_script("fetch-location", "example-event")

        requests = self.recorded_requests()
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["method"], "GET")
        self.assertEqual(requests[0]["timeout"], 30)
        self.assertEqual(
            json.loads((self.event_dir / "location").read_text())["name"],
            "Lisboa, Portugal",
        )
        self.assertNotEqual(
            (self.event_dir / "location-input").read_text(), first_input
        )

    def test_summary_cache_ignores_markup_and_refreshes_visible_text(self):
        data_path = self.event_dir / "data.json"
        data_path.write_text(
            json.dumps(
                {
                    "content": {
                        "rendered": "<div>Trail <strong>na serra</strong></div><style>.card { color: red; }</style>"
                    }
                }
            )
        )
        summary_path = self.event_dir / "oneline-description"
        summary_path.write_text("Resumo existente")

        self.run_script("fetch-oneline-description", "example-event")

        self.assertEqual(self.recorded_requests(), [])
        first_input = (self.event_dir / "oneline-description-input").read_text()
        self.assertEqual(summary_path.read_text(), "Resumo existente")

        data_path.write_text(
            json.dumps(
                {
                    "content": {
                        "rendered": "<section> Trail&nbsp;<em>na serra</em><script>ignored()</script></section>"
                    }
                }
            )
        )
        self.run_script("fetch-oneline-description", "example-event")

        self.assertEqual(self.recorded_requests(), [])
        self.assertEqual(
            (self.event_dir / "oneline-description-input").read_text(), first_input
        )
        self.assertEqual(summary_path.read_text(), "Resumo existente")

        data_path.write_text(
            json.dumps(
                {"content": {"rendered": "<p>Trail noutra serra</p>"}}
            )
        )
        self.run_script("fetch-oneline-description", "example-event")

        requests = self.recorded_requests()
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["method"], "POST")
        self.assertEqual(requests[0]["timeout"], 30)
        request_data = json.loads(requests[0]["data"])
        self.assertEqual(
            request_data["messages"][1]["content"], "Trail noutra serra"
        )
        self.assertEqual(summary_path.read_text(), "Resumo atualizado")
        self.assertNotEqual(
            (self.event_dir / "oneline-description-input").read_text(), first_input
        )

        data_path.write_text(json.dumps({"content": {"rendered": "<style>x</style>"}}))
        self.run_script("fetch-oneline-description", "example-event")
        self.assertFalse(summary_path.exists())
        self.assertFalse((self.event_dir / "oneline-description-input").exists())
        self.assertEqual(len(self.recorded_requests()), 1)


if __name__ == "__main__":
    unittest.main()
