import hashlib
import tempfile
import unittest
from pathlib import Path
from core.static_svg_assets import load_verified_static_assets

class StaticSvgAssetsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/'shapes').mkdir()
        self.blobs, files, shapes, aliases, pins = {}, [], {}, {}, {}
        for alias, cid in [('mt_00',222),('mt_01',219)]:
            rel=f'shapes/{cid}.svg'
            data=f'<svg id="{cid}"/>'.encode()
            (self.root/rel).write_bytes(data)
            self.blobs[rel]=data
            sha=hashlib.sha256(data).hexdigest()
            files.append({'path':rel,'sha256':sha})
            shapes[str(cid)]={'path':rel,'sha256':sha}
            aliases[alias]={'shape_id':cid,'source':rel,'sha256':sha,
                            'origin_x':15.95,'origin_y':15.95}
            pins[alias]={'shape_id':cid,'origin_x':15.95,'origin_y':15.95}
        self.report={'schema_version':1,'swf_sha256':'a'*64,
                     'registration_verified_for_static_aliases':True,
                     'verified_static_aliases':aliases,'shapes':shapes}
        self.anchors={'schema_version':1,'swf_sha256':'a'*64,'aliases':pins}
        self.manifest={'original':{'sha256':'a'*64},'files':files}

    def load(self, decoder):
        return load_verified_static_assets(self.report,self.anchors,self.manifest,self.root,decoder)

    def test_verified_images_and_offsets(self):
        assets=self.load(lambda data:data)
        self.assertEqual(set(assets),{'mt_00','mt_01'})
        self.assertEqual(assets['mt_00']['origin_x'],15.95)
        self.assertEqual(assets['mt_01']['image'],self.blobs['shapes/219.svg'])

    def test_hash_mismatch_before_any_decode(self):
        (self.root/'shapes/219.svg').write_bytes(b'changed')
        calls=[]
        with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):
            self.load(lambda data:calls.append(data))
        self.assertEqual(calls,[])

    def test_registration_drift_rejected(self):
        self.report['verified_static_aliases']['mt_00']['origin_y']=16
        with self.assertRaisesRegex(ValueError,'unverified static metadata'):
            self.load(lambda data:data)

    def test_swf_drift_rejected(self):
        self.manifest['original']['sha256']='b'*64
        with self.assertRaisesRegex(ValueError,'SWF provenance'):
            self.load(lambda data:data)

    def test_unverified_animated_alias_rejected(self):
        self.report['verified_static_aliases']['mt_02']={}
        with self.assertRaisesRegex(ValueError,'unverified static source'):
            self.load(lambda data:data)

    def test_missing_file_and_null_decoder(self):
        (self.root/'shapes/222.svg').unlink()
        with self.assertRaisesRegex(ValueError,'missing SVG'):
            self.load(lambda data:data)
        (self.root/'shapes/222.svg').write_bytes(self.blobs['shapes/222.svg'])
        with self.assertRaisesRegex(ValueError,'returned no image'):
            self.load(lambda data:None)
