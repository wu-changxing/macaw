// Share images: lay out the poster, then rasterise one of three formats.
// long   = poster + the whole article on the sheet + QR (WeChat Moments)
// cover  = the 3:4 poster alone (Xiaohongshu / X / LinkedIn)
// slides = the poster, the article paginated onto 3:4 pages, and a QR page;
//          at most nine images, a WeChat grid
const stage = document.getElementById('stage');
const slides = document.getElementById('slides');
const out = document.getElementById('out');
const MAX_TEXT_PAGES = 7;

function splitTitle(title, year) {
    const match = title.match(/^(.{1,6}?)\s*[：:\s]\s*(.+)$/);
    return match ? [match[1], match[2]] : [year, title];
}

function layoutPoster() {
    const [big, rest] = splitTitle(stage.dataset.title, stage.dataset.year);
    const words = stage.querySelectorAll('.poster .big');
    words.forEach(word => { word.textContent = big; });
    const probe = document.createElement('span');
    probe.textContent = big;
    words[0].append(probe);
    const size = Math.min(132, 120 * 300 / probe.offsetWidth);
    probe.remove();
    words.forEach(word => { word.style.fontSize = size + 'px'; });

    const heading = stage.querySelector('.poster .rest');
    heading.textContent = rest;
    heading.setAttribute('aria-label', stage.dataset.title);
    heading.style.top = 150 + size + 18 + 'px';
    let restSize = 30;
    while (heading.offsetTop + heading.offsetHeight > 430 && restSize > 18) {
        restSize -= 1;
        heading.style.fontSize = restSize + 'px';
    }
}

function charCount(node) {
    return node.textContent.replace(/\s/g, '').length;
}

function qr(element, size) {
    new QRCode(element, { text: stage.dataset.url, width: size * 2, height: size * 2, colorDark: '#0b1220', colorLight: '#ffffff' });
}

function ending(total, shown) {
    const line = document.createElement('div');
    line.className = 'ending';
    line.textContent = shown < total ? 'TO BE CONTINUED' : 'END';
    const note = document.createElement('span');
    const d = stage.dataset;
    note.textContent = shown < total
        ? `${d.lMore} ${(total - shown).toLocaleString('en')} ${d.lChars}`
        : `${d.lEnd} ${total.toLocaleString('en')} ${d.lChars}`;
    line.append(note);
    return line;
}

// Blocks to paginate: the body's children, with block wrappers opened up.
function blocks(container) {
    return Array.from(container.children).flatMap(node =>
        node.tagName === 'DIV' && node.children.length ? blocks(node) : [node]);
}

function newPage(number) {
    const page = document.createElement('section');
    page.className = 'slide page';
    const header = document.createElement('header');
    const title = document.createElement('span');
    title.textContent = `吴长星 · ${stage.dataset.title}`;
    const count = document.createElement('b');
    count.dataset.page = number;
    header.append(title, count);
    const content = document.createElement('div');
    content.className = 'content';
    page.append(header, content);
    slides.append(page);
    return content;
}

const overflows = content => content.scrollHeight > content.clientHeight + 1;

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
        } else if (!content.children.length) {
            content.append(node);  // taller than a page on its own: shown clipped
            shown += charCount(node);
            continue;
        } else {
            queue.unshift(node);
        }
        const tail = content.lastElementChild;  // a heading never ends a page
        if (tail && /^H[2-4]$/.test(tail.tagName) && content.children.length > 1) {
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
    const cover = document.createElement('section');
    cover.className = 'slide';
    cover.append(stage.querySelector('.poster').cloneNode(true));
    slides.append(cover);

    const total = charCount(document.getElementById('body'));
    const shown = paginate();
    const last = document.createElement('section');
    last.className = 'slide last';
    last.append(stage.querySelector('.cut').cloneNode(true), ending(total, shown));
    const colophon = stage.querySelector('.colophon').cloneNode(true);
    colophon.querySelector('.qr').replaceChildren();
    last.append(colophon.querySelector('.qr'), colophon.querySelector('.who'));
    qr(last.querySelector('.qr'), 140);
    slides.append(last);

    const count = slides.children.length;
    slides.querySelectorAll('b[data-page]').forEach(b => {
        b.textContent = `${String(b.dataset.page).padStart(2, '0')} / ${String(count).padStart(2, '0')}`;
    });
    if (shown < total) {
        const more = document.createElement('div');
        more.className = 'more';
        more.textContent = 'TO BE CONTINUED →';
        slides.querySelectorAll('.slide.page')[MAX_TEXT_PAGES - 1]?.append(more);
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
    if (stage.dataset.format === 'cover') return [stage.querySelector('.poster')];
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
const endingSlot = document.getElementById('ending');
endingSlot.replaceWith(ending(charCount(document.getElementById("body")), charCount(document.getElementById("body"))));
qr(stage.querySelector('.colophon .qr'), 84);
document.querySelectorAll('.formats button').forEach(tab => tab.addEventListener('click', () => choose(tab.dataset.format)));
document.getElementById('save').addEventListener('click', event => save(event.currentTarget));
