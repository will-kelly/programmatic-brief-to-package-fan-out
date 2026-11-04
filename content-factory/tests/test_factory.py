"""Offline end-to-end tests. Every model call goes to factory/fake_llm.py,
which plants the errors the pipeline is supposed to catch."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent


class Factory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.env = {**os.environ, "CF_LLM": "fake", "CF_STATE": str(cls.tmp / "state"),
                   "PYTHONPATH": str(HERE), "CF_BASELINE": str(cls.tmp / "baseline.json")}
        cls.cf("docs", "snapshot", "--from", str(HERE / "fixtures/docs"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    @classmethod
    def cf(cls, *args, ok=(0,)):
        r = subprocess.run([sys.executable, "-m", "factory", *args], cwd=HERE, env=cls.env,
                           capture_output=True, text=True)
        if r.returncode not in ok:
            raise AssertionError(f"cf {' '.join(args)} exited {r.returncode}\n{r.stdout}\n{r.stderr}")
        return r

    def state(self, *p):
        return self.tmp / "state" / Path(*p)

    def test_1_survey_scores_and_flags_wrong_claims(self):
        out = self.cf("survey", "-k", "2", "--only", "q-render-free-tier,q-django-postgres,q-agent-long-running").stdout
        self.assertIn("Wrong about Render", out)
        self.assertIn("F-free-postgres-expiry", out)
        self.assertIn("*(branded)*", out)
        s = json.loads((Path(self.state("surveys/LATEST").read_text().strip()) / "summary.json").read_text())
        q = {x["question_id"]: x for x in s["questions"]}
        self.assertEqual(q["q-agent-long-running"]["mention_rate"], 0)
        self.assertEqual(q["q-django-postgres"]["mention_rate"], 1)
        self.assertEqual(s["unbranded_answers"], 4)

    def test_2_gaps_rank_wrong_first_and_split_by_fix(self):
        self.cf("survey", "-k", "2", "--only", "q-render-free-tier,q-django-postgres,q-agent-long-running")
        out = self.cf("gaps", "--traffic", str(HERE / "fixtures/signals/access.log"),
                      "--citations", str(HERE / "fixtures/signals/citations.csv")).stdout
        b = json.loads(self.state("backlog.json").read_text())
        self.assertEqual(b["items"][0]["kind"], "WRONG")
        kinds = {d["question_id"]: d["kind"] for d in b["diagnosis"]}
        self.assertEqual(kinds["q-agent-long-running"], "ABSENT")
        self.assertIn("severity", out)

    def test_3_brief_run_publish_refresh(self):
        self.cf("survey", "-k", "1", "--only", "q-agent-long-running,q-render-free-tier")
        self.cf("gaps")
        b = json.loads(self.state("backlog.json").read_text())
        n = next(i for i, it in enumerate(b["items"], 1) if it["kind"] == "ABSENT")
        brief = Path(self.cf("brief", str(n)).stdout.strip())
        self.assertIn("```json", brief.read_text())

        r = self.cf("run", str(brief), ok=(0, 1))
        res = json.loads(r.stdout.split("review packet")[0])
        # The fake draft says free services spin down after 30 minutes.
        self.assertEqual(res["status"], "blocked")
        self.assertEqual(res["contradicted"], 1)
        run_dir = Path(r.stdout.split("review packet: ")[1].strip()).parent
        packet = (run_dir / "review-packet.md").read_text()
        self.assertIn("known-wrong pattern for F-free-spindown", packet)
        self.assertIn("spins down after 15 minutes", packet)

        self.cf("publish", str(run_dir), ok=(1,))           # blocked runs don't publish
        page = Path(self.cf("publish", str(run_dir), "--force").stdout.strip())
        self.assertNotIn("[C1]", page.read_text())
        cat = json.loads(self.state("catalog.json").read_text())
        self.assertTrue(all(c["source_sha"] for p in cat["pages"].values() for c in p["claims"]))

        # No docs change: nothing to refresh.
        self.assertIn("Nothing to do", self.cf("refresh").stdout)

        # The docs change one section: only claims citing it get flagged.
        docs2 = self.tmp / "docs2"
        shutil.copytree(HERE / "fixtures/docs", docs2)
        f = docs2 / "service-types.md"
        f.write_text(f.read_text().replace("cron jobs run a command", "cron jobs run a command on a schedule you set in UTC, and"))
        self.cf("docs", "snapshot", "--from", str(docs2), "--fixture")
        out = self.cf("refresh").stdout
        q = json.loads(self.state("refresh-queue.json").read_text())
        flagged = {f["id"] for p in q["pages"] for f in p["flagged"]}
        self.assertEqual(flagged, {"C1", "C2", "C3"})      # the claims citing service-types#overview
        self.assertIn("service-types#overview", out)

    def test_4_partner_draft_without_ledger(self):
        r = self.cf("check", str(HERE / "fixtures/partner/heroku-alternatives-draft.md"), "--partner", "acme", ok=(1,))
        res = json.loads(r.stdout.split("review packet")[0])
        self.assertEqual(res["status"], "blocked")
        self.assertGreaterEqual(res["contradicted"], 1)      # "free tier that includes background workers"
        self.assertGreaterEqual(res["lint_errors"], 3)       # robust, preamble opener, no concede section
        self.assertIn("acme", self.cf("metrics").stdout)

    def test_5_evals_and_escaped_errors_grow_the_suite(self):
        out = self.cf("eval", "--save-baseline").stdout
        self.assertIn("lint        1.0        1.0", out)
        self.assertIn("brands      1.0        1.0", out)
        self.assertIn("subtle-negation.md: factcheck missed C2", out)   # needs a real model judge
        self.assertIn("fake:judge", (self.tmp / "baseline.json").read_text())
        self.assertIn("no regression", self.cf("eval").stdout)

        run_dir = self.tmp / "state" / "checks" / "x" / "r1"
        run_dir.mkdir(parents=True)
        (run_dir / "draft.md").write_text("---\ntitle: t\n---\n\n# t\n")
        (run_dir / "result.json").write_text('{"estimated_minutes": 5}')
        out = self.cf("review", "done", str(run_dir), "--minutes", "7", "--escaped", "C9").stdout
        case = Path(out.split("eval case added: ")[1].split("\n")[0])
        try:
            self.assertIn("expect_flagged: C9", case.read_text())
            self.assertIn("actual expert review: 7.0", self.cf("metrics").stdout)
        finally:
            case.unlink()

    def test_6_brand_detection_ignores_the_verb(self):
        sys.path.insert(0, str(HERE))
        from factory.brands import Brands
        b = Brands()
        self.assertEqual([m["brand"] for m in b.mentions("React will render the page, then re-render it.")], [])
        self.assertEqual([m["brand"] for m in b.mentions("Use Render, not Heroku.")], ["Render", "Heroku"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
