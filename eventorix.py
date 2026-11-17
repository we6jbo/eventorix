#!/usr/bin/env python3
import argparse, json, os, pathlib, re, sqlite3, sys, time, uuid
CODE='eventorix-public-v1'
VERSION='0.1.1'
HOME=pathlib.Path.home()
# Deliberately separate from the native private installation. No inherited private state override.
if pathlib.Path(__file__).resolve().is_relative_to(pathlib.Path('/snap/eventorix')) and os.environ.get('SNAP_NAME')=='eventorix' and os.environ.get('SNAP_USER_COMMON'):
    STATE=pathlib.Path(os.environ['SNAP_USER_COMMON'])/'eventorix-public'
elif pathlib.Path('/.flatpak-info').exists():
    STATE=pathlib.Path(os.environ.get('XDG_DATA_HOME',str(HOME/'.var/app/io.github.eventorix.Eventorix/data')))/'eventorix-public'
else:
    STATE=HOME/'.local/share/eventorix-public'
BUILD_EDITION='public'
def edition_matches(requested):
    actual=pathlib.Path(__file__).resolve()
    roots=[pathlib.Path('/opt/.jci-event-service')]
    if os.environ.get('SNAP_NAME')=='eventorix' and os.environ.get('SNAP'):
        roots.append(pathlib.Path(os.environ['SNAP']))
    if pathlib.Path('/.flatpak-info').exists(): roots.append(pathlib.Path('/app'))
    return requested=='public' and BUILD_EDITION=='public' and any(actual.is_relative_to(root.resolve()) for root in roots)
os.umask(0o077)
def now(): return int(time.time())
def db():
    STATE.mkdir(parents=True,exist_ok=True); c=sqlite3.connect(STATE/'events.db',timeout=10); c.row_factory=sqlite3.Row; c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA synchronous=FULL'); c.execute('CREATE TABLE IF NOT EXISTS changes (op TEXT PRIMARY KEY, event TEXT NOT NULL, rev INTEGER NOT NULL, body TEXT NOT NULL)'); c.execute('CREATE INDEX IF NOT EXISTS changes_event ON changes(event,rev,op)'); return c
def records(c):
    return [json.loads(r[0]) for r in c.execute('SELECT body FROM changes a WHERE NOT EXISTS (SELECT 1 FROM changes b WHERE b.event=a.event AND (b.rev>a.rev OR (b.rev=a.rev AND b.op>a.op))) ORDER BY event')]
def put(c,r):
    validate(r)
    c.execute('INSERT OR IGNORE INTO changes VALUES (?,?,?,?)',(r['op'],r['id'],r['revision'],json.dumps(r,sort_keys=True)))
def validate(r):
    if not isinstance(r,dict): raise ValueError('invalid record')
    for k in ('id','op'):
        if not isinstance(r.get(k),str) or str(uuid.UUID(r[k]))!=r[k]: raise ValueError('invalid UUID')
    if type(r['revision']) is not int or not 1<=r['revision']<=100000000: raise ValueError('invalid revision')
    if r['provenance']!=CODE or r['status'] not in ('pending','due','claimed','completed','deleted'): raise ValueError('invalid metadata')
    for k in ('source','assigned_to','message'):
        if not isinstance(r[k],str) or len(r[k])>16384: raise ValueError('invalid text')
    for k in ('created_at','due_at','updated_at'):
        if type(r[k]) is not int: raise ValueError('invalid timestamp')
    return r
def emit(x): print(json.dumps(x,ensure_ascii=False))
def delta(s):
    m=re.fullmatch(r'(\d+)([smhdw])',s)
    if not m: raise ValueError('use e.g. 5m or 14d')
    return int(m[1])*dict(s=1,m=60,h=3600,d=86400,w=604800)[m[2]]
def mutate(c,r,**kw):
    r=dict(r,**kw); r.update(op=str(uuid.uuid4()),revision=r['revision']+1,updated_at=now()); put(c,r); return r
def tick(c):
    with c:
        c.execute('BEGIN IMMEDIATE')
        for r in records(c):
            if r['status']=='pending' and r['due_at']<=now(): mutate(c,r,status='due')
def all_changes(c): return [json.loads(r[0]) for r in c.execute('SELECT body FROM changes ORDER BY op')]
def merge(c,rows):
    if not isinstance(rows,list) or len(rows)>50000: raise ValueError('exchange size limit')
    with c:
        for r in rows: put(c,validate(r))
def main():
    if len(sys.argv)>1 and sys.argv[1]=='--jxl':
        identity=argparse.ArgumentParser(prog='eventorix')
        identity.add_argument('--jxl', choices=('public','we6jbo'), required=True)
        result=edition_matches(identity.parse_args().jxl)
        emit(result); sys.exit(0 if result else 1)
    a=argparse.ArgumentParser(epilog='Edition checks: --jxl public | --jxl we6jbo (standalone, true/false).'); a.add_argument('--version',action='version',version=VERSION); sub=a.add_subparsers(dest='cmd',required=True)
    for name in ('schedule','publish'):
        p=sub.add_parser(name); p.add_argument('--source',required=True); p.add_argument('--assigned-to',default='all'); p.add_argument('--message',required=True); p.add_argument('--after',default='0s'); p.add_argument('--id')
    for name in ('list','tasks','history','search'):
        p=sub.add_parser(name); p.add_argument('--source'); p.add_argument('--assigned-to'); p.add_argument('--due',action='store_true'); p.add_argument('--include-deleted',action='store_true'); p.add_argument('--message'); p.add_argument('--json',action='store_true')
    for name in ('read','delete','restore','claim','complete','update','reschedule'):
        p=sub.add_parser(name); p.add_argument('--id',required=True); p.add_argument('--message'); p.add_argument('--after'); p.add_argument('--assigned-to')
    for name in ('status','exchange','daemon','subscribe','export'):
        p=sub.add_parser(name)
        if name=='status': p.add_argument('--json',action='store_true')
        if name=='exchange': p.add_argument('--ack',action='store_true')
    x=a.parse_args(); c=db()
    if x.cmd=='export':
        emit(all_changes(c)); return
    if x.cmd=='exchange':
        payload=sys.stdin.buffer.read(64*1024*1024+1)
        if len(payload)>64*1024*1024: raise ValueError('exchange exceeds 64 MiB')
        merge(c,json.loads(payload)); rows=all_changes(c)
        emit({'acknowledged':True,'committed_at':now(),'version':VERSION,'provenance':CODE,'changes':rows} if x.ack else rows); return
    if x.cmd=='daemon':
        while True:
            tick(c)
            time.sleep(2)
    if x.cmd=='subscribe':
        seen=set()
        while True:
            tick(c)
            for r in all_changes(c):
                if r['op'] not in seen: print(json.dumps(r),flush=True); seen.add(r['op'])
            time.sleep(2)
    tick(c)
    if x.cmd in ('schedule','publish'):
        with c:
            c.execute('BEGIN IMMEDIATE'); ident=x.id or str(uuid.uuid4()); uuid.UUID(ident)
            ident=str(uuid.UUID(ident))
            old=next((r for r in records(c) if r['id']==ident),None)
            if old:
                if old['source']!=x.source: raise ValueError('event ID belongs to another source')
                emit(old); return
            n=now(); due=n+delta(x.after); r=dict(id=ident,op=str(uuid.uuid4()),revision=1,source=x.source,assigned_to=x.assigned_to,message=x.message,created_at=n,updated_at=n,due_at=due,status='pending' if due>n else 'due',provenance=CODE); put(c,validate(r))
        emit(r); return
    rows=records(c)
    if x.cmd=='status':
        emit(dict(version=VERSION,edition=BUILD_EDITION,events=len(rows),database=str(STATE/'events.db'),sync_enabled=False,provenance=CODE)); return
    if x.cmd in ('list','tasks','history','search'):
        if x.cmd=='history': rows=all_changes(c)
        emit([r for r in rows if (x.include_deleted or r['status']!='deleted') and (not x.source or r['source']==x.source) and (not x.assigned_to or r['assigned_to'] in (x.assigned_to,'all')) and (not x.due or r['status']=='due') and (not x.message or x.message.lower() in r['message'].lower())]); return
    with c:
        c.execute('BEGIN IMMEDIATE'); r=next((r for r in records(c) if r['id']==x.id),None)
        if not r: raise ValueError('event not found')
        if x.cmd=='read': emit(r); return
        if x.cmd=='claim' and r['status']!='due': raise ValueError('not due')
        if x.cmd=='complete' and r['status']!='claimed': raise ValueError('not claimed')
        if r['status']=='deleted' and x.cmd!='restore': raise ValueError('restore first')
        if x.cmd=='restore' and r['status']!='deleted': raise ValueError('not deleted')
        kw={}; statuses=dict(delete='deleted',restore='pending' if r['due_at']>now() else 'due',claim='claimed',complete='completed')
        if x.cmd in statuses: kw['status']=statuses[x.cmd]
        if x.message is not None: kw['message']=x.message
        if x.assigned_to is not None: kw['assigned_to']=x.assigned_to
        if x.after is not None: kw.update(due_at=now()+delta(x.after),status='pending')
        if x.cmd=='reschedule' and x.after is None: raise ValueError('--after required')
        r=mutate(c,r,**kw); validate(r)
    emit(r)
if __name__=='__main__':
    try: main()
    except (ValueError,RuntimeError,OSError,sqlite3.Error,KeyError,TypeError,OverflowError) as e: print('eventorix: '+str(e),file=sys.stderr); sys.exit(1)
