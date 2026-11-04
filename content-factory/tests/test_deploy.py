"""Tests for the production path: the Messages API backend, the database
state store, and the Render Workflows binding. Offline: the API client is
stubbed, the database is SQLite unless CF_TEST_PG_URL points at Postgres,
and render_sdk is replaced with a stand-in."""

import asyncio
import importlib
import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))


class TmpState(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.state = self.tmp / "state"
        os.environ["CF_STATE"] = str(self.state)
        os.environ["CF_LLM"] = "fake"
        import factory.common as common
        common.STATE = self.state
        import factory
        for m in list(sys.modules):
            if m.startswith("factory.") and m != "factory.common":
                del sys.modules[m]
                if hasattr(factory, m.split(".", 1)[1]):
                    delattr(factory, m.split(".", 1)[1])
        self.url = os.environ.get("CF_TEST_PG_URL") or f"sqlite:///{self.tmp / 'state.db'}"
        if self.url.startswith("postgres"):
            import psycopg
            with psycopg.connect(self.url) as c:
                c.execute("DROP TABLE IF EXISTS cf_files; DROP TABLE IF EXISTS cf_lines")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class Store(TmpState):
    def test_round_trip_parallel_appends_and_rewrites(self):
        from factory import store
        a, b = self.tmp / "a", self.tmp / "b"
        a.mkdir()
        (a / "catalog.json").write_text('{"pages": {}}')
        (a / "checks.jsonl").write_text('{"n": 1}\n')
        store.push(self.url, a)

        # Two tasks start from the same state and append in parallel.
        store.pull(self.url, b)
        with (a / "checks.jsonl").open("a") as f:
            f.write('{"n": 2}\n')
        with (b / "checks.jsonl").open("a") as f:
            f.write('{"n": 3}\n')
        self.assertEqual(store.push(self.url, a)["lines"], 1)
        self.assertEqual(store.push(self.url, b)["lines"], 1)

        c = self.tmp / "c"
        store.pull(self.url, c)
        rows = sorted(json.loads(l)["n"] for l in (c / "checks.jsonl").read_text().splitlines())
        self.assertEqual(rows, [1, 2, 3])
        self.assertEqual((c / "catalog.json").read_text(), '{"pages": {}}')

        # Unchanged files aren't re-sent; a rewritten log replaces the old one.
        self.assertEqual(store.push(self.url, c), {"files": 0, "lines": 0})
        (c / "checks.jsonl").write_text('{"n": 9}\n')
        store.push(self.url, c)
        d = self.tmp / "d"
        store.pull(self.url, d)
        self.assertEqual((d / "checks.jsonl").read_text(), '{"n": 9}\n')


class AnthropicBackend(TmpState):
    def test_request_shape_cost_and_refusal(self):
        os.environ["CF_LLM"] = "anthropic"
        from factory import llm
        sent = {}

        def create(**kw):
            sent.update(kw)
            return NS(stop_reason="end_turn", stop_details=None, model="claude-opus-5-5",
                      content=[NS(type="thinking", thinking=""), NS(type="text", text="ok")],
                      usage=NS(input_tokens=1000, output_tokens=500, cache_read_input_tokens=0,
                               cache_creation_input_tokens=0))

        client = NS(with_options=lambda **_: NS(beta=NS(messages=NS(create=create))))
        llm._client = client
        r = llm.ask("q", "sys", role="draft")
        self.assertEqual(r.text, "ok")
        self.assertAlmostEqual(r.cost_usd, (1000 * 4 + 500 * 20) / 1e6)
        self.assertEqual(sent["model"], "claude-opus-5-5")
        self.assertEqual(sent["output_config"], {"effort": "high"})
        self.assertEqual(sent["thinking"], {"type": "adaptive"})
        self.assertEqual(sent["fallbacks"], "default")
        self.assertIn("server-side-fallback-2026-07-01", sent["betas"])
        log = (self.state / "llm-calls.jsonl").read_text()
        self.assertIn('"backend": "anthropic"', log)

        def refuse(**kw):
            return NS(stop_reason="refusal", stop_details=NS(category="cyber"), model="claude-opus-5-5",
                      content=[], usage=NS(input_tokens=1, output_tokens=0))
        llm._client = NS(with_options=lambda **_: NS(beta=NS(messages=NS(create=refuse))))
        with self.assertRaises(llm.Refused):
            llm.ask("q", "sys", role="claim-judge")
        llm._client = None


class WorkflowsBinding(TmpState):
    def test_weekly_cycle_survives_fresh_compute(self):
        os.environ["CF_STATE_URL"] = self.url
        os.environ["CF_DOCS_SRC"] = str(HERE / "fixtures" / "docs")
        fake_sdk = types.ModuleType("render_sdk")

        class Workflows:
            def task(self, **_):
                return lambda fn: fn
            def start(self):
                pass
        fake_sdk.Workflows = Workflows
        sys.modules["render_sdk"] = fake_sdk
        from factory import store
        real_pull = store.pull

        def fresh_pull(url, root=None):
            # Every task lands on an empty disk.
            shutil.rmtree(self.state, ignore_errors=True)
            return real_pull(url, self.state)
        store.pull = fresh_pull
        sys.path.insert(0, str(HERE / "workflows"))
        try:
            rw = importlib.import_module("render_workflows")
            out = asyncio.run(rw.weekly_cycle(k=1))
        finally:
            store.pull = real_pull
            sys.modules.pop("render_workflows", None)
            del os.environ["CF_STATE_URL"]
        self.assertGreater(out["backlog"]["items"], 0)

        # A later task on another fresh disk sees everything the cycle wrote.
        shutil.rmtree(self.state)
        real_pull(self.url, self.state)
        from factory.survey import latest_dir
        s = json.loads((latest_dir() / "summary.json").read_text())
        self.assertEqual(s["answers"], 36)            # every cluster merged, k=1
        self.assertTrue((self.state / "backlog.md").exists())
        self.assertTrue((self.state / "docs" / "current.json").exists())
        calls = (self.state / "llm-calls.jsonl").read_text().splitlines()
        self.assertGreaterEqual(len(calls), 36)       # logs from every task kept


if __name__ == "__main__":
    unittest.main(verbosity=2)
