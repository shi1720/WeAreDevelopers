/* Recovery boundary tests. Real restart/browser coverage is separate. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const crypto=require('node:crypto').webcrypto;
const values=new Map();
const storage={getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v),removeItem:k=>values.delete(k)};
const context=vm.createContext({console,crypto,localStorage:storage,document:{querySelector:()=>({})},URLSearchParams,Intl,Date});
for(const file of ['app.js','operations.js']){
  const source=fs.readFileSync(path.join(__dirname,'../static',file),'utf8').replace(/\nboot\(\);\s*$/,'');
  vm.runInContext(source,context);
}
vm.runInContext("renderPending=()=>{}; session={user_id:'guest',account_scope:'namespace-one:guest'};sessionInfo={csrf_token:'ephemeral-csrf'}",context);
const run=source=>vm.runInContext(source,context);
let checks=0;
const ok=(value)=>{assert.ok(value);checks++;};
(async()=>{
  context.fetch=async(url,options)=>{
    const pending=JSON.parse(storage.getItem('tablekeeper.pending.v1.namespace-one:guest'));
    assert.equal(pending.body.party_size,2); // Durable before network starts.
    assert.equal(options.credentials,'same-origin');
    assert.equal(options.headers['X-CSRF-Token'],'ephemeral-csrf');
    assert.equal(options.headers.Authorization,undefined);
    throw new Error('lost after commit');
  };
  await assert.rejects(run("api('/reservations',{method:'POST',body:{party_size:2},key:'original-key'})"));checks++;
  let pending=JSON.parse(storage.getItem('tablekeeper.pending.v1.namespace-one:guest'));
  ok(pending.key==='original-key');
  ok(!JSON.stringify(pending).includes('csrf'));
  await assert.rejects(run("api('/reservations',{method:'POST',body:{party_size:3},key:'new-key'})"),e=>e.code==='pending_recovery');checks++;
  ok(JSON.parse(storage.getItem('tablekeeper.pending.v1.namespace-one:guest')).key==='original-key');
  run("session={user_id:'guest',account_scope:'namespace-two:guest'}");
  ok(run('readPending()')===null);
  run("session={user_id:'guest',account_scope:'namespace-one:guest'}");
  context.fetch=async(url,options)=>{
    assert.equal(options.headers['Idempotency-Key'],'original-key');
    assert.equal(options.body,'{"party_size":2}');
    return {ok:true,status:201,json:async()=>({reference:'ORIGINAL'})};
  };
  const result=await run("api('/reservations',{method:'POST',body:{party_size:2},key:'ignored-new-key'})");
  ok(result.reference==='ORIGINAL');
  ok(run('readPending()')===null);
  context.fetch=async()=>({ok:false,status:503,json:async()=>({error:{code:'store_busy'}})});
  await assert.rejects(run("api('/reservations/ORIGINAL',{method:'PATCH',body:{expected_revision:1,party_size:3},key:'edit-key'})"));checks++;
  ok(run('readPending().key')==='edit-key');
  context.fetch=async()=>({ok:false,status:409,json:async()=>({error:{code:'stale_revision'}})});
  await assert.rejects(run("api('/reservations/ORIGINAL',{method:'PATCH',body:{expected_revision:1,party_size:3},key:'edit-key'})"));checks++;
  ok(run('readPending()')===null);
  const original=storage.setItem;
  storage.setItem=()=>{throw new Error('quota');};
  let called=false;context.fetch=()=>{called=true;throw new Error('should not send');};
  await assert.rejects(run("api('/series',{method:'POST',body:{count:2},key:'series-key'})"));checks++;
  ok(!called);storage.setItem=original;
  storage.setItem('tablekeeper.pending.v1.namespace-one:guest','invalid JSON');
  await assert.rejects(run("api('/series',{method:'POST',body:{count:2},key:'series-key'})"));checks++;
  ok(!called);
  console.log(`${checks} recovery checks passed`);
})().catch(error=>{console.error(error);process.exitCode=1;});
