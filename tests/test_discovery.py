import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from discovery import search,asset_detail,handoff,load
from consume_handoff import consume
class DiscoveryTests(unittest.TestCase):
    def test_real_population(self):
        assets=[a for a in load() if not a['synthetic']]
        self.assertEqual(len(assets),4)
        for a in assets:
            self.assertIsNone(a['chamber_id']);self.assertIsNone(a['wafer_id'])
            self.assertTrue(asset_detail(a['asset_id'])['verified_sha256'])
    def test_manufacturing_filters(self):
        r=search('Find etch sensor traces for failed wafers in chamber C2')
        self.assertGreater(len(r['results']),0)
        self.assertEqual(r['raw_results'],[])
        for a in r['results']:
            self.assertTrue(a['synthetic']);self.assertEqual(a['process_step'],'etch');self.assertEqual(a['chamber_id'],'C2');self.assertEqual(a['test_outcome'],'fail');self.assertEqual(a['role'],'features')
    def test_unknown_context_is_not_invented(self):
        r=search('Find etch traces in chamber C2',{'source':'SECOM (real)'})
        self.assertEqual(r['results'],[]);self.assertGreater(len(r['warnings']),0)
    def test_link_has_one_test(self):
        a=asset_detail('TRACE-DEMO-W001')
        self.assertEqual([r['asset_id'] for r in a['related_assets']],['TEST-DEMO-W001'])
    def test_handoff_consumption(self):
        c=handoff('Find etch sensor traces for failed wafers in chamber C2',asset_ids=['TRACE-DEMO-W001'])
        result=consume(c);self.assertEqual(result['loaded'][0]['rows_loaded'],60)
    def test_out_of_scope_selection_rejected(self):
        with self.assertRaises(ValueError):handoff('etch',asset_ids=['SECOM-process_features'])
    def test_mixed_populations_rejected(self):
        c=handoff(asset_ids=['TRACE-DEMO-W001','SECOM-process_features'])
        with self.assertRaises(ValueError):consume(c)
    def test_path_escape_rejected(self):
        with self.assertRaises(ValueError):consume({'assets':[{'synthetic':True,'relative_uri':'../outside','sha256':'bad','asset_id':'x'}]})
    def test_empty_handoff_rejected(self):
        with self.assertRaises(ValueError):handoff('unmatchableword')
    def test_causality_warning(self):self.assertTrue(search('root cause of failed wafers')['warnings'])
    def test_no_fake_nand_data(self):self.assertTrue(search('NAND failures')['warnings'])
    def test_no_raw_name_match(self):self.assertTrue(search('a0001')['raw_results'])
if __name__=='__main__':unittest.main()
