#!/usr/bin/env python3
"""Static audit of the CSCE 313 handout site.

Run before pushing:   python3 tools/audit.py

Stands in for a Jekyll build - there is no Ruby on this machine (verified:
ruby/gem/bundle/jekyll are all absent), so the real build only happens on
GitHub. This catches the structural and accessibility mistakes that would
otherwise be found by a student.

Checks: front matter parses and names a real layout; no H1 in a page body; no
heading-level skips; no duplicate heading anchors; images resolve and carry
useful alt text; figures pair an image with a caption; raw HTML is balanced;
liquid tags are balanced; markdown tables have square rows; internal links
resolve; every CSS token used is defined, and every one defined is used.
"""
import os, re, sys, glob
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors, warnings = [], []

CSS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'assets/css/main.css')
css_text = open(CSS_PATH, encoding='utf-8').read() if os.path.exists(CSS_PATH) else ''

def err(f, m):  errors.append((f, m))
def warn(f, m): warnings.append((f, m))

def split_front_matter(text):
    if not text.startswith('---'):
        return None, text
    parts = text.split('---', 2)
    if len(parts) < 3:
        return None, text
    return parts[1], parts[2]

# ---------------------------------------------------------------- pages
# Discovered, not hardcoded: a new lab-N/index.md must never be able to ship
# unaudited just because someone forgot to add it to a list here.
def _lab_key(path):
    m = re.search(r'lab-(\d+)', path)
    return int(m.group(1)) if m else 0

pages = ['index.md', 'labs/index.md', 'activities/index.md'] + sorted(
    os.path.relpath(f, ROOT)
    for pat in ('lab-*', 'activity-*')
    for f in glob.glob(os.path.join(ROOT, pat, 'index.md')))
slug_re = re.compile(r'[^a-z0-9\- ]')

for rel in pages:
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        err(rel, 'missing'); continue
    text = open(path, encoding='utf-8').read()
    fm_raw, body = split_front_matter(text)

    if fm_raw is None:
        err(rel, 'no YAML front matter'); continue
    try:
        fm = yaml.safe_load(fm_raw) or {}
    except Exception as e:
        err(rel, 'front matter does not parse: %s' % e); continue

    if 'layout' not in fm:
        err(rel, 'front matter has no layout')
    else:
        lp = os.path.join(ROOT, '_layouts', fm['layout'] + '.html')
        if not os.path.exists(lp):
            err(rel, 'layout %r does not exist' % fm['layout'])
    if not fm.get('title'):
        err(rel, 'front matter has no title')
    if not fm.get('description'):
        warn(rel, 'no description - weak search/link preview')

    # a placeholder date must never reach students
    for field in ('released', 'due'):
        val = str(fm.get(field, ''))
        if fm.get('lab_number') is not None and not val:
            err(rel, 'front matter has no %s date' % field)
        elif 'TBD' in val.upper() or 'TODO' in val.upper():
            err(rel, '%s is still a placeholder: %r' % (field, val))
    if 'lab_number' in fm and re.search(r'^\| TBD \|', body, re.M):
        err(rel, 'revision history still has a TBD row')

    # ------- headings: no H1 in body (layout owns it), no level skips
    heads = []
    in_fence = False
    for i, line in enumerate(body.splitlines(), 1):
        if line.lstrip().startswith('```'):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2).strip()))

    for ln, lvl, txt in heads:
        if lvl == 1:
            err(rel, 'line %d: H1 in body (%r) - the layout renders the only H1' % (ln, txt))
    prev = 1
    for ln, lvl, txt in heads:
        if lvl > prev + 1:
            err(rel, 'line %d: heading jumps H%d -> H%d (%r)' % (ln, prev, lvl, txt))
        prev = lvl

    # ------- duplicate auto-generated ids
    seen = {}
    for ln, lvl, txt in heads:
        plain = re.sub(r'\{:.*?\}', '', txt)
        plain = re.sub(r'[`*_\[\]()]', '', plain).strip().lower()
        slug = slug_re.sub('', plain).replace(' ', '-')
        if slug in seen:
            err(rel, 'duplicate heading id %r (lines %d and %d)' % (slug, seen[slug], ln))
        seen[slug] = ln

    # ------- images: alt text and resolvable src
    for m in re.finditer(r'<img\s+([^>]*?)>', body, re.S):
        attrs = m.group(1)
        line = body[:m.start()].count('\n') + 1
        srcm = re.search(r'src="([^"]+)"', attrs)
        altm = re.search(r'alt="([^"]*)"', attrs)
        if not altm:
            err(rel, 'line %d: <img> without alt' % line)
        elif not altm.group(1).strip():
            err(rel, 'line %d: <img> with empty alt (decorative? then say so)' % line)
        elif len(altm.group(1).strip()) < 25:
            warn(rel, 'line %d: alt text is very short: %r' % (line, altm.group(1)))
        if srcm:
            src = srcm.group(1)
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), src))
            if not os.path.exists(resolved):
                err(rel, 'line %d: image not found: %s' % (line, src))

    # markdown-style images should not be used (no figcaption)
    for m in re.finditer(r'^!\[', body, re.M):
        line = body[:m.start()].count('\n') + 1
        warn(rel, 'line %d: markdown image - use <figure> so it gets a caption' % line)

    # ------- figures must pair img with figcaption
    for m in re.finditer(r'<figure>(.*?)</figure>', body, re.S):
        line = body[:m.start()].count('\n') + 1
        blk = m.group(1)
        if '<figcaption>' not in blk:
            err(rel, 'line %d: <figure> without <figcaption>' % line)
        if '<img' not in blk:
            err(rel, 'line %d: <figure> without <img>' % line)

    # ------- inline SVG: valid XML, accessible name, styled classes
    for m in re.finditer(r'<svg\b.*?</svg>', body, re.S):
        line = body[:m.start()].count('\n') + 1
        svg = m.group(0)
        try:
            import xml.etree.ElementTree as ET
            ET.fromstring(svg)
        except Exception as e:
            # a common cause is "--" inside an XML comment, which is illegal
            err(rel, 'line %d: inline <svg> is not well-formed XML: %s' % (line, e))
        if 'role="img"' not in svg:
            err(rel, 'line %d: inline <svg> without role="img"' % line)
        has_name = ('aria-labelledby=' in svg and '<title' in svg) or 'aria-label=' in svg
        if not has_name:
            err(rel, 'line %d: inline <svg> has no accessible name' % line)
        if '<desc' not in svg:
            warn(rel, 'line %d: inline <svg> has no <desc> - a diagram needs a long description' % line)
        # every url(#id) must resolve inside THIS svg - relying on an id in a
        # sibling svg works until that svg moves, then fails silently
        own_ids = set(re.findall(r'\sid="([^"]+)"', svg))
        for ref in set(re.findall(r'url\(#([^)]+)\)', svg)):
            if ref not in own_ids:
                err(rel, 'line %d: svg references url(#%s), defined outside this svg' % (line, ref))

        svg_classes = set()
        for c in re.findall(r'class="([^"]+)"', svg):
            svg_classes.update(c.split())
        for c in sorted(svg_classes):
            if ('.' + c) not in css_text:
                err(rel, 'line %d: svg class .%s has no style rule' % (line, c))

    # ------- ids unique across the whole page
    all_ids = re.findall(r'<[^>]*\sid="([^"]+)"', body)
    dupes = set(i for i in all_ids if all_ids.count(i) > 1)
    for d in sorted(dupes):
        err(rel, 'duplicate id="%s" on the page' % d)

    # ------- balanced raw HTML blocks
    for tag in ('figure', 'figcaption', 'nav', 'div', 'aside'):
        o = len(re.findall(r'<%s[\s>]' % tag, body))
        c = len(re.findall(r'</%s>' % tag, body))
        if o != c:
            err(rel, 'unbalanced <%s>: %d open, %d close' % (tag, o, c))

    # ------- tables: consistent column counts
    lines = body.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith('|') and i + 1 < len(lines) and re.match(r'^\s*\|[\s:\-|]+\|\s*$', lines[i+1]):
            head_cols = lines[i].strip().strip('|').count('|') + 1
            j = i + 2
            while j < len(lines) and lines[j].strip().startswith('|'):
                cols = lines[j].strip().strip('|').count('|') + 1
                if cols != head_cols:
                    err(rel, 'line %d: table row has %d cells, header has %d' % (j+1, cols, head_cols))
                j += 1
            i = j
        else:
            i += 1

    # ------- internal links resolve
    for m in re.finditer(r'\]\((?!https?:|mailto:|#)([^)]+)\)', body):
        target = m.group(1).split('#')[0]
        line = body[:m.start()].count('\n') + 1
        if '{{' in target or '{%' in target:
            continue
        if not target:
            continue
        cand = os.path.normpath(os.path.join(os.path.dirname(path), target))
        if not (os.path.exists(cand) or os.path.exists(cand + '.md')
                or os.path.exists(os.path.join(cand, 'index.md'))):
            err(rel, 'line %d: internal link does not resolve: %s' % (line, target))

# ---------------------------------------------------------------- layouts
for lp in glob.glob(os.path.join(ROOT, '_layouts', '*.html')):
    rel = os.path.relpath(lp, ROOT)
    t = open(lp, encoding='utf-8').read()
    for a, b in (('if', 'endif'), ('unless', 'endunless'), ('for', 'endfor')):
        o = len(re.findall(r'\{%-?\s*' + a + r'\s', t))
        c = len(re.findall(r'\{%-?\s*' + b + r'\s*-?%\}', t))
        if o != c:
            err(rel, 'unbalanced liquid {%% %s %%}: %d open, %d close' % (a, o, c))
    if t.count('{{') != t.count('}}'):
        err(rel, 'unbalanced {{ }}')
    if t.count('{%') != t.count('%}'):
        err(rel, 'unbalanced {%% %%}')

# ---------------------------------------------------------------- css
css_path = os.path.join(ROOT, 'assets/css/main.css')
css = open(css_path, encoding='utf-8').read()
defined = set(re.findall(r'(--[a-z0-9\-]+)\s*:', css))
used = set(re.findall(r'var\((--[a-z0-9\-]+)', css))
for v in sorted(used - defined):
    err('assets/css/main.css', 'var(%s) used but never defined' % v)
for v in sorted(defined - used):
    warn('assets/css/main.css', '%s defined but never used' % v)

# house rule: colours only inside :root blocks
root_spans = [m.span() for m in re.finditer(r':root[^{]*\{[^}]*\}', css, re.S)]
print_span = re.search(r'@media print\s*\{', css)
print_start = print_span.start() if print_span else len(css)
def in_root(pos):
    if pos >= print_start:
        return True   # print styles legitimately force #000/#fff
    return any(a <= pos <= b for a, b in root_spans)
for m in re.finditer(r'#[0-9a-fA-F]{3,8}\b', css):
    if not in_root(m.start()):
        line = css[:m.start()].count('\n') + 1
        warn('assets/css/main.css', 'line %d: literal colour %s outside :root' % (line, m.group(0)))

# both themes must define the same token set
light = re.search(r':root\s*\{(.*?)\}', css, re.S)
dark  = re.search(r'prefers-color-scheme:\s*dark.*?:root\s*\{(.*?)\}', css, re.S)
if light and dark:
    lt = set(re.findall(r'(--[a-z0-9\-]+)\s*:', light.group(1)))
    dk = set(re.findall(r'(--[a-z0-9\-]+)\s*:', dark.group(1)))
    colourish = re.compile(r'--(brand|bg|surface|border|text|focus|note|warn|shadow)')
    for v in sorted(c for c in lt - dk if colourish.match(c)):
        warn('assets/css/main.css', '%s has no dark-mode value' % v)

# ---------------------------------------------------------------- report
print('=' * 62)
print(' CSCE 313 handout site audit')
print('=' * 62)
print('\nPages audited (%d): %s' % (len(pages), ', '.join(pages) if pages else 'NONE'))
if errors:
    print('\nERRORS (%d)' % len(errors))
    for f, m in errors:
        print('  %-18s %s' % (f, m))
else:
    print('\nERRORS: none')
if warnings:
    print('\nWARNINGS (%d)' % len(warnings))
    for f, m in warnings:
        print('  %-18s %s' % (f, m))
print()
sys.exit(1 if errors else 0)
