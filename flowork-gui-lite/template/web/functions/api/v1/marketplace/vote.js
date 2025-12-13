//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\functions\api\v1\marketplace\vote.js total lines 174 
//#######################################################################

import { ethers } from 'ethers';

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
    const DAILY_LIMIT = 20;
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
        if (!e.message.includes('duplicate column name')) console.error("D1 Migration Error:", e);
    }

    let userStats = await db.prepare("SELECT votes_daily, last_reset_day FROM user_limits WHERE address = ?")
                             .bind(author).first();

    let currentCount = userStats?.votes_daily || 0;
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
        VALUES (?1, 0, 0, ?2, ?3)
        ON CONFLICT(address) DO UPDATE SET
            votes_daily = votes_daily + 1,
            last_reset_day = ?3
    `).bind(author, currentCount + 1, currentDay).run();

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


export async function onRequestPost(context) {
    const { request, env } = context;

    try {
        let userAddress = await verify(request);

        if (!userAddress) {
            return new Response(JSON.stringify({ error: "Unauthorized: Invalid signature" }), { status: 401 });
        }

        const body = await request.json();
        const { itemId, voteType } = body; // voteType: 1 for Like, -1 for Dislike, 0 for Remove

        if (!itemId || (voteType !== 1 && voteType !== -1 && voteType !== 0)) {
            return new Response(JSON.stringify({ error: "Missing or invalid itemId/voteType" }), { status: 400 });
        }

        const limitCheck = await checkAndUpdateUserLimit(env.DB, userAddress.toLowerCase(), 'vote');
        if (!limitCheck.allowed) {
            return new Response(
                JSON.stringify({
                    error: `Rate limit exceeded. Max votes per day: ${limitCheck.limit}.`
                }),
                { status: 429 }
            );
        }

        await env.DB.prepare(`
            CREATE TABLE IF NOT EXISTS votes (
                item_id TEXT NOT NULL,
                user_address TEXT NOT NULL,
                vote_type INTEGER NOT NULL,
                created_at INT,
                PRIMARY KEY (item_id, user_address)
            )
        `).run();

        const lowerUserAddress = userAddress.toLowerCase();
        let oldVote = null;

        oldVote = await env.DB.prepare("SELECT vote_type FROM votes WHERE item_id = ?1 AND user_address = ?2")
                            .bind(itemId, lowerUserAddress).first();

        const oldVoteType = oldVote ? oldVote.vote_type : 0;
        let finalVoteType = voteType;

        if (oldVoteType === voteType && voteType !== 0) {
            finalVoteType = 0;
        }

        if (finalVoteType === 0) {
             await env.DB.prepare("DELETE FROM votes WHERE item_id = ?1 AND user_address = ?2")
                        .bind(itemId, lowerUserAddress).run();
        } else {
            await env.DB.prepare(`
                INSERT INTO votes (item_id, user_address, vote_type, created_at)
                VALUES (?1, ?2, ?3, ?4)
                ON CONFLICT(item_id, user_address) DO UPDATE SET
                    vote_type = ?3,
                    created_at = ?4
            `).bind(itemId, lowerUserAddress, finalVoteType, Date.now()).run();
        }

        const updateSql = `
            UPDATE marketplace SET
                likes = (SELECT COUNT(item_id) FROM votes WHERE item_id = ?1 AND vote_type = 1),
                dislikes = (SELECT COUNT(item_id) FROM votes WHERE item_id = ?1 AND vote_type = -1)
            WHERE id = ?1
        `;
        await env.DB.prepare(updateSql).bind(itemId).run();

        context.waitUntil(purgeMarketplaceCache(context));


        return new Response(JSON.stringify({
            success: true,
            message: "Vote processed successfully",
            newVoteStatus: finalVoteType
        }), { status: 200 });

    } catch (e) {
        return new Response(JSON.stringify({ error: e.message }), { status: 500 });
    }
}
