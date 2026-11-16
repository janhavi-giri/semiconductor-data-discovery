"""Real SECOM -> contextual catalog -> discovery -> reproducible ML handoff."""
from pathlib import Path
import argparse, hashlib, json, sqlite3, zipfile
from datetime import datetime
import urllib.request
import pandas as pd
from bootstrap import ensure_data

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
OUT = ROOT / 'outputs'
SOURCE = 'https://archive.ics.uci.edu/static/public/179/secom.zip'

def build():
    (DATA / 'raw').mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)
    archive = DATA / 'raw/secom.zip'
    if not archive.exists():
        urllib.request.urlretrieve(SOURCE, archive)
    with zipfile.ZipFile(archive) as z:
        x = pd.read_csv(z.open('secom.data'), sep=r'\s+', header=None)
        labels = [s.split(maxsplit=1) for s in z.read('secom_labels.data').decode().splitlines()]
    assert len(x) == len(labels) == 1567
    # UCI description says 591; downloaded measurement matrix contains 590 columns.
    x.columns = [f'sensor_{i:03}' for i in range(x.shape[1])]
    ids = [f'SECOM-{i+1:04}' for i in range(len(x))]
    runs = pd.DataFrame({'sample_id':ids, 'observed_at':[datetime.strptime(v[1].strip(chr(34)), '%d/%m/%Y %H:%M:%S').isoformat() for v in labels], 'dataset_id':'secom'})
    outcomes = pd.DataFrame({'sample_id':ids, 'test_label':[int(v[0]) for v in labels]})
    outcomes['is_fail'] = (outcomes.test_label == 1).astype(int)
    features = x.copy()
    features.insert(0, 'sample_id', ids)
    profiles = pd.DataFrame([{'feature_id':c,'meaning':'Anonymized semiconductor process measurement', 'unit':'unknown', 'process_step':'unknown','missing_fraction':float(x[c].isna().mean()),'unique_non_null':int(x[c].nunique()),'eligible':int(x[c].nunique()>1 and x[c].isna().mean()<=.5),'provenance':'computed profile; physical meaning unavailable'} for c in x])
    assets = pd.DataFrame([
        {'asset_id':'process_features','physical_table':'process_features','context':'Semiconductor manufacturing process measurements sensor signals features for quality classification failure prediction anomaly detection','grain':'one anonymized sample per row','role':'features','join_key':'sample_id','label_available':1,'limitations':'sensor identities units tool chamber wafer lot recipe unavailable'},
        {'asset_id':'test_outcomes','physical_table':'test_outcomes','context':'Semiconductor manufacturing quality test pass fail outcome target label failure classification','grain':'one anonymized sample per row','role':'target','join_key':'sample_id','label_available':1,'limitations':'test result is an outcome; exclude from prediction features'},
        {'asset_id':'samples','physical_table':'samples','context':'Semiconductor sample observation timestamps chronology temporal validation split provenance','grain':'one anonymized sample per row','role':'index','join_key':'sample_id','label_available':1,'limitations':'sample_id generated from original row order; not a real wafer identifier'}])
    db = DATA / 'semiconductor.sqlite'
    db.unlink(missing_ok=True)
    with sqlite3.connect(db) as c:
        for name,frame in [('samples',runs),('process_features',features),('test_outcomes',outcomes),('feature_metadata',profiles),('asset_catalog',assets)]:
            frame.to_sql(name,c,index=False)
        for name in ['samples','process_features','test_outcomes']:
            c.execute(f'CREATE UNIQUE INDEX {name}_pk ON {name}(sample_id)')
        c.executescript('''CREATE VIEW ml_quality_dataset AS SELECT s.observed_at, f.*, t.is_fail FROM samples s JOIN process_features f USING(sample_id) JOIN test_outcomes t USING(sample_id);
        CREATE VIEW quality_summary AS SELECT COUNT(*) AS sample_count, SUM(is_fail) AS fail_count, AVG(is_fail) AS failure_fraction FROM test_outcomes;''')
    manifest = {'source':SOURCE,'citation':'McCann, M. & Johnston, A. (2008). SECOM. UCI. doi:10.24432/C54305','license':'CC BY 4.0','archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'samples':len(x),'measurement_columns_observed':x.shape[1],'fail_count':int(outcomes.is_fail.sum()),'missing_values':int(x.isna().sum().sum()),'identity':'generated sample_id from row order; labels aligned by source row','unknown':['physical sensor names','units','tool','chamber','wafer_id','lot','recipe','process step'],'note':'UCI prose reports 591 features; actual source matrix parsed here has 590. No feature invented.'}
    (OUT/'provenance.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))

def discover(question, enriched=True):
    """Transparent keyword/synonym baseline."""
    aliases={'yield':'quality','excursion':'failure','fault':'failure','defect':'failure','predict':'prediction','signals':'sensor','chronological':'temporal'}
    words=set(question.lower().strip('?.').split())
    words |= {v for k,v in aliases.items() if k in words}
    with sqlite3.connect(DATA/'semiconductor.sqlite') as c:
        rows=pd.read_sql_query('SELECT * FROM asset_catalog',c).to_dict('records')
    results=[]
    for r in rows:
        text=r['physical_table'] + (' '+r['context'] if enriched else '')
        score=len(words & set(text.lower().replace('_',' ').split()))
        if score:
            results.append({**r,'matched_terms':sorted(words & set(text.lower().replace('_',' ').split())),'score':score})
    return sorted(results,key=lambda r:(-r['score'],r['asset_id']))

def demo():
    cases=[('Find sensor signals for failure prediction','process_features'),('Find quality outcome labels','test_outcomes'),('Find chronology for temporal validation','samples')]
    results=[]
    for q,want in cases:
        raw=discover(q,False); contextual=discover(q)
        results.append({'question':q,'expected':want,'raw_top1':raw[0]['asset_id'] if raw else None,'context_top1':contextual[0]['asset_id'] if contextual else None,'evidence':contextual})
    report={'method':'Three hand-authored smoke questions, lexical ranking with curated synonyms. Not a general retrieval benchmark.','cases':results,'raw_top1_hits':sum(r['raw_top1']==r['expected'] for r in results),'context_top1_hits':sum(r['context_top1']==r['expected'] for r in results),'unsupported_question':{'question':'Which etch chamber caused failure?','answer':'Not answerable: tool, chamber and process-step identities are unavailable; no causal claim supported.'}}
    (OUT/'discovery_comparison.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

def _evaluate(f, s, purpose, provenance):
    """Chronological holdout. `f` is indexed by sample_id; `s` has sample_id, observed_at, is_fail."""
    from sklearn.impute import SimpleImputer
    from sklearn.feature_selection import VarianceThreshold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, balanced_accuracy_score, roc_auc_score
    s=s.sort_values(['observed_at','sample_id']).reset_index(drop=True)
    # Keep identical timestamp groups together at the temporal boundary.
    boundary=s.observed_at.iloc[int(.8*len(s))]
    tr=s[s.observed_at<boundary]; te=s[s.observed_at>=boundary]
    a=f.loc[tr.sample_id]; b=f.loc[te.sample_id]
    # Fit feature selection and all preprocessing on training data only.
    keep=a.columns[(a.isna().mean()<=.5)&(a.nunique()>1)]
    model=make_pipeline(SimpleImputer(strategy='median'),VarianceThreshold(),StandardScaler(),LogisticRegression(class_weight='balanced',max_iter=2000,random_state=7))
    model.fit(a[keep],tr.is_fail)
    p=model.predict_proba(b[keep])[:,1]
    r={'purpose':purpose,'input_provenance':provenance,'split':'80% approximate chronological cut, timestamp groups kept together','train_rows':len(tr),'test_rows':len(te),'train_failures':int(tr.is_fail.sum()),'test_failures':int(te.is_fail.sum()),'feature_count':len(keep),'average_precision':average_precision_score(te.is_fail,p),'roc_auc':roc_auc_score(te.is_fail,p),'balanced_accuracy_at_0_5':balanced_accuracy_score(te.is_fail,p>=.5),'test_failure_prevalence':float(te.is_fail.mean()),'limitations':'small imbalanced historical dataset; temporal proxy only; unknown measurement availability at decision time'}
    return r, list(keep)

def train():
    # A consuming application resolves assets then executes an explicit, reviewed join.
    assert discover('Find sensor signals for failure prediction')[0]['asset_id']=='process_features'
    with sqlite3.connect(DATA/'semiconductor.sqlite') as c:
        f=pd.read_sql_query('SELECT * FROM process_features',c).set_index('sample_id')
        s=pd.read_sql_query('SELECT s.sample_id,s.observed_at,t.is_fail FROM samples s JOIN test_outcomes t USING(sample_id) ORDER BY observed_at,s.sample_id',c)
    r,keep=_evaluate(f,s,'Discovery-to-ML handoff baseline; no production or causal claim','local SQLite catalog (data/semiconductor.sqlite)')
    (OUT/'ml_result.json').write_text(json.dumps(r,indent=2))
    (OUT/'ml_handoff.json').write_text(json.dumps({'feature_asset':'process_features','label_asset':'test_outcomes','index_asset':'samples','join':'sample_id','target':'is_fail','exclude':['sample_id','observed_at','test_label','is_fail'],'features':keep,'provenance':'provenance.json'},indent=2))
    print(json.dumps(r,indent=2))

def secom_contract():
    """Discovery handoff selecting the three real SECOM assets needed for the baseline."""
    from discovery import handoff
    return handoff('',{'source':'SECOM (real)'},['SECOM-process_features','SECOM-test_outcomes','SECOM-samples'])

def train_from_contract(contract=None):
    """Train from a discovery handoff contract instead of the original SQLite catalog.

    Checksums are verified and path escapes rejected by consume_handoff.consume();
    mixed real/synthetic cohorts are refused. Files are then resolved by role.
    """
    from consume_handoff import consume
    contract=contract or secom_contract()
    consume(contract)
    by_role={a['role']:a for a in contract['assets']}
    missing={'features','target','index'}-set(by_role)
    if missing:raise ValueError('Contract lacks required roles: '+', '.join(sorted(missing)))
    load=lambda role:pd.read_csv(ROOT/by_role[role]['relative_uri'])
    features,target,index=load('features'),load('target'),load('index')
    s=index[['sample_id','observed_at']].merge(target[['sample_id','is_fail']],on='sample_id',validate='one_to_one')
    f=features.set_index('sample_id')
    # Outcomes and identifiers are not predictors: only sensor channels enter the model.
    f=f[[c for c in f.columns if c.startswith('sensor_')]]
    r,keep=_evaluate(f,s,'Baseline trained from a verified discovery handoff contract; no production or causal claim','discovery handoff: '+', '.join(a['asset_id']+' sha256='+a['sha256'][:12] for a in contract['assets']))
    (OUT/'ml_result_from_handoff.json').write_text(json.dumps(r,indent=2))
    print(json.dumps(r,indent=2))
    return r

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['build','demo','train','train-from-handoff','search']); parser.add_argument('question',nargs='?',default='Find sensor signals for failure prediction'); args=parser.parse_args()
    if args.action!='build': ensure_data()
    if args.action=='search': print(json.dumps(discover(args.question),indent=2))
    elif args.action=='train-from-handoff': train_from_contract()
    else: globals()[args.action]()
