//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\functions\api\v1\marketplace\[id].js total lines 214 
//#######################################################################

import { ethers } from 'ethers'; // (English Hardcode) Added for verify function

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
      return null;
  }
}

async function checkAndUpdateUserLimit(db, author, actionType) {
    const DAILY_LIMIT = 5;
    const currentDay = Math.floor(Date.now() / 86400000); // Days since epoch

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

    let userStats = await db.prepare("SELECT deletes_daily, last_reset_day FROM user_limits WHERE address = ?")
                             .bind(author).first();

    let currentCount = userStats?.deletes_daily || 0;
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
            deletes_daily = deletes_daily + 1,
            last_reset_day = ?5
    `).bind(author, 0, currentCount + 1, 0, currentDay).run();

    return { allowed: true };
}

async function purgeMarketplaceCache(context) {
    const cache = caches.default;

    const keysToPurge = [
        new URL('/api/v1/marketplace/list?type=preset', context.request.url),
        new URL('/api/v1/marketplace/list?type=all', context.request.url)
    ];

    for (const key of keysToPurge) {
        await cache.delete(key.toString());
    }
}


export async function onRequestGet(context) {
  const { env, params } = context;
  const itemId = params.id;
  try {
    const item = await env.DB.prepare("SELECT * FROM marketplace WHERE id = ?").bind(itemId).first();
    if (!item) {
      return new Response(JSON.stringify({ error: "Item not found" }), {
        status: 404, headers: { "Content-Type": "application/json" }
      });
    }
    context.waitUntil(
        env.DB.prepare("UPDATE marketplace SET dl = dl + 1 WHERE id = ?").bind(itemId).run()
    );
    return new Response(JSON.stringify(item), {
      status: 200,
      headers: {
          "Content-Type": "application/json",
          "Cache-Control": "private, max-age=0"
      }
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message }), {
      status: 500, headers: { "Content-Type": "application/json" }
    });
  }
}

export async function onRequestDelete(context) {
    const { request, env, params } = context;
    const itemId = params.id;
    const githubFilePath = `presets/${itemId}.json`;

    try {
        let author = await verify(request);

        if (!author) {
            return new Response(JSON.stringify({ error: "Unauthorized: Invalid signature" }), { status: 401 });
        }

        const limitCheck = await checkAndUpdateUserLimit(env.DB, author.toLowerCase(), 'delete');
        if (!limitCheck.allowed) {
            return new Response(
                JSON.stringify({
                    error: `Rate limit exceeded. Max deletes per day: ${limitCheck.limit}.`
                }),
                { status: 429 }
            );
        }

        const item = await env.DB.prepare("SELECT author, download_url FROM marketplace WHERE id = ?").bind(itemId).first();
        if (!item) {
            return new Response(JSON.stringify({ error: "Item not found in database" }), { status: 404 });
        }

        const itemAuthor = item.author.toLowerCase();
        const isAdmin = ["0xf39733b34131c13e35733e9af1add78a5e768929", "0x0f1f31783a93c94f5055e2a11aa28b2368ba982d"].includes(author);

        if (itemAuthor !== author && !isAdmin) {
             return new Response(JSON.stringify({ error: "Forbidden: Not the author or administrator" }), { status: 403 });
        }

        let shouldProceedToD1 = false;


        const ghUrl = `https://api.github.com/repos/${env.GITHUB_USER}/${env.GITHUB_REPO}/contents/${githubFilePath}`;

        const ghGetResp = await fetch(ghUrl, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
                'User-Agent': 'Flowork-Gateway'
            }
        });

        if (ghGetResp.ok) {
            const ghMetadata = await ghGetResp.json();
            const sha = ghMetadata.sha;

            const ghDeleteResp = await fetch(ghUrl, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
                    'Content-Type': 'application/json',
                    'User-Agent': 'Flowork-Gateway'
                },
                body: JSON.stringify({
                    message: `Delete item: ${itemId}`,
                    sha: sha, // SHA is required for file deletion
                    committer: { name: "Flowork Bot", email: "bot@flowork.cloud" }
                })
            });

            if (!ghDeleteResp.ok) {
                throw new Error(`GitHub Delete Failed: ${ghDeleteResp.status} - ${await ghDeleteResp.text()}`);
            }
            shouldProceedToD1 = true;

        } else if (ghGetResp.status === 404) {
            console.warn(`[Delete] GitHub file not found (404) for ID ${itemId}. Proceeding with D1 delete.`);
            shouldProceedToD1 = true;
        } else {
            throw new Error(`GitHub Get Failed (Pre-Delete): ${ghGetResp.status} - ${await ghGetResp.text()}`);
        }


        if (shouldProceedToD1) {
            await env.DB.prepare("DELETE FROM marketplace WHERE id = ?").bind(itemId).run();
        } else {
             throw new Error("Internal error: GitHub deletion status was inconclusive.");
        }

        context.waitUntil(purgeMarketplaceCache(context));


        return new Response(JSON.stringify({
            success: true,
            id: itemId,
            message: "Item successfully deleted from GitHub and D1"
        }), { status: 200 });

    } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), { status: 500 });
    }
}
