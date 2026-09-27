"""The test ledger must match the published result files."""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/hypotheses/TEST_LEDGER.md"
POWER = {(r["experiment"], r["symbol"]): r for r in json.loads((ROOT / "docs/results/power_analysis.json").read_text())}


def rows():
    return json.loads(re.search(r"```json\n(.*?)```", LEDGER.read_text(encoding="utf-8"), re.S).group(1))["tests"]


def drift_p(hypothesis, symbol):
    for f in ("drift_baseline_v1", "drift_baseline_v1_vol_expansion"):
        res = json.loads((ROOT / f"docs/results/{f}.json").read_text())["results"]
        if hypothesis in res:
            return res[hypothesis][symbol]["pooled"]["test"]["p_value"]
    return None


def test_ledger_is_complete_and_unique():
    ids = [r["id"] for r in rows()]
    assert len(ids) == len(set(ids)) == 17
    assert "## Tests run (17 primary tests; 0 qualified)" in LEDGER.read_text(encoding="utf-8")
    assert sum(r["qualified"] for r in rows()) == 0


@pytest.mark.parametrize("row", [r for r in rows() if r["result_file"].startswith("docs/results/walkforward_")], ids=lambda r: r["id"])
def test_walkforward_rows_match_results(row):
    sym = row["universe"][0]
    res = json.loads((ROOT / row["result_file"]).read_text())
    assert res["symbols"][sym]["qualified"] is row["qualified"]
    assert len(res["grid"]) == row["grid"]
    pw = POWER[(row["hypothesis"], sym)]
    assert row["forced_trades"] == pw["trades"] == res["symbols"][sym]["stability"]["forced"]["pooled_test"]["trades"]
    assert row["forced_net_bps"] == pytest.approx(pw["observed_bps"], abs=0.005)
    assert row["forced_t_day"] == pytest.approx(pw["observed_bps"] / pw["se_day"], abs=0.005)
    assert row["design_mde_bps"] == pytest.approx(pw["design_mde"], abs=0.05)
    p = drift_p(row["hypothesis"], sym)
    assert (row["drift_p"] is None and p is None) or row["drift_p"] == pytest.approx(p, abs=0.0005)


def test_replication_row_matches_results():
    (row,) = [r for r in rows() if r["id"].startswith("replication_r1")]
    res = json.loads((ROOT / row["result_file"]).read_text())
    c = res["clustered"]["forced"]
    assert res["replicated"] is row["qualified"] and c["trades"] == row["forced_trades"]
    assert row["forced_net_bps"] == pytest.approx(c["mean_bps"], abs=0.005)
    assert row["forced_t_day"] == pytest.approx(c["clustered_t"], abs=0.005)
    assert row["drift_p"] == pytest.approx(res["drift"]["test"]["pooled"]["p_value"], abs=0.0005)
    assert row["design_mde_bps"] == pytest.approx(POWER[("replication_r1_pooled", "ETH+LTC+XRP")]["design_mde"], abs=0.05)


def test_fx_session_row_matches_results():
    (row,) = [r for r in rows() if r["id"].startswith("fx_session")]
    res = json.loads((ROOT / row["result_file"]).read_text())
    c = res["clustered"]["forced"]
    assert res["qualified"] is row["qualified"] and c["trades"] == row["forced_trades"]
    assert row["forced_net_bps"] == pytest.approx(c["mean_bps"], abs=0.005)
    assert row["forced_t_day"] == pytest.approx(c["clustered_t"], abs=0.005)
    assert row["drift_p"] == pytest.approx(res["drift"]["test"]["pooled"]["p_value"], abs=0.0005)
    assert row["design_mde_bps"] == pytest.approx(res["resolution"]["forced"], abs=0.005)
    assert len(res["grid"]) == row["grid"]
