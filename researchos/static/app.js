'use strict';
const $ = s => document.querySelector(s);
let records = [], selected;
const states = ['GENERATED','UNVERIFIED','SUPPORTED','ADVERSARIAL_TEST','REPRODUCED','VALIDATED','STABLE','ASSURED'];
function el(tag, text, cls) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if(cls) n.className=cls; return n; }
function message(text, error=false) { $('#message').textContent=text; $('#message').className=error?'error':'notice'; }
async function api(path, data) {
  const response = await fetch('/api/'+path,{method:data?'POST':'GET',headers:{'Authorization':'Bearer '+$('#token').value,'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined});
  const result=await response.json();
  if(!response.ok) throw new Error(result.error || (result.reasons||[]).join('; ') || 'Request failed');
  return result;
}
async function refresh() {
  records=await api('claims'); $('#connection').textContent='Connected · '+records.length+' claims';
  const stats=$('#stats'); stats.replaceChildren();
  for(const [name,value] of [['REGISTERED',records.length],['ASSURED',records.filter(r=>r.claim.state==='ASSURED').length],['CONTESTED',records.filter(r=>r.claim.state==='CONTESTED').length],['OPEN CHALLENGES',records.reduce((n,r)=>n+r.metrics.open_challenges,0)]]) { const card=el('div');card.append(el('strong',String(value)),el('small',name));stats.append(card); }
  list(); if(selected && records.some(r=>r.claim.id===selected)) render();
}
function list() {
  const parent=$('#claims');parent.replaceChildren();
  const filtered=records.filter(r=>r.claim.statement.toLowerCase().includes($('#search').value.toLowerCase()));
  if(!filtered.length) parent.append(el('p','No claims found.'));
  for(const {claim:c} of filtered) { const button=el('button',undefined,'claim '+(selected===c.id?'active':''));button.append(el('small',c.state),el('span',c.statement));button.onclick=()=>{selected=c.id;list();render();};parent.append(button); }
}
function field(form,name,label,type='text',options) {
  const wrap=el('label',label); let input;
  if(options) {input=el('select');for(const value of options){const o=el('option',value);o.value=value;input.append(o);}}
  else input=el(type==='textarea'?'textarea':'input');
  if(type!=='textarea'&&!options) input.type=type;
  input.name=name; input.required=true;
  if(type==='number'){input.min='0';input.max='1';input.step='0.01';input.value='1';}
  wrap.append(input);form.append(wrap);return input;
}
function actionForm(title,kind,fields) {
  const details=el('details');details.append(el('summary',title));const form=el('form');
  for(const f of fields) field(form,...f);
  form.append(el('button','Save record'));
  form.onsubmit=async e=>{e.preventDefault();const data=Object.fromEntries(new FormData(form));for(const f of fields)if(f[2]==='number')data[f[0]]=Number(data[f[0]]);await perform(()=>api('claims/'+selected+'/'+kind,data));};
  details.append(form);return details;
}
async function perform(fn){try{await fn();await refresh();message('Record saved.');}catch(e){message(e.message,true);}}
function render() {
  const {claim:c,metrics:m}=records.find(r=>r.claim.id===selected);const d=$('#detail');d.replaceChildren();
  d.append(el('p',c.id+' · VERSION '+c.version,'eyebrow'),el('h2',c.statement));
  const rail=el('div',undefined,'rail');for(const state of states)rail.append(el('span',state.replaceAll('_',' '),state===c.state?'current':''));d.append(rail);
  if(c.state==='CONTESTED')d.append(el('p','CONTESTED — resolve challenges and revisit the evidence.','error'));
  d.append(el('p','Provenance: '+c.provenance),el('p','Source groups: '+m.effective_source_groups+' · Validation density: '+m.validation_density.toFixed(3)+' · Open challenges: '+m.open_challenges));
  const tools=el('div',undefined,'tools'); const next=c.state==='CONTESTED'?'UNVERIFIED':states[states.indexOf(c.state)+1];
  if(next){const b=el('button','Request '+next.replaceAll('_',' '));b.onclick=()=>perform(()=>api('claims/'+c.id+'/transition',{target:next}));tools.append(b);}
  const attack=el('button','Run structural attacks','secondary');attack.onclick=()=>perform(()=>api('claims/'+c.id+'/attacks',{}));tools.append(attack);
  const exportButton=el('button','Export assurance JSON','secondary');exportButton.onclick=async()=>{try{const record=await api('claims/'+c.id+'/assurance');const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download='assurance-'+c.id+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){message(e.message,true);}};tools.append(exportButton);d.append(tools);
  const sections=[['Evidence',c.evidence.map(x=>x.source+' · '+x.method+' · '+x.result+' [group: '+x.source_group+']')],['Validation & reproduction',c.checks.map(x=>x.kind+(x.attack?' / '+x.attack:'')+' · '+x.outcome+' · v'+x.version+' · '+x.method)],['Challenges',c.challenges.map(x=>x.id+' · '+x.attack+' · '+(x.resolved?'RESOLVED: '+x.resolution:x.detail))],['Dependencies',c.dependencies]];
  for(const [title,rows] of sections){d.append(el('h3',title));const ul=el('ul');if(!rows.length)ul.append(el('li','No records yet.'));for(const row of rows)ul.append(el('li',row));d.append(ul);}
  d.append(actionForm('Attach evidence','evidence',[['source','Source'],['source_group','Independent origin group'],['method','Method'],['result','Result','textarea'],['quality','Quality','number'],['reliability','Reliability','number'],['independence','Independence estimate','number']]));
  d.append(actionForm('Record a check','check',[['kind','Check type','text',['validation','reproduction','adversarial']],['outcome','Outcome','text',['PASS','FAIL','UNCERTAIN']],['attack','Attack class (used for adversarial checks)','text',['contradiction','assumption_violation','source_poisoning']],['method','Method / result reference'],['runner','Independent executor'],['source_group','Executor origin group']]));
  d.append(actionForm('Open a challenge','challenge',[['attack','Attack class','text',['contradiction','assumption_violation','source_poisoning']],['detail','Challenge detail','textarea']]));
  d.append(actionForm('Resolve a challenge','resolve',[['challenge_id','Challenge ID'],['resolution','Resolution and evidence reference','textarea']]));
  d.append(actionForm('Add dependency','dependency',[['claim_id','Upstream claim ID']]));
  d.append(el('p','Checks are reviewer attestations; structural screens do not establish semantic correctness. Evidence changes invalidate previous checks.','muted'));
}
$('#connect').onclick=()=>refresh().then(()=>message('Connected.')).catch(e=>message(e.message,true));
$('#search').oninput=list;
$('#create').onsubmit=async e=>{e.preventDefault();const form=e.target;const data=Object.fromEntries(new FormData(form));data.critical=form.elements.critical.checked;await perform(async()=>{const c=await api('claims',data);selected=c.id;form.reset();});};
