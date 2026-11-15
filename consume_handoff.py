"""Example downstream consumer: verify selected assets and form a trace cohort.
This does not execute arbitrary SQL or train on synthetic data.
"""
import argparse,csv,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def consume(contract):
    populations={a['synthetic'] for a in contract['assets']}
    if len(populations)>1:raise ValueError('Do not combine synthetic and real populations')
    summaries=[]
    for a in contract['assets']:
        path=(ROOT/a['relative_uri']).resolve()
        if not path.is_relative_to(ROOT):raise ValueError('Asset path escapes repository')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=a['sha256']:raise ValueError('Checksum mismatch: '+a['asset_id'])
        with path.open(newline='') as f:
            reader=csv.DictReader(f);rows=list(reader);columns=reader.fieldnames
        summaries.append({'asset_id':a['asset_id'],'role':a['role'],'rows_loaded':len(rows),'columns':columns,'join_key':a['join_key'],'checksum_verified':True,'source':a['source']})
    return {'loaded':summaries,'next_step':'Use the documented role and join key; validate feature availability at the prediction time. Keep target values out of predictors.'}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('contract');args=p.parse_args()
    print(json.dumps(consume(json.loads(Path(args.contract).read_text(encoding="utf-8"))),indent=2))
