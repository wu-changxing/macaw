// The ten looks of the share images. Each look draws, for one article:
//   poster(poster, f)        the 3:4 cover (also the head of the long image)
//   finale(finale, f)        the long image's last block, with the QR
//   page(page, number, f)    one 3:4 text page; returns the column to fill
//   last(last, f, shown)     the closing 3:4 page, with the QR
// `f` holds the article's real facts (share.js `facts()`); the CSS for each
// look is scoped by [data-look] in share-looks.css. Loaded before share.js,
// whose helpers these call only once the page has loaded.
const LOOKS = {};
const RED = '#e0402f', BLUE = '#00a8ff';
const T = (zh, en) => ZH ? zh : en;  // the page's language, for the looks' own labels

/* 1. 红楔 Wedge, after Lissitzky: a red wedge on one steep axis drives into
   every page and its tip crosses into the next image. ---------------------- */
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
    label.append(element('b', '', String(number).padStart(2, '0')), element('span', 'of', ''));
    const angle = Math.atan2(w.tip[1] - w.lo[1], w.tip[0] - w.lo[0]);
    label.classList.add('rot');
    label.style.left = '262px';
    label.style.top = yAt(w.lo, w.tip, 262) + 8 + 'px';
    label.style.transform = `rotate(${angle * 180 / Math.PI}deg)`;
    return label;
}

LOOKS.wedge = {
    zh: '红楔', en: 'Wedge',
    poster(poster, f) {
        const w = COVER_WEDGE;
        poster.insertAdjacentHTML('afterbegin', art(`<circle cx="318" cy="150" r="118" fill="${INK}"/>${triangle(w)}`
            + `<line x1="${w.lo[0]}" y1="${w.lo[1] + 22}" x2="${w.tip[0]}" y2="${w.tip[1] + 22}" stroke="${BLUE}" stroke-width="4"/>`));
        const word = element('div', 'big rot', f.big);
        const line = element('div', 'rest rot', f.rest);
        poster.append(word, line);
        const size = fit(word, 148, 330, 60);
        if (f.rest.length > 10) line.style.letterSpacing = '.04em';
        const restSize = fit(line, 26, 175, 11);  // ends before the ink circle
        onEdge(word, w.up, w.tip, 6, 8, size);
        onEdge(line, w.up, w.tip, 30, 8 + size * 1.2, restSize);
        poster.append(onEdge(element('div', 'name', '吴长星'), w.up, w.tip, 170, -44, 22),
                      onEdge(element('div', 'aka lat', 'AARON · AARON404'), w.up, w.tip, 178, -66, 10));
    },
    finale(finale, f) {
        finale.innerHTML = art(`<polygon points="${points(strike([-80, 470], 140, [228, 122]))}" fill="${RED}"/>`, 420);
        closing(finale, f.chars);
    },
    page(page, number, f) {
        const w = PAGE_WEDGE, previous = number === 2 ? COVER_WEDGE : PAGE_WEDGE;
        page.innerHTML = art(triangle(w) + triangle(previous, -390)
            + `<line x1="${w.lo[0] + 40}" y1="${w.lo[1] + 44}" x2="${w.tip[0] + 60}" y2="${w.tip[1] + 38}" stroke="${BLUE}" stroke-width="3"/>`);
        const content = column(w, previous);
        page.append(element('header', '', `吴长星 · ${f.title}`), content, folio(w, number));
        return content;
    },
    last(last, f, shown) {
        last.innerHTML = art(`<polygon points="${points(strike([-60, 548], 120, [228, 286]))}" fill="${RED}"/>` + triangle(PAGE_WEDGE, -390));
        const word = element('div', 'big', f.big);
        last.append(word);
        closing(last, shown);
        fit(word, 112, 330, 48);
    },
};

/* 2. 稿纸 Manuscript: green-ruled Chinese manuscript paper; the title is
   written into its squares, one character a square. */
const squares = text => [...text.trim().replace(/\s+/g, ' ')];

// Rows of squares for `cells`, `cols` wide, with `pad` empty rows above and below.
function manuscript(cells, cols, size, pad) {
    const rows = Math.ceil(cells.length / cols);
    const filled = [...Array(pad * cols).fill(''), ...cells, ...Array(rows * cols - cells.length + pad * cols).fill('')];
    let html = '';
    for (let row = 0; row < rows + 2 * pad; row++) {
        html += `<div class="g-row">${filled.slice(row * cols, row * cols + cols).map(c => `<i>${esc(c)}</i>`).join('')}</div>`;
    }
    return { html: `<div class="g-cells" style="--s:${size}px">${html}</div>`, rows };
}

// The largest square size whose rows of the title fit the frame.
function manuscriptFor(text, width, height) {
    const cells = squares(text);
    for (const size of [64, 56, 50, 44, 40, 36, 32, 28, 24]) {
        const cols = Math.floor(width / size);
        const rows = Math.ceil(cells.length / cols);
        if ((rows + 2) * size * 1.22 <= height) return { cols, size, ...manuscript(cells, cols, size, 1) };
    }
    const cols = Math.floor(width / 24);
    return { cols, size: 24, ...manuscript(cells, cols, 24, 0) };
}

LOOKS.grid = {
    zh: '稿纸', en: 'Manuscript',
    poster(poster, f) {
        const sheet = manuscriptFor(f.title, 318, 360);
        poster.insertAdjacentHTML('beforeend', `<div class="g-top"><span>${esc(f.section)}</span><span>${f.date}</span></div>
            <div class="g-frame">${sheet.html}</div>
            <div class="g-by">${T('吴长星 著', '吴长星')}</div><div class="g-count">${sheet.cols} × ${sheet.rows + 2} = ${sheet.cols * (sheet.rows + 2)}</div>`);
    },
    finale(finale, f) {
        finale.innerHTML = `<div class="g-frame">${manuscript(squares(T('全文完', 'END')), 5, 56, 0).html}</div>`;
        closing(finale, f.chars);
    },
    page(page, number, f) {
        return textPage(page, `<div class="g-top"><span>${esc(f.title)}</span><span>${f.date}</span></div>
            <div class="g-foot"><span>${T('吴长星 著', '吴长星')}</span><span class="folio">${T('第', 'P.')} <b>${number}</b>${T(' 页', '')}<span class="of"></span></span></div>`);
    },
    last(last, f, shown) {
        last.innerHTML = `<div class="g-top"><span>${esc(f.section)}</span><span>${f.date}</span></div>
            <div class="g-frame">${manuscript(squares(f.big), Math.min(5, squares(f.big).length), 56, 0).html}</div>`;
        closing(last, shown);
    },
    total: n => ` / ${n}`,
};

/* 3. 报纸 Broadsheet: a newspaper front page; masthead, double rules, the
   article's own opening set in two columns with a drop cap. ------------- */
LOOKS.news = {
    zh: '报纸', en: 'Broadsheet',
    poster(poster, f) {
        poster.insertAdjacentHTML('beforeend', `<div class="n-ears"><span>${esc(f.section)}</span><span>${f.date}</span></div>
            <div class="n-name">AARON404</div>
            <div class="n-line"><span>${T('吴长星 主笔', 'BY 吴长星')}</span><span>${f.year}</span><span>${T(`全文 ${f.words} 字`, `${f.words} CHARACTERS`)}</span></div>
            <div class="n-head">${esc(f.title)}</div>
            <div class="n-lead"><p>${esc(f.lead)}</p></div>
            <div class="n-foot"><span>AARON404.COM</span><span>A1</span></div>`);
        fitBox(poster.querySelector('.n-head'), 20);
    },
    finale(finale, f) {
        finale.innerHTML = `<div class="n-rule"></div><div class="n-box">${T('扫码阅读原文', 'SCAN TO READ')}</div>`;
        closing(finale, f.chars);
    },
    page(page, number, f) {
        return textPage(page, `<div class="n-top"><b>AARON404</b><span>${f.date}</span></div>
            <div class="n-foot"><span>${esc(f.title)}</span><span class="folio">A<b>${number}</b><span class="of"></span></span></div>`);
    },
    last(last, f, shown) {
        last.innerHTML = `<div class="n-top"><b>AARON404</b><span>${f.date}</span></div><div class="n-box">${T('扫码阅读原文', 'SCAN TO READ')}</div>`;
        const word = element('div', 'big', f.big);
        last.append(word);
        closing(last, shown);
        fit(word, 96, 334, 40);
    },
    total: () => '',
};

/* 4. 瑞士 Swiss: a strict grid, a rule, black type, and one giant blue
   character bleeding off the corner. ------------------------------------ */
LOOKS.swiss = {
    zh: '瑞士', en: 'Swiss',
    poster(poster, f) {
        poster.insertAdjacentHTML('beforeend', `<div class="s-glyph">${esc([...f.big][0])}</div>
            <div class="s-info"><div><i>${T('作者', 'AUTHOR')}</i>吴长星</div><div><i>${T('栏目', 'SECTION')}</i>${esc(f.section)}</div><div><i>${T('日期', 'DATE')}</i>${f.date}</div></div>
            <div class="s-title">${esc(f.title)}</div>
            <div class="s-foot"><span>AARON404.COM</span><span>${f.words} ${T('字', 'CHARS')}</span></div>`);
        fitBox(poster.querySelector('.s-title'), 18);
    },
    finale(finale, f) {
        finale.innerHTML = '<div class="s-block"></div>';
        closing(finale, f.chars);
    },
    page(page, number, f) {
        return textPage(page, `<div class="s-info"><div><i>${T('作者', 'AUTHOR')}</i>吴长星</div><div><i>${T('标题', 'TITLE')}</i>${esc(f.title)}</div>
            <div class="folio"><i>${T('页', 'PAGE')}</i><b>${String(number).padStart(2, '0')}</b><span class="of"></span></div></div>
            <div class="s-foot"><span>AARON404.COM</span><span>${f.date}</span></div>`);
    },
    last(last, f, shown) {
        last.innerHTML = '<div class="s-block"></div>';
        const word = element('div', 'big', f.big);
        last.append(word);
        closing(last, shown);
        fit(word, 120, 334, 48);
    },
};

/* 5. 深夜 Terminal: the article opened in a dark editor at night; front
   matter, a heading and a blinking cursor. ------------------------------ */
function frontMatter(f) {
    const key = text => `<span class="t-k">${text}:</span> `;
    const rows = ['<em>---</em>', `${key('title')}<span class="t-s">"${esc(f.title)}"</span>`, `${key('author')}吴长星`,
                  `${key('date')}<span class="t-n">${f.date}</span>`, `${key('words')}<span class="t-n">${f.words}</span>`, '<em>---</em>'];
    return rows.map((line, index) => `<p><u>${index + 1}</u>${line}</p>`).join('');
}

LOOKS.night = {
    zh: '深夜', en: 'Terminal',
    poster(poster, f) {
        poster.insertAdjacentHTML('beforeend', `<div class="t-win"><div class="t-bar"><i></i><i></i><i></i><span>~/aaron404/${esc(f.section)}.md</span></div>
            <div class="t-code">${frontMatter(f)}</div>
            <div class="t-title"><em># </em>${esc(f.title)}<b class="t-cursor"></b></div>
            <div class="t-prompt"><em>$</em> open aaron404.com</div></div>`);
        fitBox(poster.querySelector('.t-title'), 18);
    },
    finale(finale, f) {
        finale.innerHTML = '<div class="t-win"><div class="t-bar"><i></i><i></i><i></i><span>~ — zsh</span></div><div class="t-prompt"><em>$</em> open ./qr.png</div></div>';
        closing(finale, f.chars);
    },
    page(page, number, f) {
        return textPage(page, `<div class="t-win"><div class="t-bar"><i></i><i></i><i></i><span>${esc(f.title)}.md</span>
            <span class="folio"><b>${String(number).padStart(2, '0')}</b><span class="of"></span></span></div></div>`);
    },
    last(last, f, shown) {
        last.innerHTML = '<div class="t-win"><div class="t-bar"><i></i><i></i><i></i><span>~ — zsh</span></div><div class="t-prompt"><em>$</em> open ./qr.png</div></div>';
        const word = element('div', 'big', f.big);
        last.append(word);
        closing(last, shown);
        fit(word, 96, 318, 40);
    },
};

/* 6. 水墨 Ink: rice paper, ink-wash hills, a red sun, the title set
   vertically and signed with a red seal. --------------------------------- */
const CN = '〇一二三四五六七八九';
const cnNumber = n => n < 10 ? CN[n] : `${n >= 20 ? CN[Math.floor(n / 10)] : ''}十${n % 10 ? CN[n % 10] : ''}`;
const cnYear = year => [...year].map(d => CN[d]).join('');
function cnDate(date) {
    const [year, month, day] = date.split('.');
    return `${cnYear(year)}年${cnNumber(+month)}月${cnNumber(+day)}日`;
}

const SEAL = '<div class="k-seal">吴长星印</div>';
const HILLS = '<div class="k-hills"></div>';

// Shrink a vertical line until it is at most `height` tall.
function fitTall(node, height, smallest) {
    let size = parseFloat(getComputedStyle(node).fontSize);
    while (node.offsetHeight > height && size > smallest) node.style.fontSize = --size + 'px';
}

LOOKS.ink = {
    zh: '水墨', en: 'Ink',
    poster(poster, f) {
        const big = f.big === f.year ? cnYear(f.year) : f.big;
        poster.insertAdjacentHTML('beforeend', `${HILLS}<div class="k-sun"></div>
            <div class="k-big">${esc(big)}</div><div class="k-rest">${esc(f.rest)}</div>
            <div class="k-side">${esc(f.section)}　${cnDate(f.date)}</div>${SEAL}`);
        fitTall(poster.querySelector('.k-big'), 330, 28);
    },
    finale(finale, f) {
        finale.innerHTML = HILLS + SEAL;
        closing(finale, f.chars);
    },
    page(page, number, f) {
        return textPage(page, `${HILLS}<div class="k-side">${esc(f.title)}</div>
            <div class="folio"><b>${cnNumber(number)}</b><span class="of"></span></div>`);
    },
    last(last, f, shown) {
        const big = f.big === f.year ? cnYear(f.year) : f.big;
        last.innerHTML = `${HILLS}<div class="k-sun"></div><div class="k-big">${esc(big)}</div>${SEAL}`;
        closing(last, shown);
        fitTall(last.querySelector('.k-big'), 300, 28);
    },
    total: n => ` / ${cnNumber(n)}`,
};

/* 7. 留白 Quiet: an essay page; a serif title in a field of white, a hairline,
   the author. Almost nothing, placed exactly. ----------------------------- */
LOOKS.quiet = {
    zh: '留白', en: 'Quiet',
    poster(poster, f) {
        poster.insertAdjacentHTML('beforeend', `<div class="q-top">${esc(f.section)}</div>
            <div class="q-title">${esc(f.title)}</div><div class="q-rule"></div>
            <div class="q-by">吴长星</div><div class="q-date">${f.date}</div>`);
        fitBox(poster.querySelector('.q-title'), 18);
    },
    finale(finale, f) {
        closing(finale, f.chars);
    },
    page(page, number, f) {
        return textPage(page, `<div class="q-top">${esc(f.title)}</div><div class="folio">— <b>${number}</b> —<span class="of"></span></div>`);
    },
    last(last, f, shown) {
        const word = element('div', 'big', f.big);
        last.append(word);
        closing(last, shown);
        fit(word, 64, 300, 32);
    },
    total: () => '',
};

/* 8. 包豪斯 Bauhaus: circle, square, triangle in the three primaries on
   cream, with a black bar and a heavy geometric title. ------------------ */
const PRIMARY = { red: '#d6402b', yellow: '#f0b323', blue: '#1f4fa0' };
const MOTIFS = [
    `<circle cx="331" cy="56" r="31" fill="${PRIMARY.blue}"/>`,
    `<rect x="300" y="25" width="62" height="62" fill="${PRIMARY.red}"/>`,
    `<polygon points="331,22 366,88 296,88" fill="${PRIMARY.yellow}"/>`,
];

LOOKS.bauhaus = {
    zh: '包豪斯', en: 'Bauhaus',
    poster(poster, f) {
        poster.insertAdjacentHTML('afterbegin', art(`<circle cx="292" cy="176" r="128" fill="${PRIMARY.blue}"/>`
            + `<rect x="28" y="92" width="58" height="196" fill="${PRIMARY.red}"/>`
            + `<path d="M390 520V392A128 128 0 0 0 262 520Z" fill="${PRIMARY.yellow}"/>`
            + `<rect x="28" y="306" width="334" height="10" fill="${INK}"/>`
            + `<polygon points="120,288 170,198 220,288" fill="${INK}"/>`));
        poster.insertAdjacentHTML('beforeend', `<div class="b-mark">aaron404</div><div class="b-date">${f.date}</div>
            <div class="b-title">${esc(f.title)}</div><div class="b-foot">吴长星 · ${esc(f.section)}</div>`);
        fitBox(poster.querySelector('.b-title'), 18);
    },
    finale(finale, f) {
        finale.innerHTML = art(`<circle cx="300" cy="140" r="104" fill="${PRIMARY.yellow}"/><rect x="0" y="380" width="390" height="40" fill="${INK}"/>`
            + `<rect x="28" y="64" width="40" height="40" fill="${PRIMARY.red}"/>`, 420);
        closing(finale, f.chars);
    },
    page(page, number, f) {
        page.dataset.motif = number % 3;
        return textPage(page, art(MOTIFS[number % 3] + `<rect x="28" y="102" width="56" height="6" fill="${INK}"/>`)
            + `<header>吴长星 · ${esc(f.title)}</header><div class="folio"><b>${number}</b><span class="of"></span></div>`
            + `<div class="b-foot">aaron404</div>`);
    },
    last(last, f, shown) {
        last.innerHTML = art(`<circle cx="294" cy="286" r="118" fill="${PRIMARY.yellow}"/>`
            + `<rect x="0" y="470" width="390" height="50" fill="${INK}"/><rect x="28" y="196" width="40" height="40" fill="${PRIMARY.red}"/>`
            + `<polygon points="96,236 120,196 144,236" fill="${PRIMARY.blue}"/>`);
        const word = element('div', 'big', f.big);
        last.append(word);
        closing(last, shown);
        fit(word, 112, 334, 48);
    },
    total: () => '',
};

/* 9. 小票 Receipt: a thermal-paper reading receipt with torn edges, the
   article's facts as line items, and a barcode drawn from its title. ---- */
function barcode(text) {
    let seed = [...text].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7), x = 0, bars = '';
    while (x < 226) {
        seed = (Math.imul(seed, 1103515245) + 12345) >>> 0;
        const width = 1 + (seed >>> 16) % 3;
        if ((seed >>> 9) & 1 || x === 0) bars += `<rect x="${x}" width="${width}" height="38"/>`;
        x += width;
    }
    return `<svg class="r-code" width="226" height="38" viewBox="0 0 226 38" fill="#1b1b1b" aria-hidden="true">${bars}</svg>`;
}

const row = (label, value, extra = '') => `<div class="r-row${extra}"><span>${label}</span><span>${value}</span></div>`;

LOOKS.receipt = {
    zh: '小票', en: 'Receipt',
    poster(poster, f) {
        poster.insertAdjacentHTML('beforeend', `<div class="r-paper"><div class="r-zig top"></div>
            <div class="r-head"><b>AARON404</b><span>${T('阅 读 小 票', 'READING RECEIPT')}</span></div><div class="r-dash"></div>
            ${row(T('日期', 'DATE'), f.date)}${row(T('栏目', 'SECTION'), esc(f.section))}${row(T('作者', 'AUTHOR'), '吴长星')}<div class="r-dash"></div>
            <div class="r-title">${esc(f.title)}</div><div class="r-dash"></div>
            ${row(T('字数', 'CHARACTERS'), f.words)}${row(T('阅读时长', 'READING TIME'), T(`≈ ${f.minutes} 分钟`, `≈ ${f.minutes} MIN`))}${row(T('合计', 'TOTAL'), T('1 篇', '1 ARTICLE'), ' r-total')}<div class="r-dash"></div>
            <div class="r-thanks">${T('* 谢谢阅读 *', '* THANK YOU *')}</div>${barcode(f.title)}<div class="r-no">No. ${f.date.replace(/\./g, '')}</div>
            <div class="r-zig bot"></div></div>`);
        fitBox(poster.querySelector('.r-title'), 13);
    },
    finale(finale, f) {
        finale.innerHTML = '<div class="r-paper"><div class="r-dash"></div><div class="r-zig bot"></div></div>';
        closing(finale, f.chars);
    },
    page(page, number, f) {
        return textPage(page, `<div class="r-paper"><div class="r-zig top"></div><div class="r-head small"><span>AARON404 · ${esc(f.title)}</span></div>
            <div class="r-dash"></div><div class="r-zig bot"></div></div>
            <div class="r-foot"><span class="folio">— <b>${String(number).padStart(2, '0')}</b><span class="of"></span> —</span></div>`);
    },
    last(last, f, shown) {
        last.innerHTML = `<div class="r-paper"><div class="r-zig top"></div><div class="r-head"><b>AARON404</b><span>${f.date}</span></div>
            <div class="r-dash"></div>${barcode(f.title + 'end')}<div class="r-zig bot"></div></div>`;
        closing(last, shown);
    },
};

/* 10. 极光 Aurora: a soft mesh of the theme blue, violet, rose and peach,
   with a white card carrying the title. --------------------------------- */
LOOKS.aurora = {
    zh: '极光', en: 'Aurora',
    poster(poster, f) {
        poster.insertAdjacentHTML('beforeend', `<div class="a-mesh"></div><div class="a-year">${f.year}</div>
            <div class="a-card"><span class="a-chip">${esc(f.section)}</span><div class="a-title">${esc(f.title)}</div>
            <div class="a-by"><i>吴</i><span>吴长星<small>aaron404.com</small></span><em>${f.date}</em></div></div>`);
        fitBox(poster.querySelector('.a-title'), 18);
    },
    finale(finale, f) {
        finale.innerHTML = '<div class="a-mesh"></div><div class="a-card"></div>';
        closing(finale, f.chars);
    },
    page(page, number, f) {
        return textPage(page, `<div class="a-mesh"></div><div class="a-card"></div><header>${esc(f.title)}</header>
            <div class="folio"><b>${String(number).padStart(2, '0')}</b><span class="of"></span></div>`);
    },
    last(last, f, shown) {
        last.innerHTML = '<div class="a-mesh"></div><div class="a-card"></div>';
        const word = element('div', 'big', f.big);
        last.append(word);
        closing(last, shown);
        fit(word, 96, 310, 40);
    },
};
