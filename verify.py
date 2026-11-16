import json, sqlite3
from bootstrap import ensure_data
ensure_data()
from poc import DATA,OUT,discover
with sqlite3.connect(DATA/'semiconductor.sqlite') as c:
    assert c.execute('SELECT * FROM quality_summary').fetchone()==(1567,104,104/1567)
    assert c.execute('SELECT COUNT(*) FROM ml_quality_dataset').fetchone()[0]==1567
    assert c.execute('SELECT COUNT(*) FROM test_outcomes WHERE is_fail != (test_label=1)').fetchone()[0]==0
assert discover('Find sensor signals for failure prediction')[0]['asset_id']=='process_features'
h=json.loads((OUT/'ml_handoff.json').read_text(encoding="utf-8"))
assert not set(h['exclude'])&set(h['features'])
assert all(v.startswith('sensor_') for v in h['features'])
(OUT/'verification.json').write_text(json.dumps({'data_integrity':'passed','label_mapping':'passed','join_cardinality':'passed','target_exclusion':'passed'},indent=2))
print('Data, discovery, and leakage checks passed.')
