"""Build reproducible sidecar manifests. No LLM, credentials or private data."""
from pathlib import Path
import csv, hashlib, json, math, random, sqlite3
ROOT=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_csv(path,fields,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(fields);w.writerows(rows)

def build():
    rows=[]
    real=ROOT/'data/real';real.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(ROOT/'data/semiconductor.sqlite') as c:
        for i,(table,description,concept,role) in enumerate([
            ('process_features','Real semiconductor manufacturing measurements for quality classification and failure prediction. Anonymized sensor channels, units unknown.','process_measurement','features'),
            ('test_outcomes','Real semiconductor manufacturing quality outcome labels. -1 pass +1 fail; is_fail 0 pass 1 fail. Exclude from predictors.','quality_outcome','target'),
            ('samples','Real anonymized semiconductor sample observation timestamps for chronological temporal validation. Generated sample ID is not a wafer ID.','temporal_validation','index'),
            ('feature_metadata','Real measurement quality profiles: missing fraction and constant channels. Screening for anomaly detection and ML preparation. Physical sensor names unknown.','process_measurement','profile')]):
            path=real/f'r{i+1:04}.csv'
            cur=c.execute('SELECT * FROM '+table)
            values=cur.fetchall();write_csv(path,[d[0] for d in cur.description],values)
            rows.append({'asset_id':f'SECOM-{table}','path':path.relative_to(ROOT).as_posix(),'source':'SECOM (real)','synthetic':False,'description':description,'concept':concept,'role':role,'grain':'one feature/channel per row' if role=='profile' else 'one anonymized sample per row','join_key':'feature_id' if role=='profile' else 'sample_id','row_count':len(values),'missing_fraction':None,'process_step':None,'tool_id':None,'chamber_id':None,'recipe_revision':None,'lot_id':None,'wafer_id':None,'test_outcome':None,'units':'unknown','limitations':['Physical sensor identity and units unavailable','Wafer, lot, tool, chamber, recipe and process-step IDs unavailable','Failure fraction refers to sample-level test outcomes'],'provenance':{'kind':'real_public_data','source':'https://doi.org/10.24432/C54305','license':'CC BY 4.0','transformation':'CSV export from normalized SECOM source; row-order aligned sample IDs'},'sha256':sha(path)})
    rng=random.Random(42)
    folder=ROOT/'data/synthetic';folder.mkdir(parents=True,exist_ok=True)
    for i in range(48):
        step='etch' if i%2==0 else 'deposition'
        chamber='C2' if i%4<2 else 'C1'
        wafer=f'DEMO-W{i+1:03}';lot=f'DEMO-L{i//16+1:02}'
        fail=i%7==0 or (step=='etch' and chamber=='C2' and i%3==0)
        missing_count=0;series=[]
        for tick in range(60):
            missing=(i%11==0 and tick%9==0)
            missing_count+=int(missing)
            series.append([tick,'' if missing else round(80+4*math.sin(tick/8)+rng.gauss(0,1),3),round(300+rng.gauss(0,2),3)])
        common={'source':'Synthetic fab scenario','synthetic':True,'process_step':step,'tool_id':'DEMO-ETCH-01' if step=='etch' else 'DEMO-CVD-01','chamber_id':chamber,'recipe_revision':'DEMO-RCP-A:r2' if step=='etch' else 'DEMO-RCP-B:r1','lot_id':lot,'wafer_id':wafer,'test_outcome':'fail' if fail else 'pass','join_key':'wafer_id','provenance':{'kind':'synthetic','generator':'build_demo.py; seed=42','license':'MIT','purpose':'Illustrative manufacturing context generated for the demo'},'limitations':['All IDs, outcomes and signals are synthetic','Chamber association is not evidence of causality']}
        path=folder/f'a{2*i+1:04}.csv';write_csv(path,['elapsed_seconds','pressure_pa','temperature_c'],series)
        rows.append({**common,'asset_id':f'TRACE-{wafer}','path':path.relative_to(ROOT).as_posix(),'description':f'Synthetic semiconductor {step} sensor trace process measurement for wafer {wafer} lot {lot}, chamber {chamber}, with linked quality outcome {"fail" if fail else "pass"}. Used to demonstrate discovery for anomaly detection and failure investigation.','concept':'process_measurement','role':'features','grain':'one second per row; file is one wafer process run','row_count':60,'missing_fraction':missing_count/180,'units':'elapsed_seconds=s; pressure_pa=Pa; temperature_c=degC','sha256':sha(path)})
        path=folder/f'a{2*i+2:04}.csv';write_csv(path,['wafer_id','is_fail'],[[wafer,int(fail)]])
        rows.append({**common,'asset_id':f'TEST-{wafer}','path':path.relative_to(ROOT).as_posix(),'description':f'Synthetic semiconductor quality test outcome for wafer {wafer}, lot {lot}. Pass fail label; target only, never a predictor.','concept':'quality_outcome','role':'target','grain':'one wafer-level synthetic test per file','row_count':1,'missing_fraction':0,'units':'is_fail=boolean','sha256':sha(path)})
    metadata=ROOT/'data/metadata';metadata.mkdir(parents=True,exist_ok=True)
    for row in rows:
        (metadata/(row['asset_id']+'.json')).write_text(json.dumps(row,indent=2))
    (ROOT/'data/catalog.json').write_text(json.dumps(rows,indent=2))
    print(f'Built {len(rows)} assets: 4 real SECOM exports + 96 synthetic trace/test files.')
if __name__=='__main__':build()
