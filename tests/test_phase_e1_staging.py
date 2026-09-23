from __future__ import annotations

import copy
import unittest

from tooling.release.candidate import create_candidate
from tooling.staging.e1 import evaluate_e1


def bundle():
    candidate = create_candidate(
        client_id="demo",
        source_revision="abcdef1234567890",
        artifact_paths=[],
        created_by="ci",
    )
    cid = candidate["candidate_id"]
    manifest = {
        "manifest_id": "STGMAN-demo-abcdef123456",
        "client_id": "demo",
        "candidate_id": cid,
        "candidate_digest": candidate["artifact_digest"],
        "source_revision": candidate["source_revision"],
        "runtimes": [
            {"id":"commerce","provider":"medusa","version":"2.21.1","required":True,"healthcheck":"/health"},
            {"id":"erp","provider":"tryton","version":"8.0","required":True,"healthcheck":"/"},
        ],
        "data_imports": [
            {"id":"commerce-seed","target":"medusa","required":True,"readback":"orders"},
            {"id":"erp-opening","target":"tryton","required":True,"readback":"payables"},
        ],
        "e2e_flows": ["order-to-erp"],
        "provider_checks": ["razorpay","shiprocket","meta-whatsapp-cloud"],
        "status": "validated",
    }
    runtime = {
        "candidate_id": cid,
        "runtimes": [
            {"id":"commerce","status":"pass"},
            {"id":"erp","status":"pass"},
        ],
    }
    imports = {
        "candidate_id": cid,
        "imports": [
            {"id":"commerce-seed","status":"pass","readback_status":"pass"},
            {"id":"erp-opening","status":"pass","readback_status":"pass"},
        ],
    }
    e2e = {
        "candidate_id": cid,
        "flows":[{"id":"order-to-erp","status":"pass"}],
    }
    providers = {
        "evidence_id": f"PROVSTG-{cid}",
        "candidate_id": cid,
        "providers":[
            {"id":"razorpay","mode":"sandbox","credential_ref":"env:RAZORPAY","status":"pass","evidence":"sandbox health"},
            {"id":"shiprocket","mode":"sandbox","credential_ref":"env:SHIPROCKET","status":"pass","evidence":"sandbox health"},
            {"id":"meta-whatsapp-cloud","mode":"staging","credential_ref":"env:WHATSAPP","status":"pass","evidence":"staging health"},
        ],
        "status":"passed",
    }
    observability = {
        "evidence_id": f"OBS-{cid}",
        "candidate_id": cid,
        "signals":[
            {"kind":"metric","name":"http.latency","status":"pass","evidence":"metric"},
            {"kind":"trace","name":"order.to.erp","status":"pass","evidence":"trace"},
            {"kind":"error","name":"integration.failure.visibility","status":"pass","evidence":"error path"},
            {"kind":"alert","name":"provider.unreachable","status":"pass","evidence":"alert"},
        ],
        "status":"passed",
    }
    return candidate, manifest, runtime, imports, e2e, providers, observability


class PhaseE1Tests(unittest.TestCase):
    def test_complete_e1_bundle_passes(self):
        result = evaluate_e1(
            candidate=bundle()[0], manifest=bundle()[1], runtime_evidence=bundle()[2],
            import_evidence=bundle()[3], e2e_evidence=bundle()[4],
            provider_evidence=bundle()[5], observability=bundle()[6],
        )
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["staging_validation"]["status"], "passed")

    def test_candidate_digest_mismatch_blocks(self):
        values = list(bundle())
        values[1] = copy.deepcopy(values[1])
        values[1]["candidate_digest"] = "wrong"
        result = evaluate_e1(
            candidate=values[0], manifest=values[1], runtime_evidence=values[2],
            import_evidence=values[3], e2e_evidence=values[4],
            provider_evidence=values[5], observability=values[6],
        )
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("digest mismatch" in item for item in result["blocking_items"]))

    def test_missing_runtime_blocks(self):
        values = list(bundle())
        values[2] = copy.deepcopy(values[2])
        values[2]["runtimes"] = [{"id":"commerce","status":"pass"}]
        result = evaluate_e1(
            candidate=values[0], manifest=values[1], runtime_evidence=values[2],
            import_evidence=values[3], e2e_evidence=values[4],
            provider_evidence=values[5], observability=values[6],
        )
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("erp" in item for item in result["blocking_items"]))

    def test_missing_provider_credentials_evidence_blocks(self):
        values = list(bundle())
        values[5] = copy.deepcopy(values[5])
        values[5]["providers"][0]["status"] = "not-run"
        values[5]["providers"][0]["evidence"] = "credentials unavailable"
        values[5]["status"] = "blocked"
        result = evaluate_e1(
            candidate=values[0], manifest=values[1], runtime_evidence=values[2],
            import_evidence=values[3], e2e_evidence=values[4],
            provider_evidence=values[5], observability=values[6],
        )
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("razorpay" in item for item in result["blocking_items"]))

    def test_missing_readback_blocks(self):
        values = list(bundle())
        values[3] = copy.deepcopy(values[3])
        values[3]["imports"][0]["readback_status"] = "fail"
        result = evaluate_e1(
            candidate=values[0], manifest=values[1], runtime_evidence=values[2],
            import_evidence=values[3], e2e_evidence=values[4],
            provider_evidence=values[5], observability=values[6],
        )
        self.assertEqual(result["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
