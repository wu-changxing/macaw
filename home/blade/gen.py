"""刃 / The Blade: generates the home page scene.

Writes mysite/templates/home/blade_scene.html (two inline SVG compositions, desktop and phone, with
Django template variables for every link) and home/static/home/grain.png. Stdlib only.
Run from anywhere: python home/blade/gen.py

Ground model: camera height = 1 unit, ground point (X, Z) projects to (cx + f*X/Z, HZ + f*(1-Y)/Z).
Everything on the sand (pressure waves, crater, ejecta) is built in that space, so it thins with distance.
"""
import math, random, struct, zlib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INK, DEEP, RED, BLUE = '#16202a', '#1b2530', '#E2412F', '#4FA3D8'

DESK = dict(
    name='desk', W=1440, H=900, HZ=585, f=900, cx=720,
    tip=(512, 40), bl=(352, 630), br=(588, 652), chisel_len=450,
    S=(292, 585), crater=2.7,
    waves=((6.2, .9, .06, 1, .3), (9.6, 1.1, .045, .7, .85), (13.6, 1.3, .035, .45, .85)),  # radius, width, height, strength, crest bias
    ripples=(3.9, 4.35, 4.8),
    grains=430, curtain=130, shards=9, rays=40,
    walker=(150, 652), kite=(66, 470, .42), arch=(1170, 712, 170, 40),
    name_xy=(838, 262), name_size=182,
)
PHONE = dict(
    name='phone', W=390, H=844, HZ=505, f=430, cx=195,
    tip=(224, 64), bl=(146, 516), br=(262, 532), chisel_len=330,
    S=(139, 505), crater=2.9,
    waves=((5.2, .8, .07, 1, .85), (7.6, 1, .055, .7, .85), (10.6, 1.2, .045, .5, .85)),
    ripples=(4, 4.45),
    grains=220, curtain=70, shards=6, rays=26,
    walker=(58, 548), kite=(26, 452, .3), arch=(118, 664, 118, 30),
    name_xy=(354, 262), name_size=56,
)


class Scene:
    def __init__(s, c):
        s.c, s.o = c, []
        bx = (c['bl'][0] + c['br'][0]) / 2
        by = (c['bl'][1] + c['br'][1]) / 2 + 6
        s.base = (bx, by)
        s.Z0 = c['f'] / (by - c['HZ'])
        s.X0 = (bx - c['cx']) * s.Z0 / c['f']
        ax, ay = c['tip'][0] - c['bl'][0], c['tip'][1] - c['bl'][1]
        L = math.hypot(ax, ay)
        s.u = (ax / L, ay / L)  # unit vector up the blade axis
        br = c['br']
        s.chisel = (br[0] + s.u[0] * c['chisel_len'], br[1] + s.u[1] * c['chisel_len'])

    def a(s, x):
        s.o.append(x)

    def P(s, X, Z, Y=0.0):
        c = s.c
        Z = max(Z, .25)
        return c['cx'] + c['f'] * X / Z, c['HZ'] + c['f'] * (1 - Y) / Z

    def ring(s, R, lift=0.0, t0=0.0, t1=2 * math.pi, foot=0.0, mod=lambda t: 1.0):
        """points of a ground circle around the crater; foot pushes the radius outward on the near side"""
        n = int(48 + 9 * R)
        out = []
        for k in range(n + 1):
            t = t0 + (t1 - t0) * k / n
            m = mod(t)
            r = R + foot * m * max(0.0, -math.sin(t))
            out.append(s.P(s.X0 + r * math.cos(t), s.Z0 + r * math.sin(t), lift * m))
        return out


def pts(ps):
    return ' '.join(f'{x:.0f},{y:.0f}' for x, y in ps)


def num(v):
    """shortest one-decimal form: 0.5 -> .5, -0.5 -> -.5, 3.0 -> 3"""
    t = f'{v:.1f}'.removesuffix('.0')
    if t.startswith(('0.', '-0.')):
        t = t.replace('0.', '.', 1)
    return '0' if t == '-0' else t


def nums(vs):
    out = ''
    for v in map(num, vs):
        out += v if not out or v[0] == '-' else ' ' + v
    return out


def d(ps, close=True):
    """path through ps in relative coordinates (about half the bytes of absolute ones)"""
    r = [(round(x, 1), round(y, 1)) for x, y in ps]
    rel = [c for (x0, y0), (x1, y1) in zip(r, r[1:]) for c in (x1 - x0, y1 - y0)]
    return f'M{nums(r[0])}l{nums(rel)}' + ('Z' if close else '')


def ray_to_frame(p, S, W, H):
    dx, dy = p[0] - S[0], p[1] - S[1]
    t = min((W - p[0]) / dx if dx > 0 else 1e9, (-p[0]) / dx if dx < 0 else 1e9, (H - p[1]) / dy if dy > 0 else 1e9)
    return p[0] + dx * t, p[1] + dy * t


def defs(s):
    c = s.c
    n = c['name']
    s.a(f'''<defs>
<linearGradient id="{n}-sky" x1="0" y1="0" x2="0" y2="{c['HZ']}" gradientUnits="userSpaceOnUse">
 <stop offset="0" stop-color="#7FA9C8"/><stop offset=".55" stop-color="#C2D7E7"/><stop offset="1" stop-color="#F1F5F6"/></linearGradient>
<linearGradient id="{n}-ground" x1="0" y1="{c['HZ']}" x2="0" y2="{c['H']}" gradientUnits="userSpaceOnUse">
 <stop offset="0" stop-color="#E2E2DD"/><stop offset=".3" stop-color="#D3D5D1"/><stop offset="1" stop-color="#C2C6C6"/></linearGradient>
<radialGradient id="{n}-sun" cx="{c['S'][0]}" cy="{c['HZ'] - c['f'] * .12}" r="{c['W'] * .34}" gradientUnits="userSpaceOnUse">
 <stop offset="0" stop-color="#ffffff" stop-opacity=".95"/><stop offset=".3" stop-color="#F6F9FA" stop-opacity=".55"/><stop offset="1" stop-color="#F6F9FA" stop-opacity="0"/></radialGradient>
<linearGradient id="{n}-haze" x1="0" y1="{c['HZ'] - 26}" x2="0" y2="{c['HZ'] + 22}" gradientUnits="userSpaceOnUse">
 <stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".55" stop-color="#fff" stop-opacity=".7"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<linearGradient id="{n}-face" x1="0" y1="{c['tip'][1]}" x2="0" y2="{c['br'][1]}" gradientUnits="userSpaceOnUse">
 <stop offset="0" stop-color="#DCE5EC"/><stop offset=".55" stop-color="#C2D1DC"/><stop offset="1" stop-color="#A9BBC8"/></linearGradient>
<linearGradient id="{n}-shadow" x1="{s.base[0]}" y1="{s.base[1]}" x2="{s.base[0] + c['W'] * .4}" y2="{c['H']}" gradientUnits="userSpaceOnUse">
 <stop offset="0" stop-color="#3F7DAB" stop-opacity=".9"/><stop offset="1" stop-color="#5C96C0" stop-opacity=".55"/></linearGradient>
<radialGradient id="{n}-dust"><stop offset="0" stop-color="#FBF8F2" stop-opacity=".8"/><stop offset="1" stop-color="#FBF8F2" stop-opacity="0"/></radialGradient>
<linearGradient id="{n}-rim" x1="0" y1="{s.base[1] - 8}" x2="0" y2="{s.base[1] + 30}" gradientUnits="userSpaceOnUse">
 <stop offset="0" stop-color="#E9E9E4"/><stop offset=".35" stop-color="#B9C0C3"/><stop offset="1" stop-color="#D2D4D0"/></linearGradient>
<linearGradient id="{n}-streak" x1="0" y1="{c['tip'][1]}" x2="0" y2="{c['tip'][1] - 300}" gradientUnits="userSpaceOnUse">
 <stop offset="0" stop-color="{DEEP}" stop-opacity=".5"/><stop offset="1" stop-color="{DEEP}" stop-opacity="0"/></linearGradient>
<linearGradient id="{n}-smear" x1="0" y1="{c['br'][1]}" x2="0" y2="{c['tip'][1] - 500}" gradientUnits="userSpaceOnUse">
 <stop offset="0" stop-color="#ffffff" stop-opacity=".9"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>
</defs>''')


def sky(s):
    c = s.c
    s.a(f'<g class="world par-sky" aria-hidden="true">'
        f'<rect x="-20" y="-20" width="{c["W"] + 40}" height="{c["HZ"] + 20}" fill="url(#{c["name"]}-sky)"/>'
        f'<rect x="-20" y="-20" width="{c["W"] + 40}" height="{c["HZ"] + 20}" fill="url(#{c["name"]}-sun)"/></g>')


def ground(s):
    """sand: flat gradient plus faint wind ridges at true perspective spacing, no pull toward the crater"""
    c = s.c
    s.a(f'<g class="world bg" aria-hidden="true"><rect x="-20" y="{c["HZ"]}" width="{c["W"] + 40}" height="{c["H"] - c["HZ"] + 30}" fill="url(#{c["name"]}-ground)"/>')
    Zl = 1.6
    rnd = random.Random(3)
    while c['f'] / Zl > 2.5:
        y = c['HZ'] + c['f'] / Zl
        ph = rnd.random() * 6
        p = [(x, y + 1.6 * math.sin(x / (90 + Zl * 4) + ph) * 4 / Zl) for x in range(-20, c['W'] + 41, 40)]
        s.a(f'<polyline points="{pts(p)}" fill="none" stroke="#8D989F" stroke-width="{max(.5, min(1.4, 5 / Zl)):.2f}" opacity="{min(.22, .05 + (y - c["HZ"]) / 900):.2f}"/>')
        Zl += 1 + Zl * .16
    s.a(f'<rect x="-20" y="{c["HZ"] - 26}" width="{c["W"] + 40}" height="48" fill="url(#{c["name"]}-haze)"/></g>')


def waves(s):
    """pressure waves: a raised ridge per wave; lit crest (rim light) over a shaded near-facing slope"""
    c = s.c
    ox, oy = s.base
    s.a('<g class="world waves" aria-hidden="true">')
    allw = [(R, .16, .016, .55 - .1 * i, .85) for i, R in enumerate(c['ripples'])] + list(c['waves'])
    rnd = random.Random(21)
    for i, (R, w, h, amp, bias) in enumerate(allw):
        a1, a2, p1, p2 = rnd.randint(2, 4), rnd.randint(5, 8), rnd.uniform(0, 6), rnd.uniform(0, 6)
        # a low bias lets the crest sink into the sand in places, so the ring breaks up instead of reading as a drawn ellipse
        mod = lambda t: max(0.0, bias + .6 * math.sin(a1 * t + p1) + .3 * math.sin(a2 * t + p2))
        crest = s.ring(R, h, mod=mod)
        crest_lo = s.ring(R, h * .62, mod=mod)
        foot = s.ring(R, 0, foot=w * .45, mod=mod)
        trough = s.ring(R, 0, foot=-w * .7, mod=mod)
        base = s.ring(R, 0, mod=mod)
        s.a(f'<g class="wave" style="transform-box:view-box;transform-origin:{ox:.0f}px {oy:.0f}px">'
            f'<path d="{d(trough + base[::-1])}" fill="#56656F" opacity="{.4 * amp:.2f}"/>'
            f'<path d="{d(crest + foot[::-1])}" fill="#7C8A94" opacity="{.16 * amp:.2f}"/>'
            f'<path d="{d(crest + crest_lo[::-1])}" fill="#FFFFFF" opacity="{.9 * amp:.2f}"/></g>')
    s.a('</g>')


def shadow(s):
    c = s.c
    bl, br = c['bl'], c['br']
    fl = ray_to_frame(bl, c['S'], c['W'], c['H'])
    fr = ray_to_frame(br, c['S'], c['W'], c['H'])
    poly = [bl, br, fr]
    if fr[0] >= c['W'] - .5 and fl[1] >= c['H'] - .5:
        poly.append((c['W'], c['H']))
    poly.append(fl)
    ox, oy = s.base
    desk = c['name'] == 'desk'
    mx, my = ((fl[0] + fr[0]) / 2 * .5 + ox * .5, (fl[1] + fr[1]) / 2 * .5 + oy * .5)
    ang = math.degrees(math.atan2(my - oy, mx - ox))
    s.a(f'<a class="door d-shadow world" href="{{{{ shadow_page.url }}}}" aria-label="回潮 · 长篇科幻">'
        f'<g class="shadow-g" style="transform-box:view-box;transform-origin:{ox:.0f}px {oy:.0f}px">'
        f'<polygon points="{pts(poly)}" fill="url(#{c["name"]}-shadow)"/>'
        f'<polygon class="shadow-dark" points="{pts(poly)}" fill="#1F4E72"/>'
        f'<polygon class="hit" points="{pts(poly)}"/>'
        f'<polygon class="focus" points="{pts(poly)}"/></g>'
        + (f'<g class="cap" transform="translate({mx + 40:.0f},{my + 30:.0f}) rotate({ang:.1f})">'
           f'<text class="cap-en" font-size="15">回潮 · SCI-FI →</text>'
           f'<text class="cap-zh" y="19" font-size="13">长篇科幻，从第一章开始</text></g></a>' if desk else
           f'<g class="cap" transform="translate(376,668)"><text class="cap-en" text-anchor="end" font-size="15">回潮 →</text>'
           f'<text class="cap-zh" text-anchor="end" y="19" font-size="12">SCI-FI 长篇科幻</text></g></a>'))


def hole(s):
    """crater bowl: the far wall faces the camera and sits in its own shade — the darkest value on the page"""
    c = s.c
    R = c['crater']
    lip = s.ring(R, .1)
    s.a(f'<g class="world crater" aria-hidden="true"><path d="{d(lip)}" fill="#0F161D"/>'
        f'<path d="{d(s.ring(R, .1, math.pi * .02, math.pi * .98), False)}" fill="none" stroke="#FFFFFF" stroke-width="{1.6 if c["name"] == "desk" else 1.1}" opacity=".95"/></g>')


def near_rim(s):
    """the near lip: sand thrown up toward us, crisp backlit crest, shaded outer slope"""
    c = s.c
    R = c['crater']
    t0, t1 = math.pi * .97, math.pi * 2.03
    crest = s.ring(R, .1, t0, t1)
    foot = s.ring(R + .45, 0, t0, t1)
    sw = 2 if c['name'] == 'desk' else 1.4
    s.a(f'<g class="world crater rim" aria-hidden="true"><path d="{d(crest + foot[::-1])}" fill="url(#{c["name"]}-rim)"/>'
        f'<path d="{d(crest, False)}" fill="none" stroke="#FFFFFF" stroke-width="{sw}"/>'
        '</g>')


def ejecta(s):
    """ballistic sand: launched from the lip at 48-72 deg, frozen at t+140 ms; split into behind / in front of the blade"""
    c = s.c
    R = c['crater']
    rnd = random.Random(8)
    desk = c['name'] == 'desk'
    k = 1 if desk else .75
    back, front = [], []

    def at(X, Z, vx, vz, vy, t):
        return s.P(X + vx * t, Z + vz * t, .1 + vy * t - 4.9 * t * t)

    for i in range(c['curtain'] + c['grains'] + c['shards']):
        ph = rnd.uniform(0, 2 * math.pi)
        # the blade's long axis throws more sand sideways than fore/aft
        ph = ph + .35 * math.sin(2 * ph)
        X, Z = s.X0 + R * math.cos(ph), s.Z0 + R * .8 * math.sin(ph)
        el = math.radians(rnd.uniform(50, 76))
        sp = rnd.uniform(3.4, 9.5) if i >= c['curtain'] else rnd.uniform(6, 10)
        vh, vy = sp * math.cos(el), sp * math.sin(el)
        vx, vz = vh * math.cos(ph), vh * math.sin(ph)
        t = rnd.uniform(.08, .55) * (sp / 6)
        p1 = at(X, Z, vx, vz, vy, t)
        if p1[1] > s.P(X + vx * t, Z + vz * t)[1]:
            continue
        dst = front if math.sin(ph) < -.15 else back
        if i < c['curtain']:  # sheet of the ejecta curtain: the path itself, pale and thin
            pm = at(X, Z, vx, vz, vy, t / 2)
            p0 = at(X, Z, vx, vz, vy, 0)
            cx_, cy_ = 2 * pm[0] - (p0[0] + p1[0]) / 2, 2 * pm[1] - (p0[1] + p1[1]) / 2
            dst.append(f'<path d="M{nums(p0)}q{nums((cx_ - p0[0], cy_ - p0[1], p1[0] - p0[0], p1[1] - p0[1]))}" stroke="#FFF" stroke-width="{rnd.uniform(.5, 1.1) * k:.2f}" opacity="{rnd.uniform(.25, .6):.2f}"/>')
            continue
        pt = at(X, Z, vx, vz, vy, max(0, t - .035))
        if i >= c['curtain'] + c['grains']:  # hard shard, oriented along its velocity
            ang = math.atan2(p1[1] - pt[1], p1[0] - pt[0])
            L, w = rnd.uniform(8, 15) * k, rnd.uniform(1.4, 2.4) * k
            ux, uy, nx, ny = math.cos(ang), math.sin(ang), -math.sin(ang), math.cos(ang)
            q = [(p1[0] + ux * L * .5, p1[1] + uy * L * .5), (p1[0] + nx * w, p1[1] + ny * w), (p1[0] - ux * L * .5, p1[1] - uy * L * .5), (p1[0] - nx * w * .4, p1[1] - ny * w * .4)]
            dst.append(f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in q)}" fill="#25303A"/>')
            continue
        tone = rnd.random()
        col, op, sw = (('#FFF', rnd.uniform(.75, 1), rnd.uniform(1, 2.1)) if tone < .5 else
                       ('#6F7C87', rnd.uniform(.6, .9), rnd.uniform(.8, 1.7)) if tone < .9 else
                       ('#26313B', .9, rnd.uniform(.7, 1.2)))
        dst.append(f'<path d="M{nums(pt)}l{nums((p1[0] - pt[0], p1[1] - pt[1]))}" stroke="{col}" stroke-width="{sw * k:.2f}" opacity="{op:.2f}"/>')
    s.ej_back, s.ej_front = back, front


def rays(s):
    c = s.c
    rnd = random.Random(12)
    R = c['crater'] + .5
    out = []
    for i in range(c['rays']):
        ph = math.pi * (.9 + 1.2 * i / (c['rays'] - 1)) + rnd.uniform(-.06, .06)
        L = rnd.uniform(1.2, 4.5)
        w = rnd.uniform(.03, .07)
        if math.sin(ph) < -.45:  # rays aimed at the lens stretch into spikes; leave them out
            continue
        a = (math.cos(ph), math.sin(ph))
        n = (-a[1], a[0])
        q = [s.P(s.X0 + a[0] * R + n[0] * w, s.Z0 + a[1] * R + n[1] * w), s.P(s.X0 + a[0] * (R + L), s.Z0 + a[1] * (R + L)),
             s.P(s.X0 + a[0] * R - n[0] * w, s.Z0 + a[1] * R - n[1] * w)]
        out.append(f'<path d="{d(q)}" opacity="{rnd.uniform(.3, .6):.2f}"/>')
    ox, oy = s.base
    s.a(f'<g class="world crater rays" aria-hidden="true" fill="#FFFFFF">{"".join(out)}</g>')


def ej_group(s, items, cls):
    ox, oy = s.base
    s.a(f'<g class="world crown {cls}" aria-hidden="true" fill="none" stroke-linecap="round" '
        f'style="transform-box:view-box;transform-origin:{ox:.0f}px {oy:.0f}px">{"".join(items)}</g>')


def dust(s, front=False):
    c = s.c
    ox, oy = s.base
    k = 1 if c['name'] == 'desk' else .55
    s.a(f'<g class="world dust" aria-hidden="true">')
    blobs = ((0, 8, 300, 26, .55), (-150, 2, 160, 18, .5), (170, 12, 190, 20, .5)) if front else \
            ((0, -24, 300, 70, .8), (-120, -50, 160, 60, .6), (140, -40, 180, 64, .6), (0, -120, 120, 90, .35))
    for dx, dy, rx, ry, op in blobs:
        s.a(f'<ellipse cx="{ox + dx * k:.0f}" cy="{oy + dy * k:.0f}" rx="{rx * k:.0f}" ry="{ry * k:.0f}" fill="url(#{c["name"]}-dust)" opacity="{op}"/>')
    s.a('</g>')


def streaks(s):
    c = s.c
    ux, uy = s.u
    nx, ny = -uy, ux
    T = c['tip']
    cvx, cvy = s.chisel[0] - T[0], s.chisel[1] - T[1]
    cn = cvx * nx + cvy * ny
    cu = cvx * ux + cvy * uy
    k = 1 if c['name'] == 'desk' else .55
    s.a('<g class="world streaks" aria-hidden="true">')
    for f, L in ((.0, 300), (.45, 200), (.95, 150)):
        off = cn * f
        st = cu * f + 14 * k
        x0, y0 = T[0] + nx * off + ux * st, T[1] + ny * off + uy * st
        L *= k
        s.a(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x0 + ux * L:.1f}" y2="{y0 + uy * L:.1f}" stroke="url(#{c["name"]}-streak)" stroke-width=".8"/>')
    s.a('</g>')


def blade(s):
    c = s.c
    T, BR, BL, C = c['tip'], c['br'], c['bl'], s.chisel
    ux, uy = s.u
    nx, ny = -uy, ux  # points to the right of the axis
    desk = c['name'] == 'desk'
    bev = 10 if desk else 5
    oT = (T[0] - nx * bev, T[1] - ny * bev)
    oB = (BL[0] - nx * bev, BL[1] - ny * bev)
    chis_in = (T[0] + nx * 4 - ux * 14, T[1] + ny * 4 - uy * 14)
    C2 = (C[0] - 2, C[1] + (36 if desk else 20))
    face = [T, C, BR, BL]
    pad = [(x - nx * 12, y - ny * 12) for x, y in (oT, oB)]
    ox, oy = s.base
    smear = [(oT[0] + ux * 560, oT[1] + uy * 560), (C[0] + ux * 560, C[1] + uy * 560), C, BR, BL, oB]
    sx, sy = BL[0] + nx * (22 if desk else 16) + ux * 70, BL[1] + ny * (22 if desk else 16) + uy * 70
    fs = 15 if desk else 13
    rot = math.degrees(math.atan2(uy, ux))
    s.a(f'<a class="door d-blade" href="{{{{ blade_page.url }}}}" aria-label="多余的沉思 Musings：文章">'
        f'<g class="blade-stand" style="transform-box:view-box;transform-origin:{ox:.0f}px {oy:.0f}px">'
        f'<g class="blade-fall" data-ux="{ux:.4f}" data-uy="{uy:.4f}">'
        f'<g class="blade-shudder" style="transform-box:view-box;transform-origin:{ox:.0f}px {oy:.0f}px"><g class="press">'
        f'<polygon class="smear" points="{pts(smear)}" fill="url(#{c["name"]}-smear)" opacity="0"/>'
        f'<polygon class="hit" points="{pts([pad[0], (C[0] + 12, C[1] - 8), (BR[0] + 12, BR[1] + 6), pad[1]])}"/>'
        f'<polygon class="blade-face" points="{pts(face)}" fill="url(#{c["name"]}-face)"/>'
        f'<polygon points="{pts([T, C, C2, chis_in])}" fill="#F5F8FA"/>'
        f'<polygon class="face-hi" points="{pts(face)}" fill="#ffffff"/>'
        f'<polygon points="{pts([oT, T, BL, oB])}" fill="#ffffff"/>'
        f'<line x1="{C[0]:.1f}" y1="{C[1]:.1f}" x2="{BR[0]}" y2="{BR[1]}" stroke="#7F93A2" stroke-width="1"/>'
        f'<line class="edge" x1="{oT[0]:.1f}" y1="{oT[1]:.1f}" x2="{oB[0]:.1f}" y2="{oB[1]:.1f}" stroke="{RED}" stroke-width="{3.5 if desk else 2.5}"/>'
        f'<line class="edge-thick" x1="{oT[0]:.1f}" y1="{oT[1]:.1f}" x2="{oB[0]:.1f}" y2="{oB[1]:.1f}" stroke="{RED}" stroke-width="6"/>'
        f'<g class="glint-path" data-dx="{oB[0] - oT[0]:.1f}" data-dy="{oB[1] - oT[1]:.1f}">'
        f'<g class="glint"><circle cx="{oT[0]:.1f}" cy="{oT[1]:.1f}" r="{14 if desk else 9}" fill="url(#{c["name"]}-dust)"/>'
        f'<line x1="{oT[0] - ux * 30:.1f}" y1="{oT[1] - uy * 30:.1f}" x2="{oT[0] + ux * 30:.1f}" y2="{oT[1] + uy * 30:.1f}" stroke="#fff" stroke-width="2.5"/></g></g>'
        f'<g class="spine" transform="translate({sx:.1f},{sy:.1f}) rotate({rot:.2f})">'
        f'<text class="spine-en" font-size="{fs}">MUSINGS →</text>'
        f'<text class="spine-zh" x="{fs * 7.6:.0f}" font-size="{fs - 1}">多余的沉思</text></g>'
        f'<polygon class="focus" points="{pts(face)}"/>'
        f'</g></g></g></g></a>')
    s.blade_poly = [oT, T, C, BR, BL, oB]


def flash(s):
    """hit frame: white-out, the blade as a solid ink cut-out with its red edge"""
    c = s.c
    bp = s.blade_poly
    s.a(f'<g class="flash" aria-hidden="true"><rect x="-40" y="-40" width="{c["W"] + 80}" height="{c["H"] + 80}" fill="#FFFFFF"/>'
        f'<polygon points="{pts(bp)}" fill="{INK}"/>'
        f'<line x1="{bp[0][0]:.1f}" y1="{bp[0][1]:.1f}" x2="{bp[5][0]:.1f}" y2="{bp[5][1]:.1f}" stroke="{RED}" stroke-width="5"/>'
        f'<line x1="-40" y1="{c["HZ"]}" x2="{c["W"] + 40}" y2="{c["HZ"]}" stroke="{INK}" stroke-width="1"/></g>')


def archived(s):
    c = s.c
    cx, cy, w, h = c['arch']
    desk = c['name'] == 'desk'
    q = h / 40
    lift = [(cx - w / 2, cy + h / 2), (cx + w / 2, cy + h / 2 - 10 * q), (cx + w / 2 + 12 * q, cy - h / 2 - 6 * q), (cx - w / 2 + 16 * q, cy - h / 2 + 4 * q)]
    xs, ys = [p[0] for p in lift], [p[1] for p in lift]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    hw, hh = max(170, x1 - x0 + 10), (90 if desk else 64)
    hx0, hy0 = (x0 + x1) / 2 - hw / 2, (y0 + y1) / 2 - hh * .6
    mound = f'M{x0 - 14:.0f},{y1 + 2:.0f} Q{x0 + (x1 - x0) * .3:.0f},{y1 - (y1 - y0) * .55:.0f} {x0 + (x1 - x0) * .62:.0f},{y1 - (y1 - y0) * .3:.0f} T{x1 + 22:.0f},{y1 - 4:.0f} L{x1 + 22:.0f},{y1 + 4:.0f}Z'
    fs = 14 if desk else 13
    capy = y0 - 22 if desk else y1 + 22
    s.a(f'<a class="door d-arch world" href="{{{{ doors.Archived.link }}}}" target="_blank" rel="noopener" aria-label="Archived：过时的博客和不正确的想法（外部网站，新标签页打开）">'
        f'<rect class="hit" x="{hx0:.0f}" y="{hy0:.0f}" width="{hw:.0f}" height="{hh:.0f}"/>'
        f'<g class="press"><g class="lift">'
        f'<polygon points="{pts([(x + 3, y + 3) for x, y in lift])}" fill="#8796A1" opacity=".45"/>'
        f'<polygon points="{pts(lift)}" fill="#ECE7DB" stroke="#8E8A80" stroke-width=".8"/>'
        + ''.join(f'<line x1="{lift[3][0] + (lift[0][0] - lift[3][0]) * f + 14 * q:.1f}" y1="{lift[3][1] + (lift[0][1] - lift[3][1]) * f:.1f}" '
                  f'x2="{lift[2][0] + (lift[1][0] - lift[2][0]) * f - 30 * q:.1f}" y2="{lift[2][1] + (lift[1][1] - lift[2][1]) * f:.1f}" stroke="#A7A397" stroke-width=".6"/>'
                  for f in (.3, .5, .7)) +
        f'<line x1="{lift[0][0]:.1f}" y1="{lift[0][1]:.1f}" x2="{lift[3][0]:.1f}" y2="{lift[3][1]:.1f}" stroke="#B4776C" stroke-width="2"/>'
        f'<polygon class="focus" points="{pts(lift)}"/></g>'
        f'<path d="{mound}" fill="#CBCECB" stroke="#8F9BA3" stroke-width=".6"/></g>'
        f'<circle class="pulse" cx="{(x0 + x1) / 2:.0f}" cy="{(y0 + y1) / 2:.0f}" r="{40 * q + 10:.0f}" fill="url(#{c["name"]}-dust)"/>'
        f'<g class="cap" transform="translate({x0:.0f},{capy:.0f})"><text class="cap-en" font-size="{fs}">ARCHIVED ↗</text>'
        f'<text class="cap-zh" y="{fs + 5}" font-size="{fs - 1}">过时的博客和不正确的想法</text></g></a>')


def walker(s):
    c = s.c
    fx, fy = c['walker']
    h = fy - c['HZ']  # head on the horizon: eye-level camera
    k = h / 72
    S = c['S']
    dx, dy = fx - S[0], fy - S[1]
    L = math.hypot(dx, dy)
    sh_end = (fx + dx / L * 4.2 * h * .55, fy + dy / L * 4.2 * h * .1 + 4 * k)

    def fig(front):
        if front:
            body = (f'M{fx - 9 * k:.1f},{fy:.1f} L{fx - 8 * k:.1f},{fy - 30 * k:.1f} L{fx - 12 * k:.1f},{fy - 32 * k:.1f} L{fx - 10 * k:.1f},{fy - 56 * k:.1f} '
                    f'Q{fx:.1f},{fy - 62 * k:.1f} {fx + 10 * k:.1f},{fy - 56 * k:.1f} L{fx + 12 * k:.1f},{fy - 32 * k:.1f} L{fx + 8 * k:.1f},{fy - 30 * k:.1f} '
                    f'L{fx + 9 * k:.1f},{fy:.1f} L{fx + 2 * k:.1f},{fy:.1f} L{fx:.1f},{fy - 24 * k:.1f} L{fx - 2 * k:.1f},{fy:.1f}Z')
        else:
            body = (f'M{fx - 6 * k:.1f},{fy:.1f} L{fx - 3 * k:.1f},{fy - 28 * k:.1f} L{fx - 8 * k:.1f},{fy - 32 * k:.1f} L{fx - 6 * k:.1f},{fy - 56 * k:.1f} '
                    f'Q{fx + 2 * k:.1f},{fy - 62 * k:.1f} {fx + 8 * k:.1f},{fy - 55 * k:.1f} L{fx + 9 * k:.1f},{fy - 30 * k:.1f} L{fx + 4 * k:.1f},{fy - 28 * k:.1f} '
                    f'L{fx + 10 * k:.1f},{fy:.1f} L{fx + 5 * k:.1f},{fy:.1f} L{fx + 1 * k:.1f},{fy - 18 * k:.1f} L{fx - 1 * k:.1f},{fy:.1f}Z')
        hx = fx + (0 if front else 1.5 * k)
        return f'<path d="{body}" fill="#2F3B46"/><circle cx="{hx:.1f}" cy="{fy - 64 * k:.1f}" r="{6 * k:.1f}" fill="#2F3B46"/>'

    s.hand = (fx + 9 * k, fy - 46 * k)
    desk = c['name'] == 'desk'
    fs = 14 if desk else 13
    wcx, wcy = (fx + 18 * k + 4, fy - 40 * k) if desk else (fx - 40, fy + 26)
    m = max(k, .67)
    s.a(f'<a class="door d-walker world" href="{{{{ doors.Bilibili.link }}}}" target="_blank" rel="noopener" aria-label="Bilibili：给我发消息（外部网站，新标签页打开）">'
        f'<rect class="hit" x="{fx - 36 * m:.0f}" y="{fy - 82 * m:.0f}" width="{72 * m:.0f}" height="{96 * m:.0f}"/>'
        f'<g class="press"><polygon points="{pts([(fx - 3 * k, fy), (fx + 3 * k, fy), sh_end])}" fill="#3F7AA6" opacity=".55"/>'
        f'<g class="w-side">{fig(False)}</g><g class="w-front">{fig(True)}</g>'
        f'<rect class="focus" x="{fx - 14 * k:.0f}" y="{fy - 74 * k:.0f}" width="{28 * k:.0f}" height="{76 * k:.0f}"/></g>'
        f'<circle class="pulse" cx="{fx:.0f}" cy="{fy - 34 * k:.0f}" r="{44 * k:.0f}" fill="url(#{c["name"]}-dust)"/>'
        f'<g class="cap" transform="translate({wcx:.0f},{wcy:.0f})"><text class="cap-en" font-size="{fs}">BILIBILI ↗</text>'
        f'<text class="cap-zh" y="{fs + 5}" font-size="{fs - 1}">给我发消息</text></g></a>')


def kite(s):
    """Scratch: a small, distant kite low over the horizon; a minor door, so it stays quiet. c['kite'] = (x, y, scale)"""
    c = s.c
    kx, ky, k = c['kite']
    desk = c['name'] == 'desk'
    hx, hy = s.hand
    top, right, bottom, left = (kx, ky - 34 * k), (kx + 22 * k, ky - 4 * k), (kx, ky + 34 * k), (kx - 22 * k, ky - 4 * k)
    tail = f'M{kx:.1f},{bottom[1]:.1f} q{-8 * k:.1f},{14 * k:.1f} {3 * k:.1f},{26 * k:.1f}'
    bow = f'<path d="M{kx - 6 * k:.1f},{ky + 50 * k:.1f} l{8 * k:.1f},{-3 * k:.1f} l0,{6 * k:.1f}z" fill="{BLUE}"/>'
    fs = 12 if desk else 10
    capx, capy = (kx + 16, ky - 2) if desk else (kx + 16, ky + 3)
    zh = f'<text class="cap-zh" y="{fs + 4}" font-size="{fs - 1}">基于浏览器的scratch编程</text>' if desk else ''
    s.a(f'<path d="M{hx:.1f},{hy:.1f} Q{(kx + hx) / 2 + 6:.0f},{max(hy, ky) - 30:.0f} {kx:.1f},{bottom[1]:.1f}" fill="none" stroke="#2F3B46" stroke-width=".6" opacity=".8" class="world string"/>')
    s.a(f'<a class="door d-kite world" href="{{{{ doors.Scratch.link }}}}" target="_blank" rel="noopener" aria-label="Scratch：基于浏览器的scratch编程（外部网站，新标签页打开）">'
        f'<rect class="hit" x="{kx - 24:.0f}" y="{ky - 26:.0f}" width="48" height="52"/>'
        f'<g class="press"><g class="lift">'
        f'<polygon points="{pts([top, right, bottom, left])}" fill="#F7FAFC" stroke="#2F3B46" stroke-width=".8"/>'
        f'<polygon points="{pts([top, right, (kx, ky - 4 * k)])}" fill="{BLUE}"/>'
        f'<path d="{tail}" fill="none" stroke="#2F3B46" stroke-width=".6"/>{bow}'
        f'<rect class="focus" x="{kx - 14:.0f}" y="{ky - 18:.0f}" width="28" height="36"/></g></g>'
        f'<g class="cap" transform="translate({capx:.0f},{capy:.0f})"><text class="cap-en" font-size="{fs}">SCRATCH ↗</text>{zh}</g></a>')


def name(s):
    c = s.c
    x, y = c['name_xy']
    n = c['name_size']
    if c['name'] == 'desk':
        s.a(f'<g class="world name" aria-hidden="true"><text x="{x}" y="{y}" class="nm" font-size="{n}" letter-spacing="6">吴长星</text>'
            f'<text x="{x + 8}" y="{y + 42}" class="nm-sub" font-size="14" letter-spacing="2.4">AARON · aaron404</text></g>')
    else:
        s.a(f'<g class="world name" aria-hidden="true"><text x="{x}" y="{y}" class="nm" font-size="{n}" writing-mode="tb" letter-spacing="4">吴长星</text>'
            f'<text class="nm-sub" font-size="12" letter-spacing="1.6" transform="translate({x - 40},{y + 4}) rotate(90)">AARON · aaron404</text></g>')


def build(c):
    s = Scene(c)
    # desktop anchors right: on screens narrower than 16:10 the left edge (walker, kite) is cropped, never the name
    align = 'xMaxYMid' if c['name'] == 'desk' else 'xMidYMid'
    s.a(f'<svg class="scene" viewBox="0 0 {c["W"]} {c["H"]}" preserveAspectRatio="{align} slice" xmlns="http://www.w3.org/2000/svg">')
    defs(s)
    s.a('<g class="par"><g class="shake"><g class="punch">')
    sky(s)
    ground(s)
    waves(s)
    shadow(s)
    archived(s)
    walker(s)
    kite(s)
    rays(s)
    dust(s)
    hole(s)
    ejecta(s)
    ej_group(s, s.ej_back, 'crown-back')
    streaks(s)
    blade(s)
    near_rim(s)
    ej_group(s, s.ej_front, 'crown-front')
    dust(s, front=True)
    name(s)
    s.a('</g></g></g>')
    flash(s)
    s.a('</svg>')
    return ''.join(s.o)


def grain_png(size=96):
    """grey gaussian noise tile, written as a minimal 8-bit greyscale PNG"""
    rnd = random.Random(1)
    rows = b''.join(b'\0' + bytes(max(0, min(255, int(rnd.gauss(128, 34)))) for _ in range(size)) for _ in range(size))

    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 0, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b''))


HEADER = '{# Generated by home/blade/gen.py. Edit the generator, not this file. #}\n'

if __name__ == '__main__':
    scene = REPO / 'mysite/templates/home/blade_scene.html'
    scene.write_text(HEADER + f'<div class="stage desk">{build(DESK)}</div>\n<div class="stage phone">{build(PHONE)}</div>\n')
    (REPO / 'home/static/home/grain.png').write_bytes(grain_png())
    print(scene, len(scene.read_bytes()) // 1024, 'KB')
