/* Policy and recurring experiences extend the shared booking shell. */
function requireSignIn() {
  if(session) return false;
  main.innerHTML='<section class="page-heading"><p class="eyebrow">Your account</p><h1>A place to return to.</h1><p class="lede">Sign in to manage your reservations or restaurant.</p><a class="pill-link" href="/login">Sign in</a></section>';
  return true;
}
function termsHTML(terms,restaurant) {
  if(!terms) return '<p class="small-note">This original confirmation predates policy snapshots. Open the current reservation to see its accepted terms.</p>';
  return `<dl class="terms"><dt>Policy</dt><dd>Version ${terms.policy_version}</dd><dt>Dining time</dt><dd>${terms.reservation_duration_minutes} minutes</dd><dt>Start intervals</dt><dd>${terms.slot_minutes} minutes</dd><dt>Change deadline</dt><dd>${terms.cancellation_cutoff_minutes} minutes before arrival</dd></dl><details><summary>Opening hours and table capacities</summary><ul class="plain-list">${terms.opening_hours.map(h=>`<li>${escapeHTML(h.weekday)} · ${escapeHTML(h.opens)}–${escapeHTML(h.closes)}</li>`).join('')}</ul><ul class="plain-list">${Object.entries(terms.capacities).map(([id,capacity])=>`<li>${escapeHTML(tableLabels(restaurant,[id]))} · ${capacity} seats</li>`).join('')}</ul></details>`;
}
function bindIdempotentForm(form, messages, path, makeBody, onSuccess, prefix) {
  let receipt=null, pending=false;
  form.onsubmit=async event=>{
    event.preventDefault(); if(pending) return;
    let body;
    try { body=makeBody(); } catch(error) { clearFeedback(messages);feedback(messages,`${prefix}-error`,error.message);return; }
    const signature=JSON.stringify(body);
    if(!receipt || receipt.signature!==signature) receipt={signature,body,key:newKey()};
    const request=receipt; const controls=[...form.querySelectorAll('input,select,button')];
    clearFeedback(messages);pending=true;controls.forEach(control=>control.disabled=true);
    try { const result=await api(path,{method:'POST',body:request.body,key:request.key});await onSuccess(result); }
    catch(error) { feedback(messages,`${prefix}-${error instanceof Refusal?'error':'uncertain'}`,error instanceof Refusal?friendly(error):'The response was lost. This may have been saved. Submit the same form again to recover the original result safely.',error instanceof Refusal?'error':'uncertain'); }
    finally { pending=false;controls.forEach(control=>control.disabled=false); }
  };
}

async function enhanceReservation(reservation,restaurant,detail) {
  const extra=document.createElement('div');extra.className='reservation-extra';detail.append(extra);
  extra.innerHTML=`<section data-testid="accepted-terms"><h3>The promise we kept</h3><p class="small-note">Revision ${reservation.revision ?? '—'} · These terms belong to this reservation. Later restaurant policies do not rewrite them.</p>${termsHTML(reservation.accepted_terms,restaurant)}</section><section><h3>Your reservation history</h3><div data-testid="reservation-history"><p class="loading">Loading your history…</p></div></section>${reservation.status==='confirmed'?'<section><h3>Make it a regular evening</h3><p class="small-note">Keep this booking as your first visit. Every following visit is checked against its own date’s policy, with all visits reserved together.</p><form id="adopt-series" class="compact-form"><div><label for="series-count">Total visits, including this one</label><input id="series-count" type="number" min="2" max="12" value="4" data-testid="series-count" required></div><div><label for="series-interval">Weeks between visits</label><input id="series-interval" type="number" min="1" max="4" value="1" data-testid="series-interval" required></div><button class="primary" data-testid="series-create">Reserve regular visits</button></form><div id="series-feedback"></div></section>':''}`;
  const historyMount=extra.querySelector('[data-testid="reservation-history"]');
  try {
    const history=await api(`/reservations/${encodeURIComponent(reservation.reference)}/history`);
    if(!detail.isConnected) return;
    historyMount.innerHTML=`<ol class="timeline">${history.entries.map(entry=>`<li><div class="timeline-heading"><strong>${escapeHTML({created:'Reserved',changed:'Changed',cancelled:'Cancelled'}[entry.event] || entry.event)}</strong><span>Revision ${entry.revision}</span></div><p class="small-note">${escapeHTML(entry.at)}</p>${entry.changes.length?`<ul class="plain-list">${entry.changes.map(change=>`<li>${escapeHTML({table_id:'Table',table_ids:'Tables',starts_at_local:'Arrival',party_size:'Guests'}[change.field] || change.field)}: ${escapeHTML(historyValue(change.to,change.field,restaurant))}</li>`).join('')}</ul>`:''}<details><summary>Terms at this point</summary>${termsHTML(entry.accepted_terms,restaurant)}</details></li>`).join('')}</ol>`;
  } catch(error) { historyMount.replaceChildren();feedback(historyMount,'history-error',error instanceof Refusal?friendly(error):'History could not be loaded. Look up the reservation again to retry.'); }
  const form=extra.querySelector('#adopt-series');
  if(form) bindIdempotentForm(form,extra.querySelector('#series-feedback'),'/series',()=>({anchor_reference:reservation.reference,count:Number(form.querySelector('#series-count').value),interval_weeks:Number(form.querySelector('#series-interval').value)}), result=>{
    const messages=extra.querySelector('#series-feedback');clearFeedback(messages);
    const message=feedback(messages,'series-created',`${result.occurrences.length} visits reserved. Your original booking is still your first visit.`,'success');
    const link=document.createElement('a');link.href=`/series?series_id=${encodeURIComponent(result.series_id)}`;link.textContent='View your regular evenings →';message.append(document.createElement('br'),link);
  },'series');
}
function historyValue(value,field,restaurant) {
  if(field==='table_id') return tableLabels(restaurant,[value]);
  if(field==='table_ids') return tableLabels(restaurant,value);
  return value;
}

let managerGeneration=0;
async function managerScreen() {
  document.title='Restaurant policies — Tablekeeper';
  if(requireSignIn()) return;
  main.innerHTML='<section class="page-heading"><p class="eyebrow">For a thoughtful service</p><h1>Set the terms.<br>Keep the promise.</h1><p class="lede">Publish the rules for future decisions. Existing guests keep the terms they accepted.</p></section><section class="search-panel"><label for="manager-restaurant">Your restaurant</label><select id="manager-restaurant" data-testid="manager-restaurant"><option>Loading restaurants…</option></select></section><div id="manager-content"></div>';
  try {
    const list=await api('/restaurants'); const restaurants=await Promise.all(list.restaurants.map(r=>api(`/restaurants/${encodeURIComponent(r.id)}`)));
    const managed=restaurants.filter(r=>(r.manager_user_ids||[]).includes(session.user_id));
    const select=document.querySelector('#manager-restaurant');select.replaceChildren();
    if(!managed.length) { select.innerHTML='<option>No managed restaurants</option>';document.querySelector('#manager-content').innerHTML='<div class="empty" style="margin-top:25px"><h2>Your guest experience comes first.</h2>This account does not manage a restaurant. <a href="/">Find a table</a> instead.</div>';return; }
    for(const restaurant of managed) { const option=document.createElement('option');option.value=restaurant.id;option.textContent=restaurant.name;select.append(option); }
    select.onchange=()=>loadManager(managed.find(r=>r.id===select.value));
    await loadManager(managed[0]);
  } catch(error) { feedback(document.querySelector('#manager-content'),'manager-error',error instanceof Refusal?friendly(error):'Restaurant details could not be loaded. Reload to try again.'); }
}
async function loadManager(restaurant) {
  const generation=++managerGeneration;const mount=document.querySelector('#manager-content');mount.innerHTML='<p class="loading">Loading published policies…</p>';
  try {
    const list=await api(`/restaurants/${encodeURIComponent(restaurant.id)}/policies`);
    if(generation!==managerGeneration) return;
    const source=list.policies.at(-1) || {...restaurant,capacities:Object.fromEntries(restaurant.tables.map(t=>[t.id,t.capacity]))};
    mount.innerHTML=`<div class="manager-layout"><section class="auth-card policy-editor"><p class="eyebrow">${escapeHTML(restaurant.timezone)}</p><h2>Publish a booking policy</h2><p class="small-note">This is a complete policy. Use the date when these rules should start applying. A newer policy on the same date takes precedence for new decisions.</p><form id="policy-form"><div class="field"><label for="effective">Effective from</label><input id="effective" type="date" value="${today()}" data-testid="policy-effective" required></div><div class="compact-form three"><div><label for="policy-grid">Start interval (minutes)</label><input id="policy-grid" type="number" min="1" max="1440" value="${source.slot_minutes}" required></div><div><label for="policy-duration">Dining time (minutes)</label><input id="policy-duration" type="number" min="1" max="1440" value="${source.reservation_duration_minutes}" data-testid="policy-duration" required></div><div><label for="policy-cutoff">Change deadline (minutes)</label><input id="policy-cutoff" type="number" min="0" max="10080" value="${source.cancellation_cutoff_minutes}" required></div></div><fieldset><legend>Opening hours</legend><p class="small-note">Uncheck a day to close. Hours are local to ${escapeHTML(restaurant.timezone)} and finish on the same day.</p>${['mon','tue','wed','thu','fri','sat','sun'].map(day=>{const hours=source.opening_hours.find(h=>h.weekday===day);return `<div class="hours-row"><label class="check-label"><input type="checkbox" name="${day}-open" ${hours?'checked':''}>${day}</label><label><span class="sr-only">${day} opens</span><input type="time" name="${day}-opens" value="${hours?.opens || '18:00'}" required></label><span>to</span><label><span class="sr-only">${day} closes</span><input type="time" name="${day}-closes" value="${hours?.closes || '23:00'}" required></label></div>`;}).join('')}</fieldset><fieldset><legend>Table capacities</legend><div class="capacity-fields">${restaurant.tables.map((table,index)=>`<div><label for="capacity-${index}">${escapeHTML(table.label)}</label><input id="capacity-${index}" type="number" min="1" max="100" value="${source.capacities[table.id]}" required></div>`).join('')}</div></fieldset><button class="primary" data-testid="policy-publish">Publish policy</button></form><div id="policy-feedback"></div></section><aside class="policy-list"><h2>Published policies</h2><p class="small-note">Publication order is shown here. The latest applicable effective date wins, then the newest version on that date.</p><div id="policy-list" data-testid="policy-list"></div></aside></div>`;
    renderPolicyList(list.policies,restaurant);
    if(typeof renderClosureWorkspace==='function') renderClosureWorkspace(restaurant,mount);
    const form=mount.querySelector('#policy-form');
    bindIdempotentForm(form,mount.querySelector('#policy-feedback'),`/restaurants/${encodeURIComponent(restaurant.id)}/policies`,()=>({effective_from:form.querySelector('#effective').value,slot_minutes:Number(form.querySelector('#policy-grid').value),reservation_duration_minutes:Number(form.querySelector('#policy-duration').value),cancellation_cutoff_minutes:Number(form.querySelector('#policy-cutoff').value),opening_hours:['mon','tue','wed','thu','fri','sat','sun'].filter(day=>form.elements[`${day}-open`].checked).map(day=>({weekday:day,opens:form.elements[`${day}-opens`].value,closes:form.elements[`${day}-closes`].value})),capacities:Object.fromEntries(restaurant.tables.map((table,index)=>[table.id,Number(form.querySelector(`#capacity-${index}`).value)]))}),async result=>{
      feedback(mount.querySelector('#policy-feedback'),'policy-success',`Policy ${result.policy_version} published, effective ${result.effective_from}. Existing reservations keep their accepted terms.`,'success');
      try { const updated=await api(`/restaurants/${encodeURIComponent(restaurant.id)}/policies`); if(generation===managerGeneration) renderPolicyList(updated.policies,restaurant); }
      catch(_) { feedback(mount.querySelector('#policy-feedback'),'policy-list-error','The policy was published, but its list could not be refreshed. Reload to see the latest list.','uncertain'); }
    },'policy');
  } catch(error) { if(generation===managerGeneration) {mount.replaceChildren();feedback(mount,'manager-error',error instanceof Refusal?friendly(error):'Policies could not be loaded. Select the restaurant again to retry.');} }
}
function renderPolicyList(policies,restaurant) {
  const mount=document.querySelector('#policy-list');
  mount.innerHTML=policies.length ? policies.map(policy=>`<article class="policy-card"><p class="eyebrow">Version ${policy.policy_version}</p><h3>From ${escapeHTML(policy.effective_from)}</h3>${termsHTML(policy,restaurant)}</article>`).join('') : '<div class="empty">No published policies yet.<br>The original restaurant rules still apply.</div>';
}

async function seriesScreen() {
  document.title='Regular evenings — Tablekeeper';if(requireSignIn()) return;
  main.innerHTML='<section class="page-heading"><p class="eyebrow">Make a lovely habit</p><h1>A place to come back to.</h1><p class="lede">Every visit has its own reference and accepted terms. One changed evening never erases the others.</p></section><div id="series-content"><p class="loading">Loading your regular evenings…</p></div>';
  const mount=document.querySelector('#series-content');
  try {
    const id=new URLSearchParams(location.search).get('series_id');
    const list=id ? {series:[await api(`/series/${encodeURIComponent(id)}`)]} : await api('/api/series');
    if(!list.series.length) {mount.innerHTML='<div class="empty"><h2>Start with one evening.</h2>Open a confirmed reservation and choose “Make it a regular evening”.<p><a href="/lookup">Find your reservation →</a></p></div>';return;}
    const restaurantIds=[...new Set(list.series.flatMap(series=>series.occurrences.map(o=>o.reservation.restaurant_id)))];
    const restaurants=await Promise.all(restaurantIds.map(rid=>api(`/restaurants/${encodeURIComponent(rid)}`)));
    mount.innerHTML=list.series.map(series=>`<section class="series-card" data-testid="series-detail"><div class="section-heading"><div><p class="eyebrow">${series.occurrences.length} visits · Every ${series.interval_weeks} ${series.interval_weeks===1?'week':'weeks'}</p><h2>Your regular evenings</h2><p>Agreement revision ${series.revision}</p></div><a href="/series?series_id=${encodeURIComponent(series.series_id)}">Link to this agreement</a></div><ol class="occurrences">${series.occurrences.map(occurrence=>{const booking=occurrence.reservation;const restaurant=restaurants.find(r=>r.id===booking.restaurant_id);return `<li><div class="visit-number">${occurrence.index+1}</div><div><h3>${escapeHTML(booking.starts_at_local.replace('T',' · '))}</h3><p>${escapeHTML(restaurant.name)} · ${escapeHTML(tableLabels(restaurant,idsOf(booking)))}</p><p class="small-note">${booking.party_size} guests · ${escapeHTML(restaurant.timezone)} · Policy ${booking.accepted_terms.policy_version}</p>${occurrence.exception?'<span class="exception">Individually changed</span>':''}</div><div class="visit-actions"><span class="status ${booking.status==='cancelled'?'cancelled':''}">${escapeHTML(booking.status)}</span><a href="/lookup?reference=${encodeURIComponent(booking.reference)}">${escapeHTML(booking.reference)} →</a></div></li>`;}).join('')}</ol></section>`).join('');
    if(typeof enhanceSeries==='function') [...mount.querySelectorAll('.series-card')].forEach((card,index)=>enhanceSeries(list.series[index],card));
  } catch(error) {mount.replaceChildren();feedback(mount,'series-error',error instanceof Refusal?friendly(error):'Regular evenings could not be loaded. Reload to try again.');}
}
if(location.pathname==='/manager') managerScreen();
if(location.pathname==='/series') seriesScreen();
