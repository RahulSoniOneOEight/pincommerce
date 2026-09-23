import unittest
from tooling.experience.visual_baseline import compare_hashes,load_baselines
class VisualBaselineTests(unittest.TestCase):
    def test_exact_png_hash_baseline(self):
        b=load_baselines(); captures=[]
        for p,views in b["captures"].items():
            for v,h in views.items(): captures.append({"pattern":p,"viewport_id":v,"screenshot_sha256":h})
        self.assertEqual(compare_hashes({"captures":captures},b)["status"],"passed")
    def test_change_blocks(self):
        b={"mode":"exact-png-hash","captures":{"x":{"mobile":"sha256:a"}}}
        r=compare_hashes({"captures":[{"pattern":"x","viewport_id":"mobile","screenshot_sha256":"sha256:b"}]},b)
        self.assertEqual(r["status"],"blocked")
if __name__=="__main__": unittest.main()
