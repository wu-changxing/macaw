// 刃 / The Blade: intro once per session, parallax, and the blade-to-page transition.
// Without JavaScript, or with reduced motion, the page is the final still.
(() => {
const phoneMQ = matchMedia('(max-width:640px),(max-aspect-ratio:3/4)');
const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const OUT = 'cubic-bezier(.2,.8,.2,1)';
const root = () => document.querySelector(phoneMQ.matches ? '.blade-home .phone' : '.blade-home .desk');
const q = (r, s) => r.querySelector(s), qa = (r, s) => [...r.querySelectorAll(s)];
let drift = null;

function animator(list) {
  return (el, kf, o) => { if (el) list.push(el.animate(kf, Object.assign({ fill: 'both' }, o))); };
}

function glint(r, delay, duration) {
  const gp = q(r, '.glint-path');
  return q(r, '.glint').animate([
    { opacity: 0, transform: 'translate(0,0)' }, { opacity: 1, offset: .15 }, { opacity: 1, offset: .8 },
    { opacity: 0, transform: `translate(${gp.dataset.dx}px,${gp.dataset.dy}px)` }],
    { delay, duration, easing: 'ease-in-out' });
}

// 0-1500 ms beat sheet: hold, shadow first, 80 ms fall, ink flash, shake, recoil, waves, doors, sections, glint
function intro(r) {
  const A = [], an = animator(A);
  const bf = q(r, '.blade-fall');
  const T = d => `translate(${(bf.dataset.ux * d).toFixed(1)}px,${(bf.dataset.uy * d).toFixed(1)}px)`;
  an(q(r, '.shadow-g'), [{ opacity: 0, transform: 'scaleX(1.35)' }, { opacity: 1, transform: 'scaleX(1)' }],
     { delay: 120, duration: 180, easing: 'cubic-bezier(.5,0,.9,.5)' });
  an(bf, [{ transform: T(1100), easing: 'cubic-bezier(.7,0,1,.6)' }, { transform: T(-18), offset: 80 / 480, easing: 'cubic-bezier(.2,1.4,.4,1)' },
          { transform: T(6), offset: .55 }, { transform: T(0) }], { delay: 300, duration: 480 });
  an(q(r, '.smear'), [{ opacity: .35 }, { opacity: 0 }], { delay: 300, duration: 80 });
  an(q(r, '.blade-shudder'), [0, .6, -.6, .4, -.4, .2, -.1, 0].map(d => ({ transform: `rotate(${d}deg)` })), { delay: 400, duration: 380, fill: 'none' });
  an(q(r, '.edge'), [{ opacity: 1 }, { opacity: .7 }, { opacity: 1 }], { delay: 380, duration: 140, fill: 'none' });
  an(q(r, '.flash'), [{ opacity: 1 }, { opacity: 1, offset: .6 }, { opacity: 0 }], { delay: 380, duration: 60, fill: 'none' });
  const pu = q(r, '.punch');
  pu.style.transformBox = 'view-box';
  pu.style.transformOrigin = q(r, '.blade-shudder').style.transformOrigin;
  an(pu, [{ transform: 'scale(1.045)' }, { transform: 'scale(1)' }], { delay: 380, duration: 520, easing: 'cubic-bezier(.1,.9,.2,1)', fill: 'none' });
  an(q(r, '.shake'), [[0, 0], [3, 12], [-2, -8], [1, 5], [0, -3], [0, 1], [0, 0]].map(([x, y]) => ({ transform: `translate(${x}px,${y}px)` })),
     { delay: 380, duration: 260, fill: 'none' });
  qa(r, '.wave').forEach((el, i) => an(el, [{ transform: 'scale(.2)', opacity: 0 }, { opacity: 1, offset: .05 }, { transform: 'scale(1)', opacity: 1 }],
     { delay: 380 + i * 35, duration: 360 + i * 70, easing: 'cubic-bezier(.1,.8,.2,1)' }));
  qa(r, '.crater').forEach(el => an(el, [{ opacity: 0 }, { opacity: 1 }], { delay: 380, duration: 1 }));
  an(q(r, '.streaks'), [{ opacity: 0 }, { opacity: 1, offset: .1 }, { opacity: 1, offset: .4 }, { opacity: 0 }], { delay: 300, duration: 600, fill: 'none' });
  qa(r, '.crown').forEach(el => an(el, [{ opacity: 0, transform: 'scale(.12)' }, { opacity: 1, offset: .08 }, { opacity: 1, transform: 'scale(1)' }],
     { delay: 380, duration: 170, easing: 'cubic-bezier(.15,.7,.3,1)' }));
  an(q(r, '.dust'), [{ opacity: 0 }, { opacity: 1 }], { delay: 380, duration: 420, easing: OUT });
  qa(r, '.pulse').forEach((el, i) => an(el, [{ opacity: 0 }, { opacity: .95 }, { opacity: 0 }], { delay: 900 + i * 70, duration: 260, fill: 'none' }));
  an(q(r, '.spine'), [{ opacity: 0 }, { opacity: 1 }], { delay: 880, duration: 180, easing: OUT });
  an(q(document, '.blade-sections .rule'), [{ transform: 'scaleX(0)' }, { transform: 'scaleX(1)' }], { delay: 960, duration: 260, easing: OUT });
  qa(document, '.blade-sections a').forEach((el, i) => an(el, [{ opacity: 0, transform: 'translateY(6px)' }, { opacity: 1, transform: 'none' }],
     { delay: 1000 + i * 30, duration: 140, easing: OUT }));
  A.push(glint(r, 1300, 200));
  return A;
}

function startDrift(r) {
  const s = q(r, '.d-shadow'), g = q(r, '.shadow-g');
  s.style.transformBox = 'view-box';
  s.style.transformOrigin = g.style.transformOrigin;
  drift = s.animate([{ transform: 'rotate(0deg)' }, { transform: 'rotate(-1deg)' }], { duration: 60000, iterations: Infinity, direction: 'alternate', easing: 'ease-in-out' });
}
document.addEventListener('visibilitychange', () => drift && (document.hidden ? drift.pause() : drift.play()));

function start() {
  const r = root();
  if (reduce) return;
  if (sessionStorage.getItem('blade-intro')) { startDrift(r); return; }
  sessionStorage.setItem('blade-intro', '1');
  const A = intro(r);
  const evs = ['pointerdown', 'keydown', 'wheel', 'touchstart'];
  const skip = () => { A.forEach(a => a.finish()); off(); };
  const off = () => evs.forEach(e => removeEventListener(e, skip, true));
  evs.forEach(e => addEventListener(e, skip, { capture: true, passive: true }));
  Promise.all(A.map(a => a.finished)).then(() => { off(); startDrift(r); });
}

// parallax: capped at 8 px, frozen over doors and for 150 ms after leaving one
let frozenUntil = 0;
addEventListener('pointermove', e => {
  if (reduce || e.pointerType !== 'mouse' || phoneMQ.matches || document.body.classList.contains('leaving')) return;
  if (e.target.closest && e.target.closest('a.door')) { frozenUntil = performance.now() + 150; return; }
  if (performance.now() < frozenUntil) return;
  const r = root(), x = (e.clientX / innerWidth - .5) * 2, y = (e.clientY / innerHeight - .5) * 2;
  const u = Math.max(innerWidth / 1440, innerHeight / 900);  // the scene's "slice" scale, for the HTML credit block
  q(r, '.par').style.transform = `translate(${(-x * 8).toFixed(1)}px,${(-y * 4).toFixed(1)}px)`;
  q(r, '.par-sky').style.transform = `translate(${(x * 5).toFixed(1)}px,${(y * 2).toFixed(1)}px)`;
  q(document, '.blade-sections').style.transform = `translate(${(-x * 8 * u).toFixed(1)}px,${(-y * 4 * u).toFixed(1)}px)`;
});

// blade -> page sheet, then follow the link (900 ms)
let leaving = [];
function toSheet(e) {
  if (reduce || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
  e.preventDefault();
  const href = e.currentTarget.getAttribute('href'), r = root(), A = [], an = animator(A);
  document.body.classList.add('leaving');
  const sheet = document.getElementById('sheet'), soft = document.getElementById('softshadow');
  const vw = innerWidth, vh = innerHeight, w = Math.min(720, vw - 24), top = vw < 640 ? 48 : 96;
  const left = (vw - w) / 2, h = vh - top + 40;
  [sheet, soft].forEach(el => Object.assign(el.style, { left: left + 'px', top: top + 'px', width: w + 'px', height: h + 'px' }));
  const bb = q(r, '.blade-face').getBoundingClientRect();
  const from = `translate(${bb.left - left + bb.width * .1}px,${bb.top - top - 30}px) scale(${bb.width * .8 / w},${bb.height / h})`;
  qa(r, '.d-arch,.d-walker,.d-kite,.string,.name,.crown,.waves,.crater,.dust').concat(qa(document, '.blade-lang,.blade-sections'))
    .forEach(el => an(el, [{ opacity: 1 }, { opacity: 0 }], { duration: 150 }));
  const bf = q(r, '.blade-fall');
  const lean = Math.atan2(+bf.dataset.ux, -bf.dataset.uy) * 180 / Math.PI;
  an(q(r, '.blade-stand'), [{ transform: 'none' }, { transform: `translateY(-40px) rotate(${-lean}deg)` }], { duration: 450, easing: OUT });
  an(q(r, '.d-shadow'), [{ opacity: 1 }, { opacity: 0 }], { delay: 150, duration: 450 });
  qa(r, '.par-sky,.bg').forEach(el => an(el, [{ opacity: 1 }, { opacity: 0 }], { delay: 150, duration: 450 }));
  an(q(r, '.d-blade'), [{ opacity: 1 }, { opacity: 0 }], { delay: 470, duration: 80 });
  an(soft, [{ opacity: 0, transform: from }, { opacity: 1, transform: 'none' }], { delay: 300, duration: 400, easing: OUT });
  an(sheet, [{ opacity: 0 }, { opacity: 1 }], { delay: 450, duration: 70 });
  an(sheet, [{ transform: from }, { transform: 'none' }], { delay: 450, duration: 250, easing: OUT });
  an(q(sheet, '.edge-red'), [{ opacity: 1 }, { opacity: 0 }], { delay: 750, duration: 150 });
  an(q(sheet, '.edge-blue'), [{ opacity: 0 }, { opacity: 1 }], { delay: 750, duration: 150 });
  leaving = A;
  setTimeout(() => { location.href = href; }, 900);
}

// coming back through the history cache: show the poster again, not the blank sheet
addEventListener('pageshow', e => {
  if (!e.persisted) return;
  leaving.forEach(a => a.cancel());
  leaving = [];
  document.body.classList.remove('leaving');
});

qa(document, '.blade-home .d-blade').forEach(a => {
  a.addEventListener('click', toSheet);
  a.addEventListener('mouseenter', () => reduce || glint(root(), 0, 600));
});

start();
})();
