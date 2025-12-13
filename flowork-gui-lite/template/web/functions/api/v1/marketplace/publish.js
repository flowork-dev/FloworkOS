//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\functions\api\v1\marketplace\publish.js total lines 296 
//#######################################################################

import { ethers } from 'ethers';

async function checkAndUpdateUserLimit(db, author, actionType) {
    const DAILY_LIMIT = 13;
    const currentDay = Math.floor(Date.now() / 86400000); // Days since epoch

    const UNLIMITED_USERS = [
        "0x9f655d3e73ff7347aeabe61e475102d9914c8403",
        "0xf39733b34131c13e35733e9af1add78a5e768929",
        "0x5629e3a400B9cC203555c5eE4A11F17ed622b60A"
    ];

    if (UNLIMITED_USERS.includes(author.toLowerCase())) {
        return { allowed: true };
    }

    await db.prepare(`
        CREATE TABLE IF NOT EXISTS user_limits (
            address TEXT PRIMARY KEY,
            publishes_daily INTEGER DEFAULT 0,
            deletes_daily INTEGER DEFAULT 0,
            votes_daily INTEGER DEFAULT 0,
            last_reset_day INTEGER
        )
    `).run();

    try {
        await db.prepare('ALTER TABLE user_limits ADD COLUMN votes_daily INTEGER DEFAULT 0').run();
    } catch (e) {
        if (!e.message.includes('duplicate column name')) console.error("D1 Migration Error (user_limits):", e);
    }

    let userStats = await db.prepare("SELECT publishes_daily, last_reset_day FROM user_limits WHERE address = ?")
                             .bind(author).first();

    let currentCount = userStats?.publishes_daily || 0;
    let lastReset = userStats?.last_reset_day || 0;

    if (lastReset !== currentDay) {
        currentCount = 0; // (English Hardcode) New day, reset counter
        lastReset = currentDay;
    }

    if (currentCount >= DAILY_LIMIT) {
        return { allowed: false, limit: DAILY_LIMIT, current: currentCount };
    }

    await db.prepare(`
        INSERT INTO user_limits (address, publishes_daily, deletes_daily, votes_daily, last_reset_day)
        VALUES (?1, ?2, ?3, ?4, ?5)
        ON CONFLICT(address) DO UPDATE SET
            publishes_daily = publishes_daily + 1,
            last_reset_day = ?5
    `).bind(author, currentCount + 1, 0, 0, currentDay).run();

    return { allowed: true };
}

async function purgeMarketplaceCache(context) {
    const cache = caches.default;

    const keysToPurge = [
        new URL('/api/v1/marketplace/list?type=preset', context.request.url),
        new URL('/api/v1/marketplace/list?type=all', context.request.url),
        new URL('/api/v1/marketplace/list?type=module', context.request.url),
        new URL('/api/v1/marketplace/list?type=plugin', context.request.url),
        new URL('/api/v1/marketplace/list?type=tool', context.request.url),
        new URL('/api/v1/marketplace/list?type=trigger', context.request.url)
    ];

    for (const key of keysToPurge) {
        await cache.delete(key.toString());
    }
}


async function verify(req) {
  try {
    const addr = req.headers.get('X-User-Address');
    const sig = req.headers.get('X-Signature');
    const msg = req.headers.get('X-Signed-Message');

    if (!addr || !sig || !msg) return null;

    const parts = msg.split('|');
    const ts = parseInt(parts[parts.length - 1].trim());
    if (isNaN(ts)) return null;

    const now = Date.now() / 1000;
    if (now - ts > 600 || ts - now > 600) return null;

    const recovered = ethers.verifyMessage(msg, sig);
    return (recovered.toLowerCase() === addr.toLowerCase()) ? addr.toLowerCase() : null;
  } catch (e) {
      console.error("[Publish] Verification Failed:", e);
      return null;
  }
}

async function insertToDb(env, id, type, name, desc, author, price, url, ts) {
    await env.DB.prepare(`
        INSERT INTO marketplace (id, type, name, desc, author, price, download_url, created_at, likes, dislikes)
        VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, 0, 0)
        ON CONFLICT(id) DO UPDATE SET
            name = ?3,
            desc = ?4,
            price = ?6,
            download_url = ?7,
            created_at = ?8
    `).bind(id, type, name, desc, author, price, url, ts).run();
}

async function ensureMarketplaceSchema(db) {
    try {
        await db.prepare('ALTER TABLE marketplace ADD COLUMN likes INTEGER DEFAULT 0').run();
    } catch (e) {
        if (!e.message.includes('duplicate column name')) console.error("D1 Migration Error (likes):", e);
    }
    try {
        await db.prepare('ALTER TABLE marketplace ADD COLUMN dislikes INTEGER DEFAULT 0').run();
    } catch (e) {
        if (!e.message.includes('duplicate column name')) console.error("D1 Migration Error (dislikes):", e);
    }
}


export async function onRequestPost(context) {
  const { request, env } = context;

  try {
    let author = await verify(request);

    if (!author) {
      return new Response(JSON.stringify({ error: "Unauthorized: Invalid signature" }), { status: 401 });
    }

    const limitCheck = await checkAndUpdateUserLimit(env.DB, author.toLowerCase(), 'publish');
    if (!limitCheck.allowed) {
        return new Response(
            JSON.stringify({
                error: `Rate limit exceeded. Max publishes per day: ${limitCheck.limit}.`
            }),
            { status: 429 }
        );
    }

    await ensureMarketplaceSchema(env.DB);

    if (!env.GITHUB_TOKEN || !env.GITHUB_USER || !env.GITHUB_REPO) {
        throw new Error("Server Config Error: Missing GITHUB_TOKEN / USER / REPO");
    }

    const body = await request.json();
    const { type, name, desc, data, price = 0, id: existingId } = body;
    if (!type || !name || !data) {
        return new Response(JSON.stringify({ error: "Missing required fields (type, name, data)" }), { status: 400 });
    }

    const id = existingId || crypto.randomUUID();
    const nowTs = Date.now();

    let folderName = 'presets';
    let fileExtension = 'json';
    let contentBase64 = "";

    if (type === 'preset') {
        folderName = 'presets';
        const fileContent = {
          id, meta: { name, description: desc, author, price, type, created_at: nowTs }, content: data
        };
        contentBase64 = btoa(unescape(encodeURIComponent(JSON.stringify(fileContent, null, 2))));

    } else {
        if (type === 'module') folderName = 'modules';
        else if (type === 'plugin') folderName = 'plugins';
        else if (type === 'tool') folderName = 'tools';
        else if (type === 'trigger') folderName = 'triggers';

        fileExtension = 'json';

        let finalJson = {};

        if (typeof data === 'object') {
            finalJson = {
                ...data,
                name: name,         // Ensure top-level metadata sync
                description: desc,
                author: author,
                updated_at: nowTs
            };
        } else {
            finalJson = {
                id,
                type,
                name,
                description: desc,
                author,
                zip_data: data, // Wrap the raw string
                created_at: nowTs
            };
        }

        const jsonString = JSON.stringify(finalJson, null, 2);
        contentBase64 = btoa(unescape(encodeURIComponent(jsonString)));
    }

    const fileName = `${id}.${fileExtension}`;
    const githubFilePath = `${folderName}/${fileName}`;

    const ghUrl = `https://api.github.com/repos/${env.GITHUB_USER}/${env.GITHUB_REPO}/contents/${githubFilePath}`;

    let sha = null;
    try {
        const checkResp = await fetch(ghUrl, {
            headers: {
                'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
                'User-Agent': 'Flowork-Gateway'
            }
        });
        if (checkResp.ok) {
            const existingFile = await checkResp.json();
            sha = existingFile.sha;
            console.log(`[Publish] File exists at ${githubFilePath}. Overwriting SHA: ${sha}`);
        }
    } catch (e) {
        console.log(`[Publish] File check failed (New item): ${e.message}`);
    }

    const ghPayload = {
        message: sha ? `Update ${type}: ${name}` : `New ${type}: ${name}`,
        content: contentBase64, // (English Hardcode) This is now guaranteed to be a String
        committer: { name: "Flowork Bot", email: "bot@flowork.cloud" }
    };
    if (sha) {
        ghPayload.sha = sha;
    }

    const ghResp = await fetch(ghUrl, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
        'Content-Type': 'application/json',
        'User-Agent': 'Flowork-Gateway'
      },
      body: JSON.stringify(ghPayload)
    });

    if (!ghResp.ok) {
      throw new Error(`GitHub Upload Failed: ${await ghResp.text()}`);
    }

    const rawDownloadUrl = `https://raw.githubusercontent.com/${env.GITHUB_USER}/${env.GITHUB_REPO}/main/${githubFilePath}`;

    try {
        await insertToDb(env, id, type, name, desc, author, price, rawDownloadUrl, nowTs);
    } catch(dbErr) {
        if (dbErr.message.includes("no such table")) {
             console.log("[DB_MIGRATION] Table not found. Creating...");
             await env.DB.prepare(`
              CREATE TABLE marketplace (
                id TEXT PRIMARY KEY,
                type TEXT,
                name TEXT,
                desc TEXT,
                author TEXT,
                price REAL,
                download_url TEXT,
                created_at INT,
                likes INTEGER DEFAULT 0,
                dislikes INTEGER DEFAULT 0
              )
            `).run();
            await insertToDb(env, id, type, name, desc, author, price, rawDownloadUrl, nowTs);
        } else {
             throw dbErr;
        }
    }

    context.waitUntil(purgeMarketplaceCache(context));

    return new Response(JSON.stringify({
      success: true,
      id: id,
      message: sha ? "Updated successfully" : "Published successfully"
    }), { status: 201 });

  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
}
