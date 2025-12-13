//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\functions\api\v1\cron\trigger.js total lines 89 
//#######################################################################

function textReportResponse(message, status = 200) {
    return new Response(message, { // Kembalikan string mentah
        status: status,
        headers: { 'Content-Type': 'text/plain' } // Set content type ke text
    });
}
async function purgeCacheByUrl(env, url) {
    const { CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID } = env;
    if (!CLOUDFLARE_API_TOKEN || !CLOUDFLARE_ZONE_ID) {
        console.error("[Cron Worker] Cache purge failed: Missing CLOUDFLARE_API_TOKEN or CLOUDFLARE_ZONE_ID env variables.");
        return;
    }
    console.log(`[Cron Worker] Purging cache for: ${url}`);
    try {
        await fetch(`https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/purge_cache`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${CLOUDFLARE_API_TOKEN}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ files: [url] })
        });
    } catch (e) {
        console.error(`[Cron Worker] Cache purge fetch request failed: ${e.message}`);
    }
}

export async function onRequest(context) {
    const { request, env } = context;
    const { DB } = env;

    const SECRET_KEY = env.CRON_SECRET_KEY;
    if (!SECRET_KEY) {
        return textReportResponse("Error: Server is not configured for cron jobs (CRON_SECRET_KEY is not set).", 500);
    }

    const url = new URL(request.url);
    const providedKey = url.searchParams.get('key');
    if (providedKey !== SECRET_KEY) {
        console.warn("[Cron Worker] Unauthorized cron trigger attempt.");
        return textReportResponse("Error: Unauthorized.", 401);
    }

    const now = new Date().toISOString();
    console.log(`[Cron Worker] Manual trigger received. Checking for articles to publish as of ${now}...`);

    try {
        const stmt = DB.prepare(
            `SELECT id, slug, language FROM articles WHERE status = ?1 AND publish_at IS NOT NULL AND publish_at <= ?2`
        ).bind('pending', now);
        const { results } = await stmt.all();

        if (!results || results.length === 0) {
            console.log("[Cron Worker] No articles to publish.");
            return textReportResponse("Success: No articles to publish.");
        }

        console.log(`[Cron Worker] Found ${results.length} articles to publish...`);

        const purgePromises = [];
        const updatePromises = [];
        for (const article of results) {
            const updateStmt = DB.prepare(
                `UPDATE articles SET status = 'published', updated_at = ?1 WHERE id = ?2`
            ).bind(now, article.id);

            updatePromises.push(updateStmt.run());
            const lang = article.language || 'en';

            const articleUrl = `https://flowork.cloud/p-${article.slug}-${lang}.html`;

            purgePromises.push(purgeCacheByUrl(env, articleUrl));
        }
        purgePromises.push(purgeCacheByUrl(env, `https://flowork.cloud/sitemap.xml`));
        await Promise.all(updatePromises);
        await Promise.all(purgePromises);
        console.log(`[Cron Worker] Successfully published ${results.length} articles.`);
        return textReportResponse(`Success: Published ${results.length} articles.`);
    } catch (e) {
        console.error("[Cron Worker] Scheduled Publisher failed:", e.message);
        return textReportResponse(`Error: ${e.message}`, 500);
    }
}
