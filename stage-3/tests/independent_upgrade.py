"""Run separately against genuine predecessor containers; secrets stay in memory."""
import os
import time
import independent_contract as contract
from independent_policies import IndependentPolicies,policy_fixture


def main():
    target=os.environ.get('TABLEKEEPER_BASE_URL','http://127.0.0.1:18094')
    for stage,source in [(1,os.environ.get('TABLEKEEPER_STAGE1_URL','http://127.0.0.1:18091')),
                         (2,os.environ.get('TABLEKEEPER_STAGE2_URL','http://127.0.0.1:18092'))]:
        started=time.monotonic();contract.BASE=source;x=IndependentPolicies();x.setUp()
        body=x.booking(table='table-a') if stage==1 else x.pair_body(party=2)
        original=x.expect(201,'POST','/reservations',body,x.a,'legacy')
        ref=original['reference'];changed=x.expect(200,'PATCH','/reservations/'+ref,{'party_size':1},x.a)
        moves={'moves':[{'reference':ref,'starts_at_local':'2032-06-17T19:00'}]}
        receipt=x.expect(201,'POST','/reservation-moves',moves,x.a,'batch')
        exported=x.snapshot();contract.BASE=target
        x.reset();x.expect(204,'POST','/_test/import',exported)
        current=x.expect(200,'GET','/reservations/'+ref,token=x.a)
        for k,v in receipt['reservations'][0].items():assert current[k]==v
        assert current['revision']==1 and current['accepted_terms']['policy_version']==0
        assert x.expect(200,'POST','/reservations',body,x.a,'legacy')==original
        assert x.expect(200,'POST','/reservation-moves',moves,x.a,'batch')==receipt
        agreement=x.expect(201,'POST','/series',dict(anchor_reference=ref,count=3,interval_weeks=1),x.a,'adopt')
        assert agreement['occurrences'][0]['reservation']==current
        snap=x.snapshot();x.reset();x.expect(204,'POST','/_test/import',snap)
        assert x.expect(200,'GET','/series/'+agreement['series_id'],token=x.a)==agreement
        assert x.expect(200,'POST','/reservations',body,x.a,'legacy')==original
        print('PASS actual-stage-'+str(stage)+'-import-adoption-original-receipts duration_seconds='+str(round(time.monotonic()-started,3)))


if __name__=='__main__':main()
