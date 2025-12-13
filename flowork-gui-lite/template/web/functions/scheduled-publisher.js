//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\functions\scheduled-publisher.js total lines 86 
//#######################################################################

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

export default {
  async scheduled(event, env, ctx) {
    console.log(`[Cron Worker] Running scheduled task at: ${new Date(event.scheduledTime)}`);

    try {
      const db = env.DB;
      const now = new Date().toISOString();

      const stmtSelect = db.prepare(
        `SELECT id, slug, language FROM articles
         WHERE status = ?1 AND publish_at IS NOT NULL AND publish_at <= ?2`
      ).bind('pending', now);

      const { results } = await stmtSelect.all();

      if (!results || results.length === 0) {
        console.log("[Cron Worker] No articles to publish.");
        return;
      }

      console.log(`[Cron Worker] Found ${results.length} articles to publish.`);


      const stmtUpdate = db.prepare(
        `UPDATE articles SET status = 'published', updated_at = ?1 WHERE id = ?2`
      );

      let successCount = 0;
      const purgePromises = [];

      for (const article of results) {
        try {
          await stmtUpdate.bind(now, article.id).run();

          const lang = article.language || 'en';
          const articleUrl = `https://flowork.cloud/p-${article.slug}-${lang}.html`;

          purgePromises.push(purgeCacheByUrl(env, articleUrl));

          console.log(`[Cron Worker] Successfully published article ID: ${article.id}`);
          successCount++;
        } catch (e) {
          console.error(`[Cron Worker] FAILED to publish article ID: ${article.id}. Error: ${e.cause || e.message}`);
        }
      }

      if (successCount > 0) {
        purgePromises.push(purgeCacheByUrl(env, `https://flowork.cloud/sitemap.xml`));
      }

      await Promise.all(purgePromises);

      console.log(`[Cron Worker] Published ${successCount} out of ${results.length} articles.`);

    } catch (e) {
      console.error(`[Cron Worker] CRITICAL ERROR during scheduled task: ${e.message}`);
    }
  }
};
