// Share images: ten looks (share-looks.js), three formats.
// long   = poster + the whole article + an ending with the QR (WeChat Moments)
// cover  = the 3:4 poster alone (Xiaohongshu / X / LinkedIn)
// slides = the poster, the article paginated onto 3:4 pages, and a QR page;
//          at most nine images, a WeChat grid
// Everything inside #canvas is drawn at 390 CSS px and rasterised at 2x by
// dom-to-image; the bar, the look picker and the output list are not.
const stage = document.getElementById('stage');
const slides = document.getElementById('slides');
const canvas = document.getElementById('canvas');
const out = document.getElementById('out');
const result = document.getElementById('result');
const MAX_TEXT_PAGES = 7;
const INK = '#0b1220';
const ZH = document.documentElement.lang.startsWith('zh');
const POSTER_TITLE = document.querySelector('#poster h1');
const POSTER_META = document.querySelector('#poster .meta');
const WHO = document.querySelector('#finale .who').cloneNode(true);
WHO.querySelector('.u').textContent = decodeURI(stage.dataset.url);  // readable, not %E5…

function element(tag, className, text) {
    const node = document.createElement(tag);
    node.className = className;
    if (text != null) node.textContent = text;
    return node;
}

const esc = text => String(text).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

function art(inner, height = 520) {
    return `<svg class="art" width="390" height="${height}" viewBox="0 0 390 ${height}" aria-hidden="true">${inner}</svg>`;
}

// Shrink a one-line node from `size` until it is at most `width` long.
function fit(node, size, width, smallest) {
    node.style.fontSize = size + 'px';
    while (node.offsetWidth > width && size > smallest) node.style.fontSize = --size + 'px';
    return size;
}

// Shrink a fixed-size box's text from its CSS size until nothing overflows it.
function fitBox(node, smallest) {
    let size = parseFloat(getComputedStyle(node).fontSize);
    while ((node.scrollHeight > node.clientHeight + 1 || node.scrollWidth > node.clientWidth + 1) && size > smallest) {
        node.style.fontSize = --size + 'px';
    }
}

function splitTitle(title, year) {
    const match = title.match(/^(.{1,6}?)\s*[：:\s]\s*(.+)$/);
    return match ? [match[1], match[2]] : [year, title];
}

const charCount = node => node.textContent.replace(/\s/g, '').length;

// What every look may print: real facts about this article, nothing invented.
function facts() {
    const d = stage.dataset;
    const body = document.getElementById('body');
    const chars = charCount(body);
    const [big, rest] = splitTitle(d.title, d.year);
    const lead = Array.from(body.querySelectorAll('p')).map(p => p.textContent.trim()).join(' ').slice(0, 420);
    return { title: d.title, big, rest, year: d.year, date: d.date, section: d.section, url: d.url,
             chars, words: chars.toLocaleString('en'), minutes: Math.max(1, Math.round(chars / 400)), lead };
}

function qr(node) {
    new QRCode(node, { text: stage.dataset.url, width: 216, height: 216, colorDark: INK, colorLight: '#ffffff' });
}

function ending(total, shown) {
    const line = element('div', 'ending', shown < total ? 'TO BE CONTINUED' : 'END');
    const d = stage.dataset;
    line.append(element('span', '', shown < total
        ? `${d.lMore} ${(total - shown).toLocaleString('en')} ${d.lChars}`
        : `${d.lEnd} ${total.toLocaleString('en')} ${d.lChars}`));
    return line;
}

// The parts every last page and ending share: the ending line, the QR, the author.
function closing(section, shown) {
    const code = element('div', 'qr');
    section.append(ending(FACTS.chars, shown), code, WHO.cloneNode(true));
    qr(code);
}

// A text page: the look's own art and header, then the column the paginator fills.
function textPage(page, html) {
    page.innerHTML = html;
    const content = element('div', 'content');
    page.append(content);
    return content;
}

// Blocks to paginate: the body's children, with block wrappers opened up.
function blocks(container) {
    return Array.from(container.children).flatMap(node =>
        node.tagName === 'DIV' && node.children.length ? blocks(node) : [node]);
}

function newPage(number) {
    const page = element('section', 'slide page');
    slides.append(page);
    return LOOKS[look].page(page, number, FACTS);
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
    rest.classList.add('cont');  // a continued paragraph is not indented again
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
    let content = newPage(2), pages = 1, shown = 0;
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
        content = newPage(++pages + 1);
    }
    return shown;
}

function buildSlides() {
    if (slides.children.length) return;
    slides.hidden = false;
    const cover = element('section', 'slide poster');
    cover.append(...document.getElementById('poster').cloneNode(true).childNodes);
    cover.querySelector('h1')?.remove();
    slides.append(cover);

    const shown = paginate();
    const last = element('section', 'slide last');
    slides.append(last);
    LOOKS[look].last(last, FACTS, shown);

    const count = slides.children.length;
    const total = LOOKS[look].total || (n => `/ ${String(n).padStart(2, '0')}`);
    slides.querySelectorAll('.folio .of').forEach(of => { of.textContent = total(count); });
    if (shown < FACTS.chars) {
        const pages = slides.querySelectorAll('.slide.page');
        pages[pages.length - 1].append(element('div', 'more', 'TO BE CONTINUED →'));
    }
}

// Draw the poster and the long image's ending in a look; slides are redrawn on demand.
function dress(name) {
    look = name;
    localStorage.setItem('share-look', name);
    canvas.dataset.look = name;
    document.querySelectorAll('.looks button').forEach(button => button.setAttribute('aria-pressed', button.dataset.look === name));
    stage.hidden = false;  // measured while drawn
    const poster = document.getElementById('poster');
    poster.replaceChildren(POSTER_TITLE, POSTER_META);
    LOOKS[name].poster(poster, FACTS);
    const finale = document.getElementById('finale');
    finale.replaceChildren();
    LOOKS[name].finale(finale, FACTS);
    slides.replaceChildren();
    choose(stage.dataset.format);
}

// The picker shows each look's real poster for this article, at a fifth of its size.
function buildPicker() {
    const strip = document.getElementById('looks');
    for (const [name, def] of Object.entries(LOOKS)) {
        const button = element('button', '');
        button.type = 'button';
        button.dataset.look = name;
        const thumb = element('span', 'thumb');
        thumb.dataset.look = name;
        thumb.setAttribute('aria-hidden', 'true');
        const poster = element('section', 'poster');
        poster.append(POSTER_META.cloneNode(true));
        thumb.append(poster);
        button.append(thumb, element('span', 'name', ZH ? def.zh : def.en));
        button.addEventListener('click', () => dress(name));
        strip.append(button);
        def.poster(poster, FACTS);
    }
}

function choose(format) {
    document.querySelectorAll('.formats button').forEach(tab => tab.setAttribute('aria-selected', tab.dataset.format === format));
    stage.dataset.format = format;
    if (format === 'slides') buildSlides();
    stage.hidden = format === 'slides';
    slides.hidden = format !== 'slides';
    const spec = document.getElementById('spec');
    spec.textContent = `${ZH ? LOOKS[look].zh : LOOKS[look].en} · ${spec.dataset[format].replace('{n}', slides.children.length)}`;
    showDesk();
}

// The artwork is drawn at 390px; on a narrower screen the canvas is scaled
// down to fit, and the sizer takes the scaled height so the page scrolls right.
function fitCanvas() {
    const scale = Math.min(1, (document.documentElement.clientWidth - 32) / 390);
    canvas.style.transform = scale < 1 ? `scale(${scale})` : '';
    document.getElementById('sizer').style.height = `${canvas.offsetHeight * scale}px`;
}

function showDesk() {
    result.hidden = true;
    document.getElementById('desk').hidden = false;
    fitCanvas();
}

function targets() {
    if (stage.dataset.format === 'cover') return [document.getElementById('poster')];
    if (stage.dataset.format === 'slides') return Array.from(slides.children);
    return [stage];
}

function fileName(index, total) {
    const title = stage.dataset.title.replace(/[\\/:*?"<>|\s]+/g, '-');
    const format = result.dataset['l' + stage.dataset.format[0].toUpperCase() + stage.dataset.format.slice(1)];
    const part = total > 1 ? `-${String(index + 1).padStart(2, '0')}` : '';
    return `${title}-${ZH ? LOOKS[look].zh : LOOKS[look].en}-${format}${part}.png`;
}

async function render(node) {
    const scale = 2;
    return domtoimage.toBlob(node, {
        width: node.offsetWidth * scale, height: node.offsetHeight * scale,
        style: { transform: `scale(${scale})`, transformOrigin: 'top left' },
    });
}

async function make(button) {
    const label = button.textContent;
    button.disabled = true;
    const nodes = targets();
    const files = [];
    for (const [index, node] of nodes.entries()) {
        button.textContent = `${result.dataset.lMaking} ${index + 1}/${nodes.length}`;
        files.push(new File([await render(node)], fileName(index, nodes.length), { type: 'image/png' }));
    }
    button.textContent = label;
    button.disabled = false;
    await showResult(files);
}

// A phone saves through the share sheet ("Save image" puts it in Photos);
// a computer downloads the files.
const touch = matchMedia('(pointer: coarse)').matches;
const sharing = files => touch && navigator.canShare && navigator.canShare({ files });

async function keep(files) {
    if (sharing(files)) {
        await navigator.share({ files }).catch(error => { if (error.name !== 'AbortError') throw error; });
        return;
    }
    // In-app browsers (WeChat) neither share nor download: long-press is the way.
    if (touch) {
        document.querySelector('.result .hint').classList.add('flash');
        return;
    }
    for (const file of files) {
        const link = Object.assign(document.createElement('a'), { href: URL.createObjectURL(file), download: file.name });
        link.click();
        await new Promise(done => setTimeout(done, 300));
    }
}

// Images are shown as data URLs: long-press "Save image" works on them everywhere,
// including in-app browsers where a blob: image cannot be saved.
const dataUrl = file => new Promise(done => {
    const reader = new FileReader();
    reader.onload = () => done(reader.result);
    reader.readAsDataURL(file);
});

async function showResult(files) {
    const sources = await Promise.all(files.map(dataUrl));
    const d = result.dataset;
    const word = sharing(files) ? d.lSave : d.lDownload;
    document.getElementById('count').innerHTML = `<b>${files.length}</b>${d.lReady}`;
    const all = document.getElementById('keep-all');
    all.textContent = files.length > 1 ? (sharing(files) ? d.lAllSave : d.lAllDownload) : word;
    all.onclick = () => keep(files);
    out.dataset.format = stage.dataset.format;
    out.replaceChildren(...files.map((file, index) => {
        const figure = document.createElement('figure');
        const image = Object.assign(new Image(), { src: sources[index], alt: `${stage.dataset.title} ${index + 1}/${files.length}` });
        const caption = document.createElement('figcaption');
        const number = element('span', '', `${String(index + 1).padStart(2, '0')} / ${String(files.length).padStart(2, '0')}`);
        const button = element('button', '', word);
        button.type = 'button';
        button.onclick = () => keep([file]);
        caption.append(number, button);
        figure.append(image, caption);
        return figure;
    }));
    document.getElementById('desk').hidden = true;
    result.hidden = false;
    scrollTo({ top: 0 });
}

const FACTS = facts();
let look = LOOKS[localStorage.getItem('share-look')] ? localStorage.getItem('share-look') : 'wedge';
buildPicker();
document.querySelectorAll('.formats button').forEach(tab => tab.addEventListener('click', () => choose(tab.dataset.format)));
document.getElementById('save').addEventListener('click', event => make(event.currentTarget));
document.getElementById('again').addEventListener('click', showDesk);
addEventListener('resize', fitCanvas);
new ResizeObserver(fitCanvas).observe(canvas);
dress(look);
