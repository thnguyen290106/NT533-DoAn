import json
from pathlib import Path
import tempfile
import unittest

from analysis.wan import report


class WanReportTests(unittest.TestCase):
    def test_loss_probe_errors_and_partial_line_are_separate(self):
        samples=[{'utc':f'2026-11-20T14:00:0{i}+00:00','exit_code':code,'rtt_ms':rtt}
                 for i,(code,rtt) in enumerate([(0,10),(0,14),(1,None),(124,None),(0,90)])]
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'wan.jsonl'
            file.write_text(''.join(json.dumps(row)+'\n' for row in samples)+'{"partial":',encoding='utf-8')
            actual=report(file,samples[0]['utc'],samples[-1]['utc'])
        self.assertEqual(actual['samples'],samples[:-1])
        self.assertEqual((actual['sent'],actual['received'],actual['lost'],actual['probe_errors']),(3,2,1,1))
        self.assertAlmostEqual(actual['loss_ratio'],1/3)
        self.assertEqual((actual['rtt_ms']['p95'],actual['rtt_ms']['p99'],actual['jitter_ms']),(14,14,2))
