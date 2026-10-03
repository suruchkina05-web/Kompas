# app/site.py
"""Сайт пациента «Компас»: одна страница, открывается по адресу /app."""
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

PAGE = """<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>Компас: маршрут пациента по результатам лучевой диагностики</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
 :root{--ink:#1e2a3a;--mut:#667085;--line:#e6eaf0;--bg:#f4f6fb;--brand:#4f46e5;--brand2:#06b6d4;--ok:#16a34a;--warn:#f59e0b;--bad:#dc2626}
 *{box-sizing:border-box} body{margin:0;font-family:-apple-system,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--ink);line-height:1.5}
 header{background:linear-gradient(120deg,var(--brand),var(--brand2));color:#fff;padding:28px 20px}
 header .in{max-width:900px;margin:0 auto} header h1{margin:0;font-size:30px} header p{margin:6px 0 0;opacity:.92}
 .wrap{max-width:900px;margin:0 auto;padding:20px}
 .card{background:#fff;border-radius:14px;padding:20px;margin-bottom:18px;box-shadow:0 2px 10px rgba(30,42,58,.06)}
 h2{margin:0 0 10px;font-size:19px} h3{margin:18px 0 8px;font-size:16px}
 textarea{width:100%;min-height:96px;border:1px solid var(--line);border-radius:10px;padding:12px;font:inherit;resize:vertical}
 .row{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;align-items:center}
 button{border:0;border-radius:10px;padding:10px 16px;font:inherit;font-weight:600;cursor:pointer;background:var(--brand);color:#fff}
 button:hover{filter:brightness(1.08)} button:disabled{opacity:.6;cursor:wait}
 button.ghost{background:#eef0ff;color:var(--brand)} button.plain{background:#f1f3f7;color:var(--ink)}
 .err{color:var(--bad);margin-top:8px;min-height:1em}
 .hint{color:var(--mut);font-size:13px}
 .state{background:#f7f8ff;border-radius:10px;padding:10px 14px;margin-bottom:14px;font-size:14px}
 .flags{border:2px solid #fecaca;background:#fff5f5;border-radius:12px;padding:14px 18px;margin-bottom:16px}
 .flags b{color:var(--bad)} .flags ul{margin:8px 0 0;padding-left:20px}
 .zone{margin-top:20px} .zone .zt{font-weight:700;font-size:16px;margin-bottom:8px}
 .zt.now{color:var(--bad)} .zt.two_weeks{color:#b45309} .zt.planned{color:var(--mut)}
 .step{border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:10px;background:#fff}
 .step.new{border-color:var(--ok);box-shadow:0 0 0 3px #dcfce7}
 .sh{display:flex;gap:10px;align-items:flex-start} .sh b{flex:1}
 .ico{font-size:20px} .why{margin:8px 0 0;color:#344054}
 .badge{font-size:12px;padding:3px 9px;border-radius:99px;background:#eef2ff;color:var(--brand);white-space:nowrap}
 .badge.doctor_decides{background:#fff4e5;color:#b45309}
 .q{margin-top:10px;background:#f7f8ff;border-radius:10px;padding:10px 14px}
 .qt{font-weight:600;font-size:13px;color:var(--brand)} .q ul{margin:6px 0 0;padding-left:18px;font-size:14px}
 .src{margin-top:8px;font-size:12px;color:var(--mut)}
 .done{display:flex;gap:8px;color:var(--mut);font-size:14px;padding:4px 0}
 .diff{border:2px solid #bbf7d0;background:#f0fdf4;border-radius:12px;padding:14px 18px;margin-bottom:16px}
 .diff .add{color:var(--ok);font-weight:600} .diff .rem{color:var(--bad);text-decoration:line-through}
 .cols{display:grid;grid-template-columns:1fr 1fr;gap:14px} @media(max-width:700px){.cols{grid-template-columns:1fr}}
 .col{border-radius:12px;padding:14px;border:1px solid var(--line)} .col.ok{background:#f0fdf4} .col.miss{background:#fffbeb}
 .col h4{margin:0 0 8px} .col li{margin-bottom:6px;font-size:14px}
 .disc{font-size:13px;color:var(--mut);margin-top:14px}
 .busy{color:var(--mut);margin-top:8px}
 footer{max-width:900px;margin:0 auto;padding:10px 20px 40px;color:var(--mut);font-size:13px}
 .hidden{display:none}
</style></head><body>
<header><div class="in"><h1>Компас</h1><p>Персональный маршрут после КТ, маммографии и рентгенографии: что сделать, в каком порядке и что спросить у врача</p></div></header>
<div class="wrap">
 <div class="card">
  <h2>1. Ваши данные и заключения лучевой диагностики</h2>
  <textarea id="doc" placeholder="Например: Пациентка Елена, 48 лет. Маммография от 2026-09-10: BI-RADS 4, узловое образование с нечёткими контурами в левой молочной железе."></textarea>
  <div class="row">
   <button id="go">Построить маршрут</button>
   <button class="ghost" id="ex1">Пример 1: Маммография BI-RADS 4</button>
   <button class="ghost" id="ex2">Пример 2: Новое КТ ОГК</button>
   <button class="plain" id="reset">Начать заново</button>
  </div>
  <div class="hint">Добавьте новое заключение в то же поле и нажмите кнопку ещё раз: маршрут перестроится с учётом всех обследований.</div>
  <div class="busy" id="busy"></div><div class="err" id="err"></div>
 </div>

 <div id="result" class="card hidden">
  <h2>2. Ваш маршрут <span class="badge" id="ver"></span></h2>
  <div class="state" id="state"></div>
  <div id="diff"></div>
  <div id="flags"></div>
  <div id="zones"></div>
  <div id="doneBox"></div>
 </div>

 <div id="cmpCard" class="card hidden">
  <h2>3. Сверить с назначениями врача</h2>
  <div class="hint">Вставьте текст заключения или назначений врача. Сервис покажет, что совпало с маршрутом и что стоит уточнить.</div>
  <textarea id="orders" placeholder="Например: Консультация онколога-маммолога, УЗИ молочных желез, биопсия образования левой молочной железы под контролем УЗИ."></textarea>
  <div class="row"><button id="cmp">Сверить</button><button class="ghost" id="ex3">Пример назначений</button></div>
  <div class="err" id="cerr"></div>
  <div id="cmpOut"></div>
 </div>
</div>
<footer>Сервис не ставит диагнозы и не назначает лечение. Это не оценка работы врача: итоговые решения принимает клинический специалист. Маршрут построен по клиническим рекомендациям Минздрава РФ и стандартизированным шкалам (BI-RADS и др.).</footer>

<script>
const sid = 'web_' + Math.random().toString(36).slice(2, 8);
const $ = id => document.getElementById(id);
function el(t, c, x){ const e = document.createElement(t); if (c) e.className = c; if (x !== undefined) e.textContent = x; return e; }
const ICON = {lab:'🧪', visit:'🩺', imaging:'🔬', lifestyle:'🥗', urgent:'🚨', biopsy:'💉'};
const CONF = {medium:'по рекомендации', high:'по рекомендации', doctor_decides:'решает врач'};
const ZONES = [['now','Срочно'],['two_weeks','В ближайшие 2 недели'],['planned','Планово, по назначению врача']];
const EX1 = 'Пациентка Елена, 48 лет. Маммография от 2026-09-10: BI-RADS 4, узловое образование с нечёткими контурами в верхней наружной доле левой молочной железы.';
const EX2 = 'Дополнительно КТ ОГК от 2026-09-25: выявлено очаговое образование верхней доли правого лёгкого 8 мм с неровными контурами.';
const EX3 = 'Консультация онколога через 2 недели. УЗИ молочных желез и регионарных лимфоузлов. Биопсия образования левой молочной железы.';

async function api(path, body){
  const r = await fetch(path, {method:'POST', headers:{'Content-Type':'application/json'}, body: body ? JSON.stringify(body) : undefined});
  let d = {}; try { d = await r.json(); } catch(e) {}
  if (!r.ok) throw new Error(d.detail || 'Ошибка сервера');
  return d;
}

function stepCard(s, isNew){
  const c = el('div', 'step' + (isNew ? ' new' : ''));
  const h = el('div', 'sh');
  h.appendChild(el('span', 'ico', ICON[s.kind] || '🔬'));
  h.appendChild(el('b', '', s.title));
  if (isNew) h.appendChild(el('span', 'badge', 'новое'));
  h.appendChild(el('span', 'badge ' + s.confidence, CONF[s.confidence] || ''));
  c.appendChild(h);
  if (s.why) c.appendChild(el('p', 'why', s.why));
  if (s.questions_for_doctor && s.questions_for_doctor.length){
    const q = el('div', 'q'); q.appendChild(el('div', 'qt', 'Что спросить у врача'));
    const ul = el('ul'); s.questions_for_doctor.forEach(x => ul.appendChild(el('li', '', x))); q.appendChild(ul); c.appendChild(q);
  }
  if (s.sources && s.sources[0]) c.appendChild(el('div', 'src', 'Источник: ' + s.sources[0].document.split(' (')[0] + ', ' + s.sources[0].section));
  return c;
}

function render(d){
  $('result').classList.remove('hidden'); $('cmpCard').classList.remove('hidden');
  $('ver').textContent = 'версия ' + d.plan.version;
  const st = d.state;

  const findings = (st.findings || []).map(f => {
    let txt = f.modality + ': ' + f.finding;
    if (f.bi_rads) txt += ' (' + f.bi_rads + ')';
    return txt;
  }).join('; ') || 'находок лучевой диагностики нет';

  const labs = (st.labs || []).map(l => l.code + ' ' + l.value + ' ' + l.unit).join('; ');
  const details = [findings, labs].filter(Boolean).join(' | ');
  const complaintsText = (st.complaints && st.complaints.length) ? st.complaints.join(', ') : 'не указаны';

  $('state').textContent = 'Пациент: ' + (st.sex === 'f' ? 'женщина' : 'мужчина') + ', ' + st.age + ' лет. Жалобы: ' + complaintsText + '. Данные обследований: ' + details + '.';

  const newIds = new Set(d.diff ? d.diff.added.map(s => s.id) : []);
  const dv = $('diff'); dv.innerHTML = '';
  if (d.diff){
    const b = el('div', 'diff'); b.appendChild(el('b', '', 'Что изменилось в маршруте'));
    b.appendChild(el('p', '', d.diff.explanation));
    if (d.diff.added.length){ const p = el('div'); p.appendChild(el('span', 'add', 'Добавлено: ')); p.appendChild(el('span', '', d.diff.added.map(s => s.title).join('; '))); b.appendChild(p); }
    if (d.diff.removed.length){ const p = el('div'); p.appendChild(el('span', '', 'Больше не нужно: ')); p.appendChild(el('span', 'rem', d.diff.removed.map(s => s.title).join('; '))); b.appendChild(p); }
    dv.appendChild(b);
  }

  const fv = $('flags'); fv.innerHTML = '';
  if (d.plan.red_flags && d.plan.red_flags.length){
    const f = el('div', 'flags'); f.appendChild(el('b', '', 'Когда не ждать, а обращаться срочно (103 / 112):'));
    const ul = el('ul'); d.plan.red_flags.forEach(x => ul.appendChild(el('li', '', x))); f.appendChild(ul); fv.appendChild(f);
  }

  const zv = $('zones'); zv.innerHTML = '';
  const active = d.plan.steps.filter(s => !s.skipped_reason);
  ZONES.forEach(([z, label]) => {
    const items = active.filter(s => s.zone === z); if (!items.length) return;
    const box = el('div', 'zone'); box.appendChild(el('div', 'zt ' + z, label));
    items.forEach(s => box.appendChild(stepCard(s, newIds.has(s.id)))); zv.appendChild(box);
  });
  if (!active.length) zv.appendChild(el('p', 'hint', 'По вашим данным дополнительных шагов не требуется.'));

  const dn = $('doneBox'); dn.innerHTML = '';
  const skipped = d.plan.steps.filter(s => s.skipped_reason);
  if (skipped.length){
    dn.appendChild(el('h3', '', 'Уже сделано'));
    skipped.forEach(s => dn.appendChild(el('div', 'done', '✓ ' + s.title + ' (' + s.skipped_reason + ')')));
  }
  $('result').scrollIntoView({behavior:'smooth'});
}

async function build(){
  const text = $('doc').value.trim(); if (!text) return;
  $('go').disabled = true; $('busy').textContent = 'Строим маршрут, это займёт несколько секунд…'; $('err').textContent = '';
  try { render(await api('/patients/documents', {patient_id: sid, raw_text: text})); }
  catch(e){ $('err').textContent = 'Не получилось: ' + e.message; }
  finally { $('go').disabled = false; $('busy').textContent = ''; }
}

function list(title, cls, items, fmt){
  const c = el('div', 'col ' + cls); c.appendChild(el('h4', '', title));
  if (!items.length) c.appendChild(el('div', 'hint', 'Нет'));
  const ul = el('ul'); items.forEach(i => ul.appendChild(el('li', '', fmt(i)))); c.appendChild(ul); return c;
}

async function compare(){
  const text = $('orders').value.trim(); if (!text) return;
  $('cmp').disabled = true; $('cerr').textContent = '';
  try {
    const d = await api('/patients/' + sid + '/doctor-orders', {raw_text: text});
    const out = $('cmpOut'); out.innerHTML = '';
    const cols = el('div', 'cols');
    cols.appendChild(list('✅ Совпадает с маршрутом', 'ok', d.matched, s => s.title));
    cols.appendChild(list('🔎 Возможно, не хватает: обсудите с врачом', 'miss', d.possibly_missing, s => s.title));
    out.appendChild(cols);
    if (d.unclear && d.unclear.length){ out.appendChild(el('h3', '', '⚠️ Нужно уточнить')); const ul = el('ul'); d.unclear.forEach(x => ul.appendChild(el('li', '', x))); out.appendChild(ul); }
    if (d.questions_for_doctor && d.questions_for_doctor.length){ out.appendChild(el('h3', '', 'Вопросы к врачу')); const ul = el('ul'); d.questions_for_doctor.forEach(x => ul.appendChild(el('li', '', x))); out.appendChild(ul); }
    out.appendChild(el('div', 'disc', 'Это не диагноз и не оценка работы врача. Расхождения могут иметь клиническое объяснение, которое известно только врачу.'));
  } catch(e){ $('cerr').textContent = 'Не получилось: ' + e.message; }
  finally { $('cmp').disabled = false; }
}

async function reset(){
  try { await api('/patients/' + sid + '/reset'); } catch(e) {}
  $('doc').value = ''; $('orders').value = ''; $('cmpOut').innerHTML = ''; $('err').textContent = '';
  $('result').classList.add('hidden'); $('cmpCard').classList.add('hidden');
  window.scrollTo({top:0, behavior:'smooth'});
}

$('go').onclick = build; $('cmp').onclick = compare; $('reset').onclick = reset;
$('ex1').onclick = () => { $('doc').value = EX1; };
$('ex2').onclick = () => { $('doc').value = EX2; };
$('ex3').onclick = () => { $('orders').value = EX3; };
</script></body></html>"""


@router.get("/app", response_class=HTMLResponse)
def patient_site():
    return PAGE