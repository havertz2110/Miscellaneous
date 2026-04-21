# Extract Facebook Friends

A browser-console script that walks your Facebook friends list and saves every friend (name + profile URL) into a local `.txt` file.

Nothing leaves your machine — the script only reads the DOM of a page you already have open.

> **Scope:** Personal use. Please respect Facebook's Terms of Service and only extract data you have the right to (i.e. your own friends list). Do not use on an account that isn't yours.

---

## 🖱️ How to use

1. Log in to Facebook and open **https://www.facebook.com/friends/list**
2. Press **F12** (or right-click → Inspect) and switch to the **Console** tab
3. Open [`extract-fb-friends.js`](./extract-fb-friends.js), copy the whole file, paste into the console, press **Enter**
4. Let it run — the script auto-scrolls, shows progress in the console, then downloads `facebook-friends-YYYY-MM-DD.txt`

No manual scrolling required. On a typical account (~500 friends) it finishes in about a minute.

---

## 📄 Output format

Tab-separated text, one friend per line — opens as two clean columns if you paste into Excel / Google Sheets, or read it straight in Notepad:

```
# Facebook friends export — 2026-04-22T03:15:00.000Z
# Total: 487
# Name	profileURL
Anh Nguyen	https://www.facebook.com/anh.nguyen.123
Bảo Trần	https://www.facebook.com/profile.php?id=100001234567890
Chi Le	https://www.facebook.com/chile.official
…
```

Names are sorted using the Vietnamese locale, so diacritics (đ/ê/ô/…) sort naturally.

---

## ⚙️ Tweakable parameters

At the top of the script:

```javascript
const SCROLL_DELAY_MS = 1200;            // wait after each scroll; raise if your network is slow
const STABLE_ROUNDS   = 4;               // how many consecutive no-progress rounds end the scroll
const HARD_TIMEOUT_MS = 10 * 60 * 1000;  // 10-minute overall safety cap
```

For very large accounts (3000+ friends) it's safer to raise `HARD_TIMEOUT_MS` to `20 * 60 * 1000`.

---

## 🧠 Design notes

- **Handles virtualization.** Facebook's friend list unmounts entries that scroll out of view. The script collects incrementally during scroll *and* does a reverse pass on the way back up, so items that were virtualized-out at the end are still captured.
- **Deduplicated by profile URL.** Each friend appears exactly once even if Facebook re-renders them multiple times.
- **Tracking params stripped** from each profile URL (`__cft__`, `__tn__`, `eav`, `paipv`, `rdid`). The saved URLs are clean and short.
- **Selector chosen to be DOM-resilient.** The script looks for `a[role="link"]` anchors whose `href` points to a profile path — less fragile than Facebook-internal attributes like `data-visualcompletion`, but **no** selector is guaranteed future-proof on Facebook.
- **No data URL size limit.** Uses a `Blob` + `URL.createObjectURL`, so even 10k-friend exports download fine.
- After a successful run, the full array stays on `window.__fbFriends` for quick filtering / re-export in the console.

---

## 🔎 Bonus console snippets (after the script finishes)

```javascript
// Only friends who haven't picked a custom username (still on /profile.php)
__fbFriends.filter(f => f.profileURL.includes('profile.php'))

// Count friends whose name starts with "Nguyen"
__fbFriends.filter(f => f.name.startsWith('Nguyen')).length

// Copy just the names to clipboard
copy(__fbFriends.map(f => f.name).join('\n'))
```

---

## ⚠️ Caveats

- Facebook's DOM changes regularly. If the script suddenly returns zero friends, the most likely cause is a DOM change — update the selector in `harvest()`.
- Running this repeatedly in a short window may get the account flagged. Use sparingly.
- If you reach the timeout and still see `collected=` growing in the logs, restart the script with a larger `HARD_TIMEOUT_MS`.

---

## 🙏 Credit

Original idea from this StackOverflow answer: https://stackoverflow.com/questions/50095522/how-to-get-whole-facebook-friends-list-from-api
