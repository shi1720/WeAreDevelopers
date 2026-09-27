/* Manager seating repairs and owner recurring amendments. */
function restaurantInstant(local,zone) {
  if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(local)) throw new Error('Choose a complete local date and time.');
  const [year,month,day,hour,minute]=local.split(/[-T:]/).map(Number);
  const naive=new Date(0);naive.setUTCFullYear(year,month-1,day);naive.setUTCHours(hour,minute,0,0);
  const formatter=new Intl.DateTimeFormat('en-GB',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'});
  const parts=instant=>Object.fromEntries(formatter.formatToParts(new Date(instant)).map(part=>[part.type,part.value]));
  const offsets=new Set();
  for(let delta=-48;delta<=48;delta+=6) {
    const instant=naive.getTime()+delta*3600000,p=parts(instant),wall=new Date(0);
    wall.setUTCFullYear(Number(p.year),Number(p.month)-1,Number(p.day));wall.setUTCHours(Number(p.hour),Number(p.minute),0,0);
    offsets.add(wall.getTime()-instant);
  }
  const candidates=[...offsets].map(offset=>naive.getTime()-offset).filter(instant=>{
    const p=parts(instant);return Number(p.year)===year && Number(p.month)===month && Number(p.day)===day && Number(p.hour)===hour && Number(p.minute)===minute;
  }).sort((a,b)=>a-b);
  if(!candidates.length) throw new Error('This local time does not exist in the restaurant timezone. Choose a time outside the daylight-saving gap.');
  return new Date(candidates[0]).toISOString().replace('Z','+00:00');
}

function renderClosureWorkspace(restaurant,managerMount) {
  const workspace=document.createElement('section');workspace.className='closure-workspace';managerMount.prepend(workspace);
  workspace.innerHTML=`<div class="closure-heading"><div><p class="eyebrow">Keep the promise, even when the floor changes</p><h2>A closed table.<br>An evening still kept.</h2><p class="lede">Review the smallest safe seating change before making it. Guests keep their arrival times, party sizes and accepted terms.</p></div><div class="promise-stamp" aria-hidden="true">Same evening.<br>Same promise.</div></div><form class="closure-form" data-testid="closure-form"><div><label for="closure-table">Table to close</label><select id="closure-table" data-testid="closure-table">${restaurant.tables.map(t=>`<option value="${escapeHTML(t.id)}">${escapeHTML(t.label)}</option>`).join('')}</select></div><div><label for="closure-from">Closed from</label><input id="closure-from" type="datetime-local" data-testid="closure-from" value="2035-06-14T19:00" required></div><div><label for="closure-to">Until</label><input id="closure-to" type="datetime-local" data-testid="closure-to" value="2035-06-14T21:00" required></div><button class="primary" data-testid="closure-preview">Preview seating repair</button></form><p class="small-note">Times are local to <strong>${escapeHTML(restaurant.timezone)}</strong>. A repeated daylight-saving time uses its first occurrence. Preview does not close the table or move any booking.</p><div class="closure-feedback"></div><div class="closure-preview-mount"></div>`;
  const form=workspace.querySelector('form'),messages=workspace.querySelector('.closure-feedback'), previewMount=workspace.querySelector('.closure-preview-mount');
  let previewRequest=null,plan=null,applyKey=null,pending=false;
  form.oninput=()=>{if(pending)return;plan=null;applyKey=null;previewMount.replaceChildren();clearFeedback(messages);};
  async function preview(event) {
    event.preventDefault();if(pending)return;clearFeedback(messages);previewMount.replaceChildren();
    let body;
    try {
      body={table_id:form.querySelector('#closure-table').value,from:restaurantInstant(form.querySelector('#closure-from').value,restaurant.timezone),to:restaurantInstant(form.querySelector('#closure-to').value,restaurant.timezone)};
      if(Date.parse(body.from)>=Date.parse(body.to))throw new Error('The closure must end after it starts.');
    } catch(error) {feedback(messages,'closure-error',error.message);return;}
    const signature=JSON.stringify(body);
    if(!previewRequest || previewRequest.signature!==signature)previewRequest={signature,body,key:newKey()};
    pending=true;const controls=[...form.querySelectorAll('input,select,button')];controls.forEach(c=>c.disabled=true);
    const loading=feedback(messages,'closure-loading','Checking every considered booking for the smallest safe seating change…','loading');
    try {
      const result=await api(`/restaurants/${encodeURIComponent(restaurant.id)}/replans`,{method:'POST',body:previewRequest.body,key:previewRequest.key});
      // The helper is manager-only and returns the stored before snapshots for this exact plan.
      const detail=await api(`/api/restaurants/${encodeURIComponent(restaurant.id)}/replans/${encodeURIComponent(result.plan_id)}`);
      plan=detail.plan ? {...detail.plan,before_reservations:detail.reservations} : detail;
      applyKey=newKey();renderPlan();
    } catch(error) {
      const text=error.code==='no_feasible_plan'?'No safe seating plan fits this closure. No booking was changed. Try a shorter closure or another table; guests’ times, party sizes and accepted terms cannot be compromised.':error.code==='planning_limit'?'This closure exceeds the supported planning bounds (6 tables, 4 pairs, 6 considered bookings). Nothing was changed.':error instanceof Refusal?friendly(error):'The preview response could not be confirmed. Retry unchanged to recover the same preview safely.';
      feedback(messages,error instanceof Refusal?'closure-error':'closure-uncertain',text,error instanceof Refusal?'error':'uncertain');
    } finally {loading.remove();pending=false;controls.forEach(c=>c.disabled=false);}
  }
  form.onsubmit=preview;
  function renderPlan() {
    clearFeedback(messages);
    const before=new Map(plan.before_reservations.map(r=>[r.reference,r]));
    previewMount.innerHTML=`<section class="repair-plan" data-testid="replan-preview"><div class="section-heading"><div><p class="eyebrow">Preview only · Restaurant revision ${plan.restaurant_revision}</p><h2>The smallest safe change.</h2></div><span class="status">Not applied</span></div><div class="repair-metrics"><div><strong data-testid="replan-moved-count">${plan.moved_count}</strong><span>${plan.moved_count===1?'booking moves':'bookings move'}</span></div><div><strong>${plan.assignments.length}</strong><span>bookings considered</span></div><div><strong>${plan.unused_seats}</strong><span>unused seats after repair</span></div></div><p class="promise-line">Arrival times, guest counts and accepted terms stay exactly the same.</p><div class="repair-map">${restaurant.tables.map(table=>`<div class="map-table ${table.id===plan.closure.table_id?'map-closed':''}"><span class="map-shape" aria-hidden="true">${table.id===plan.closure.table_id?'×':'○'}</span><strong>${escapeHTML(table.label)}</strong><span>${table.id===plan.closure.table_id?'Proposed closure':`${plan.assignments.filter(a=>a.table_ids.includes(table.id)).length} considered bookings after repair`}</span></div>`).join('')}</div><div class="assignments">${plan.assignments.map(assignment=>{const record=before.get(assignment.reference);return `<article class="assignment ${assignment.changed?'assignment-moved':''}" data-testid="replan-assignment"><div class="assignment-heading"><strong>${escapeHTML(assignment.reference)}</strong><span class="status">${assignment.changed?'Moves':'Stays'}</span></div><div class="seating-change"><div><small>Before</small><span>${escapeHTML(tableLabels(restaurant,idsOf(record)))}</span></div><span class="change-arrow" aria-hidden="true">→</span><div><small>After</small><span>${escapeHTML(tableLabels(restaurant,assignment.table_ids))}</span></div></div><p class="small-note" data-testid="replan-preserved">${escapeHTML(record.starts_at_local.replace('T',' · '))} · ${record.party_size} guests · ${record.accepted_terms.reservation_duration_minutes} minutes · Policy ${record.accepted_terms.policy_version} preserved</p><details><summary>View preserved accepted terms</summary>${termsHTML(record.accepted_terms,restaurant)}</details></article>`;}).join('') || '<div class="empty">No existing bookings overlap this closure. Applying still closes the selected table.</div>'}</div><div class="apply-bar"><p class="small-note">Applying closes ${escapeHTML(tableLabels(restaurant,[plan.closure.table_id]))} and saves all seating changes together. If bookings changed after this preview, you must preview again.</p><button class="primary" data-testid="replan-apply">Apply seating repair</button></div><div class="apply-feedback"></div></section>`;
    previewMount.querySelector('[data-testid="replan-apply"]').onclick=apply;
  }
  async function apply() {
    if(pending || !plan)return;pending=true;
    const button=previewMount.querySelector('[data-testid="replan-apply"]'),applyMessages=previewMount.querySelector('.apply-feedback');clearFeedback(applyMessages);
    const controls=[...form.querySelectorAll('input,select,button'),button];controls.forEach(c=>c.disabled=true);button.textContent='Applying all changes…';
    let applied=false,stale=false;
    try {
      const result=await api(`/restaurants/${encodeURIComponent(restaurant.id)}/replans/${encodeURIComponent(plan.plan_id)}/apply`,{method:'POST',body:{},key:applyKey});
      applied=true;previewMount.querySelector('.section-heading .status').textContent='Applied';
      feedback(applyMessages,'replan-success',`Seating repaired. ${result.reservations.length} bookings kept their promises. The closure and all table changes are saved together.`,'success');
    } catch(error) {
      stale=error instanceof Refusal && error.code==='stale_plan';
      const text=stale?'The restaurant changed after this preview. Nothing from this attempt was applied. Preview again to review a fresh safe plan.':error.code==='plan_already_applied'?'This plan has already been applied. Create a new preview for the current restaurant state.':error instanceof Refusal?friendly(error):'The apply response was lost. The repair may already be saved. Retry applying this unchanged plan to recover the original result safely.';
      feedback(applyMessages,error instanceof Refusal?'replan-error':'replan-uncertain',text,error instanceof Refusal?'error':'uncertain');
      if(stale || error.code==='plan_already_applied') {
        stale=true;const again=document.createElement('button');again.className='secondary';again.dataset.testid='replan-refresh';again.textContent='Preview again';
        again.onclick=()=>{previewRequest=null;applyKey=null;plan=null;form.requestSubmit();};applyMessages.append(again);
      }
    } finally {pending=false;controls.forEach(c=>c.disabled=false);button.disabled=applied||stale;button.textContent=applied?'Seating repair applied':stale?'New preview needed':'Apply seating repair';}
  }
}

function enhanceSeries(initial,card) {
  const section=document.createElement('section');section.className='series-amend-panel';card.append(section);
  let current=initial,request=null,pending=false;
  section.innerHTML=`<h3>A new time for your regular evenings</h3><p class="small-note">Keep the original scheduled dates and tables. Cancelled and individually changed visits are skipped. Each changed visit adopts the policy for its own date.</p><form class="compact-form" data-testid="series-amend-form"><div><label for="from-${escapeHTML(initial.series_id)}">Start with visit</label><select id="from-${escapeHTML(initial.series_id)}" data-testid="series-from-index">${initial.occurrences.map(o=>`<option value="${o.index}">Visit ${o.index+1} · ${escapeHTML(o.reservation.starts_at_local.slice(0,10))}</option>`).join('')}</select></div><div><label for="time-${escapeHTML(initial.series_id)}">New local arrival time</label><input id="time-${escapeHTML(initial.series_id)}" type="time" value="${initial.occurrences[0].reservation.starts_at_local.slice(11,16)}" data-testid="series-local-time" required></div><button class="primary" data-testid="series-amend-submit">Update eligible visits</button></form><div class="eligibility" data-testid="series-eligibility"></div><div class="series-amend-feedback"></div><button class="quiet-button" data-testid="series-refresh">Refresh agreement</button>`;
  const form=section.querySelector('form'), from=form.querySelector('select'), time=form.querySelector('input'), messages=section.querySelector('.series-amend-feedback'), refresh=section.querySelector('[data-testid="series-refresh"]');
  function eligibility() {
    const start=Number(from.value);
    section.querySelector('.eligibility').innerHTML=`<p class="small-note">Using agreement revision <strong>${current.revision}</strong></p><ul class="plain-list">${current.occurrences.map(o=>`<li><strong>Visit ${o.index+1}</strong> · ${o.index<start?'Unchanged: before selected visit':o.reservation.status==='cancelled'?'Skipped: cancelled':o.exception?'Skipped: individually changed':'Eligible for the new time'}</li>`).join('')}</ul>`;
  }
  from.onchange=eligibility;eligibility();
  refresh.onclick=async()=>{
    if(pending) return;refresh.disabled=true;clearFeedback(messages);
    try { current=await api(`/series/${encodeURIComponent(current.series_id)}`);request=null;eligibility();feedback(messages,'series-refreshed','Agreement refreshed. Review the eligible visits before submitting.','success'); }
    catch(error) {feedback(messages,'series-amend-error',error instanceof Refusal?friendly(error):'The agreement could not be refreshed. Try again.');}
    finally {refresh.disabled=false;}
  };
  form.onsubmit=async event=>{
    event.preventDefault();if(pending)return;
    const body={expected_revision:current.revision,from_index:Number(from.value),local_time:time.value};
    const signature=JSON.stringify(body);
    if(!request || request.signature!==signature)request={signature,body,key:newKey()};
    pending=true;clearFeedback(messages);const controls=[...form.querySelectorAll('input,select,button'),refresh];controls.forEach(c=>c.disabled=true);
    try {
      const result=await api(`/series/${encodeURIComponent(current.series_id)}/amend`,{method:'POST',body:request.body,key:request.key});
      feedback(messages,'series-amend-success',`Agreement updated to revision ${result.revision}. All eligible changes were saved together. Cancelled and individually changed visits were preserved.`,'success');
      const link=document.createElement('a');link.href=`/series?series_id=${encodeURIComponent(current.series_id)}`;link.textContent='View updated visits →';messages.append(link);
      await seriesScreen();
      feedback(document.querySelector('#series-content'),'series-amend-success',`Agreement updated to revision ${result.revision}. The visits below have been refreshed.`,'success');
    } catch(error) {
      const stale=error instanceof Refusal && error.code==='stale_revision';
      const message=stale?'This agreement changed since you opened it. Refresh the agreement, review eligible visits, then try again.':error.code==='table_unavailable'?'At least one visit conflicts with another booking or a closed table. No visits changed. Choose another arrival time.':error.code==='cutoff_passed'?'At least one eligible visit is too close to its arrival time to change. No visits changed. Choose a later starting visit.':error instanceof Refusal?friendly(error):'The response was lost. Retry unchanged to recover this same amendment safely.';
      feedback(messages,error instanceof Refusal?'series-amend-error':'series-amend-uncertain',message,error instanceof Refusal?'error':'uncertain');
    } finally {pending=false;controls.forEach(c=>c.disabled=false);}
  };
}
