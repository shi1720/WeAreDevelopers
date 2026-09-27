/* Tablekeeper: server-authoritative bookings, explicit uncertain outcomes. */
'use strict';
const main = document.querySelector('#main');
const account = document.querySelector('#account');
const SESSION_KEY = 'tablekeeper.session';
let session = null;
try { session = JSON.parse(localStorage.getItem(SESSION_KEY)); } catch (_) {}
if (!session || typeof session.token !== 'string') session = null;
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const idsOf = reservation => reservation.table_ids || [reservation.table_id];
const displayDate = value => {
  const [year, month, day] = value.split('-').map(Number);
  return new Intl.DateTimeFormat('en-GB', {weekday:'short', day:'numeric', month:'long', year:'numeric', timeZone:'UTC'}).format(new Date(Date.UTC(year, month - 1, day)));
};
function today() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}
function newKey() {
  const bytes = crypto.getRandomValues(new Uint8Array(18));
  return Array.from(bytes, b => b.toString(16).padStart(2,'0')).join('');
}
class Refusal extends Error {
  constructor(status, body) { super(body?.error?.message || 'The request could not be completed.'); this.status = status; this.code = body?.error?.code; }
}
async function api(path, {method='GET', body, key}={}) {
  const headers = {'Accept':'application/json'};
  if (session) headers.Authorization = `Bearer ${session.token}`;
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (key) headers['Idempotency-Key'] = key;
  const response = await fetch(path, {method, headers, body: body === undefined ? undefined : JSON.stringify(body), cache:'no-store'});
  let result;
  try { result = await response.json(); } catch (_) { throw new Error('The response could not be read.'); }
  if (!response.ok) throw new Refusal(response.status, result);
  return result;
}
function friendly(error) {
  const messages = {
    table_unavailable:'That seating option was just taken. We refreshed the times below. Your selection is still here so you can choose another table or time.',
    cutoff_passed:'This reservation is too close to its start to change or cancel online.',
    unauthenticated:'Please sign in with your email and password to continue.',
    email_taken:'An account already uses this email. Try signing in.',
    not_found:'We could not find that reservation in your account. Check the reference and try again.',
    party_exceeds_capacity:'This table cannot seat that many guests. Choose a larger seating option.',
    combination_not_allowed:'These tables cannot be booked together. Choose one of the paired options shown.',
  };
  return messages[error.code] || error.message || 'Something went wrong. Please try again.';
}
function feedback(parent, testid, text, style='error') {
  const node = document.createElement('div');
  node.className = `feedback ${style}`; node.dataset.testid = testid;
  node.setAttribute('role', style === 'error' ? 'alert' : 'status'); node.textContent = text;
  parent.append(node); return node;
}
function clearFeedback(parent) { parent.querySelectorAll('.feedback').forEach(n => n.remove()); }
function renderAccount() {
  account.replaceChildren();
  if (session) {
    const user = document.createElement('span'); user.dataset.testid='current-user'; user.textContent=session.display_name;
    const logout = document.createElement('button'); logout.className='quiet-button'; logout.dataset.testid='logout-button'; logout.textContent='Sign out';
    logout.onclick=() => { session=null; localStorage.removeItem(SESSION_KEY); location.assign('/'); };
    account.append(user,logout);
  } else account.innerHTML='<a class="pill-link" href="/login">Sign in</a>';
}
const illustration = `<figure class="illustration"><svg viewBox="0 0 360 290" role="img" aria-label="Illustration of a thoughtfully set dining table"><path d="M50 240V95a130 130 0 0 1 260 0v145" fill="#e5e8d6"/><path d="M70 238V100a110 110 0 0 1 220 0v138" fill="none" stroke="#b9c2a8" stroke-width="1.5"/><path d="M180 0v88M69 103h221" stroke="#b9c2a8" stroke-width="1.5"/><ellipse cx="180" cy="193" rx="124" ry="57" fill="#b16a4c"/><path d="M74 201v35m212-35v35" stroke="#704b36" stroke-width="8" stroke-linecap="round"/><ellipse cx="180" cy="183" rx="124" ry="57" fill="#e6d1af" stroke="#b18359" stroke-width="2"/><ellipse cx="126" cy="184" rx="34" ry="24" fill="#fffaf0" stroke="#ac9472"/><ellipse cx="126" cy="184" rx="24" ry="16" fill="none" stroke="#d6c8ae"/><ellipse cx="232" cy="184" rx="34" ry="24" fill="#fffaf0" stroke="#ac9472"/><ellipse cx="232" cy="184" rx="24" ry="16" fill="none" stroke="#d6c8ae"/><path d="M78 172v26m5-26v26m195-26v26" stroke="#777968" stroke-width="2" stroke-linecap="round"/><path d="M173 164l-5-27h26l-5 27z" fill="#a04a30"/><path d="M180 140v-44m0 29c-22-1-27-16-23-24 19 0 26 12 23 24m0-11c21-1 28-14 24-24-19 1-28 10-24 24" fill="#6d835f" stroke="#526b48" stroke-width="2"/><ellipse cx="151" cy="153" rx="10" ry="7" fill="#faf4e6" stroke="#a4a58d"/><path d="M151 159v12m-6 1h12" stroke="#8a927d"/><ellipse cx="210" cy="153" rx="10" ry="7" fill="#faf4e6" stroke="#a4a58d"/><path d="M210 159v12m-6 1h12" stroke="#8a927d"/></svg><figcaption>Good company. A place to gather.</figcaption></figure>`;

function authScreen(signup) {
  const action = signup ? 'signup' : 'login';
  document.title = `${signup ? 'Create an account' : 'Sign in'} — Tablekeeper`;
  main.innerHTML=`<div class="auth-layout"><section class="auth-intro"><p class="eyebrow">Your evening starts here</p><h1>A little less planning.<br><em>A little more together.</em></h1><p class="lede">Keep your reservations in one place, and leave room for the good part.</p>${illustration}</section><section class="auth-card"><h2>${signup?'Make yourself at home.':'Welcome back.'}</h2><form id="auth-form">${signup?'<div class="field"><label for="display-name">Your name</label><input id="display-name" autocomplete="name" data-testid="signup-display-name" required></div>':''}<div class="field"><label for="email">Email address</label><input id="email" type="email" autocomplete="email" data-testid="${action}-email" required></div><div class="field"><label for="password">Password</label><input id="password" type="password" autocomplete="${signup?'new-password':'current-password'}" data-testid="${action}-password" ${signup?'minlength="8"':''} required>${signup?'<p class="inline-note">At least 8 characters.</p>':''}</div><button class="primary" data-testid="${action}-submit">${signup?'Create account':'Sign in'}</button></form><div id="auth-feedback"></div><p>${signup?'Already have an account? <a href="/login">Sign in</a>':'New to Tablekeeper? <a href="/signup">Create an account</a>'}</p></section></div>`;
  document.querySelector('#auth-form').onsubmit=async event => {
    event.preventDefault(); const button=event.currentTarget.querySelector('button'); button.disabled=true;
    const messages=document.querySelector('#auth-feedback'); clearFeedback(messages);
    const body={email:document.querySelector('#email').value,password:document.querySelector('#password').value};
    if(signup) body.display_name=document.querySelector('#display-name').value;
    try { session=await api(`/auth/${action}`,{method:'POST',body}); localStorage.setItem(SESSION_KEY,JSON.stringify(session)); location.assign('/'); }
    catch(error) { feedback(messages,'auth-error', error instanceof Refusal ? friendly(error) : 'We could not connect. Please try again.'); }
    finally { button.disabled=false; }
  };
}

let searchGeneration=0, shownSearch=null, selection=null, attempt=null, bookingPending=false;
async function searchScreen() {
  main.innerHTML=`<section class="hero"><div><p class="eyebrow">Make room for a lovely evening</p><h1>Good company.<br><em>Your table is waiting.</em></h1><p class="lede">Find a place, choose your moment, and bring your favourite people. We’ll keep the table.</p></div>${illustration}</section><section class="search-panel" aria-label="Find a table"><form id="search-form" class="search-fields"><div class="restaurant-field"><label for="restaurant">Restaurant</label><select id="restaurant" data-testid="restaurant-select"><option value="">Loading restaurants…</option></select></div><div><label for="date">Date</label><input id="date" type="date" data-testid="date-input" required></div><div><label for="party">Guests</label><input id="party" type="number" min="1" step="1" value="2" data-testid="party-size-input" required></div><button class="primary" data-testid="search-button">Find a table <span aria-hidden="true">↗</span></button></form></section><div id="search-feedback" aria-live="polite"></div><section id="results"><div class="empty" style="margin-top:30px"><h2>An evening to look forward to.</h2>Choose your restaurant, date and guests to see the available tables.</div></section>`;
  document.querySelector('#date').value=today();
  document.querySelector('#search-form').onsubmit=event=>{event.preventDefault();runSearch();};
  try {
    const data=await api('/restaurants'); const select=document.querySelector('#restaurant'); select.replaceChildren();
    for(const restaurant of data.restaurants) { const option=document.createElement('option'); option.value=restaurant.id; option.textContent=restaurant.name; select.append(option); }
    if(!data.restaurants.length) { select.innerHTML='<option value="">No restaurants available</option>'; feedback(document.querySelector('#search-feedback'),'search-error','There are no restaurants to browse yet. Please check back later.','uncertain'); }
  } catch(error) { feedback(document.querySelector('#search-feedback'),'search-error','Restaurants could not be loaded. Reload the page to try again.'); }
}
async function runSearch({preserve=false, values=null}={}) {
  const generation=++searchGeneration;
  const query=values || {restaurant_id:document.querySelector('#restaurant').value,date:document.querySelector('#date').value,party_size:document.querySelector('#party').value};
  const messages=document.querySelector('#search-feedback'); clearFeedback(messages);
  const loading=feedback(messages,'search-loading','Finding a place for your evening…','loading');
  if(!preserve) { selection=null; attempt=null; shownSearch=null; document.querySelector('#results').replaceChildren(); }
  try {
    const [restaurant,availability,policyList]=await Promise.all([api(`/restaurants/${encodeURIComponent(query.restaurant_id)}`),api(`/availability?${new URLSearchParams({...query,explain:'true'})}`),api(`/restaurants/${encodeURIComponent(query.restaurant_id)}/policies`)]);
    if(generation!==searchGeneration) return;
    const policy=policyList.policies.filter(p=>p.effective_from<=query.date).sort((a,b)=>b.effective_from.localeCompare(a.effective_from)||b.policy_version-a.policy_version)[0];
    if(policy) { restaurant.tables=restaurant.tables.map(table=>({...table,capacity:policy.capacities[table.id]})); restaurant.policy_version=policy.policy_version; }
    shownSearch={restaurant,availability,query:{...query}}; renderResults(preserve);
  } catch(error) {
    if(generation!==searchGeneration) return;
    feedback(messages,'search-error',error instanceof Refusal?friendly(error):'We could not load availability. Please try your search again.');
  } finally { if(generation===searchGeneration) loading.remove(); }
}
function tableLabels(restaurant, ids) { return ids.map(id=>restaurant.tables.find(t=>t.id===id)?.label || id).join(' + '); }
function renderResults(preserve=false) {
  const {restaurant,availability,query}=shownSearch;
  const results=document.querySelector('#results');
  let retained=preserve ? document.querySelector('#booking-panel') : null;
  results.innerHTML=`<div class="section-heading"><div><p class="eyebrow">A seat at ${escapeHTML(restaurant.name)}</p><h2>${escapeHTML(displayDate(query.date))}</h2><p>${escapeHTML(query.party_size)} guests · All times in ${escapeHTML(restaurant.timezone)}</p></div><div class="legend"><span><i class="dot"></i>Available</span><span><i class="dot unavailable"></i>Unavailable</span></div></div><div class="results-layout ${selection?'':'no-booking'}"><div id="table-results"></div><div id="booking-mount"></div></div>`;
  const grid=document.querySelector('#table-results'); grid.className='table-grid';
  if(!availability.slots.length) { grid.className='empty'; grid.dataset.testid='no-slots'; grid.innerHTML='<h2>A quieter day.</h2>No seating times are available on this date. Try another day.'; }
  else {
    grid.dataset.testid='availability-grid';
    const choices=restaurant.tables.map(t=>({ids:[t.id],capacity:t.capacity}));
    for(const ids of restaurant.combinable || []) if(availability.slots.some(s=>(s.available_options||[]).some(o=>o.table_ids.length===2 && o.table_ids.every((id,i)=>id===ids[i])))) choices.push({ids,capacity:ids.reduce((n,id)=>n+restaurant.tables.find(t=>t.id===id).capacity,0)});
    for(const choice of choices) {
      const card=document.createElement('article'); card.className='table-card';
      card.innerHTML=`<div class="table-title"><div><h3>${escapeHTML(tableLabels(restaurant,choice.ids))}</h3><p>${choice.ids.length===2?'Two tables, one gathering':'A table for your evening'} · Seats ${choice.capacity}</p></div><span class="table-icon" aria-hidden="true">${choice.ids.length===2?'◫':'○'}</span></div><div class="times"></div>`;
      for(const slot of availability.slots) {
        const time=slot.starts_at_local.slice(11,16);
        const available=choice.ids.length===1 ? slot.available_table_ids.includes(choice.ids[0]) : (slot.available_options||[]).some(o=>o.table_ids.length===2 && o.table_ids.every((id,i)=>id===choice.ids[i]));
        const button=document.createElement('button'); button.className='slot'; button.textContent=time; button.dataset.testid=`slot-${choice.ids.join('+')}-${time}`; button.dataset.available=String(available); button.setAttribute('aria-disabled',String(!available));
        button.setAttribute('aria-label',`${tableLabels(restaurant,choice.ids)}, ${time}, ${available?'available':'unavailable'}`);
        if(!available && choice.ids.length===1) {
          const decision=slot.explain?.find(d=>d.table_id===choice.ids[0]);
          if(decision) { const reasons=decision.rules.filter(rule=>!rule.holds).map(rule=>rule.rule==='capacity'?'Not enough seats for this party':'Already reserved'); button.title=reasons.join(' · '); button.setAttribute('aria-label',`${tableLabels(restaurant,choice.ids)}, ${time}: ${reasons.join('; ')}`); }
        }
        button.setAttribute('aria-pressed',String(Boolean(selection && selection.local===slot.starts_at_local && JSON.stringify(selection.ids)===JSON.stringify(choice.ids))));
        button.onclick=()=>{if(!available || bookingPending) return; if(!session) { clearFeedback(document.querySelector('#search-feedback')); feedback(document.querySelector('#search-feedback'),'auth-error','Please sign in to reserve your table.'); return; } selection={restaurant,ids:[...choice.ids],local:slot.starts_at_local,party:Number(query.party_size)}; attempt=null; renderResults(); renderBooking(); document.querySelector('#booking-party').focus({preventScroll:true});};
        card.querySelector('.times').append(button);
      }
      grid.append(card);
    }
  }
  if(retained) document.querySelector('#booking-mount').append(retained);
  else if(selection) renderBooking();
}
function renderBooking() {
  const mount=document.querySelector('#booking-mount'); if(!mount || !selection) return;
  const labels=tableLabels(selection.restaurant,selection.ids);
  mount.innerHTML=`<aside id="booking-panel" class="booking" data-testid="booking-form"><p class="eyebrow">Your evening, reserved</p><h2>A place for you.</h2><div class="summary" data-testid="booking-summary">${escapeHTML(labels)}<br>${escapeHTML(selection.local)}<p class="small-note">${escapeHTML(selection.restaurant.name)} · ${escapeHTML(selection.restaurant.timezone)}</p></div><form id="booking-request"><label for="booking-party">Number of guests</label><input id="booking-party" type="number" min="1" step="1" value="${selection.party}" data-testid="booking-party-size" required><button class="primary" data-testid="booking-submit">Confirm reservation</button></form><p class="small-note">Your table is confirmed only when you receive a booking reference.</p><div id="booking-feedback"></div><div id="confirmation-mount"></div></aside>`;
  document.querySelector('#booking-party').oninput=event=>{if(attempt && Number(event.target.value)===attempt.body.party_size) return;attempt=null;clearFeedback(document.querySelector('#booking-feedback'));document.querySelector('#confirmation-mount').replaceChildren();};
  document.querySelector('#booking-request').onsubmit=submitBooking;
}
async function submitBooking(event) {
  event.preventDefault(); if(bookingPending) return;
  const selected=selection; const panel=document.querySelector('#booking-panel');
  const input=panel.querySelector('#booking-party'); const button=panel.querySelector('button');
  const body={restaurant_id:selected.restaurant.id,starts_at_local:selected.local,party_size:Number(input.value)};
  // Single-table requests intentionally retain the stage-1 wire shape for upgrade retries.
  if(selected.ids.length===1) body.table_id=selected.ids[0]; else body.table_ids=[...selected.ids];
  const signature=JSON.stringify(body);
  if(!attempt || attempt.signature!==signature || attempt.user!==session?.user_id) attempt={signature,body,key:newKey(),user:session?.user_id};
  const request=attempt; const messages=panel.querySelector('#booking-feedback'); clearFeedback(messages);
  panel.querySelector('#confirmation-mount').replaceChildren();
  bookingPending=true; button.disabled=true;input.disabled=true;button.textContent='Confirming…';
  try {
    const reservation=await api('/reservations',{method:'POST',body:request.body,key:request.key});
    if(selection!==selected || !panel.isConnected) return;
    const labels=tableLabels(selected.restaurant,idsOf(reservation));
    panel.querySelector('#confirmation-mount').innerHTML=`<section class="confirmation" data-testid="confirmation" role="status"><p class="eyebrow">It’s in the book</p><h3>We’ll keep your table.</h3><span class="reference" data-testid="confirmation-reference">${escapeHTML(reservation.reference)}</span><p class="small-note" data-testid="confirmation-details">${escapeHTML(selected.restaurant.name)} · ${escapeHTML(labels)} · ${escapeHTML(reservation.starts_at_local)}</p><p class="small-note" data-testid="confirmation-tables">${escapeHTML(labels)}</p><a href="/lookup?reference=${encodeURIComponent(reservation.reference)}">View your reservation →</a></section>`;
    button.textContent='Confirm reservation';
  } catch(error) {
    if(selection!==selected || !panel.isConnected) return;
    if(error instanceof Refusal) {
      feedback(messages,'booking-error',friendly(error));
      if(error.code==='table_unavailable' && shownSearch) await runSearch({preserve:true,values:shownSearch.query});
    } else feedback(messages,'booking-uncertain','We couldn’t confirm the response. Your reservation may have been saved. Retry this unchanged request to recover the same booking safely.','uncertain');
  } finally {
    bookingPending=false;button.disabled=false;input.disabled=false;button.textContent=panel.querySelector('[data-testid="booking-uncertain"]')?'Retry confirmation':'Confirm reservation';
  }
}

let lookupGeneration=0;
function lookupScreen() {
  document.title='Your reservation — Tablekeeper';
  main.innerHTML=`<section class="page-heading"><p class="eyebrow">Keep the evening yours</p><h1>Your place is in the book.</h1><p class="lede">Find the details of your reservation, or let us know if your plans have changed.</p></section><div class="lookup-layout"><section class="lookup-card"><h2>Find your reservation</h2><form id="lookup-form"><div><label for="reference">Booking reference</label><input id="reference" data-testid="lookup-reference-input" autocomplete="off" placeholder="Your confirmation reference" required></div><button class="primary" data-testid="lookup-submit">Find reservation</button></form><p class="small-note">Sign in with the account you used to book. Your reservations are private to you.</p><div id="lookup-feedback"></div></section><div id="detail-mount"><div class="empty">A little reminder of what’s ahead.<br>Your reservation details will appear here.</div></div></div>`;
  const input=document.querySelector('#reference'); input.value=new URLSearchParams(location.search).get('reference') || '';
  document.querySelector('#lookup-form').onsubmit=event=>{event.preventDefault();lookup(input.value);};
  if(input.value && session) lookup(input.value);
}
async function lookup(reference) {
  const generation=++lookupGeneration; const messages=document.querySelector('#lookup-feedback'); clearFeedback(messages);
  document.querySelector('#detail-mount').innerHTML='<p class="loading" role="status">Finding your reservation…</p>';
  try {
    const reservation=await api(`/reservations/${encodeURIComponent(reference)}`);
    const restaurant=await api(`/restaurants/${encodeURIComponent(reservation.restaurant_id)}`);
    if(generation!==lookupGeneration) return;
    renderDetail(reservation,restaurant);
  } catch(error) {
    if(generation!==lookupGeneration) return;
    document.querySelector('#detail-mount').replaceChildren(); feedback(messages,'reservation-error',error instanceof Refusal?friendly(error):'We could not load the reservation. Please try again.');
  }
}
function renderDetail(reservation,restaurant) {
  const mount=document.querySelector('#detail-mount');
  mount.innerHTML=`<section class="detail" data-testid="reservation-detail"><p class="eyebrow">${escapeHTML(restaurant.name)}</p><h2>Your evening</h2><span class="status ${reservation.status==='cancelled'?'cancelled':''}" data-testid="reservation-status">${escapeHTML(reservation.status)}</span><dl><dt>Reference</dt><dd>${escapeHTML(reservation.reference)}</dd><dt>When</dt><dd>${escapeHTML(reservation.starts_at_local.replace('T',' · '))}</dd><dt>Timezone</dt><dd>${escapeHTML(restaurant.timezone)}</dd><dt>Your table</dt><dd data-testid="reservation-tables">${escapeHTML(tableLabels(restaurant,idsOf(reservation)))}</dd><dt>Guests</dt><dd>${reservation.party_size}</dd></dl>${reservation.status==='confirmed'?'<button class="secondary danger" data-testid="reservation-cancel-button">Cancel reservation</button>':'<p class="small-note">This reservation has been cancelled. <a href="/">Find another evening</a>.</p>'}<div id="cancel-feedback"></div></section>`;
  const cancel=mount.querySelector('button');
  if(cancel) cancel.onclick=async()=>{
    cancel.disabled=true;clearFeedback(document.querySelector('#cancel-feedback'));
    try { const result=await api(`/reservations/${encodeURIComponent(reservation.reference)}/cancel`,{method:'POST',body:{}});renderDetail(result,restaurant); }
    catch(error) { feedback(document.querySelector('#cancel-feedback'),'reservation-error',error instanceof Refusal?friendly(error):'The response was lost. Try cancel again to check the current state.');cancel.disabled=false; }
  };
  if(typeof enhanceReservation==='function') enhanceReservation(reservation,restaurant,mount.querySelector('.detail'));
}
renderAccount();
if(location.pathname==='/signup') authScreen(true);
else if(location.pathname==='/login') authScreen(false);
else if(location.pathname==='/lookup') lookupScreen();
else if(location.pathname==='/') searchScreen();
