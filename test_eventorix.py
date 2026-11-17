import json, os, pathlib, subprocess, sys, tempfile, unittest, uuid
CLI=pathlib.Path(__file__).with_name('eventorix.py')
class Test(unittest.TestCase):
 def test_lifecycle_and_isolation(self):
  with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
   private=pathlib.Path(a)/'.local/share/eventorix'; private.mkdir(parents=True); sentinel=private/'events.db'; sentinel.write_bytes(b'private fixture')
   def run(*args,home=a,inp=None):
    p=subprocess.run([sys.executable,str(CLI),*args],env=dict(os.environ,HOME=home,EVENTORIX_STATE=str(private)),input=inp,text=True,capture_output=True,check=True); return json.loads(p.stdout)
   i=str(uuid.uuid4()); args=('schedule','--id',i,'--after','14d','--source','Fixture','--message','review')
   first=run(*args); self.assertEqual(first,run(*args)); self.assertEqual(first['status'],'pending')
   self.assertEqual(run('list')[0]['id'],i); self.assertEqual(run('update','--id',i,'--message','changed')['revision'],2)
   run('reschedule','--id',i,'--after','0s'); self.assertEqual(run('tasks','--due')[0]['id'],i)
   run('claim','--id',i); run('complete','--id',i); run('delete','--id',i); self.assertEqual(run('list'),[])
   ack=run('exchange','--ack',home=b,inp=json.dumps(run('export'))); self.assertTrue(ack['acknowledged']); self.assertEqual(run('list',home=b),[])
   run('restore','--id',i,home=b); run('exchange',inp=json.dumps(run('export',home=b))); self.assertEqual(run('list')[0]['id'],i)
   self.assertEqual(sentinel.read_bytes(),b'private fixture'); self.assertIn('eventorix-public',run('status')['database'])
 def test_identity_source_not_installed(self):
  with tempfile.TemporaryDirectory() as d:
   for flag in ('public','we6jbo'):
    p=subprocess.run([sys.executable,str(CLI),'--jxl',flag],env=dict(os.environ,HOME=d),text=True,capture_output=True); self.assertEqual(p.stdout.strip(),'false'); self.assertEqual(p.returncode,1)
   self.assertEqual(list(pathlib.Path(d).iterdir()),[])
if __name__=='__main__': unittest.main()
