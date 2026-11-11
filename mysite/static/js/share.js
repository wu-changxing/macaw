// Share images: one look, the red wedge (after Lissitzky), three formats.
// long   = poster + the whole article + the last wedge striking the QR (WeChat Moments)
// cover  = the 3:4 poster alone (Xiaohongshu / X / LinkedIn)
// slides = the poster, the article paginated onto 3:4 pages, and a QR page;
//          at most nine images, a WeChat grid
// Every wedge points at the same tip, 80px past the right edge, so the tip of
// one image's wedge stabs into the next image's opening lines.
const stage = document.getElementById('stage');
const slides = document.getElementById('slides');
const out = document.getElementById('out');
const MAX_TEXT_PAGES = 7;
const RED = '#e0402f', INK = '#0b1220', BLUE = '#00a8ff';
const TIP = [470, 262];
const COVER_WEDGE = wedge([-120, 760], 250);
const PAGE_WEDGE = wedge([-40, 600], 92);

// A red triangle from a base centred on `base`, `half` wide each side, to TIP.
function wedge(base, half) {
    const length = Math.hypot(TIP[0] - base[0], TIP[1] - base[1]);
    const normal = [-(TIP[1] - base[1]) / length, (TIP[0] - base[0]) / length];
    const a = [base[0] - half * normal[0], base[1] - half * normal[1]];
    const b = [base[0] + half * normal[0], base[1] + half * normal[1]];
    return a[1] < b[1] ? { up: a, lo: b, tip: TIP } : { up: b, lo: a, tip: TIP };
}

// A wedge with a given base that stops on `tip` (the last one, against the QR).
function strike(base, half, tip) {
    const length = Math.hypot(tip[0] - base[0], tip[1] - base[1]);
    const normal = [(tip[1] - base[1]) / length, -(tip[0] - base[0]) / length];
    return [[base[0] + half * normal[0], base[1] + half * normal[1]], tip,
            [base[0] - half * normal[0], base[1] - half * normal[1]]];
}

const yAt = (p, q, x) => p[1] + (q[1] - p[1]) * (x - p[0]) / (q[0] - p[0]);
const points = (list, dx = 0) => list.map(([x, y]) => `${x + dx},${y}`).join(' ');
const triangle = (w, dx = 0) => `<polygon points="${points([w.up, w.tip, w.lo], dx)}" fill="${RED}"/>`;

function art(inner, height = 520) {
    return `<svg class="art" width="390" height="${height}" viewBox="0 0 390 ${height}" aria-hidden="true">${inner}</svg>`;
}

function element(tag, className, text) {
    const node = document.createElement(tag);
    node.className = className;
    if (text != null) node.textContent = text;
    return node;
}

// Place a rotated line so its baseline sits `gap` px above edge p->q at x.
function onEdge(node, p, q, x, gap, size) {
    const angle = Math.atan2(q[1] - p[1], q[0] - p[0]);
    const lift = size * 0.92;
    node.classList.add('rot');
    node.style.fontSize = size + 'px';
    node.style.left = x + Math.sin(angle) * lift + 'px';
    node.style.top = yAt(p, q, x) - gap - Math.cos(angle) * lift + 'px';
    node.style.transform = `rotate(${angle * 180 / Math.PI}deg)`;
    return node;
}

// Shrink a rotated line from `size` until it is at most `width` long.
function fit(node, size, width, smallest) {
    node.style.fontSize = size + 'px';
    while (node.offsetWidth > width && size > smallest) node.style.fontSize = --size + 'px';
    return size;
}

function splitTitle(title, year) {
    const match = title.match(/^(.{1,6}?)\s*[：:\s]\s*(.+)$/);
    return match ? [match[1], match[2]] : [year, title];
}

function layoutPoster() {
    const poster = document.getElementById('poster');
    const w = COVER_WEDGE;
    const [big, rest] = splitTitle(stage.dataset.title, stage.dataset.year);
    poster.insertAdjacentHTML('afterbegin', art(`<circle cx="318" cy="150" r="118" fill="${INK}"/>${triangle(w)}`
        + `<line x1="${w.lo[0]}" y1="${w.lo[1] + 22}" x2="${w.tip[0]}" y2="${w.tip[1] + 22}" stroke="${BLUE}" stroke-width="4"/>`));
    const word = element('div', 'big rot', big);
    const line = element('div', 'rest rot', rest);
    poster.append(word, line);
    const size = fit(word, 148, 330, 60);
    if (rest.length > 10) line.style.letterSpacing = '.04em';
    const restSize = fit(line, 26, 175, 11);  // ends before the ink circle
    onEdge(word, w.up, w.tip, 6, 8, size);
    onEdge(line, w.up, w.tip, 30, 8 + size * 1.2, restSize);
    poster.append(onEdge(element('div', 'name', '吴长星'), w.up, w.tip, 170, -44, 22),
                  onEdge(element('div', 'aka lat', 'AARON · AARON404'), w.up, w.tip, 178, -66, 10));
}

function charCount(node) {
    return node.textContent.replace(/\s/g, '').length;
}

function qr(element, size) {
    new QRCode(element, { text: stage.dataset.url, width: size * 2, height: size * 2, colorDark: INK, colorLight: '#ffffff' });
}

function ending(total, shown) {
    const line = element('div', 'ending', shown < total ? 'TO BE CONTINUED' : 'END');
    const d = stage.dataset;
    line.append(element('span', '', shown < total
        ? `${d.lMore} ${(total - shown).toLocaleString('en')} ${d.lChars}`
        : `${d.lEnd} ${total.toLocaleString('en')} ${d.lChars}`));
    return line;
}

// The long image's last block: END, the QR, and a wedge that stops against it.
function layoutFinale(total) {
    const finale = document.getElementById('finale');
    finale.insertAdjacentHTML('afterbegin', art(`<polygon points="${points(strike([-80, 470], 140, [228, 122]))}" fill="${RED}"/>`, 420));
    document.getElementById('ending').replaceWith(ending(total, total));
    qr(finale.querySelector('.qr'), 102);
}

// Blocks to paginate: the body's children, with block wrappers opened up.
function blocks(container) {
    return Array.from(container.children).flatMap(node =>
        node.tagName === 'DIV' && node.children.length ? blocks(node) : [node]);
}

// The text column: its bottom is pushed into a slope by this page's wedge and
// its left side is pierced by the previous image's tip.
function column(w, previous) {
    const content = element('div', 'content');
    const above = x => yAt(w.up, w.tip, x) - 18;
    const level = above(150);
    const upper = yAt(previous.up, previous.tip, 390), lower = yAt(previous.lo, previous.tip, 390);
    const left = [[28, upper - 14], [Math.min(100, TIP[0] - 390 + 16), TIP[1] - 8], [28, lower + 14],
                  [28, level], [100, level], [100, 520], [28, 520]];
    const right = [[100, level], [150, level], [362, above(362)], [362, 520], [100, 520]];
    const shape = (list, x0) => `polygon(${list.map(([x, y]) => `${x - x0}px ${y - 64}px`).join(',')})`;
    const fl = element('div', 'fl'), fr = element('div', 'fr');
    fl.style.shapeOutside = shape(left, 28);
    fr.style.shapeOutside = shape(right, 100);
    content.append(fl, fr);
    return content;
}

function folio(w, number) {
    const label = element('div', 'folio');
    const count = element('b', '', String(number).padStart(2, '0'));
    count.dataset.page = number;
    label.append(count, element('span', 'of', ''));
    const angle = Math.atan2(w.tip[1] - w.lo[1], w.tip[0] - w.lo[0]);
    label.classList.add('rot');
    label.style.left = '262px';
    label.style.top = yAt(w.lo, w.tip, 262) + 8 + 'px';
    label.style.transform = `rotate(${angle * 180 / Math.PI}deg)`;
    return label;
}

function newPage(number, previous) {
    const w = PAGE_WEDGE;
    const page = element('section', 'slide page');
    page.innerHTML = art(triangle(w) + triangle(previous, -390)
        + `<line x1="${w.lo[0] + 40}" y1="${w.lo[1] + 44}" x2="${w.tip[0] + 60}" y2="${w.tip[1] + 38}" stroke="${BLUE}" stroke-width="3"/>`);
    const content = column(w, previous);
    page.append(element('header', '', `吴长星 · ${stage.dataset.title}`), content, folio(w, number));
    slides.append(page);
    return content;
}

const overflows = content => content.scrollHeight > content.clientHeight + 1;
const placed = content => content.querySelectorAll(':scope > :not(.fl, .fr)').length;

// Put as much of a text block as fits (whole child nodes, then characters of
// one text node); return what is left for the next page.
function fitText(content, node) {
    const part = node.cloneNode(false);
    content.append(part);
    const kids = Array.from(node.childNodes);
    let index = 0, cut = '';
    for (; index < kids.length; index++) {
        const kid = kids[index].cloneNode(true);
        part.append(kid);
        if (!overflows(content)) continue;
        kid.remove();
        if (kid.nodeType === Node.TEXT_NODE) cut = fitCharacters(content, part, kid.data);
        break;
    }
    if (charCount(part) < 20) { part.remove(); return node; }
    if (index === kids.length) return null;  // it all fitted; only its margin did not
    const rest = node.cloneNode(false);
    rest.append(kids[index].nodeType === Node.TEXT_NODE ? kids[index].data.slice(cut.length) : kids[index].cloneNode(true),
                ...kids.slice(index + 1).map(kid => kid.cloneNode(true)));
    while (rest.firstChild?.nodeName === 'BR') rest.firstChild.remove();
    return rest;
}

function fitCharacters(content, part, text) {
    const piece = document.createTextNode('');
    part.append(piece);
    let low = 0, high = text.length;
    while (low < high) {
        const middle = Math.ceil((low + high) / 2);
        piece.data = text.slice(0, middle);
        if (overflows(content)) high = middle - 1; else low = middle;
    }
    while (low > 0 && /^[，。！？、；：”’）」』,.!?;:)]/.test(text.slice(low))) low--;  // no page opens on punctuation
    piece.data = text.slice(0, low);
    return piece.data;
}

function paginate() {
    const queue = blocks(document.getElementById('body')).map(node => node.cloneNode(true));
    let content = newPage(2, COVER_WEDGE), pages = 1, shown = 0;
    while (queue.length) {
        const node = queue.shift();
        content.append(node);
        if (!overflows(content)) { shown += charCount(node); continue; }
        node.remove();
        if (/^(P|LI|BLOCKQUOTE)$/.test(node.tagName)) {
            const rest = fitText(content, node);
            if (rest !== node) shown += charCount(node) - (rest ? charCount(rest) : 0);
            if (rest) queue.unshift(rest);
        } else if (!placed(content)) {
            content.append(node);  // taller than a page on its own: shown clipped
            shown += charCount(node);
            continue;
        } else {
            queue.unshift(node);
        }
        const tail = content.lastElementChild;  // a heading never ends a page
        if (tail && /^H[2-4]$/.test(tail.tagName) && placed(content) > 1) {
            tail.remove(); shown -= charCount(tail); queue.unshift(tail);
        }
        if (pages === MAX_TEXT_PAGES) break;
        content = newPage(++pages + 1, PAGE_WEDGE);
    }
    return shown;
}

// The QR page: the title word, the ending, and the last wedge against the QR.
function lastSlide(total, shown) {
    const last = element('section', 'slide last');
    last.innerHTML = art(`<polygon points="${points(strike([-60, 548], 120, [228, 286]))}" fill="${RED}"/>` + triangle(PAGE_WEDGE, -390));
    const word = element('div', 'big', splitTitle(stage.dataset.title, stage.dataset.year)[0]);
    const finale = document.getElementById('finale');
    const code = element('div', 'qr');
    last.append(ending(total, shown), word, code, finale.querySelector('.who').cloneNode(true));
    slides.append(last);
    fit(word, 112, 330, 48);
    qr(code, 102);
}

function buildSlides() {
    if (slides.children.length) return;
    slides.hidden = false;
    const cover = element('section', 'slide poster');
    cover.append(...document.getElementById('poster').cloneNode(true).childNodes);
    cover.querySelector('h1')?.remove();
    slides.append(cover);

    const total = charCount(document.getElementById('body'));
    const shown = paginate();
    lastSlide(total, shown);

    const count = String(slides.children.length).padStart(2, '0');
    slides.querySelectorAll('.folio .of').forEach(of => { of.textContent = `/ ${count}`; });
    if (shown < total) {
        const pages = slides.querySelectorAll('.slide.page');
        pages[pages.length - 1].append(element('div', 'more', 'TO BE CONTINUED →'));
    }
}

function choose(format) {
    document.querySelectorAll('[data-format]').forEach(tab => {
        if (tab.tagName === 'BUTTON') tab.setAttribute('aria-selected', tab.dataset.format === format);
    });
    stage.dataset.format = format;
    out.replaceChildren();
    document.getElementById('hint').hidden = true;
    if (format === 'slides') buildSlides();
    stage.hidden = format === 'slides';
    slides.hidden = format !== 'slides';
}

function targets() {
    if (stage.dataset.format === 'cover') return [document.getElementById('poster')];
    if (stage.dataset.format === 'slides') return Array.from(slides.children);
    return [stage];
}

async function save(button) {
    button.disabled = true;
    out.replaceChildren();
    const slug = location.pathname.split('/').filter(Boolean).pop() || 'aaron404';
    const nodes = targets();
    for (const [index, node] of nodes.entries()) {
        const scale = 2;
        const url = await domtoimage.toPng(node, {
            width: node.offsetWidth * scale, height: node.offsetHeight * scale,
            style: { transform: `scale(${scale})`, transformOrigin: 'top left' },
        });
        const figure = document.createElement('figure');
        const image = new Image();
        image.src = url;
        image.alt = `${stage.dataset.title} ${index + 1}/${nodes.length}`;
        const link = document.createElement('a');
        link.href = url;
        link.download = `${slug}-${stage.dataset.format}-${String(index + 1).padStart(2, '0')}.png`;
        link.textContent = link.download;
        figure.append(image, link);
        out.append(figure);
    }
    document.getElementById('hint').hidden = false;
    out.scrollIntoView({ behavior: 'smooth' });
    button.disabled = false;
}

layoutPoster();
layoutFinale(charCount(document.getElementById('body')));
document.querySelectorAll('.formats button').forEach(tab => tab.addEventListener('click', () => choose(tab.dataset.format)));
document.getElementById('save').addEventListener('click', event => save(event.currentTarget));
