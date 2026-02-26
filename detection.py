class IntersectionController {
  constructor() {
    // redTime here is the MINIMUM red gap (all-red clearance between phases).
    // The actual displayed red countdown for each direction =
    //   opposite side's green + opposite side's yellow + own clearance gap
    // Cycle layout (no overlap, no wasted time):
    //   [NS green] [NS yellow] [NS clearance] [EW green] [EW yellow] [EW clearance]
    //    ←————————— NS phase ——————————→      ←————————— EW phase ——————————→
    this.directions = {
      north: { id:'north', label:'NORTH', greenTime:30, yellowTime:5, clearance:0 },
      south: { id:'south', label:'SOUTH', greenTime:30, yellowTime:5, clearance:0 },
      east:  { id:'east',  label:'EAST',  greenTime:25, yellowTime:5, clearance:0 },
      west:  { id:'west',  label:'WEST',  greenTime:25, yellowTime:5, clearance:0 },
    };
    this.cycleTime  = 0;
    this.cycleCount = 0;
    this.running    = true;
    this.speed      = 1;
  }

  // ── Derived phase lengths ──
  get NSg()      { return this.directions.north.greenTime; }
  get NSy()      { return this.directions.north.yellowTime; }
  get NSc()      { return this.directions.north.clearance; }   // all-red gap after NS yellow
  get EWg()      { return this.directions.east.greenTime; }
  get EWy()      { return this.directions.east.yellowTime; }
  get EWc()      { return this.directions.east.clearance; }    // all-red gap after EW yellow
  get NSphase()  { return this.NSg + this.NSy + this.NSc; }   // total NS phase
  get EWphase()  { return this.EWg + this.EWy + this.EWc; }   // total EW phase
  get full()     { return this.NSphase + this.EWphase; }

  // What the Red countdown shows for each group:
  //   NS red = full EW phase (they wait while EW moves + clears)
  //   EW red = full NS phase (they wait while NS moves + clears)
  redOf(dir) {
    if (dir === 'north' || dir === 'south') return this.EWphase;
    return this.NSphase;
  }

  getStates(t) {
    const ct = t % this.full;

    //  Timeline positions:
    //  0 ────── NSg ────── NSg+NSy ────── NSphase ────── NSphase+EWg ────── NSphase+EWg+EWy ────── full
    //  |  NS_G  |   NS_Y  |   NS_C(gap)  |    EW_G      |     EW_Y         |    EW_C(gap)         |
    const T_NSg = this.NSg;
    const T_NSy = this.NSg + this.NSy;
    const T_NSc = this.NSphase;           // end of NS clearance = start of EW green
    const T_EWg = this.NSphase + this.EWg;
    const T_EWy = this.NSphase + this.EWg + this.EWy;
    // T_EWc = full

    let nsPhase, nsLeft, nsTotal, ewPhase, ewLeft, ewTotal;

    if (ct < T_NSg) {
      // ── NS GREEN ── EW RED (EW waits entire NS phase, countdown = T_NSc - ct)
      nsPhase = 'green';  nsLeft = T_NSg - ct;   nsTotal = this.NSg;
      ewPhase = 'red';    ewLeft = T_NSc - ct;   ewTotal = this.EWphase;

    } else if (ct < T_NSy) {
      // ── NS YELLOW ── EW RED
      nsPhase = 'yellow'; nsLeft = T_NSy - ct;           nsTotal = this.NSy;
      ewPhase = 'red';    ewLeft = T_NSc - ct;           ewTotal = this.EWphase;

    } else if (ct < T_NSc) {
      // ── NS CLEARANCE (all-red gap) ── EW RED
      // NS just finished yellow — brief all-red.
      // NS shows RED, counts down until NS goes green again next cycle = (full - ct + T_NSg) ...
      // but more usefully: how long until NS gets green = full - ct (wrap around)
      nsPhase = 'red';    nsLeft = this.full - ct;       nsTotal = this.NSphase;
      ewPhase = 'red';    ewLeft = T_NSc - ct;           ewTotal = this.EWphase;

    } else if (ct < T_EWg) {
      // ── EW GREEN ── NS RED (counting down from NSphase)
      // NS red countdown = time until NS gets green = full - ct
      nsPhase = 'red';    nsLeft = this.full - ct;       nsTotal = this.NSphase;
      ewPhase = 'green';  ewLeft = T_EWg - ct;           ewTotal = this.EWg;

    } else if (ct < T_EWy) {
      // ── EW YELLOW ── NS RED
      nsPhase = 'red';    nsLeft = this.full - ct;       nsTotal = this.NSphase;
      ewPhase = 'yellow'; ewLeft = T_EWy - ct;           ewTotal = this.EWy;

    } else {
      // ── EW CLEARANCE (all-red gap) ── NS RED
      nsPhase = 'red';    nsLeft = this.full - ct;       nsTotal = this.NSphase;
      ewPhase = 'red';    ewLeft = this.full - ct;       ewTotal = this.EWphase;
    }

    return {
      north: { phase:nsPhase, timeLeft:Math.max(0,nsLeft), total:nsTotal },
      south: { phase:nsPhase, timeLeft:Math.max(0,nsLeft), total:nsTotal },
      east:  { phase:ewPhase, timeLeft:Math.max(0,ewLeft), total:ewTotal },
      west:  { phase:ewPhase, timeLeft:Math.max(0,ewLeft), total:ewTotal },
    };
  }

  tick(dt) {
    if (!this.running) return;
    dt *= this.speed;
    const prev = this.cycleTime;
    this.cycleTime = (this.cycleTime + dt) % this.full;
    if (this.cycleTime < prev) {
      this.cycleCount++;
      addLog(`Cycle ${this.cycleCount} started`);
    }
  }
}

// ================================================================
// EMERGENCY STATE
// 'off' | 'alert' | 'confirm'
// This will later be driven by your external system feed.
// To connect: call  setEmergency('alert')  or  setEmergency('confirm')
//             from your incoming data handler.
// ================================================================
let emergencyState = 'off';

// ── This is the hook your system will call ──
// Example: when your server sends a message, call setEmergency('confirm')
function setEmergency(state) {
  emergencyState = state;
  updateEmergencyUI();
  const msg = state === 'confirm' ? '🚨 EV CONFIRMED arriving!' : state === 'alert' ? '⚠ EV ALERT received from system' : 'Emergency cleared — back to normal';
  addLog(msg, state === 'confirm' ? 'emrg' : state === 'alert' ? 'alert' : '');

  // highlight the correct button
  document.querySelectorAll('.emrg-btn').forEach(b => b.classList.remove('selected'));
  if(state==='off')     document.getElementById('ebOff').classList.add('selected');
  if(state==='alert')   document.getElementById('ebAlert').classList.add('selected');
  if(state==='confirm') document.getElementById('ebConfirm').classList.add('selected');
}

function updateEmergencyUI() {
  const s = emergencyState;

  // Big light
  const bl = document.getElementById('emrgBigLight');
  bl.className = 'emrg-big-light ' + (s==='confirm'?'el-confirm':s==='alert'?'el-alert':'el-off');

  // Panel border
  const panel = document.getElementById('emrgPanel');
  panel.className = 'emrg-panel' + (s==='confirm'?' state-confirm':s==='alert'?' state-alert':'');

  // State label
  const sl = document.getElementById('emrgStateLabel');
  sl.className = 'emrg-state-label' + (s==='confirm'?' sl-confirm':s==='alert'?' sl-alert':'');
  sl.textContent = s==='confirm'?'STATE: CONFIRMED':s==='alert'?'STATE: ALERT':'STATE: OFF';

  // Title + desc
  document.getElementById('emrgTitle').textContent =
    s==='confirm'?'EV CONFIRMED ARRIVING':s==='alert'?'SYSTEM ALERT':'NO EMERGENCY';
  document.getElementById('emrgDesc').textContent =
    s==='confirm'?'Emergency vehicle approaching. All signals updated.':
    s==='alert'  ?'Alert received from system. Monitoring approach.':
                  'System standing by. Waiting for input from external source.';

  // Header pill
  const pill = document.getElementById('emrgPill');
  pill.className = 'emrg-pill' + (s==='confirm'?' confirm':s==='alert'?' alert':'');
  pill.textContent = s==='confirm'?'🚨 EV: CONFIRMED':s==='alert'?'⚠ EV: ALERT':'🟣 EMRG: OFF';

  // Banner
  const banner = document.getElementById('emrgBanner');
  banner.className = 'emrg-banner' + (s!=='off'?' show':'') + (s==='confirm'?' confirm':s==='alert'?' alert':'');
  document.getElementById('emrgBannerIcon').textContent  = s==='confirm'?'🚨':'⚠';
  document.getElementById('emrgBannerText').textContent  = s==='confirm'?'EMERGENCY VEHICLE CONFIRMED — APPROACHING INTERSECTION':'SYSTEM ALERT: POSSIBLE EMERGENCY VEHICLE DETECTED';

  // Update all 4 purple bulbs
  DIRS.forEach(dir => updatePurpleBulb(dir));

  // Update housing border colour
  DIRS.forEach(dir => {
    const h = document.getElementById(`tl-${dir}`);
    h.classList.remove('emrg-active-confirm','emrg-active-alert');
    if(s==='confirm') h.classList.add('emrg-active-confirm');
    else if(s==='alert') h.classList.add('emrg-active-alert');
  });
}

function updatePurpleBulb(dir) {
  const el = document.getElementById(`b-${dir}-p`);
  if(!el) return;
  const s = emergencyState;
  el.className = `bulb ${s==='confirm'?'p-confirm':s==='alert'?'p-alert':'p-off'}`;
}

// ================================================================
// GLOBALS
// ================================================================
const ctrl = new IntersectionController();
const DIRS = ['north','south','east','west'];
const CM   = { green:'#00ff7f', yellow:'#ffcc00', red:'#ff3040' };
const CIRC = 2 * Math.PI * 55; // 345.4
let lastTs = null, t0 = Date.now(), editDir = 'NS', prevSec = {};

// ── BULBS ──
function updateBulbs(dir, phase) {
  document.getElementById(`b-${dir}-r`).className = `bulb ${phase==='red'   ?'r-on':'r-off'}`;
  document.getElementById(`b-${dir}-y`).className = `bulb ${phase==='yellow'?'y-on':'y-off'}`;
  document.getElementById(`b-${dir}-g`).className = `bulb ${phase==='green' ?'g-on':'g-off'}`;
  updatePurpleBulb(dir); // always keep purple in sync

  // housing glow (only set if not overridden by emergency)
  const h = document.getElementById(`tl-${dir}`);
  if(emergencyState === 'off') {
    h.classList.remove('emrg-active-confirm','emrg-active-alert');
    h.classList.toggle('active', phase==='green');
  }
}

// ── COUNTDOWN DISPLAY ──
function updateCountdown(dir, phase, timeLeft) {
  const box = document.getElementById(`cd-${dir}`);
  const num = document.getElementById(`cdn-${dir}`);
  const lbl = document.getElementById(`cdl-${dir}`);
  const s   = Math.ceil(timeLeft);

  box.className = `countdown-display cd-${phase}`;
  num.className = `cd-number cd-${phase}-col`;
  lbl.className = `cd-label  cd-${phase}-col`;

  // Flip animation on tick
  if(prevSec[dir] !== s) {
    num.classList.add('num-flip');
    setTimeout(()=>num.classList.remove('num-flip'), 250);
    prevSec[dir] = s;
  }
  num.textContent = (s < 10 ? '0' : '') + s;
  lbl.textContent = phase==='green'?'GO':phase==='yellow'?'WAIT':'STOP';

  // phase badge
  const badge = document.getElementById(`badge-${dir}`);
  if(badge){ badge.textContent = phase.toUpperCase(); badge.className = `phase-badge ${phase}`; }
}

// ── DIRECTION CARD ──
function updateDirCard(dir, info) {
  const card = document.getElementById(`card-${dir}`);
  if(!card) return;
  card.classList.toggle('active-card', info.phase!=='red');
  const ind = card.querySelector('.dir-phase-indicator');
  ind.className = `dir-phase-indicator phase-${info.phase}`;
  const d = ctrl.directions[dir];
  card.querySelector('.tc-val.g').textContent = d.greenTime+'s';
  card.querySelector('.tc-val.y').textContent = d.yellowTime+'s';
  card.querySelector('.tc-val.r').textContent = ctrl.redOf(dir)+'s';
  const fill = card.querySelector('.mini-fill');
  const lbl  = card.querySelector('.mini-label');
  const pct  = Math.min(1, info.timeLeft/info.total);
  fill.style.width = (pct*100)+'%';
  fill.style.background = CM[info.phase];
  lbl.textContent = `${Math.ceil(info.timeLeft)}s remaining`;
}

// (updateTimeline defined later after buildDirCards)
function mkSeg(cls,pct,txt){
  const s=document.createElement('div'); s.className=`seg ${cls}`; s.style.width=pct+'%';
  if(pct>5) s.textContent=txt; return s;
}
function updateCursors(){
  const pct=(ctrl.cycleTime/ctrl.full)*100;
  ['ns','ew'].forEach(id=>{ const c=document.getElementById(`cursor-${id}`); if(c) c.style.left=pct+'%'; });
}
function updateRing(states){
  let a=null;
  for(const d of DIRS){ if(states[d].phase!=='red'){a=states[d];break;} }
  if(!a) a=states.north;
  const ring=document.getElementById('ringFill');
  ring.style.strokeDashoffset=CIRC*(1-a.timeLeft/a.total);
  ring.style.stroke=CM[a.phase];
  document.getElementById('centerTime').textContent=Math.ceil(a.timeLeft);
  document.getElementById('centerTime').style.color=CM[a.phase];
  document.getElementById('centerCycle').textContent=`CYCLE ${ctrl.cycleCount}`;
}
function updateHeader(){
  document.getElementById('cycleCount').textContent=ctrl.cycleCount;
  const s=Math.floor((Date.now()-t0)/1000);
  document.getElementById('elapsed').textContent=`${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;
}

function render(){
  const states = ctrl.getStates(ctrl.cycleTime);
  DIRS.forEach(dir => {
    updateBulbs(dir, states[dir].phase);
    updateCountdown(dir, states[dir].phase, states[dir].timeLeft);
    updateDirCard(dir, states[dir]);
  });
  updateRing(states); updateCursors(); updateHeader();
}

// ── LOOP ──
function loop(ts){
  if(lastTs!==null) ctrl.tick((ts-lastTs)/1000);
  lastTs=ts; render(); requestAnimationFrame(loop);
}

// ── CONTROLS ──
function toggleRun(){
  ctrl.running=!ctrl.running;
  const btn=document.getElementById('btnRun');
  btn.textContent=ctrl.running?'⏸ PAUSE':'▶ RUN';
  btn.classList.toggle('active',ctrl.running);
  document.getElementById('sysStatus').textContent=ctrl.running?'RUNNING':'PAUSED';
  addLog(ctrl.running?'System resumed':'System paused');
}
function resetSystem(){
  ctrl.cycleTime=0; ctrl.cycleCount=0; t0=Date.now(); prevSec={};
  addLog('System reset'); render();
}
function skipPhase(){
  const ct=ctrl.cycleTime, NSy=ctrl.NSg+ctrl.NSy, EWg=NSy+ctrl.EWg;
  if(ct<ctrl.NSg){ctrl.cycleTime=ctrl.NSg;addLog('Skipped → NS yellow');}
  else if(ct<NSy){ctrl.cycleTime=NSy;addLog('Skipped → EW green');}
  else if(ct<EWg){ctrl.cycleTime=EWg;addLog('Skipped → EW yellow');}
  else{ctrl.cycleTime=0;ctrl.cycleCount++;addLog('Skipped → new cycle');}
}
function setSpeed(v){ ctrl.speed=Number(v); document.getElementById('speedLabel').textContent=v+'x'; }
function selectEditDir(d, e) {
  editDir = d;
  document.querySelectorAll('.dir-sel-btn').forEach(b => b.classList.remove('sel'));
  e.target.classList.add('sel');
  const dir = d === 'NS' ? ctrl.directions.north : ctrl.directions.east;
  document.getElementById('editGreen').value  = dir.greenTime;
  document.getElementById('editYellow').value = dir.yellowTime;
  document.getElementById('editClear').value  = dir.clearance;
  previewTiming();
}

function previewTiming() {
  // Values being edited (this direction)
  const g = Math.max(1, parseInt(document.getElementById('editGreen').value)  || 0);
  const y = Math.max(1, parseInt(document.getElementById('editYellow').value) || 0);
  const c = Math.max(0, parseInt(document.getElementById('editClear').value)  || 0);

  // Other direction's current values (unchanged)
  const otherDir = editDir === 'NS' ? ctrl.directions.east : ctrl.directions.north;
  const og = otherDir.greenTime;
  const oy = otherDir.yellowTime;
  const oc = otherDir.clearance;

  // Red for THIS direction = other side's full phase (og + oy + oc)
  const r  = og + oy + oc;
  // Red for OTHER direction = this phase (g + y + c)
  const or = g + y + c;

  // Full cycle = this phase + other phase
  const full = (g + y + c) + (og + oy + oc);

  // Update the auto red display
  document.getElementById('editRed').value = r;

  // Update cycle total
  document.getElementById('cycleTotal').textContent = full + 's';

  // Preview bar: show full cycle split
  // [G][Y][C(gap)][RED(=other G+Y+C)][otherG][otherY][otherC]
  // The "RED" segment here = other's phase (when this direction is waiting)
  // But visually cleaner: show this-phase and other-phase
  const pG   = (g  / full) * 100;
  const pY   = (y  / full) * 100;
  const pC   = (c  / full) * 100;
  const pRed = (r  / full) * 100;   // = other phase visually (this direction RED)

  document.getElementById('pvG').style.width   = pG   + '%';
  document.getElementById('pvY').style.width   = pY   + '%';
  document.getElementById('pvC').style.width   = pC   + '%';
  document.getElementById('pvRed').style.width = '0%';  // hidden — the "red" is shown as other side's green below
  // Other side's phase (other green + other yellow + other clearance) = the red period for this dir
  document.getElementById('pvEWG').style.width = (og / full * 100) + '%';
  document.getElementById('pvEWY').style.width = (oy / full * 100) + '%';
  document.getElementById('pvEWC').style.width = (oc / full * 100) + '%';

  document.getElementById('pvG').textContent   = g  + 's';
  document.getElementById('pvEWG').textContent = og + 's';

  const dirLabel = editDir === 'NS' ? 'N/S' : 'E/W';
  const othLabel = editDir === 'NS' ? 'E/W' : 'N/S';
  document.getElementById('pvGlbl').textContent = `${dirLabel}: G${g}+Y${y}${c>0?'+C'+c:''}=${g+y+c}s`;
  document.getElementById('pvYlbl').textContent = `→`;
  document.getElementById('pvRlbl').textContent = `${othLabel}: G${og}+Y${oy}${oc>0?'+C'+oc:''}=${og+oy+oc}s  (${dirLabel} RED=${r}s)`;
}

function applyTiming() {
  const g = Math.max(5, parseInt(document.getElementById('editGreen').value)  || 30);
  const y = Math.max(2, parseInt(document.getElementById('editYellow').value) || 5);
  const c = Math.max(0, parseInt(document.getElementById('editClear').value)  || 0);

  if (editDir === 'NS') {
    ctrl.directions.north.greenTime = ctrl.directions.south.greenTime = g;
    ctrl.directions.north.yellowTime= ctrl.directions.south.yellowTime= y;
    ctrl.directions.north.clearance = ctrl.directions.south.clearance = c;
    const r = ctrl.directions.east.greenTime + ctrl.directions.east.yellowTime + ctrl.directions.east.clearance;
    addLog(`NS applied → G=${g}s Y=${y}s C=${c}s | NS-RED=${r}s (auto)`);
  } else {
    ctrl.directions.east.greenTime  = ctrl.directions.west.greenTime  = g;
    ctrl.directions.east.yellowTime = ctrl.directions.west.yellowTime = y;
    ctrl.directions.east.clearance  = ctrl.directions.west.clearance  = c;
    const r = ctrl.directions.north.greenTime + ctrl.directions.north.yellowTime + ctrl.directions.north.clearance;
    addLog(`EW applied → G=${g}s Y=${y}s C=${c}s | EW-RED=${r}s (auto)`);
  }

  ctrl.cycleTime = 0; prevSec = {};
  updateTimeline(); buildDirCards(); previewTiming(); render();
}
function addLog(msg, cls=''){
  const log=document.getElementById('cycleLog');
  const s=Math.floor((Date.now()-t0)/1000);
  const ts=`${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;
  const e=document.createElement('div');
  e.className='log-entry'+(cls?` log-${cls}`:'');
  e.innerHTML=`<span class="log-time">${ts}</span><span>${msg}</span>`;
  log.insertBefore(e,log.firstChild);
  while(log.children.length>30) log.removeChild(log.lastChild);
}

// ── BUILD DIR CARDS ──
function buildDirCards(){
  const c=document.getElementById('dirCards'); c.innerHTML='';
  DIRS.forEach(dir=>{
    const d=ctrl.directions[dir];
    const autoRed = ctrl.redOf(dir);
    const card=document.createElement('div'); card.className='dir-card'; card.id=`card-${dir}`;
    card.innerHTML=`
      <div class="dir-card-header">
        <span class="dir-name">${d.label}</span>
        <div class="dir-phase-indicator phase-red"></div>
      </div>
      <div class="dir-timings">
        <div class="timing-cell"><div class="tc-label">GREEN</div><div class="tc-val g">${d.greenTime}s</div></div>
        <div class="timing-cell"><div class="tc-label">YELLOW</div><div class="tc-val y">${d.yellowTime}s</div></div>
        <div class="timing-cell"><div class="tc-label">RED</div><div class="tc-val r">${autoRed}s</div></div>
      </div>
      <div class="progress-bar-wrap">
        <div class="mini-bar"><div class="mini-fill" style="width:0%;background:var(--red)"></div></div>
        <div class="mini-label">waiting…</div>
      </div>`;
    c.appendChild(card);
  });
}

// ── TIMELINE ──
function updateTimeline() {
  const grid = document.getElementById('timelineGrid');
  if (!grid) return; grid.innerHTML = '';
  const full = ctrl.full;
  const addRow = (label, segments) => {
    const row=document.createElement('div'); row.className='tl-row';
    const lbl=document.createElement('div'); lbl.className='tl-row-label'; lbl.textContent=label;
    const bw =document.createElement('div'); bw.className='tl-bar-container';
    const segs=document.createElement('div'); segs.className='tl-segments';
    segments.forEach(([cls,dur])=>{ if(dur>0) segs.appendChild(mkSeg(cls,dur/full*100,Math.round(dur)+'s')); });
    const cur=document.createElement('div'); cur.className='tl-cursor';
    cur.id=`cursor-${label.replace('/','').toLowerCase()}`;
    bw.appendChild(segs); bw.appendChild(cur);
    row.appendChild(lbl); row.appendChild(bw); grid.appendChild(row);
  };
  addRow('N/S',[['green',ctrl.NSg],['yellow',ctrl.NSy],['red',ctrl.NSc+ctrl.EWphase]]);
  addRow('E/W',[['red',ctrl.NSphase],['green',ctrl.EWg],['yellow',ctrl.EWy],['red',ctrl.EWc]]);
}

// ── INIT ──
buildDirCards();
updateTimeline();
updateEmergencyUI();
previewTiming();
ctrl.running = true;
requestAnimationFrame(loop);