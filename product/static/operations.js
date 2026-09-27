/* Operational shell. Credentials stay in HttpOnly cookies, never web storage. */
'use strict';
let materialInFlight=false;
const pendingStorage=()=>{
  if(typeof session?.account_scope!=='string' || !session.account_scope) throw new Error('Your account recovery scope is unavailable. Sign in again before changing bookings.');
  return `tablekeeper.pending.v1.${session.account_scope}`;
};
function readPending() {
  if(!session) return null;
  const raw=localStorage.getItem(pendingStorage());
  if(!raw) return null;
  const value=JSON.parse(raw);
  if(!value || typeof value.path!=='string' || !value.path.startsWith('/') || typeof value.key!=='string' || !['POST','PATCH','PUT','DELETE'].includes(value.method)) throw new Error('Saved recovery information is invalid. Do not submit another change; contact the venue.');
  return value;
}
function preparePending(path,method,body,key) {
  if(materialInFlight) throw new Refusal(409,{error:{code:'pending_recovery'}});
  let old;
  try { old=readPending(); } catch(error) { throw new Refusal(409,{error:{message:`Recovery storage cannot be read. ${error.message}`}}); }
  if(old && (old.path!==path || old.method!==method || JSON.stringify(old.body)!==JSON.stringify(body))) throw new Refusal(409,{error:{code:'pending_recovery'}});
  const request=old || {path,method,body:JSON.parse(JSON.stringify(body ?? {})),key:key || newKey(),created_at:new Date().toISOString()};
  try { localStorage.setItem(pendingStorage(),JSON.stringify(request)); }
  catch(_) { throw new Refusal(409,{error:{message:'Your browser could not save retry recovery. Allow site storage before submitting; nothing was sent.'}}); }
  materialInFlight=true;
  renderPending();
  return request;
}
function clearPending(key) {
  try { if(readPending()?.key===key) localStorage.removeItem(pendingStorage()); }
  catch(_) { /* Keep the UI explicit if storage becomes unavailable. */ }
}
function pendingAction(request) {
  if(request.path.endsWith('/cancel'))return 'Cancel booking';
  if(request.path.includes('/replans/'))return 'Apply seating repair';
  if(request.path.endsWith('/replans'))return 'Preview seating repair';
  if(request.path.endsWith('/policies'))return 'Publish booking policy';
  if(request.path.endsWith('/amend'))return 'Update regular evenings';
  if(request.path==='/series')return 'Reserve regular evenings';
  if(request.method==='PATCH')return 'Change booking';
  return 'Reserve your table';
}
function renderPending() {
  let mount=document.querySelector('#pending-recovery');
  if(!mount) { mount=document.createElement('section');mount.id='pending-recovery';mount.className='recovery-wrap';main.before(mount); }
  mount.replaceChildren();
  let request;
  try { request=readPending(); }
  catch(error) { feedback(mount,'recovery-error',error.message);return; }
  if(!request) return;
  mount.innerHTML=`<div class="recovery-card" role="status"><p class="eyebrow">${materialInFlight?'Saving your request':'A request needs checking'}</p><h2>${materialInFlight?'Waiting for confirmation.':'Recover before making another change.'}</h2><p>The server may already have saved this request. An unchanged retry checks that same request safely, even after a restart.</p><p class="small-note">${escapeHTML(pendingAction(request))} · Started ${escapeHTML(new Date(request.created_at).toLocaleString())}</p><div class="button-row"><button class="primary" data-testid="recover-request" ${materialInFlight?'disabled':''}>Recover original result</button><button class="quiet-button" data-testid="discard-request" ${materialInFlight?'disabled':''}>Review discard options</button></div><div class="recovery-feedback"></div></div>`;
  mount.querySelector('[data-testid="recover-request"]').onclick=async()=>{
    const messages=mount.querySelector('.recovery-feedback');
    try {
      const result=await api(request.path,{method:request.method,body:request.body,key:request.key});
      mount.innerHTML='<div class="recovery-card"><h2>Original result recovered.</h2><p>Your saved request is confirmed. Review the current details below.</p><div class="recovered-result"></div></div>';
      const target=mount.querySelector('.recovered-result');
      if(result.reference) { const a=document.createElement('a');a.href=`/lookup?reference=${encodeURIComponent(result.reference)}`;a.textContent=`View booking ${result.reference}`;target.append(a); }
      else if(result.series_id) { const a=document.createElement('a');a.href=`/series?series_id=${encodeURIComponent(result.series_id)}`;a.textContent='View updated visits';target.append(a); }
      else { const a=document.createElement('a');a.href=location.pathname; a.textContent='Refresh current details';target.append(a); }
      await routeScreen();
    } catch(error) {
      renderPending();
      feedback(document.querySelector('#pending-recovery'),'recovery-error',error instanceof Refusal?friendly(error):'The result is still uncertain. Keep this saved request and retry when the connection returns.');
      if(error.status===401) {const link=document.createElement('a');link.href='/login';link.textContent='Sign in again to recover this request';document.querySelector('#pending-recovery').append(link);}
      if(error.status===403) {const link=document.createElement('a');link.href=location.pathname;link.textContent='Reload security token';document.querySelector('#pending-recovery').append(link);}
    }
  };
  mount.querySelector('[data-testid="discard-request"]').onclick=()=>{
    const messages=mount.querySelector('.recovery-feedback');messages.innerHTML='<p><strong>Discarding does not undo a saved change.</strong> Check your bookings, recurring visits or manager roster first. A new request could otherwise duplicate an existing booking.</p><label class="check-label"><input type="checkbox" data-testid="discard-understood">I have checked the current state and understand the risk.</label><button class="secondary danger" data-testid="confirm-discard" disabled>Discard saved retry</button>';
    const check=messages.querySelector('input'),button=messages.querySelector('button');check.onchange=()=>button.disabled=!check.checked;
    button.onclick=()=>{clearPending(request.key);renderPending();};
  };
}

async function routeScreen() {
  renderAccount();
  const path=location.pathname;
  if(sessionInfo.setup_required && !sessionInfo.demo_enabled && path!=='/login') return setupScreen();
  if(path==='/setup') return setupScreen();
  if(path==='/login') return authScreen(false);
  if(path==='/signup') return authScreen(true);
  if(path==='/lookup') return lookupScreen();
  if(path==='/bookings') return bookingsScreen();
  if(path==='/account') return accountScreen();
  if(path==='/manager') return managerScreen();
  if(path==='/series') return seriesScreen();
  if(path==='/demo') return demoScreen();
  return searchScreen();
}
async function boot() {
  main.innerHTML='<section class="empty" role="status">Opening your table book…</section>';
  try {
    sessionInfo=await api('/api/session');session=sessionInfo.authenticated?sessionInfo:null;
    renderDemoBanner();renderPending();await routeScreen();
  } catch(error) {
    main.innerHTML='<section class="empty"><h1>We could not open the table book.</h1><p>Your bookings have not been changed. Check your connection and retry.</p><button class="primary" id="retry-boot">Try again</button></section>';
    document.querySelector('#retry-boot').onclick=boot;
  }
}

function renderDemoBanner() {
  document.querySelector('#demo-banner')?.remove();
  if(!sessionInfo.demo && !sessionInfo.demo_enabled) return;
  const banner=document.createElement('aside');banner.id='demo-banner';banner.className='demo-banner';
  banner.innerHTML=sessionInfo.demo ? '<strong>Synthetic demo</strong><span>Only made-up guests. This private demo expires; do not enter real guest data.</span><a href="/demo">Demo controls</a>' : '<strong>Try Tablekeeper</strong><span>Explore an isolated demo with synthetic guests.</span><a href="/demo">Start a private demo</a>';
  document.querySelector('.masthead').after(banner);
}
function demoScreen() {
  main.innerHTML=`<section class="page-heading"><p class="eyebrow">A small venue, thoughtfully run</p><h1>Make yourself at home.<br><em>Try a synthetic evening.</em></h1><p class="lede">This demo belongs to this browser session. Use made-up information only. Another visitor cannot access your bookings or roster.</p></section><section class="auth-card"><h2>${sessionInfo.demo?'Your demo controls':'Start your private demo'}</h2><p>Explore the guest booking flow, then switch to the restaurant view to see policies, the date roster and seating repairs.</p><div class="button-row">${sessionInfo.demo?'<button class="primary" data-demo="guest">Explore as guest</button><button class="secondary" data-demo="manager">Explore as manager</button><button class="quiet-button" id="reset-demo">Reset this demo</button>':sessionInfo.demo_enabled?'<button class="primary" id="start-demo">Create synthetic demo</button>':'<p>Public demo is not enabled on this service.</p>'}</div><div id="demo-feedback"></div></section>`;
  const run=async(path,body,destination)=>{
    const messages=document.querySelector('#demo-feedback');clearFeedback(messages);
    try { await api(path,{method:'POST',body});location.assign(destination); }
    catch(error) { feedback(messages,'demo-error',error instanceof Refusal?friendly(error):'The demo response was not confirmed. Reload to check the current demo before trying again.'); }
  };
  document.querySelector('#start-demo')?.addEventListener('click',()=>run('/api/demo/start',{},'/'));
  main.querySelectorAll('[data-demo]').forEach(button=>button.onclick=()=>run('/api/demo/role',{role:button.dataset.demo},button.dataset.demo==='manager'?'/manager':'/'));
  document.querySelector('#reset-demo')?.addEventListener('click',()=>{
    const messages=document.querySelector('#demo-feedback');messages.innerHTML='<p>Reset deletes only this visitor’s synthetic bookings and restores the demo. Saved retries for the old demo remain isolated.</p><button class="secondary danger" id="confirm-reset">Reset my synthetic demo</button>';
    messages.querySelector('button').onclick=()=>run('/api/demo/reset',{},'/');
  });
}

function accountScreen() {
  if(requireSignIn()) return;
  main.innerHTML='<section class="page-heading"><p class="eyebrow">Your private account</p><h1>Keep your account yours.</h1><p class="lede">Change your password here. Sign in again after a successful change.</p></section><section class="auth-card"><form id="password-form"><div class="field"><label for="current-password">Current password</label><input id="current-password" type="password" autocomplete="current-password" required></div><div class="field"><label for="new-password">New password</label><input id="new-password" type="password" autocomplete="new-password" minlength="12" required></div><button class="primary">Change password</button></form><div id="password-feedback"></div><p class="small-note">There is no email verification or automated password recovery. No recovery email is sent. Contact the venue operator if you cannot sign in.</p></section>';
  document.querySelector('#password-form').onsubmit=async event=>{
    event.preventDefault();const button=event.currentTarget.querySelector('button'),messages=document.querySelector('#password-feedback');button.disabled=true;clearFeedback(messages);
    try {sessionInfo=await api('/auth/password',{method:'POST',body:{current_password:document.querySelector('#current-password').value,new_password:document.querySelector('#new-password').value}});await api('/auth/logout',{method:'POST',body:{}});location.assign('/login');}
    catch(error) {feedback(messages,'password-error',error instanceof Refusal?friendly(error):'The response was lost. Try signing in with your new password to check whether it changed.');button.disabled=false;}
  };
}

async function bookingsScreen(view='upcoming',offset=0) {
  if(requireSignIn()) return;
  document.title='Your bookings | Tablekeeper';
  main.innerHTML=`<section class="page-heading"><p class="eyebrow">Your evenings, all together</p><h1>A place in your diary.</h1><p class="lede">Find your bookings without a reference, review accepted terms or make a change.</p></section><div class="button-row" aria-label="Booking views"><button class="${view==='upcoming'?'primary':'secondary'}" id="upcoming-bookings">Upcoming</button><button class="${view==='past'?'primary':'secondary'}" id="past-bookings">Past</button><a href="/lookup">Find by reference</a></div><section id="bookings-list" aria-live="polite"><p class="loading">Loading your bookings…</p></section>`;
  document.querySelector('#upcoming-bookings').onclick=()=>bookingsScreen('upcoming');document.querySelector('#past-bookings').onclick=()=>bookingsScreen('past');
  const mount=document.querySelector('#bookings-list');
  try {
    const result=await api(`/reservations?${new URLSearchParams({view,limit:'25',offset:String(offset)})}`);
    const venues=await Promise.all([...new Set(result.reservations.map(r=>r.restaurant_id))].map(id=>api(`/restaurants/${encodeURIComponent(id)}`)));
    if(!mount.isConnected)return;
    mount.innerHTML=result.reservations.length?`<div class="booking-list">${result.reservations.map(r=>{const venue=venues.find(v=>v.id===r.restaurant_id);return `<article class="policy-card" data-testid="booking-list-item"><span class="status ${r.status==='cancelled'?'cancelled':''}">${escapeHTML(r.status)}</span><h2>${escapeHTML(r.starts_at_local.replace('T',' · '))}</h2><p>${r.party_size} guests · ${escapeHTML(tableLabels(venue,idsOf(r)))}</p><p class="small-note">${escapeHTML(venue.name)} · ${escapeHTML(venue.timezone)}</p><a href="/lookup?reference=${encodeURIComponent(r.reference)}">View or edit ${escapeHTML(r.reference)} →</a></article>`;}).join('')}</div>`:'<div class="empty"><h2>No bookings in this view.</h2><p>Your next evening can start with a table.</p><a href="/">Find a table →</a></div>';
    const paging=document.createElement('div');paging.className='button-row';
    if(offset>0){const b=document.createElement('button');b.className='secondary';b.textContent='Previous 25';b.onclick=()=>bookingsScreen(view,Math.max(0,offset-25));paging.append(b);}
    if(result.next_offset!==null && result.next_offset!==undefined){const b=document.createElement('button');b.className='secondary';b.textContent='Next 25';b.onclick=()=>bookingsScreen(view,result.next_offset);paging.append(b);}
    mount.append(paging);
  } catch(error) {mount.replaceChildren();feedback(mount,'bookings-error',error instanceof Refusal?friendly(error):'Your bookings could not be loaded. Choose Upcoming or Past to try again.');}
}

function setupScreen() {
  if(!sessionInfo.setup_required) {
    main.innerHTML='<section class="empty"><h1>Your venue is already set up.</h1><p>Setup is consumed once and cannot be reopened.</p><a href="/login">Sign in</a></section>';return;
  }
  document.title='Set up your venue | Tablekeeper';
  main.innerHTML=`<section class="page-heading"><p class="eyebrow">A thoughtful start</p><h1>Give your venue<br><em>a place to gather.</em></h1><p class="lede">One small venue, one private table book. Your operator supplies the one-time setup secret separately.</p></section><form id="setup-form" class="setup-layout"><section class="auth-card"><h2>Your owner account</h2><div class="field"><label for="setup-secret">One-time setup secret</label><input id="setup-secret" type="password" autocomplete="off" required><p class="inline-note">Never put this secret in a link. It is not saved in browser storage.</p></div><div class="field"><label for="setup-name">Owner name</label><input id="setup-name" autocomplete="name" required maxlength="100"></div><div class="field"><label for="setup-email">Owner email</label><input id="setup-email" type="email" autocomplete="email" required></div><div class="field"><label for="setup-password">Owner password</label><input id="setup-password" type="password" autocomplete="new-password" minlength="12" required></div><h2>Your venue</h2><div class="field"><label for="venue-name">Venue name</label><input id="venue-name" required maxlength="100" placeholder="The Orangery"></div><div class="field"><label for="venue-timezone">IANA timezone</label><input id="venue-timezone" required value="Europe/London"><p class="inline-note">For example Europe/London or Asia/Kolkata. Inventory and timezone are fixed after setup.</p></div><div class="compact-form three"><div><label for="setup-grid">Start interval (minutes)</label><input id="setup-grid" type="number" min="1" max="1440" value="30" required></div><div><label for="setup-duration">Dining time (minutes)</label><input id="setup-duration" type="number" min="1" max="1440" value="90" required></div><div><label for="setup-cutoff">Change deadline (minutes)</label><input id="setup-cutoff" type="number" min="0" max="10080" value="60" required></div></div><fieldset><legend>Opening hours</legend><p class="small-note">Hours use the venue timezone and end on the same day. Uncheck closed days.</p>${['mon','tue','wed','thu','fri','sat','sun'].map(day=>`<div class="hours-row"><label class="check-label"><input type="checkbox" name="${day}-open" checked>${day}</label><label><span class="sr-only">${day} opens</span><input type="time" name="${day}-opens" value="17:00" required></label><span>to</span><label><span class="sr-only">${day} closes</span><input type="time" name="${day}-closes" value="23:00" required></label></div>`).join('')}</fieldset></section><section class="auth-card"><p class="eyebrow">Designed for small venues</p><h2>Set your tables.</h2><p>Choose 1 to 6 tables. Table labels help guests choose; capacities limit who can sit there.</p><div class="field"><label for="table-count">Number of tables</label><select id="table-count">${[1,2,3,4,5,6].map(n=>`<option ${n===4?'selected':''}>${n}</option>`).join('')}</select></div><div id="setup-tables"></div><fieldset><legend>Declared pairs</legend><p class="small-note">At most four pairs. Only these two-table combinations can be booked together.</p><div id="setup-pairs"></div></fieldset><div class="feedback uncertain"><strong>Seating repair limit</strong><p>A closure plan considers at most six overlapping confirmed bookings, including bookings that stay put. It never splits a larger closure into independent plans with a promise of global correctness.</p></div><p class="small-note">Later hours, capacities, duration and change deadlines use effective-dated policies. Existing accepted terms stay unchanged.</p><button class="primary" data-testid="setup-submit">Create venue and owner</button><div id="setup-feedback"></div></section></form>`;
  const form=document.querySelector('#setup-form');
  function tables() {
    const old=[...form.querySelectorAll('[data-table-label]')].map(n=>n.value);
    const count=Number(form.querySelector('#table-count').value);
    form.querySelector('#setup-tables').innerHTML=Array.from({length:count},(_,i)=>`<div class="table-setup-row"><div><label for="table-label-${i}">Table ${i+1} label</label><input id="table-label-${i}" data-table-label value="${escapeHTML(old[i] || ['Window nook','Garden table','Round table','Quiet alcove','Terrace','Corner'][i])}" required maxlength="80"></div><div><label for="table-capacity-${i}">Seats</label><input id="table-capacity-${i}" type="number" min="1" max="100" value="${i<2?2:4}" required></div></div>`).join('');
    const pairs=[];for(let i=0;i<count;i++)for(let j=i+1;j<count;j++)pairs.push(`<label class="check-label"><input type="checkbox" name="pair" value="${i},${j}">Table ${i+1} + Table ${j+1}</label>`);
    form.querySelector('#setup-pairs').innerHTML=pairs.join('') || '<p class="small-note">Add a second table to declare a pair.</p>';
  }
  form.querySelector('#table-count').onchange=tables;tables();
  form.onsubmit=async event=>{
    event.preventDefault();const messages=form.querySelector('#setup-feedback'),button=form.querySelector('[data-testid="setup-submit"]');clearFeedback(messages);
    const count=Number(form.querySelector('#table-count').value),pairs=[...form.querySelectorAll('[name="pair"]:checked')];
    if(pairs.length>4){feedback(messages,'setup-error','Choose at most four declared pairs.');return;}
    const value=id=>form.querySelector(`#${id}`).value;
    try { new Intl.DateTimeFormat('en',{timeZone:value('venue-timezone')}); } catch(_) {feedback(messages,'setup-error','Enter a valid IANA timezone, such as Europe/London.');return;}
    const body={setup_secret:value('setup-secret'),owner:{email:value('setup-email'),password:value('setup-password'),display_name:value('setup-name')},restaurant:{name:value('venue-name'),timezone:value('venue-timezone'),slot_minutes:Number(value('setup-grid')),reservation_duration_minutes:Number(value('setup-duration')),cancellation_cutoff_minutes:Number(value('setup-cutoff')),opening_hours:['mon','tue','wed','thu','fri','sat','sun'].filter(day=>form.elements[`${day}-open`].checked).map(day=>({weekday:day,opens:form.elements[`${day}-opens`].value,closes:form.elements[`${day}-closes`].value})),tables:Array.from({length:count},(_,i)=>({id:`table_${i+1}`,label:value(`table-label-${i}`),capacity:Number(value(`table-capacity-${i}`))})),combinable:pairs.map(p=>p.value.split(',').map(i=>`table_${Number(i)+1}`))}};
    button.disabled=true;
    try {await api('/api/setup',{method:'POST',body});form.querySelector('#setup-secret').value='';location.assign('/manager');}
    catch(error){form.querySelector('#setup-secret').value='';feedback(messages,'setup-error',error instanceof Refusal?friendly(error):'The setup response was lost. Reload to check whether setup finished. If it did, sign in with your new owner account; do not create another venue.');button.disabled=false;}
  };
}

function addBookingEditor(reservation,restaurant,detail) {
  if(reservation.status!=='confirmed')return;
  const section=document.createElement('section');section.className='booking-editor';detail.append(section);
  section.innerHTML=`<h3>Make room for a change.</h3><p class="small-note">Find available seating, then review the proposed terms. Your current booking stays in place until the server confirms the change.</p><form class="compact-form" data-testid="edit-search-form"><div><label for="edit-date">New date</label><input id="edit-date" type="date" value="${escapeHTML(reservation.starts_at_local.slice(0,10))}" required></div><div><label for="edit-party">Guests</label><input id="edit-party" type="number" min="1" value="${reservation.party_size}" required></div><button class="secondary" data-testid="edit-search">Find change options</button></form><div class="edit-feedback"></div><div class="edit-options"></div><div class="edit-review"></div>`;
  const form=section.querySelector('form'),messages=section.querySelector('.edit-feedback'),options=section.querySelector('.edit-options'),review=section.querySelector('.edit-review');let generation=0;
  form.oninput=()=>{generation++;options.replaceChildren();review.replaceChildren();};
  form.onsubmit=async event=>{
    event.preventDefault();const current=++generation;clearFeedback(messages);options.replaceChildren();review.replaceChildren();
    const date=form.querySelector('#edit-date').value,party=Number(form.querySelector('#edit-party').value);
    try {
      const [available,policies]=await Promise.all([api(`/availability?${new URLSearchParams({restaurant_id:restaurant.id,date,party_size:String(party),exclude_reference:reservation.reference})}`),api(`/restaurants/${encodeURIComponent(restaurant.id)}/policies`)]);
      if(current!==generation)return;
      const policy=policies.policies.filter(p=>p.effective_from<=date).sort((a,b)=>b.effective_from.localeCompare(a.effective_from)||b.policy_version-a.policy_version)[0];
      if(!policy)throw new Error('The policy for this date could not be loaded.');
      options.innerHTML='<label for="edit-choice">Available table and arrival</label><select id="edit-choice" data-testid="edit-choice"><option value="">Choose a proposed change</option></select><p class="small-note">Availability can change. The final save checks seating and your booking revision together.</p>';
      const select=options.querySelector('select'),choices=[];
      for(const slot of available.slots) {
        const seats=slot.available_options || slot.available_table_ids.map(id=>({table_ids:[id]}));
        for(const seat of seats) {
          const choice={starts_at_local:slot.starts_at_local,table_ids:seat.table_ids,party_size:party,expected_revision:reservation.revision};
          const option=document.createElement('option');option.value=String(choices.length);option.textContent=`${slot.starts_at_local.slice(11,16)} · ${tableLabels(restaurant,seat.table_ids)}`;choices.push(choice);select.append(option);
        }
      }
      if(!choices.length){options.innerHTML='<div class="empty">No seating options fit. Try another date or party size.</div>';return;}
      select.onchange=()=>{
        const chosen=choices[Number(select.value)];if(select.value==='' || !chosen){review.replaceChildren();return;}
        review.innerHTML=`<section class="policy-card" data-testid="edit-terms"><p class="eyebrow">Review before saving</p><h3>${escapeHTML(chosen.starts_at_local.replace('T',' · '))}</h3><p>${party} guests · ${escapeHTML(tableLabels(restaurant,chosen.table_ids))} · ${escapeHTML(restaurant.timezone)}</p><p>Current accepted policy: ${reservation.accepted_terms.policy_version}. Proposed policy: ${policy.policy_version}.</p>${termsHTML(policy,restaurant)}<p class="small-note">The current accepted change deadline still controls whether you can edit. An individual change becomes a permanent exception to any recurring agreement.</p><button class="primary" data-testid="edit-confirm">Accept terms and save change</button><div class="edit-save-feedback"></div></section>`;
        review.querySelector('button').onclick=async()=>{
          const button=review.querySelector('button'),saveMessages=review.querySelector('.edit-save-feedback');button.disabled=true;clearFeedback(saveMessages);
          try {const result=await api(`/reservations/${encodeURIComponent(reservation.reference)}`,{method:'PATCH',body:chosen,key:newKey()});renderDetail(result,restaurant);feedback(document.querySelector('#detail-mount'),'edit-success','Your change is confirmed. The details above show the saved booking.','success');}
          catch(error){feedback(saveMessages,'edit-error',error instanceof Refusal?friendly(error):'The result is uncertain. Recover the saved request above before making another change.');button.disabled=false;if(error.code==='stale_revision'){const reload=document.createElement('button');reload.className='secondary';reload.textContent='Reload current booking';reload.onclick=()=>lookup(reservation.reference);saveMessages.append(reload);}}
        };
      };
    }catch(error){feedback(messages,'edit-search-error',error instanceof Refusal?friendly(error):error.message || 'Change options could not be loaded. Try again.');}
  };
}

function addRoster(restaurant,mount) {
  const section=document.createElement('section');section.className='roster-workspace';mount.prepend(section);
  section.innerHTML=`<div class="section-heading"><div><p class="eyebrow">The service at a glance</p><h2>Your date roster</h2><p>Operational booking details for ${escapeHTML(restaurant.name)} only. Times use ${escapeHTML(restaurant.timezone)}.</p></div></div><form class="compact-form"><div><label for="roster-date">Service date</label><input id="roster-date" type="date" value="${today()}" required></div><button class="secondary" data-testid="roster-load">Load roster</button></form><div class="roster-results" aria-live="polite"></div>`;
  let generation=0;
  async function loadRoster(offset=0,afterRepair=false) {
    const current=++generation,results=section.querySelector('.roster-results');results.innerHTML='<p class="loading">Loading this service…</p>';
    try {
      const data=await api(`/api/roster?${new URLSearchParams({restaurant_id:restaurant.id,date:section.querySelector('input').value,limit:'50',offset:String(offset)})}`);
      if(current!==generation || !section.isConnected)return;
      const rows=data.reservations || data.roster || [];
      results.innerHTML=rows.length?`<div class="roster-list">${rows.map(r=>`<article class="policy-card" data-testid="roster-row"><span class="status">${escapeHTML(r.status)}</span><h3>${escapeHTML(r.starts_at_local?.slice(11,16))} · ${r.party_size} guests</h3><p>${escapeHTML(r.display_name || r.guest_name || 'Guest')} · ${escapeHTML(tableLabels(restaurant,idsOf(r)))}</p><p class="small-note">Reference ${escapeHTML(r.reference)}</p></article>`).join('')}</div>`:'<div class="empty"><h3>A clear service book.</h3>No bookings for this date.</div>';
      const paging=document.createElement('div');paging.className='button-row';
      if(offset>0){const button=document.createElement('button');button.className='secondary';button.textContent='Previous 50';button.onclick=()=>loadRoster(Math.max(0,offset-50));paging.append(button);}
      if(data.next_offset!==null && data.next_offset!==undefined){const button=document.createElement('button');button.className='secondary';button.textContent='Next 50';button.onclick=()=>loadRoster(data.next_offset);paging.append(button);}
      results.append(paging);
    }catch(error){
      if(current!==generation || !section.isConnected)return;
      results.replaceChildren();
      feedback(results,'roster-error',afterRepair?'The seating repair is saved, but the roster could not be refreshed. Choose Load roster to see the current seating.':error instanceof Refusal?friendly(error):'The roster could not be loaded. Try again.');
    }
  };
  // Operator follow-up outside the accepted BAND run: keep the selected service date.
  section.addEventListener('seating-repair-applied',()=>{loadRoster(0,true);});
  section.querySelector('form').onsubmit=event=>{event.preventDefault();loadRoster();};
  section.querySelector('form').requestSubmit();
}

boot();
