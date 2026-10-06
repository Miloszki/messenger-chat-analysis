'use strict'

// Renders a month summary purely from report.json (see mca/core/report.py).
// The report is loaded from ?report=<url> or ./report.json; every relative
// path inside it (photos, videos) is resolved against the report's own URL.

const REPORT_URL = new URL(
  new URLSearchParams(location.search).get('report') || 'report.json',
  location.href,
)

const LOCALE = 'pl-PL'
// matplotlib Set2, assigned to sorted labels exactly like day_label_calendar.png
const LABEL_PALETTE = ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f', '#e5c494', '#b3b3b3']
const WORD_COLORS = ['#667eea', '#764ba2', '#e53e8a', '#3b82f6', '#16a34a', '#f59e0b', '#0ea5e9', '#a855f7']
const WEEKDAYS_SHORT = ['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'Sb', 'Nd']

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

function h(tag, attrs, ...children) {
  const el = document.createElement(tag)
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value == null || value === false) continue
    if (key === 'class') el.className = value
    else if (key === 'style') Object.assign(el.style, value)
    else if (key === 'dataset') Object.assign(el.dataset, value)
    else if (key.startsWith('on')) el.addEventListener(key.slice(2), value)
    else el.setAttribute(key, value === true ? '' : value)
  }
  appendChildren(el, children)
  return el
}

function appendChildren(el, children) {
  for (const child of children.flat(Infinity)) {
    if (child == null || child === false) continue
    el.append(child instanceof Node ? child : document.createTextNode(String(child)))
  }
}

const fmt = (n) => (n == null ? '–' : Number(n).toLocaleString(LOCALE, { maximumFractionDigits: 1 }))
const assetUrl = (path) => new URL(path, REPORT_URL).href
const nonEmpty = (arr) => Array.isArray(arr) && arr.length > 0

function parseDate(iso) {
  const [y, m, d] = iso.slice(0, 10).split('-').map(Number)
  return new Date(y, m - 1, d)
}

function formatLongDate(iso) {
  return parseDate(iso).toLocaleDateString(LOCALE, { weekday: 'long', day: 'numeric', month: 'long' })
}

function formatTime(isoDateTime) {
  return isoDateTime.slice(11, 16)
}

function plural(n, one, few, many) {
  if (n === 1) return one
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few
  return many
}

function labelColors(labels) {
  const unique = [...new Set(labels.filter((l) => l != null))].sort()
  return Object.fromEntries(unique.map((l, i) => [l, LABEL_PALETTE[i % LABEL_PALETTE.length]]))
}

// deterministic shuffle so the word cloud layout is stable between reloads
function stableShuffle(items, key) {
  const hash = (s) => {
    let x = 2166136261
    for (const ch of s) x = Math.imul(x ^ ch.codePointAt(0), 16777619)
    return x >>> 0
  }
  return [...items].sort((a, b) => hash(key(a)) - hash(key(b)))
}

function sectionShell(id, title, ...children) {
  return h('section', { id }, h('h2', { class: 'section-title' }, title), children)
}

function subsection(title, ...children) {
  return h('div', { class: 'subsection' }, h('h3', { class: 'section-subtitle' }, title), children)
}

function emptyNote(text) {
  return h('p', { class: 'empty-state-inline' }, text)
}

// ---------------------------------------------------------------------------
// reusable components
// ---------------------------------------------------------------------------

function barChart(rows, { markers = [], format = fmt } = {}) {
  const max = Math.max(...rows.map((r) => r.value), ...markers.map((m) => m.value), 1)
  const pct = (v) => `${(v / max) * 88}%` // leave room for the value label

  const chart = h('div', { class: 'bar-chart' })
  for (const row of rows) {
    chart.append(
      h(
        'div',
        { class: 'bar-row', title: `${row.label}: ${format(row.value)}` },
        h('div', { class: 'bar-label' }, row.label),
        h(
          'div',
          { class: 'bar-track' },
          h('div', { class: 'bar-fill', style: { width: pct(row.value), background: row.color || null } }),
          h('span', { class: 'bar-value', style: { left: pct(row.value) } }, format(row.value)),
        ),
      ),
    )
  }

  if (markers.length) {
    // markers live in the track column, so offset them past the label column
    const layer = h('div', { class: 'bar-markers' })
    for (const m of markers) {
      layer.append(h('div', { class: `bar-marker ${m.kind}`, style: { left: pct(m.value) }, title: m.title }))
    }
    chart.append(layer)
    new ResizeObserver(() => {
      const track = chart.querySelector('.bar-track')
      if (!track) return
      layer.style.left = `${track.offsetLeft}px`
      layer.style.width = `${track.offsetWidth}px`
    }).observe(chart)
  }
  return chart
}

function sortableTable(columns, rows, defaultSort) {
  let sortKey = defaultSort.key
  let asc = defaultSort.asc ?? false

  const thead = h('thead')
  const tbody = h('tbody')
  const table = h('table', { class: 'data-table' }, thead, tbody)

  function render() {
    const sorted = [...rows].sort((a, b) => {
      const va = a[sortKey]
      const vb = b[sortKey]
      if (va == null && vb == null) return 0
      if (va == null) return 1
      if (vb == null) return -1
      const cmp = typeof va === 'string' ? va.localeCompare(vb, LOCALE) : va - vb
      return asc ? cmp : -cmp
    })

    thead.replaceChildren(
      h(
        'tr',
        null,
        columns.map((col) =>
          h(
            'th',
            {
              class: [col.numeric && 'num', col.key === sortKey && 'sorted', col.key === sortKey && asc && 'asc']
                .filter(Boolean)
                .join(' '),
              onclick: () => {
                if (sortKey === col.key) asc = !asc
                else {
                  sortKey = col.key
                  asc = !col.numeric
                }
                render()
              },
            },
            col.title,
          ),
        ),
      ),
    )
    tbody.replaceChildren(
      ...sorted.map((row) =>
        h(
          'tr',
          null,
          columns.map((col) =>
            h('td', { class: col.numeric ? 'num' : null }, col.render ? col.render(row) : fmt(row[col.key])),
          ),
        ),
      ),
    )
  }

  render()
  return h('div', { class: 'table-wrapper' }, table)
}

function rankList(items, nameKey) {
  return h(
    'ol',
    { class: 'rank-list' },
    items.map((item) =>
      h(
        'li',
        null,
        h('span', { class: 'rl-rank' }, item.rank),
        h('span', { class: 'rl-name' }, item[nameKey]),
        h('span', { class: 'rl-count' }, fmt(item.count)),
      ),
    ),
  )
}

function rankBadge(rank) {
  return rank ? h('span', { class: `rank-badge r${rank}` }, rank) : '–'
}

// ---------------------------------------------------------------------------
// sections — each returns an element, or null when the data is missing
// ---------------------------------------------------------------------------

function renderStats(report) {
  const { chat, participants, words, emojis, media } = report
  const sum = (key) => (participants || []).reduce((acc, p) => acc + (p[key] || 0), 0)

  const cards = [
    {
      primary: true,
      icon: '💬',
      label: 'Wiadomości',
      value: chat?.message_count,
      sub: chat?.participant_count != null ? `od ${fmt(chat.participant_count)} uczestników` : null,
    },
    { icon: '📸', iconClass: 'stat-icon-image', label: 'Wysłane zdjęcia', value: participants ? sum('photo_count') : null,
      sub: nonEmpty(media?.photos) ? `${media.photos.length} w topce` : null },
    { icon: '🎬', iconClass: 'stat-icon-video', label: 'Wysłane filmy', value: participants ? sum('video_count') : null,
      sub: nonEmpty(media?.videos) ? `${media.videos.length} w topce` : null },
    { icon: '🔤', iconClass: 'stat-icon-text', label: 'Słowa', value: words?.total_count,
      sub: words ? `${fmt(words.unique_count)} unikalnych` : null },
    { icon: '😀', label: 'Emoji', value: emojis?.total_count, sub: emojis ? `${fmt(emojis.unique_count)} unikalnych` : null },
  ].filter((c) => c.value != null)

  if (!cards.length) return null

  return h(
    'div',
    { class: 'stats-grid', id: 'stats' },
    cards.map((c) =>
      h(
        'div',
        { class: `stat-card${c.primary ? ' stat-card-primary' : ''}` },
        h('div', { class: `stat-icon ${c.iconClass || ''}` }, c.icon),
        h(
          'div',
          { class: 'stat-content' },
          h('p', { class: 'stat-label' }, c.label),
          h('p', { class: 'stat-value' }, fmt(c.value)),
          c.sub && h('p', { class: 'stat-sublabel' }, c.sub),
        ),
      ),
    ),
  )
}

function renderTop3(report) {
  const items = report.top_participants?.items
  if (!nonEmpty(items)) return null
  return sectionShell(
    'top3',
    'Top 3 aktywni na grupie',
    h(
      'div',
      { class: 'panel' },
      h(
        'div',
        { class: 'podium' },
        items.map((p) =>
          h(
            'div',
            { class: `podium-place rank-${p.rank}` },
            h('div', { class: 'podium-name' }, p.name),
            h('div', { class: 'podium-count' }, `${fmt(p.message_count)} wiadomości`),
            h('div', { class: 'podium-block' }, p.rank),
          ),
        ),
      ),
    ),
  )
}

function renderParticipants(report) {
  const participants = report.participants
  if (!nonEmpty(participants)) return null
  const volume = report.message_volume || {}
  const threshold = volume.min_messages_threshold ?? 0

  const chartRows = participants
    .filter((p) => p.message_count > threshold)
    .map((p) => ({ label: p.name, value: p.message_count }))

  const markers = []
  if (volume.mean != null) markers.push({ kind: 'mean', value: volume.mean, title: `Średnia: ${fmt(volume.mean)}` })
  if (volume.median != null) markers.push({ kind: 'median', value: volume.median, title: `Mediana: ${fmt(volume.median)}` })

  const chart = chartRows.length
    ? h(
        'div',
        { class: 'panel' },
        barChart(chartRows, { markers }),
        markers.length &&
          h(
            'div',
            { class: 'chart-legend' },
            volume.mean != null &&
              h('span', { class: 'legend-item' }, h('span', { class: 'legend-line', style: { borderColor: '#e53e3e' } }),
                `Średnia: ${fmt(volume.mean)}`),
            volume.median != null &&
              h('span', { class: 'legend-item' }, h('span', { class: 'legend-line', style: { borderColor: '#38a169' } }),
                `Mediana: ${fmt(volume.median)}`),
          ),
      )
    : emptyNote(`Nikt nie wysłał więcej niż ${threshold} wiadomości`)

  const columns = [
    { key: 'podium_rank', title: '🏆', render: (p) => rankBadge(p.podium_rank) },
    { key: 'name', title: 'Uczestnik', render: (p) => p.name },
    { key: 'message_count', title: 'Wiadomości', numeric: true },
    { key: 'avg_message_length', title: 'Śr. długość', numeric: true },
    { key: 'emoji_count', title: 'Emoji', numeric: true },
    { key: 'photo_count', title: 'Zdjęcia', numeric: true },
    { key: 'video_count', title: 'Filmy', numeric: true },
  ].filter((col) => !col.numeric || participants.some((p) => p[col.key] != null)) // drop columns with no data
  const table = sortableTable(
    columns,
    participants,
    { key: 'message_count' },
  )

  return h(
    'section',
    { id: 'participants' },
    h(
      'div',
      { class: 'section-header' },
      h('h2', { class: 'section-title' }, 'Wiadomości na osobę'),
      threshold ? h('span', { class: 'section-note' }, `wykres: więcej niż ${threshold} wiadomości`) : null,
    ),
    chart,
    subsection('Wszyscy uczestnicy', table),
  )
}

function renderMessageLength(report) {
  const items = report.message_length?.items
  if (!nonEmpty(items)) return null
  return sectionShell(
    'avg-lengths',
    'Średnia długość wiadomości',
    h(
      'div',
      { class: 'panel' },
      barChart(items.map((i) => ({ label: i.name, value: i.avg_length })), {
        format: (v) => `${fmt(v)} zn.`,
      }),
    ),
  )
}

function renderWords(report) {
  const words = report.words
  if (!nonEmpty(words?.items)) return null

  const cloudItems = words.items.slice(0, 80)
  const max = cloudItems[0].count
  const min = cloudItems[cloudItems.length - 1].count
  const scale = (c) => (max === min ? 0.5 : Math.sqrt((c - min) / (max - min)))

  const cloud = h(
    'div',
    { class: 'word-cloud panel' },
    stableShuffle(cloudItems, (w) => w.word).map((w) =>
      h(
        'span',
        {
          title: `#${w.rank} ${w.word}: ${fmt(w.count)}`,
          style: {
            fontSize: `${0.8 + scale(w.count) * 2.8}rem`,
            color: WORD_COLORS[w.rank % WORD_COLORS.length],
            opacity: String(0.55 + scale(w.count) * 0.45),
          },
        },
        w.word,
      ),
    ),
  )

  return h(
    'section',
    { id: 'words' },
    h(
      'div',
      { class: 'section-header' },
      h('h2', { class: 'section-title' }, 'Najczęściej używane słowa'),
      h('span', { class: 'section-note' }, `top ${cloudItems.length} z ${fmt(words.unique_count)} unikalnych`),
    ),
    h('div', { class: 'word-layout' }, cloud, rankList(words.items.slice(0, 10), 'word')),
  )
}

function renderEmojis(report) {
  const items = report.emojis?.items
  if (!nonEmpty(items)) return null
  const max = items[0].count
  return sectionShell(
    'emojis',
    'Najczęściej używane emoji',
    h(
      'div',
      { class: 'emoji-grid' },
      items.map((e) =>
        h(
          'div',
          { class: 'emoji-tile', title: `#${e.rank}: ${fmt(e.count)}` },
          h('span', { class: 'emoji-char', style: { fontSize: `${1.4 + Math.sqrt(e.count / max) * 1.6}rem` } }, e.emoji),
          h('span', { class: 'emoji-count' }, `×${fmt(e.count)}`),
        ),
      ),
    ),
  )
}

function renderActiveDays(report) {
  const items = report.activity?.most_active_days?.items
  if (!nonEmpty(items)) return null
  const colors = labelColors((report.activity.day_labels?.items || []).map((d) => d.label))

  return sectionShell(
    'active-days',
    'Najbardziej aktywne dni',
    h(
      'div',
      { class: 'day-cards' },
      items.map((d) =>
        h(
          'div',
          { class: 'day-card' },
          h('div', { class: 'day-card-rank' }, `#${d.rank}`),
          h('div', { class: 'day-card-date' }, formatLongDate(d.date)),
          h('div', { class: 'day-card-count' }, fmt(d.message_count), h('small', null, 'wiadomości')),
          d.label && h('span', { class: 'label-pill', style: { background: colors[d.label] || '#e2e8f0' } }, d.label),
        ),
      ),
    ),
  )
}

function renderCalendar(report) {
  const dayLabels = report.activity?.day_labels
  const month = report.chat?.month
  if (!nonEmpty(dayLabels?.items) || !month) return null

  const byDate = Object.fromEntries(dayLabels.items.map((d) => [d.date, d.label]))
  const colors = labelColors(dayLabels.items.map((d) => d.label))
  const daysInMonth = new Date(month.year, month.number, 0).getDate()
  const leadingBlanks = (new Date(month.year, month.number - 1, 1).getDay() + 6) % 7 // Monday-first

  const grid = h('div', { class: 'calendar' }, WEEKDAYS_SHORT.map((d) => h('div', { class: 'calendar-head' }, d)))
  for (let i = 0; i < leadingBlanks; i++) grid.append(h('div', { class: 'calendar-cell empty' }))
  for (let day = 1; day <= daysInMonth; day++) {
    const iso = `${month.year}-${String(month.number).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    const label = byDate[iso]
    grid.append(
      h(
        'div',
        {
          class: `calendar-cell${label ? '' : ' no-label'}`,
          style: { background: label ? colors[label] : null },
          title: `${formatLongDate(iso)}${label ? ` — ${label}` : ' — brak wiadomości'}`,
        },
        day,
      ),
    )
  }

  const counts = dayLabels.label_counts || {}
  const legend = h(
    'div',
    { class: 'calendar-legend' },
    Object.keys(colors).map((label) =>
      h(
        'span',
        { class: 'legend-item' },
        h('span', { class: 'legend-swatch', style: { background: colors[label] } }),
        label,
        counts[label] != null &&
          h('span', { class: 'legend-count' }, `(${counts[label]} ${plural(counts[label], 'dzień', 'dni', 'dni')})`),
      ),
    ),
  )

  return sectionShell(
    'calendar',
    'Kalendarz dni',
    h('div', { class: 'panel calendar-layout' }, grid, legend),
  )
}

function renderSummaries(report) {
  const s = report.summaries
  if (!s) return null
  const parts = []

  if (s.month?.text) {
    parts.push(subsection('Podsumowanie miesiąca', h('p', { class: 'summary-text' }, s.month.text)))
  }

  if (nonEmpty(s.active_days)) {
    parts.push(
      subsection(
        'Najbardziej aktywne dni',
        h(
          'div',
          { class: 'card-list' },
          s.active_days.map((d) =>
            h(
              'div',
              { class: 'day-summary-card' },
              h('div', { class: 'day-summary-date' }, formatLongDate(d.date)),
              h('p', { class: 'day-summary-text' }, d.summary),
            ),
          ),
        ),
      ),
    )
  }

  if (nonEmpty(s.ollama_digest?.threads)) {
    parts.push(
      subsection(
        'Wątki rozmów',
        h(
          'div',
          { class: 'card-list' },
          s.ollama_digest.threads.map((t) =>
            h(
              'div',
              { class: 'digest-thread-card' },
              h(
                'div',
                { class: 'digest-thread-header' },
                h(
                  'span',
                  { class: 'digest-thread-title' },
                  `Wątek ${t.rank} · ${formatLongDate(t.start)}, ${formatTime(t.start)}–${formatTime(t.end)}`,
                ),
                h(
                  'div',
                  { class: 'digest-thread-stats' },
                  h('span', { class: 'digest-stat' }, `${fmt(t.message_count)} wiad.`),
                  h('span', { class: 'digest-stat' }, `★ ${Number(t.importance_score).toFixed(1)}`),
                ),
              ),
              nonEmpty(t.keywords) &&
                h('div', { class: 'digest-thread-topic' }, t.keywords.map((k) => h('span', { class: 'digest-keyword' }, k))),
              nonEmpty(t.authors) && h('div', { class: 'digest-participants' }, t.authors.join(' · ')),
              t.summary && h('p', { class: 'digest-thread-summary' }, t.summary),
            ),
          ),
        ),
      ),
    )
  }

  if (s.digest?.text) {
    parts.push(
      subsection(
        'Digest algorytmiczny',
        h('details', { class: 'raw-digest' }, h('summary', null, 'Pokaż pełny tekst'), h('pre', null, s.digest.text)),
      ),
    )
  }

  if (!parts.length) return null
  return sectionShell('summaries', 'AI Podsumowanie', parts)
}

function renderLinks(report) {
  const links = report.links
  if (!nonEmpty(links?.items)) return null
  return h(
    'section',
    { id: 'links' },
    h(
      'div',
      { class: 'section-header' },
      h('h2', { class: 'section-title' }, 'Linki'),
      h('span', { class: 'section-note' }, `top ${links.items.length} z ${fmt(links.total_count)}`),
    ),
    h(
      'div',
      { class: 'links-list' },
      links.items.map((link) => {
        const href = /^[a-z]+:\/\//i.test(link.url) ? link.url : `https://${link.url}`
        return h(
          'div',
          { class: 'link-item' },
          h('a', { class: 'link-url', href, target: '_blank', rel: 'noopener noreferrer' }, link.url),
          h(
            'div',
            { class: 'link-meta' },
            h('span', { class: 'link-sender' }, `wysłane przez ${link.sender}`),
            h('span', { class: 'link-reactions' },
              `${link.reaction_count} ${plural(link.reaction_count, 'reakcja', 'reakcje', 'reakcji')}`),
          ),
        )
      }),
    ),
  )
}

function renderMedia(report, kind) {
  const items = report.media?.[kind]
  if (!nonEmpty(items)) return null
  const isVideo = kind === 'videos'

  const grid = h(
    'div',
    { class: 'media-grid' },
    items.map((item, index) =>
      h(
        'button',
        {
          class: 'media-item',
          type: 'button',
          title: `${item.sender} · ${item.reaction_count} reakcji`,
          onclick: () => Lightbox.open(items, index, isVideo),
        },
        isVideo
          ? [
              h('video', { src: `${assetUrl(item.path)}#t=0.1`, preload: 'metadata', muted: true }),
              h('div', { class: 'video-overlay' }, playIcon()),
            ]
          : h('img', { src: assetUrl(item.path), alt: `Zdjęcie od ${item.sender}`, loading: 'lazy' }),
        h('span', { class: `rank-badge media-rank ${item.rank <= 3 ? `r${item.rank}` : ''}`,
          style: item.rank > 3 ? { background: 'rgba(0,0,0,0.6)' } : null }, item.rank),
        h(
          'div',
          { class: 'media-badge' },
          h('span', { class: 'mb-sender' }, item.sender),
          h('span', { class: 'mb-reactions' }, `❤ ${item.reaction_count}`),
        ),
      ),
    ),
  )

  return sectionShell(
    isVideo ? 'videos' : 'photos',
    isVideo ? `Top ${items.length} nagrania` : `Top ${items.length} zdjęcia`,
    grid,
  )
}

function playIcon() {
  const ns = 'http://www.w3.org/2000/svg'
  const svg = document.createElementNS(ns, 'svg')
  svg.setAttribute('width', '48')
  svg.setAttribute('height', '48')
  svg.setAttribute('viewBox', '0 0 24 24')
  svg.setAttribute('fill', 'white')
  const path = document.createElementNS(ns, 'path')
  path.setAttribute('d', 'M8 5v14l11-7z')
  svg.append(path)
  return svg
}

// ---------------------------------------------------------------------------
// lightbox
// ---------------------------------------------------------------------------

const Lightbox = {
  el: document.getElementById('lightbox'),
  items: [],
  index: 0,
  isVideo: false,

  open(items, index, isVideo) {
    Object.assign(this, { items, index, isVideo })
    this.el.hidden = false
    document.body.style.overflow = 'hidden'
    this.render()
  },

  close() {
    this.el.hidden = true
    document.body.style.overflow = ''
    document.getElementById('lightbox-media').replaceChildren()
  },

  step(delta) {
    const next = this.index + delta
    if (next < 0 || next >= this.items.length) return
    this.index = next
    this.render()
  },

  render() {
    const item = this.items[this.index]
    const src = assetUrl(item.path)
    document.getElementById('lightbox-media').replaceChildren(
      this.isVideo ? h('video', { src, controls: true, autoplay: true }) : h('img', { src, alt: `Zdjęcie od ${item.sender}` }),
    )
    document.getElementById('lightbox-caption').textContent =
      `#${item.rank} · ${item.sender} · ${item.reaction_count} ${plural(item.reaction_count, 'reakcja', 'reakcje', 'reakcji')}`
    document.getElementById('lightbox-counter').textContent = `${this.index + 1} / ${this.items.length}`
    this.el.querySelector('.lightbox-prev').disabled = this.index === 0
    this.el.querySelector('.lightbox-next').disabled = this.index === this.items.length - 1
  },

  init() {
    this.el.addEventListener('click', (e) => {
      const action = e.target.closest('[data-action]')?.dataset.action
      if (action === 'close' || e.target === this.el) this.close()
      else if (action === 'prev') this.step(-1)
      else if (action === 'next') this.step(1)
    })
    document.addEventListener('keydown', (e) => {
      if (this.el.hidden) return
      if (e.key === 'Escape') this.close()
      else if (e.key === 'ArrowLeft') this.step(-1)
      else if (e.key === 'ArrowRight') this.step(1)
    })
  },
}

// ---------------------------------------------------------------------------
// page shell: header, nav with scroll spy, dark mode
// ---------------------------------------------------------------------------

const SECTIONS = [
  { id: 'top3', icon: '🏆', label: 'Top 3', render: renderTop3 },
  { id: 'participants', icon: '👥', label: 'Uczestnicy', render: renderParticipants },
  { id: 'words', icon: '🔤', label: 'Słowa', render: renderWords },
  { id: 'emojis', icon: '😀', label: 'Emoji', render: renderEmojis },
  { id: 'active-days', icon: '🔥', label: 'Aktywne dni', render: renderActiveDays },
  { id: 'calendar', icon: '📅', label: 'Kalendarz', render: renderCalendar },
  { id: 'summaries', icon: '🤖', label: 'AI Podsumowanie', render: renderSummaries },
  { id: 'links', icon: '🔗', label: 'Linki', render: renderLinks },
  { id: 'avg-lengths', icon: '📏', label: 'Długość wiad.', render: renderMessageLength },
  { id: 'photos', icon: '📸', label: 'Zdjęcia', render: (r) => renderMedia(r, 'photos') },
  { id: 'videos', icon: '🎬', label: 'Nagrania', render: (r) => renderMedia(r, 'videos') },
]

function renderHeader(report) {
  const chat = report.chat || {}
  const month = chat.month
  const monthName = month
    ? new Date(month.year, month.number - 1, 1).toLocaleDateString(LOCALE, { month: 'long', year: 'numeric' })
    : ''
  document.getElementById('title').replaceChildren(chat.name || 'Czat', monthName ? h('small', null, monthName) : '')
  document.title = `MCA - ${chat.name || 'Podsumowanie'}${monthName ? ` · ${monthName}` : ''}`

  if (chat.period) {
    const opts = { day: 'numeric', month: 'short' }
    const from = new Date(chat.period.first_message_at).toLocaleDateString(LOCALE, opts)
    const to = new Date(chat.period.last_message_at).toLocaleDateString(LOCALE, opts)
    document.getElementById('header-period').textContent = `${from} – ${to}`
  }
}

function renderNav(rendered) {
  const nav = document.getElementById('nav')
  const buttons = {}
  for (const { id, icon, label } of rendered) {
    buttons[id] = h(
      'button',
      {
        class: 'nav-item',
        type: 'button',
        title: label,
        onclick: () => document.getElementById(id).scrollIntoView({ behavior: 'smooth', block: 'start' }),
      },
      h('span', { class: 'nav-icon' }, icon),
      h('span', { class: 'nav-label' }, label),
    )
    nav.append(buttons[id])
  }

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue
        for (const [id, btn] of Object.entries(buttons)) btn.classList.toggle('active', id === entry.target.id)
      }
    },
    { rootMargin: '-20% 0px -70% 0px', threshold: 0 },
  )
  for (const { id } of rendered) observer.observe(document.getElementById(id))
  nav.hidden = rendered.length === 0
}

function initDarkMode() {
  const button = document.getElementById('dark-toggle')
  const sync = () => {
    const dark = document.documentElement.classList.contains('dark')
    button.textContent = dark ? '☀️' : '🌙'
    button.title = dark ? 'Tryb jasny' : 'Tryb ciemny'
  }
  button.addEventListener('click', () => {
    const dark = document.documentElement.classList.toggle('dark')
    try {
      localStorage.setItem('darkMode', String(dark))
    } catch (e) {}
    sync()
  })
  sync()
}

function showError(message, detail) {
  document.getElementById('loading').hidden = true
  document.getElementById('error').hidden = false
  document.getElementById('error-message').textContent = message
  document.getElementById('error-detail').textContent = detail || ''
}

async function main() {
  initDarkMode()
  Lightbox.init()

  // report.js (window.MCA_REPORT) works from file://; ?report=<url> always wins over it
  const explicitReport = new URLSearchParams(location.search).has('report')
  let report = !explicitReport ? window.MCA_REPORT : null
  if (!report) try {
    const response = await fetch(REPORT_URL)
    if (!response.ok) throw new Error(`HTTP ${response.status} dla ${REPORT_URL.pathname}`)
    report = await response.json()
  } catch (err) {
    const hint = location.protocol === 'file:' ? ' — brak report.js obok index.html (albo otwórz przez serwer HTTP)' : ''
    showError('Nie udało się wczytać report.json', `${err.message}${hint}`)
    return
  }

  renderHeader(report)

  const content = document.getElementById('content')
  const stats = renderStats(report)
  if (stats) content.append(stats)

  const rendered = []
  for (const section of SECTIONS) {
    let el = null
    try {
      el = section.render(report)
    } catch (err) {
      console.error(`Section ${section.id} failed to render`, err)
    }
    if (!el) continue
    el.style.animationDelay = `${Math.min(rendered.length, 8) * 0.06}s`
    content.append(el)
    rendered.push(section)
  }

  const footer = document.getElementById('footer')
  footer.textContent = report.generated_at
    ? `Wygenerowano ${new Date(report.generated_at).toLocaleString(LOCALE)} · schemat v${report.schema_version}`
    : ''

  document.getElementById('loading').hidden = true
  for (const id of ['header', 'content', 'footer']) document.getElementById(id).hidden = false
  renderNav(rendered)
}

main()
