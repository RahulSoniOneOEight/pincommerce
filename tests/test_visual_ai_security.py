import json
import unittest

from tooling.experience.security_advisories import collect_osv
from tooling.experience.visual_ai_qa import normalize_review


class Response:
    def __init__(self, payload): self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps(self.payload).encode()


class VisualAISecurityTests(unittest.TestCase):
    def test_visual_ai_review_is_advisory_only(self):
        result = normalize_review({
            "provider":"visual-provider",
            "model":"vision-model",
            "screenshot_sha256":"sha256:abc",
            "findings":[{"severity":"major","category":"hierarchy","message":"CTA is weak"}],
        })
        self.assertEqual(result["status"], "review")
        self.assertFalse(result["approval_authority"])

    def test_osv_advisories_are_normalized(self):
        opener=lambda request,timeout=30: Response({"vulns":[{"id":"OSV-1","summary":"demo","aliases":["CVE-1"]}]})
        result=collect_osv("pkg","npm","1.0.0",opener=opener)
        self.assertEqual(result[0]["id"],"OSV-1")


if __name__ == "__main__":
    unittest.main()
