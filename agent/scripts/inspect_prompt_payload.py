import asyncio
import json
from agent.investigation_agent import gather_evidence_node

async def inspect():
    st = {'txn_id': '3476682'}
    ev = await gather_evidence_node(st)
    ch = ev.get('customer_history', {})
    print('cust_hist keys:', ch.keys() if isinstance(ch, dict) else type(ch))
    if isinstance(ch, dict):
        for k, v in ch.items():
            l = len(v) if hasattr(v, '__len__') else v
            print(f'  ch.{k}: {l}')
            
    ps = ev.get('pattern_signals', {})
    print('pattern_signals keys:', ps.keys())
    ds = ps.get('device_sharing', {})
    print('device_sharing keys:', ds.keys())
    for k, v in ds.items():
        l = len(v) if hasattr(v, '__len__') else v
        print(f'  ds.{k}: {l}')

asyncio.run(inspect())
