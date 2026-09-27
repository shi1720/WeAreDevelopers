"""Exercise genuine stages 1–3 exports; source services are disposable."""
import os
import time
import independent_contract as contract
from independent_series_amend import IndependentSeriesAmend


def main():
    target = os.environ['TABLEKEEPER_BASE_URL']
    for stage in (1, 2, 3):
        started = time.monotonic()
        contract.BASE = os.environ['TABLEKEEPER_STAGE'+str(stage)+'_URL']
        x = IndependentSeriesAmend(); x.setUp()
        anchor = x.create()
        if stage == 3:
            series = x.adopt(anchor)
            second = series['occurrences'][1]['reference']
            moved = x.expect(200, 'PATCH', '/reservations/'+second, {'starts_at_local':'2032-06-25T19:00'}, x.a)
            third = series['occurrences'][2]['reference']
            cancelled = x.expect(200, 'POST', '/reservations/'+third+'/cancel', {}, x.a)
            original_series = series
        else:
            x.expect(200, 'PATCH', '/reservations/'+anchor['reference'], {'party_size':1}, x.a)
        exported = x.snapshot()
        contract.BASE = target
        x.reset(); x.expect(204, 'POST', '/_test/import', exported)
        x.assertEqual(anchor, x.expect(200, 'POST', '/reservations', x.booking(), x.a, 'create'))
        if stage < 3:
            series = x.adopt(x.expect(200, 'GET', '/reservations/'+anchor['reference'], token=x.a))
        current = x.current(series)
        body = {'expected_revision':current['revision'],'from_index':0,'local_time':'20:00'}
        changed = x.expect(201, 'POST', x.amend_path(series), body, x.a, 'upgrade-amend')
        if stage == 3:
            x.assertEqual(changed['occurrences'][1]['reservation'], moved)
            x.assertEqual(changed['occurrences'][2]['reservation'], cancelled)
            x.assertEqual(original_series, x.expect(200, 'POST', '/series', {'anchor_reference':anchor['reference'],'count':3,'interval_weeks':1}, x.a, 'series'))
        x.expect(200, 'POST', '/reservations/'+anchor['reference']+'/cancel', {}, x.a)
        x.assertEqual(changed, x.expect(200, 'POST', x.amend_path(series), body, x.a, 'upgrade-amend'))
        snapshot = x.snapshot(); x.reset(); x.expect(204, 'POST', '/_test/import', snapshot)
        x.assertEqual(changed, x.expect(200, 'POST', x.amend_path(series), body, x.a, 'upgrade-amend'))
        print('PASS actual-stage-'+str(stage)+' migration/amend/exceptions/cancellation/receipts/roundtrip seconds='+str(round(time.monotonic()-started, 3)))


if __name__ == '__main__':
    main()
