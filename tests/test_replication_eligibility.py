import json
import re
from pathlib import Path

from qfx.research.replication_eligibility import CANDIDATES, FIRST_AT_OR_BEFORE, LAST_AT_OR_AFTER, SPEC_PATH, check, symbol_of

ROOT = Path(__file__).resolve().parents[1]
HEADER = "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\r\n"


def frozen():
    text = (ROOT / SPEC_PATH).read_text(encoding="utf-8")
    return json.loads(re.search(r"```json\n(.*?)```", text, re.S).group(1))


def test_constants_match_frozen_spec():
    spec = frozen()
    assert spec["version"] == 2 and spec["status"] == "frozen"
    assert list(CANDIDATES) == spec["eligibility"]["candidates"]
    assert FIRST_AT_OR_BEFORE.isoformat().replace("+00:00", "Z") == spec["eligibility"]["first_h1_at_or_before"]
    assert LAST_AT_OR_AFTER.isoformat().replace("+00:00", "Z") == spec["eligibility"]["last_h1_at_or_after"]


def test_symbol_of_handles_upload_prefix():
    assert symbol_of(Path("8a2cf904-ETHUSD.m_H1_202101010000_202609270000.csv")) == "ETHUSD.m"
    assert symbol_of(Path("ETHUSD.m_H1_202101010000_202609270000.csv")) == "ETHUSD.m"


def _write(tmp_path, name, start_day, days):
    rows = []
    for d in range(days):
        for h in range(24):
            y, m, dd = start_day
            rows.append(f"{y}.{m:02d}.{dd + d:02d}\t{h:02d}:00:00\t1.0\t1.1\t0.9\t1.05\t10\t0\t5\r\n")
    p = tmp_path / name
    p.write_text(HEADER + "".join(rows), encoding="utf-8")
    return p


def test_late_history_is_ineligible(tmp_path):
    r = check(_write(tmp_path, "SOLUSD.m_H1_x.csv", (2022, 8, 15), 3))
    assert not r.eligible and any("first H1" in x for x in r.reasons)


def test_non_candidate_is_ineligible(tmp_path):
    r = check(_write(tmp_path, "BTCEUR.m_H1_x.csv", (2020, 12, 1), 3))
    assert not r.eligible and "not in the frozen candidate list" in r.reasons
