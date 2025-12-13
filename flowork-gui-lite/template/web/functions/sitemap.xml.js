//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\functions\sitemap.xml.js total lines 51 
//#######################################################################

export async function onRequest(context) {
    const { env } = context;
    const { DB } = env;
    const now = new Date().toISOString();

    try {
        const stmt = env.DB.prepare(
            `SELECT slug, language, updated_at FROM articles
             WHERE status = 'published'
             AND visibility = 'public'
             AND (publish_at IS NULL OR publish_at <= ?)`
        ).bind(now);
        const { results } = await stmt.all();
        const baseUrl = "https://flowork.cloud";
        let xml = `<?xml version="1.0" encoding="UTF-8"?>`;
        xml += `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">`;
        xml += `<url><loc>${baseUrl}/</loc><priority>1.0</priority></url>`;
        xml += `<url><loc>${baseUrl}/login</loc><priority>0.5</priority></url>`;
        xml += `<url><loc>${baseUrl}/register</loc><priority>0.5</priority></url>`;

        if (results) {
            for (const article of results) {
                const lang = article.language || 'en';
                const url = `${baseUrl}/p-${article.slug}-${lang}.html`; // Format URL baru

                const lastMod = article.updated_at ? new Date(article.updated_at).toISOString() : new Date(now).toISOString();

                xml += `<url><loc>${url}</loc><lastmod>${lastMod}</lastmod><priority>0.8</priority></url>`;
            }
        }

        xml += `</urlset>`;

        return new Response(xml, {
            headers: {
                'Content-Type': 'application/xml',
                'Cache-Control': 'public, max-age=3600'
            }
        });

    } catch (e) {
        console.error("Failed to generate sitemap.xml:", e.message);
        return new Response(e.message, { status: 500 });
    }
}
