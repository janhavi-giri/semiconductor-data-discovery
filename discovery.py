"""Explainable metadata discovery. Keyword/synonym ranking, not LLM retrieval."""
from pathlib import Path
import csv, hashlib, json, re
from bootstrap import ensure_data
ROOT=Path(__file__).resolve().parent
FILTERS=('source','process_step','chamber_id','test_outcome','role','lot_id')
STOP={'find','for','the','and','with','from','data','me','which','show','a','of','in','to','can','i','that','are','on','is','an','all','it','what','by'}

def tokens(text):return set(re.findall(r'[a-z0-9]+',str(text).lower()))-STOP

def load():
    ensure_data()
    return json.loads((ROOT/'data/catalog.json').read_text(encoding="utf-8"))

def search(query='',filters=None):
    filters=filters or {}
    unknown=set(filters)-set(FILTERS)-{'max_missing'}
    if unknown:raise ValueError('Unsupported filters: '+str(sorted(unknown)))
    terms=json.loads((ROOT/'ontology.json').read_text(encoding="utf-8"))['terms']
    q=tokens(query);expanded=set(q)
    for concept,term in terms.items():
        synonyms=set().union(*(tokens(v) for v in term['synonyms']))
        if q&synonyms:expanded|=synonyms|tokens(concept)
    # Parse only supported, explicit context. Unsupported physical context is not guessed.
    step=next((v for v in ('etch','deposition') if v in expanded),None)
    chamber=re.search(r'\b(c[12])\b',query,re.I)
    inferred={}
    if step:inferred['process_step']=step
    if chamber:inferred['chamber_id']=chamber.group(1).upper()
    if q&{'failed','fail','failures'}:inferred['test_outcome']='fail'
    if q&{'trace','traces','signals','sensor'}:inferred['role']='features'
    effective={**inferred,**{k:v for k,v in filters.items() if v not in ('',None)}}
    raw=[];enriched=[];filter_only=[];filename_filtered=[]
    for asset in load():
        name=Path(asset['path']).name
        lexical=sorted(q&tokens(name))
        # Baseline is filename-only, has no semantic filters.
        if lexical:raw.append({'asset_id':asset['asset_id'],'path':asset['path'],'score':len(lexical),'matched_terms':lexical})
        passes=not any(str(asset.get(k))!=str(v) for k,v in effective.items() if k in FILTERS)
        if passes and 'max_missing' in effective and (asset['missing_fraction'] is None or asset['missing_fraction']>float(effective['max_missing'])):passes=False
        if passes:
            filter_only.append(asset['asset_id'])
            if lexical:filename_filtered.append(asset['asset_id'])
        if not passes:continue
        context=' '.join(str(asset.get(k) or '') for k in ('description','concept','role','process_step','chamber_id','recipe_revision','lot_id','wafer_id','test_outcome','units'))
        matched=sorted(expanded&tokens(context)); score=len(matched)
        if q and not score:continue
        enriched.append({**asset,'score':score,'matched_terms':matched,'match_explanation':{'query_terms':sorted(q),'expanded_terms':sorted(expanded-q),'filters_satisfied':effective}})
    enriched.sort(key=lambda r:(-r['score'],r['asset_id']))
    warnings=[]
    if any(w in q for w in ('cause','caused','causal','root')):warnings.append('Discovery identifies associated data; it cannot establish root cause. No causal model is implemented.')
    if any(w in q for w in ('nand','dram')):warnings.append('The dataset and synthetic scenario lack verified NAND or DRAM product identifiers.')
    if filters.get('source')=='SECOM (real)' and (step or chamber or any(filters.get(k) for k in ('process_step','chamber_id','lot_id'))):warnings.append('SECOM does not provide process-step, chamber or lot identities. No real asset satisfies that context.')
    if not enriched:warnings.append('No assets satisfy this query and its known context. Relax filters or supply authoritative metadata; do not invent missing identities.')
    return {'query':query,'method':'deterministic keyword and ontology-synonym ranking','inferred_filters':inferred,'effective_filters':effective,'raw_results':raw,'results':enriched,'warnings':warnings,'ablations':{'filename_only':len(raw),'filename_plus_same_metadata_filters':len(filename_filtered),'metadata_filters_only_no_text':len(filter_only),'metadata_ranked':len(enriched)},'comparison_note':'The filename-only baseline has no metadata filters, so it cannot be an unbiased benchmark. The ablations separate the effect of the metadata itself (filters applied to filenames, or filters alone) from keyword and synonym ranking. This is a mechanism demonstration, not an independent retrieval benchmark.'}

def asset_detail(asset_id):
    all_assets=load()
    asset=next((a for a in all_assets if a['asset_id']==asset_id),None)
    if not asset:raise KeyError(asset_id)
    related=[{'asset_id':a['asset_id'],'path':a['path'],'role':a['role'],'relationship':'same synthetic wafer_id' if asset['synthetic'] else 'same SECOM source; see join_key'} for a in all_assets if a['asset_id']!=asset_id and ((asset['synthetic'] and a['wafer_id']==asset['wafer_id']) or (not asset['synthetic'] and not a['synthetic']))]
    path=ROOT/asset['path']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=asset['sha256']:raise ValueError('Asset checksum differs from catalog; rebuild metadata before use')
    with path.open(newline='') as f:
        reader=csv.DictReader(f); fields=reader.fieldnames
        preview=[row for _,row in zip(range(6),reader)]
    return {**asset,'related_assets':related,'columns':fields,'preview':preview,'verified_sha256':True}

def handoff(query='',filters=None,asset_ids=None):
    found=search(query,filters)
    selected=found['results']
    if asset_ids is not None:
        requested=set(asset_ids);selected=[a for a in selected if a['asset_id'] in requested]
        if requested!={a['asset_id'] for a in selected}:raise ValueError('Selected assets are absent from discovery results')
    if not selected:raise ValueError('No matching assets to hand off')
    details=[asset_detail(a['asset_id']) for a in selected]
    return {'contract_version':'1.0','query':query,'filters':found['effective_filters'],'retrieval_method':found['method'],'assets':[{'asset_id':a['asset_id'],'relative_uri':a['path'],'sha256':a['sha256'],'source':a['source'],'synthetic':a['synthetic'],'role':a['role'],'grain':a['grain'],'join_key':a['join_key'],'units':a['units'],'related_assets':a['related_assets'],'limitations':a['limitations'],'provenance':a['provenance']} for a in details],'consumer_rules':['Resolve relative_uri against repository root; verify SHA-256 before reading','Join only on documented keys and check cardinality','Never mix synthetic and real observations into a training population','Exclude test outcomes, IDs and context-only fields from predictors','Fit all preprocessing on training data; evaluate on held-out data'],'warnings':found['warnings']}
