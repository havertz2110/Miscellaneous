/*
 * Facebook friends → .txt extractor (browser-console script)
 *
 * Usage:
 *   1. Log in to Facebook, open https://www.facebook.com/friends/list
 *   2. Press F12 → Console tab
 *   3. Paste this entire file, press Enter
 *   4. Script auto-scrolls, collects, then downloads `facebook-friends-YYYY-MM-DD.txt`
 *
 * Output format (tab-separated — opens in Excel/Sheets as 2 columns):
 *   Name<TAB>profileURL
 *
 * Notes:
 *   - Relies on Facebook's current DOM. FB changes their DOM regularly; if it
 *     stops working, update the selector in `harvest()`.
 *   - Never runs outside the browser; no data leaves your machine.
 */

(async () => {
  const SCROLL_DELAY_MS = 1200;   // wait after each scroll
  const STABLE_ROUNDS   = 4;      // stop when this many consecutive rounds add nothing
  const HARD_TIMEOUT_MS = 10 * 60 * 1000; // 10 min safety cap

  /** profileURL -> name (Map provides natural dedup + insertion order) */
  const found = new Map();

  /** Strip Facebook tracking params (__cft__, __tn__, eav, paipv, …) */
  const normalizeUrl = (href) => {
    try {
      const u = new URL(href, location.origin);
      for (const k of [...u.searchParams.keys()]) {
        if (k.startsWith('__') || k === 'eav' || k === 'paipv' || k === 'rdid') {
          u.searchParams.delete(k);
        }
      }
      return u.origin + u.pathname + (u.search || '');
    } catch {
      return href;
    }
  };

  /** Return true if this href looks like a profile link (not a group/page/etc.) */
  const looksLikeProfile = (href) => {
    if (!href) return false;
    if (!/facebook\.com\//.test(href) && !href.startsWith('/')) return false;
    if (/\/(groups|pages|photo|watch|events|marketplace|stories|reel|video|media|gaming|ads|business)\//.test(href)) return false;
    return true;
  };

  /** Scrape the current DOM for friend anchors and merge into `found` */
  const harvest = () => {
    const anchors = document.querySelectorAll(
      'a[href*="facebook.com/"][role="link"], a[href^="/"][role="link"]'
    );
    for (const a of anchors) {
      const raw = a.getAttribute('href');
      if (!looksLikeProfile(raw)) continue;

      const name = (a.innerText || a.textContent || '').trim();
      if (!name || name.length > 80) continue;        // empty / too long -> likely not a person
      if (!/\p{L}/u.test(name)) continue;             // must contain at least one letter

      const key = normalizeUrl(raw);
      // Keep the longest name seen for this URL (some anchors are avatar-only with no text)
      const prev = found.get(key);
      if (!prev || name.length > prev.length) found.set(key, name);
    }
  };

  const startedAt = Date.now();
  let stable = 0;
  let lastHeight = -1;
  let lastCount = -1;

  console.log('%c[FB-Friends] Starting…', 'color:#4ade80;font-weight:bold');

  // Pass 1 — scroll down until stable or timeout
  while (stable < STABLE_ROUNDS && Date.now() - startedAt < HARD_TIMEOUT_MS) {
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(r => setTimeout(r, SCROLL_DELAY_MS));
    harvest();

    const h = document.body.scrollHeight;
    const c = found.size;
    if (h === lastHeight && c === lastCount) stable++;
    else { stable = 0; lastHeight = h; lastCount = c; }
    console.log(`[FB-Friends] scroll… height=${h} collected=${c}`);
  }

  // Pass 2 — scroll back up to recover items virtualized out of the DOM
  console.log('[FB-Friends] reverse pass to recover virtualized entries…');
  for (let y = document.body.scrollHeight; y >= 0; y -= 800) {
    window.scrollTo(0, y);
    await new Promise(r => setTimeout(r, 250));
    harvest();
  }

  // Build sorted result
  const result = [...found.entries()]
    .map(([profileURL, name]) => ({ name, profileURL }))
    .sort((a, b) => a.name.localeCompare(b.name, 'vi'));

  // --- Export .txt (tab-separated) ---
  const stamp = new Date().toISOString();
  const lines = [
    `# Facebook friends export — ${stamp}`,
    `# Total: ${result.length}`,
    `# Name\tprofileURL`,
    ...result.map(f => `${f.name}\t${f.profileURL}`),
  ];
  const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' });

  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `facebook-friends-${stamp.slice(0, 10)}.txt`;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);

  console.log(
    `%c[FB-Friends] ✓ Done — ${result.length} friends downloaded (.txt)`,
    'color:#4ade80;font-weight:bold',
  );
  console.table(result);
  // Also stash on window for inspection / re-export
  window.__fbFriends = result;
})();
