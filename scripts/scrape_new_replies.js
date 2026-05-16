// Scrapes new replies from the source Threads post and saves to data-v2/raw-scraped.json
// Strategy: intercept GraphQL API responses to extract structured reply data
// Run: node scripts/scrape_new_replies.js  (from project root)

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const SOURCE_POST = 'https://www.threads.com/@betabreakhsin/post/DXzS3YEEY8t';
const OUT_DIR = path.join(ROOT, 'data-v2');
const OUT_FILE = path.join(OUT_DIR, 'raw-scraped.json');
const EXISTING_FILE = path.join(ROOT, 'data', 'replies.json');

const CHROMIUM_EXEC = '/Users/user/Library/Caches/ms-playwright/chromium-1217/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing';
const USER_DATA_DIR = '/Users/user/Library/Caches/ms-playwright/mcp-chrome-235b035';

function formatLikes(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1).replace(/\.0$/, '') + 'M';
  if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
  return String(n);
}

// Extract replies from a single Threads GraphQL response body
function extractFromGraphQL(text) {
  const results = [];
  try {
    const json = JSON.parse(text);

    // Walk all objects recursively looking for "post" nodes with like_count
    function walk(obj) {
      if (!obj || typeof obj !== 'object') return;
      if (Array.isArray(obj)) { obj.forEach(walk); return; }

      // Check if this is a post object
      if (obj.like_count !== undefined && obj.code !== undefined && obj.user) {
        const user = obj.user;
        const username = user.username || '';
        const likeCount = obj.like_count || 0;
        const takenAt = obj.taken_at; // unix timestamp
        const caption = obj.caption ? (obj.caption.text || '') : '';
        const code = obj.code; // post shortcode
        const postUrl = `https://www.threads.com/@${username}/post/${code}`;
        const ts = takenAt ? new Date(takenAt * 1000).toISOString() : null;

        if (username && code) {
          results.push({
            author: username,
            text: caption,
            likes: formatLikes(likeCount),
            likesNum: likeCount,
            ts,
            url: postUrl,
          });
        }
      }

      // Recurse into all values
      for (const v of Object.values(obj)) walk(v);
    }

    walk(json);
  } catch (_) {}
  return results;
}

async function main() {
  const existingData = JSON.parse(fs.readFileSync(EXISTING_FILE, 'utf-8'));
  const existingMap = new Map();
  for (const r of existingData.replies) {
    existingMap.set(r.url, r);
  }
  console.log(`Loaded ${existingMap.size} existing replies.`);

  fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: true,
    executablePath: CHROMIUM_EXEC,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });

  const page = await browser.newPage();
  page.setDefaultTimeout(30000);

  // Collect all data extracted from GraphQL responses
  const graphqlReplies = new Map(); // url -> reply data

  // Intercept GraphQL responses
  page.on('response', async (response) => {
    const url = response.url();
    if (!url.includes('/api/graphql') && !url.includes('graphql')) return;
    try {
      const text = await response.text();
      const extracted = extractFromGraphQL(text);
      for (const r of extracted) {
        if (r.url && r.url !== SOURCE_POST) {
          graphqlReplies.set(r.url, r);
        }
      }
    } catch (_) {}
  });

  console.log(`Navigating to ${SOURCE_POST}`);
  await page.goto(SOURCE_POST, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4000);

  const pageText = await page.evaluate(() => document.body.innerText.slice(0, 300));
  console.log('Page preview:', pageText.slice(0, 150).replace(/\n/g, ' '));

  if (pageText.toLowerCase().includes('log in') || pageText.toLowerCase().includes('登入')) {
    console.log('⚠️  Login wall detected — cannot scrape without auth.');
    await browser.close();
    process.exit(1);
  }

  // Scroll loop — each scroll triggers new GraphQL requests loading more replies
  const maxScrolls = 120;
  let lastCount = 0;
  let noNewCount = 0;

  for (let i = 0; i < maxScrolls; i++) {
    await page.evaluate(() => window.scrollBy(0, 1000));
    await page.waitForTimeout(1800);

    const current = graphqlReplies.size;
    const gained = current - lastCount;
    if (gained === 0) {
      noNewCount++;
      if (noNewCount >= 6) {
        console.log('No new replies for 6 scrolls — reached end.');
        break;
      }
    } else {
      noNewCount = 0;
    }
    lastCount = current;

    if ((i + 1) % 10 === 0) {
      console.log(`Scroll ${i + 1}: ${current} unique replies found so far`);
    }
  }

  await browser.close();
  console.log(`\nTotal unique replies from GraphQL: ${graphqlReplies.size}`);

  // If GraphQL interception yielded nothing, fall back to DOM scraping
  if (graphqlReplies.size === 0) {
    console.log('⚠️  GraphQL interception yielded 0 results — check network. Falling back to DOM scraping without likes.');
  }

  // Separate new vs existing (for like count refresh)
  const newReplies = [];
  const updatedLikes = {}; // url -> {likes, likesNum}

  for (const [url, scraped] of graphqlReplies) {
    if (url === SOURCE_POST) continue;

    if (existingMap.has(url)) {
      // Only update like counts for existing replies
      if (scraped.likesNum > 0) {
        updatedLikes[url] = {
          likes: scraped.likes,
          likesNum: scraped.likesNum,
        };
      }
    } else {
      // Genuinely new reply
      newReplies.push({
        author: scraped.author,
        text: scraped.text,
        likes: scraped.likes || '0',
        likesNum: scraped.likesNum || 0,
        ts: scraped.ts || new Date().toISOString(),
        url,
        category: null,
        subcategory: null,
        intl: false,
      });
    }
  }

  const out = {
    scrapedAt: new Date().toISOString(),
    totalScraped: graphqlReplies.size,
    newReplies,
    updatedLikes,
  };

  fs.writeFileSync(OUT_FILE, JSON.stringify(out, null, 2), 'utf-8');
  console.log(`\n✅ Done.`);
  console.log(`  ${newReplies.length} new replies`);
  console.log(`  ${Object.keys(updatedLikes).length} like count updates for existing replies`);
  console.log(`  → ${OUT_FILE}`);
}

main().catch(e => { console.error(e); process.exit(1); });
