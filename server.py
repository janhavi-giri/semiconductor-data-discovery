"""Local-only demo server, stdlib runtime. Start: python server.py"""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs,urlparse
import argparse,json
from bootstrap import ensure_data
from discovery import ROOT,load,search,asset_detail,handoff,FILTERS
class Handler(BaseHTTPRequestHandler):
    def send(self,status,body,kind='application/json'):
        data=(json.dumps(body,allow_nan=False).encode() if kind=='application/json' else body.encode())
        self.send_response(status);self.send_header('Content-Type',kind+'; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
    def do_GET(self):
        u=urlparse(self.path);p=parse_qs(u.query);q=p.get('q',[''])[0]
        filters={k:p[k][0] for k in (*FILTERS,'max_missing') if k in p and p[k][0]!=''}
        try:
            if u.path=='/':return self.send(200,(ROOT/'web/index.html').read_text(encoding="utf-8"),'text/html')
            if u.path=='/api/health':return self.send(200,{'status':'ok','asset_count':len(load()),'engine':'local metadata discovery'})
            if u.path=='/api/catalog':return self.send(200,load())
            if u.path=='/api/search':return self.send(200,search(q,filters))
            if u.path=='/api/asset':return self.send(200,asset_detail(p.get('id',[''])[0]))
            if u.path=='/api/handoff':return self.send(200,handoff(q,filters,p.get('id')))
            if u.path=='/api/ontology':return self.send(200,json.loads((ROOT/'ontology.json').read_text(encoding="utf-8")))
            if u.path=='/api/results':
                return self.send(200,{name:json.loads((ROOT/'outputs'/name).read_text(encoding="utf-8")) for name in ['provenance.json','ml_result.json','discovery_comparison.json']})
            return self.send(404,{'error':'Route not found'})
        except (ValueError,KeyError) as e:return self.send(400,{'error':str(e)})
        except Exception:return self.send(500,{'error':'Local data unavailable. Run python build_demo.py and retry.'})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8501);a=p.parse_args()
    if not ensure_data():raise SystemExit('Demo data missing. Restore data.zip or run python build_demo.py')
    print(f'Open http://127.0.0.1:{a.port} (Ctrl+C to stop)',flush=True)
    ThreadingHTTPServer((a.host,a.port),Handler).serve_forever()
