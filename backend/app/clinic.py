"""Панель клиники: воронка пациентов на СИНТЕТИЧЕСКИХ данных лучевой диагностики.

Маршруты пациентов строятся настоящим планировщиком (по графу рекомендаций КТ/маммографии),
а статусы шагов (сделан / ожидает / просрочен) симулируются.
"""
import random
from datetime import date, timedelta

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.planner import build_plan
from app.rules.engine import load_steps
from app.schemas import ClinicFunnel, ImagingFinding, PatientState

router = APIRouter()

N_PATIENTS = 150
_DATA: list[dict] | None = None


# ---------- синтетика ----------

def _finding(
    modality: str,
    finding_text: str,
    bi_rads: str | None = None,
    organ: str | None = None,
    days_ago: int = 5,
) -> ImagingFinding:
    return ImagingFinding(
        modality=modality,
        finding=finding_text,
        bi_rads=bi_rads,
        organ=organ,
        taken_on=date.today() - timedelta(days=days_ago),
    )


def _make_patient(rng: random.Random, i: int) -> PatientState:
    sex = rng.choice(["f", "f", "f", "m"])
    age = rng.randint(25, 75)
    days = rng.randint(1, 40)
    kind = rng.random()
    findings: list[ImagingFinding] = []

    if kind < 0.30 and sex == "f":
        # Высокий риск oncology/BI-RADS 4/5 (Маммография)
        bi_rads = rng.choice(["BI-RADS 4", "BI-RADS 5"])
        findings.append(
            _finding(
                modality="Mammography",
                finding_text="Узловое образование с нечёткими контурами",
                bi_rads=bi_rads,
                organ="молочная железа",
                days_ago=days,
            )
        )
    elif kind < 0.55:
        # Очаговые изменения лёгких (КТ ОГК)
        findings.append(
            _finding(
                modality="CT",
                finding_text="Очаговое образование верхней доли правого лёгкого > 6 мм",
                organ="лёгкие",
                days_ago=days,
            )
        )
    elif kind < 0.75:
        # Патология по рентгенографии (инфильтрат / пневмония)
        findings.append(
            _finding(
                modality="X-ray",
                finding_text="Участки инфильтрации в нижней доле левого лёгкого",
                organ="лёгкие",
                days_ago=days,
            )
        )
    else:
        # Без патологии / Норма (BI-RADS 1 или 2)
        if sex == "f":
            findings.append(
                _finding(
                    modality="Mammography",
                    finding_text="Без патологических изменений",
                    bi_rads="BI-RADS 1",
                    organ="молочная железа",
                    days_ago=days,
                )
            )
        else:
            findings.append(
                _finding(
                    modality="X-ray",
                    finding_text="Легочные поля без очаговых и инфильтративных теней",
                    organ="лёгкие",
                    days_ago=days,
                )
            )

    return PatientState(
        patient_id=f"syn_{i}",
        sex=sex,
        age=age,
        complaints=[],
        findings=findings,
    )


def _status(rng: random.Random, zone: str) -> str:
    r = rng.random()
    if zone == "now":
        return "done" if r < 0.7 else "overdue"
    if zone == "two_weeks":
        return "done" if r < 0.45 else ("overdue" if r < 0.8 else "planned")
    return "done" if r < 0.15 else "planned"


def _data() -> list[dict]:
    """Генерируется один раз, числа стабильны (seed=42)."""
    global _DATA
    if _DATA is None:
        rng = random.Random(42)
        data = []
        for i in range(1, N_PATIENTS + 1):
            state = _make_patient(rng, i)
            plan = build_plan(state)
            active = [s for s in plan.steps if not s.skipped_reason]
            data.append({"n": i, "steps": {s.id: _status(rng, s.zone) for s in active}})
        _DATA = data
    return _DATA


# ---------- расчёт ----------

def compute_funnel() -> ClinicFunnel:
    data = _data()
    titles = {sid: meta["title"] for sid, meta in load_steps().items()}
    with_plan = [p for p in data if p["steps"]]

    by_step: dict[str, dict[str, int]] = {}
    for p in with_plan:
        for sid, st in p["steps"].items():
            by_step.setdefault(sid, {"planned": 0, "done": 0, "overdue": 0})[st] += 1
    by_step = dict(sorted(by_step.items(), key=lambda kv: -kv[1]["overdue"]))

    stuck = []
    for p in with_plan:
        for sid, st in p["steps"].items():
            if st == "overdue":
                stuck.append(
                    {
                        "patient": f"Пациент №{p['n']:03d}",
                        "step_id": sid,
                        "step": titles.get(sid, sid),
                    }
                )
    stuck = stuck[:15]

    return ClinicFunnel(
        total_patients=len(data),
        got_plan=len(with_plan),
        reached_next_step=sum(1 for p in with_plan if "done" in p["steps"].values()),
        overdue_patients=sum(1 for p in with_plan if "overdue" in p["steps"].values()),
        by_step=by_step,
        step_titles=titles,
        stuck=stuck,
    )


# ---------- эндпоинты ----------

@router.get("/clinic/funnel", response_model=ClinicFunnel)
def clinic_funnel():
    return compute_funnel()


@router.post("/clinic/remind")
def clinic_remind(step_id: str):
    """Демо: сообщения не отправляются, считаем, кому они ушли бы."""
    titles = {sid: meta["title"] for sid, meta in load_steps().items()}
    count = sum(1 for p in _data() if p["steps"].get(step_id) == "overdue")
    return {
        "sent": count,
        "step": titles.get(step_id, step_id),
        "note": "Демо: сообщения не отправляются, это расчёт на синтетических данных лучевой диагностики.",
    }


PAGE = """<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>Третье Мнение: Панель маршрутизации клиники</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
 body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f5f7fa;color:#1f2937}
 .wrap{max-width:1000px;margin:0 auto;padding:24px}
 h1{margin:0 0 4px} .sub{color:#6b7280;margin-bottom:16px}
 .banner{background:#e0f2fe;border:1px solid #7dd3fc;border-radius:8px;padding:10px 14px;margin-bottom:20px;font-size:14px;color:#0369a1}
 .cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:24px}
 .card{background:#fff;border-radius:10px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
 .num{font-size:32px;font-weight:700} .lbl{color:#6b7280;font-size:14px}
 table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08)}
 th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #eef0f3;font-size:14px;vertical-align:middle}
 .bar{display:flex;height:14px;border-radius:7px;overflow:hidden;background:#e5e7eb;min-width:180px}
 .done{background:#22c55e} .overdue{background:#ef4444} .planned{background:#9ca3af}
 .legend span{display:inline-block;margin-right:14px;font-size:13px}
 .dot{display:inline-block;width:10px;height:10px;border-radius:5px;margin-right:5px}
 button{background:#2563eb;color:#fff;border:0;border-radius:6px;padding:6px 10px;cursor:pointer;font-size:13px}
 button:hover{background:#1d4ed8}
 h2{margin:28px 0 10px;font-size:18px}
 ul{background:#fff;border-radius:10px;padding:12px 28px;box-shadow:0 1px 3px rgba(0,0,0,.08);font-size:14px}
</style></head><body><div class="wrap">
<h1>Панель маршрутизации («Третье Мнение»)</h1>
<div class="sub">Маршруты пациентов после КТ, маммографии и рентгенографии</div>
<div class="banner">Демо на синтетических данных лучевой диагностики. Маршруты строятся по клиническим рекомендациям, статусы шагов смоделированы.</div>
<div class="cards" id="cards"></div>
<div class="legend"><span><i class="dot done"></i>выполнено</span><span><i class="dot overdue"></i>просрочено</span><span><i class="dot planned"></i>запланировано</span></div>
<h2>Где пациенты «утекают» после обследований</h2>
<table id="steps"><thead><tr><th>Шаг маршрута</th><th>Статусы</th><th>Просрочили</th><th>Действие</th></tr></thead><tbody></tbody></table>
<h2>Пациенты с просроченными повторными визитами</h2>
<ul id="stuck"></ul>
</div>
<script>
function el(tag, cls, text){const e=document.createElement(tag); if(cls)e.className=cls; if(text!==undefined)e.textContent=text; return e;}
async function load(){
  const d = await (await fetch('/clinic/funnel')).json();
  const pct = (a,b)=> b? Math.round(100*a/b)+'%' : '0%';
  const cards = document.getElementById('cards');
  [[d.got_plan, 'получили маршрут (из '+d.total_patients+')'],
   [pct(d.reached_next_step,d.got_plan), 'сделали хотя бы один шаг'],
   [pct(d.overdue_patients,d.got_plan), 'просрочили хотя бы один шаг']].forEach(([n,l])=>{
    const c=el('div','card'); c.appendChild(el('div','num',String(n))); c.appendChild(el('div','lbl',l)); cards.appendChild(c);
  });
  const tb = document.querySelector('#steps tbody');
  Object.entries(d.by_step).forEach(([sid,s])=>{
    const total=s.done+s.overdue+s.planned;
    const tr=el('tr');
    tr.appendChild(el('td','',d.step_titles[sid]||sid));
    const td=el('td'); const bar=el('div','bar');
    ['done','overdue','planned'].forEach(k=>{const seg=el('div',k); seg.style.width=(100*s[k]/total)+'%'; seg.title=k+': '+s[k]; bar.appendChild(seg);});
    td.appendChild(bar); tr.appendChild(td);
    tr.appendChild(el('td','',s.overdue+' из '+total));
    const tdb=el('td');
    if(s.overdue>0){const b=el('button','','Напомнить'); b.onclick=async()=>{
      const r=await (await fetch('/clinic/remind?step_id='+encodeURIComponent(sid),{method:'POST'})).json();
      alert('Напоминание ушло бы '+r.sent+' пациентам: '+r.step+'\\n'+r.note);}; tdb.appendChild(b);}
    tr.appendChild(tdb); tb.appendChild(tr);
  });
  const ul=document.getElementById('stuck');
  d.stuck.forEach(s=>ul.appendChild(el('li','',s.patient+': '+s.step)));
}
load();
</script></body></html>"""


@router.get("/clinic", response_class=HTMLResponse)
def clinic_page():
    return PAGE