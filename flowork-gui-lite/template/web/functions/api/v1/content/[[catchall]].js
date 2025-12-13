//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\functions\api\v1\content\[[catchall]].js total lines 671 
//#######################################################################

import { ethers } from 'ethers';

function handleOptions(request) {
    const origin = request.headers.get('Origin');
    const accessControlRequestMethod = request.headers.get('Access-Control-Request-Method');
    const accessControlRequestHeaders = request.headers.get('Access-Control-Request-Headers');
    const headers = new Headers();
    if (origin) {
        headers.set('Access-Control-Allow-Origin', origin);
    }
    headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    if (accessControlRequestHeaders) {
        headers.set('Access-Control-Allow-Headers', accessControlRequestHeaders);
    } else {
        headers.set('Access-Control-Allow-Headers', 'Content-Type, X-User-Address, X-Signature, X-Signed-Message, X-Flowork-Engine-ID');
    }
    headers.set('Access-Control-Max-Age', '86400');
    return new Response(null, {
        status: 204,
        headers: headers
    });
}
function jsonResponse(data, status = 200, headers = {}) {
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
    };
    return new Response(JSON.stringify(data), {
        status: status,
        headers: { ...defaultHeaders, ...headers }
    });
}
async function verifySignature(request) {
    try {
        const address = request.headers.get('X-User-Address');
        const signature = request.headers.get('X-Signature');
        const message = request.headers.get('X-Signed-Message');
        if (!address || !signature || !message) {
            console.warn('[AUTH] Missing crypto headers');
            return null;
        }
        const messageParts = message.split('|');
        if (messageParts.length < 3) {
            console.warn('[AUTH] Invalid message format');
            return null;
        }
        const timestamp = parseInt(messageParts[messageParts.length - 1], 10);
        const nowInSeconds = Math.floor(Date.now() / 1000);
        if (Math.abs(nowInSeconds - timestamp) > 300) {
            console.warn(`[AUTH] Stale signature. Now: ${nowInSeconds}, TS: ${timestamp}`);
            return null;
        }
        const recoveredAddress = ethers.verifyMessage(message, signature);
        if (recoveredAddress.toLowerCase() === address.toLowerCase()) {
            return recoveredAddress;
        } else {
            console.warn('[AUTH] Signature mismatch');
            return null;
        }
    } catch (e) {
        console.error(`[AUTH] Signature verification error: ${e.message}`);
        return null;
    }
}
async function purgeCacheByUrl(env, url) {
    const { CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID } = env;
    if (!CLOUDFLARE_API_TOKEN || !CLOUDFLARE_ZONE_ID) {
        console.error("[Cache Purge] Failed: Missing CLOUDFLARE_API_TOKEN or CLOUDFLARE_ZONE_ID env variables.");
        return;
    }
    console.log(`[Cache Purge] Purging cache for: ${url}`);
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
        console.error(`[Cache Purge] Fetch request failed: ${e.message}`);
    }
}

async function handleGetMyArticles(context, authorId) {
    const { env } = context;
    try {
        const stmt = env.DB.prepare(
            `SELECT id, title, slug, category, status, publish_at, updated_at, language
             FROM articles WHERE author_id = ? ORDER BY updated_at DESC`
        ).bind(authorId);
        const { results } = await stmt.all();
        return jsonResponse(results || []);
    } catch (e) {
        return jsonResponse({ error: e.message }, 500);
    }
}

async function handleCreateArticle(context, authorId, request) {
    const { env } = context;
    try {
        const data = await request.json();
        if (!data.title || !data.slug || !data.content || !data.category) {
            return jsonResponse({ error: "Missing required fields: title, slug, content, category" }, 400);
        }
        const now = new Date().toISOString();
        const desiredStatus = data.status || 'pending';
        const dbStatus = (desiredStatus === 'scheduled') ? 'pending' : desiredStatus;
        const publish_at = (desiredStatus === 'scheduled' && data.publish_at) ? data.publish_at : null;
        const language = data.language || 'en';
        const price = (data.category === 'marketplace' && data.price) ? parseFloat(data.price) : null;
        const product_url = (data.category === 'marketplace' && data.product_url) ? data.product_url : null;
        const meta_description = data.meta_description || null;
        const keywords = data.keywords || null;
        const tags = data.tags || null;
        const newId = crypto.randomUUID();
        const stmt = env.DB.prepare(
            `INSERT INTO articles
             (id, title, slug, content, category, author_id, author_username, status, visibility, language, price, product_url, publish_at, created_at, updated_at, meta_description, keywords, tags)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12, ?13, ?14, ?14, ?15, ?16, ?17)`
        ).bind(
            newId, data.title, data.slug, data.content, data.category,
            authorId, authorId,
            dbStatus, data.visibility || 'public',
            language, price, product_url, publish_at, now,
            meta_description, keywords, tags
        );
        await stmt.run();
        if (dbStatus === 'published' || (dbStatus === 'pending' && publish_at)) {
            const articleUrl = `https://flowork.cloud/p-${data.slug}-${language}.html`;
            await purgeCacheByUrl(env, articleUrl);
        }
        const createdArticle = { ...data, id: newId, author_id: authorId, created_at: now, updated_at: now, publish_at: publish_at, status: desiredStatus };
        return jsonResponse(createdArticle, 201);
    } catch (e) {
        if (e.message.includes('UNIQUE constraint failed')) {
            return jsonResponse({ error: 'This slug is already in use.' }, 409);
        }
        console.error("Create Article Error:", e.message);
        return jsonResponse({ error: e.message }, 500);
    }
}

async function handleGetArticleForEdit(context, authorId, articleId) {
     const { env } = context;
    try {
        const stmt = env.DB.prepare(
            `SELECT * FROM articles WHERE id = ? AND author_id = ?`
        ).bind(articleId, authorId);
        const result = await stmt.first();
        if (result) {
            if (result.status === 'pending' && result.publish_at && new Date(result.publish_at) > new Date()) {
                result.status = 'scheduled';
            }
            return jsonResponse(result);
        } else {
            console.warn(`[GetForEdit] Article not found for ID: ${articleId}, author: ${authorId}`);
            return jsonResponse({ error: "Article not found or you do not have permission to edit it." }, 404);
        }
    } catch (e) {
        console.error(`[GetForEdit] Error: ${e.message}`);
        return jsonResponse({ error: e.message }, 500);
    }
}

async function handleUpdateArticle(context, authorId, articleId, request) {
    const { env } = context;
    try {
        const data = await request.json();
        if (!articleId || data.id !== articleId) {
            return jsonResponse({ error: "Article ID mismatch." }, 400);
        }
        const now = new Date().toISOString();
        const desiredStatus = data.status || 'pending';
        const dbStatus = (desiredStatus === 'scheduled') ? 'pending' : desiredStatus;
        const publish_at = (desiredStatus === 'scheduled' && data.publish_at) ? data.publish_at : null;
        const language = data.language || 'en';
        const price = (data.category === 'marketplace' && data.price) ? parseFloat(data.price) : null;
        const product_url = (data.category === 'marketplace' && data.product_url) ? data.product_url : null;
        const meta_description = data.meta_description || null;
        const keywords = data.keywords || null;
        const tags = data.tags || null;
        const stmt = env.DB.prepare(
            `UPDATE articles
             SET title = ?1, slug = ?2, content = ?3, category = ?4, status = ?5,
                 visibility = ?6, language = ?7, price = ?8, product_url = ?9,
                 publish_at = ?10,
                 meta_description = ?11, keywords = ?12, tags = ?13
             WHERE id = ?14 AND author_id = ?15`
        ).bind(
            data.title, data.slug, data.content, data.category, dbStatus, // ?1 - ?5
            data.visibility, language, price, product_url,             // ?6 - ?9
            publish_at,                                                // ?10
            meta_description, keywords, tags,                          // ?11 - ?13
            articleId, authorId                                        // ?14 - ?15
        );

        await stmt.run();
        const articleUrl = `https://flowork.cloud/p-${data.slug}-${language}.html`;
        await purgeCacheByUrl(env, articleUrl);
        await purgeCacheByUrl(env, `https://flowork.cloud/sitemap.xml`);
        return jsonResponse({ status: 'updated', slug: data.slug });
    } catch (e) {
         if (e.message.includes('UNIQUE constraint failed')) {
            return jsonResponse({ error: 'This slug is already in use.' }, 409);
        }
        console.error(`[UpdateArticle] Error: ${e.message}`);
        return jsonResponse({ error: e.message }, 500);
    }
}

async function handleDeleteArticle(context, authorId, articleId) {
    const { env } = context;
    try {
        const stmtGetInfo = env.DB.prepare(
            `SELECT slug, language FROM articles WHERE id = ? AND author_id = ?`
        ).bind(articleId, authorId);
        const articleInfo = await stmtGetInfo.first();
        const stmt = env.DB.prepare(
            `DELETE FROM articles WHERE id = ? AND author_id = ?`
        ).bind(articleId, authorId);
        await stmt.run();
        if (articleInfo) {
            const articleUrl = `https://flowork.cloud/p-${articleInfo.slug}-${articleInfo.language}.html`;
            await purgeCacheByUrl(env, articleUrl);
            await purgeCacheByUrl(env, `https://flowork.cloud/sitemap.xml`);
        }
        console.log(`[DeleteArticle] Article delete processed for: ${articleId}, author: ${authorId}`);
        return jsonResponse({ status: 'deleted', message: 'Article deleted successfully.', id: articleId }, 200);
    } catch (e) {
        console.error(`[DeleteArticle] Error: ${e.message}`);
        return jsonResponse({ error: e.message }, 500);
    }
}

async function handleGetComments(context, slug) {
    const { env } = context;
     try {
        const articleStmt = env.DB.prepare(`SELECT id FROM articles WHERE slug = ? AND status = 'published'`).bind(slug);
        const article = await articleStmt.first();
        if (!article) {
            return jsonResponse({ error: "Article not found" }, 404);
        }
        const stmt = env.DB.prepare(
            `SELECT id, parent_id, author_username, content, created_at
             FROM comments
             WHERE article_id = ? AND status = 'approved'
             ORDER BY created_at DESC`
        ).bind(article.id);
        const { results } = await stmt.all();
        return jsonResponse(results || [], 200, { 'Cache-Control': 'public, max-age=300' });
    } catch (e) {
        return jsonResponse({ error: e.message }, 500);
    }
}

async function handleGetPublicArticle(context, slug, lang) {
    const { env } = context;
    const now = new Date().toISOString();
    console.log(`[API Public] Fetching article: slug=${slug}, lang=${lang}`);
    try {
        const stmt = env.DB.prepare(
            `SELECT * FROM articles
             WHERE slug = ?1
             AND language = ?2
             AND status = 'published'
             AND visibility = 'public'
             AND (publish_at IS NULL OR publish_at <= ?3)
             LIMIT 1`
        ).bind(slug, lang, now);
        const result = await stmt.first();
        if (!result) {
            console.warn(`[API Public] Article not found or not published: ${slug} (${lang})`);
            return jsonResponse({ error: "Article not found or not yet published." }, 404);
        }
        return jsonResponse(result, 200, { 'Cache-Control': 'public, max-age=1800' });
    } catch (e) {
        console.error(`[API Public] Error fetching article: ${e.message}`);
        return jsonResponse({ error: e.message }, 500);
    }
}

async function getArticleAuthorId(db, articleId) {
    if (!articleId) return null;
    const stmt = db.prepare(`SELECT author_id FROM articles WHERE id = ?`).bind(articleId);
    const result = await stmt.first();
    return result ? result.author_id : null;
}

async function handleDeleteComment(context, authorId, commentId) {
    const { env } = context;
    try {
        const stmtGetComment = env.DB.prepare(
            `SELECT id, author_id, article_id FROM comments WHERE id = ?`
        ).bind(commentId);
        const comment = await stmtGetComment.first();

        if (!comment) {
            return jsonResponse({ error: "Comment not found." }, 404);
        }

        const articleAuthorId = await getArticleAuthorId(env.DB, comment.article_id);

        if (comment.author_id.toLowerCase() !== authorId.toLowerCase() && articleAuthorId?.toLowerCase() !== authorId.toLowerCase()) {
            return jsonResponse({ error: "You do not have permission to delete this comment." }, 403);
        }

        const stmtDelete = env.DB.prepare(
            `DELETE FROM comments WHERE id = ?`
        ).bind(commentId);
        await stmtDelete.run();

        console.log(`[DeleteComment] Comment ${commentId} deleted by user ${authorId}`);
        return jsonResponse({ status: 'deleted', id: commentId }, 200);

    } catch (e) {
        console.error(`[DeleteComment] Error: ${e.message}`);
        return jsonResponse({ error: e.message }, 500);
    }
}

async function handleUpdateComment(context, authorId, commentId, request) {
    const { env } = context;
    try {
        const data = await request.json();
        const { content } = data;
        if (!content) {
            return jsonResponse({ error: "Content is required." }, 400);
        }

        const stmtGetComment = env.DB.prepare(
            `SELECT id, author_id FROM comments WHERE id = ?`
        ).bind(commentId);
        const comment = await stmtGetComment.first();

        if (!comment) {
            return jsonResponse({ error: "Comment not found." }, 404);
        }
        if (comment.author_id.toLowerCase() !== authorId.toLowerCase()) {
            return jsonResponse({ error: "You do not have permission to edit this comment." }, 403);
        }
        const stmtUpdate = env.DB.prepare(
            `UPDATE comments SET content = ?1, status = 'pending' WHERE id = ?2`
        ).bind(content, commentId);

        await stmtUpdate.run();

        console.log(`[UpdateComment] Comment ${commentId} updated by user ${authorId}`);
        return jsonResponse({ status: 'updated', id: commentId });

    } catch (e) {
        console.error(`[UpdateComment] Error: ${e.message}`);
        return jsonResponse({ error: e.message }, 500);
    }
}

async function handleVoteComment(context, authorId, commentId, request) {
    const { env } = context;
    const { vote_type } = await request.json();

    if (vote_type !== 'up' && vote_type !== 'down') {
        return jsonResponse({ error: "Invalid vote type." }, 400);
    }

    if (!env.FLOWORK_KV) {
         console.error("[VoteComment] CRITICAL: FLOWORK_KV binding not configured.");
         return jsonResponse({ error: "Voting service is not configured." }, 500);
    }

    const voteKey = `vote:${commentId}:${authorId}`;
    const scoreKey = `score:${commentId}`;

    try {
        const existingVote = await env.FLOWORK_KV.get(voteKey);
        let score = parseInt(await env.FLOWORK_KV.get(scoreKey) || '0', 10);
        let voteDelta = 0;

        if (existingVote === vote_type) {
            voteDelta = (vote_type === 'up') ? -1 : 1;
            await env.FLOWORK_KV.delete(voteKey);
        } else if (existingVote) {
            voteDelta = (vote_type === 'up') ? 2 : -2;
            await env.FLOWORK_KV.put(voteKey, vote_type);
        } else {
            voteDelta = (vote_type === 'up') ? 1 : -1;
            await env.FLOWORK_KV.put(voteKey, vote_type);
        }

        const newScore = score + voteDelta;
        await env.FLOWORK_KV.put(scoreKey, newScore.toString());

        console.log(`[VoteComment] User ${authorId} voted on ${commentId}. Score changed by ${voteDelta} to ${newScore}.`);
        return jsonResponse({ status: 'success', new_score: newScore });

    } catch (e) {
         console.error(`[VoteComment] KV Error: ${e.message}`);
         return jsonResponse({ error: e.message }, 500);
    }
}

async function handleFlagComment(context, authorId, commentId, request) {
    const { env } = context;
    try {
        console.log(`[FlagComment] User ${authorId} flagged comment ${commentId}`);


        return jsonResponse({ status: 'success', message: 'Comment flagged for review.' });
    } catch (e) {
        return jsonResponse({ error: e.message }, 500);
    }
}
async function handleGetCategories(context) {
    const { env } = context;
    const now = new Date().toISOString();
    try {
        const stmt = env.DB.prepare(
            `SELECT category, COUNT(id) as count FROM articles
             WHERE status = 'published'
             AND visibility = 'public'
             AND (publish_at IS NULL OR publish_at <= ?1)
             GROUP BY category
             ORDER BY category ASC`
        ).bind(now);
        const { results } = await stmt.all();
        return jsonResponse(results || [], 200, { 'Cache-Control': 'public, max-age=3600' });
    } catch (e) {
        console.error(`[GetCategories] Error: ${e.message}`);
        return jsonResponse({ error: e.message }, 500);
    }
}


async function handlePostComment(context, authorId, slug, request) {
    const { env } = context;
    try {
        const data = await request.json();
        const { content, parent_id } = data;
        if (!content) {
            return jsonResponse({ error: "Comment content is required" }, 400);
        }
        const articleStmt = env.DB.prepare(`SELECT id FROM articles WHERE slug = ? AND status = 'published'`).bind(slug);
        const article = await articleStmt.first();
        if (!article) {
            return jsonResponse({ error: "Article not found" }, 404);
        }
        const author_username = authorId;
        const now = new Date().toISOString();
        const status = 'pending'; // All comments must be approved
        const newId = crypto.randomUUID();
        const stmt = env.DB.prepare(
            `INSERT INTO comments
             (id, article_id, parent_id, author_id, author_username, content, status, created_at)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)`
        ).bind(
            newId, article.id, parent_id || null, authorId, author_username,
            content, status, now
        );
        await stmt.run();
        return jsonResponse({
            id: newId, parent_id: parent_id || null, author_id: authorId,
            author_username: author_username, content: content, status: status,
            created_at: now
        }, 201);
    } catch (e) {
        return jsonResponse({ error: e.message }, 500);
    }
}

async function handleGetRecentArticles(context) {
    const { env, request } = context;
    const url = new URL(request.url);
    const category = url.searchParams.get('category');
    const lang = url.searchParams.get('lang'); // Ambil param 'lang'
    const current_id = url.searchParams.get('current_id'); // Ambil param 'current_id'
    const limit = 10;
    const now = new Date().toISOString();
    console.log(`[API Recent] Fetching: category=${category}, lang=${lang}, excluding_id=${current_id}`);

    try {
        let stmt;
        let params = [];

        if (category && lang && current_id) { // Skenario utama dari sidebar
            let query = `
                SELECT title, slug, language, SUBSTR(content, 1, 100) as snippet FROM articles
                WHERE status = 'published' AND visibility = 'public'
                AND (publish_at IS NULL OR publish_at <= ?1)
                AND category = ?2
                AND language = ?3
                AND id != ?4
                ORDER BY publish_at DESC, created_at DESC LIMIT ?5`;
            params = [now, category, lang, current_id, limit];
            stmt = env.DB.prepare(query).bind(...params);

        } else if (category) { // Fallback jika hanya kategori (logika lama, disesuaikan)
             let query = `
                SELECT title, slug, language, SUBSTR(content, 1, 100) as snippet FROM articles
                WHERE status = 'published' AND visibility = 'public'
                AND (publish_at IS NULL OR publish_at <= ?1)
                AND category = ?2
                ORDER BY publish_at DESC, created_at DESC LIMIT ?3`;
            params = [now, category, limit];
            stmt = env.DB.prepare(query).bind(...params);
        } else {
             let query = `
                SELECT title, slug, language, SUBSTR(content, 1, 100) as snippet FROM articles
                WHERE status = 'published' AND visibility = 'public'
                AND (publish_at IS NULL OR publish_at <= ?1)
                ORDER BY publish_at DESC, created_at DESC LIMIT ?2`;
            params = [now, limit];
            stmt = env.DB.prepare(query).bind(...params);
        }

        const { results } = await stmt.all();
        console.log(`[API Recent] Found ${results.length} related articles.`);
        return jsonResponse(results || [], 200, { 'Cache-Control': 'public, max-age=600' });
    } catch (e) {
        console.error(`[API Recent] Error: ${e.message}`);
        return jsonResponse({ error: e.message }, 500);
    }
}

async function handleGetArticleList(context) {
    const { env, request } = context;
    const url = new URL(request.url);
    const author = url.searchParams.get('author');
    const category = url.searchParams.get('category');
    const tag = url.searchParams.get('tag');
    const language = url.searchParams.get('language');
    const now = new Date().toISOString();
    const limit = 20;

    console.log(`[API Public List] Received request: author=${author}, category=${category}, tag=${tag}, language=${language}`);

    try {
        let stmt;
        let query = `SELECT id, title, slug, language, publish_at, created_at, author_username, category, tags, SUBSTR(content, 1, 100) as snippet
                     FROM articles
                     WHERE status = 'published' AND visibility = 'public'
                     AND (publish_at IS NULL OR publish_at <= ?1)`;

        const params = [now];

        if (author) {
            query += " AND author_username = ?2";
            params.push(author);
        } else if (category) {
            query += " AND category = ?2";
            params.push(category);
        } else if (tag) {
            query += " AND tags LIKE ?2";
            params.push(`%${tag}%`);
        } else if (language) {
            query += " AND language = ?2";
            params.push(language);
        } else {
             return jsonResponse({ error: "No filter specified (author, category, tag, or language)." }, 400);
        }

        query += " ORDER BY publish_at DESC, created_at DESC LIMIT ?3";
        params.push(limit);

        stmt = env.DB.prepare(query);
        if (params.length === 2) {
             stmt = stmt.bind(params[0], params[1]);
        } else if (params.length === 3) {
             stmt = stmt.bind(params[0], params[1], params[2]);
        } else {
             stmt = stmt.bind(params[0]);
        }

        const { results } = await stmt.all();
        return jsonResponse(results || [], 200, { 'Cache-Control': 'public, max-age=600' });

    } catch (e) {
        console.error(`[API Public List] Error: ${e.message}`);
        return jsonResponse({ error: e.message }, 500);
    }
}


export async function onRequest(context) {
    const { request } = context;
    if (request.method === 'OPTIONS') {
        return handleOptions(request);
    }
    const url = new URL(request.url);
    const { pathname } = url;
    const segments = pathname.split('/').filter(Boolean);
    const contentApiPrefixIndex = segments.indexOf('content');
    if (contentApiPrefixIndex === -1) {
        console.warn(`[API Worker] Path does not contain 'content'. Path: ${pathname}`);
        return jsonResponse({ error: 'Invalid API path for content worker' }, 404);
    }
    const route = segments.slice(contentApiPrefixIndex + 1).join('/');

    let match = route.match(/^articles\/public\/([^/]+)\/([^/]+)$/);
    if (match && request.method === 'GET') {
        return handleGetPublicArticle(context, match[1], match[2]);
    }
    if (route === 'articles/recent' && request.method === 'GET') {
        return handleGetRecentArticles(context);
    }
    if (route === 'articles/categories/list' && request.method === 'GET') {
        return handleGetCategories(context);
    }
    if (route === 'articles/list' && request.method === 'GET') {
        return handleGetArticleList(context);
    }
    match = route.match(/^articles\/([^/]+)\/comments$/);
    if (match && request.method === 'GET') {
        return handleGetComments(context, match[1]);
    }

    const authorId = await verifySignature(request);
    if (!authorId) {
        return jsonResponse({ error: 'Invalid or missing signature' }, 401);
    }
    try {
        if (route === 'my-articles' && request.method === 'GET') {
            return handleGetMyArticles(context, authorId);
        }
        if (route === 'articles' && request.method === 'POST') {
            return handleCreateArticle(context, authorId, request);
        }
        match = route.match(/^articles\/([^/]+)\/edit$/);
        if (match && request.method === 'GET') {
            return handleGetArticleForEdit(context, authorId, match[1]);
        }
        match = route.match(/^articles\/([^/]+)$/);
        if (match && request.method === 'PUT') {
            return handleUpdateArticle(context, authorId, match[1], request);
        }
        match = route.match(/^articles\/([^/]+)$/);
        if (match && request.method === 'DELETE') {
            return handleDeleteArticle(context, authorId, match[1]);
        }
        match = route.match(/^articles\/([^/]+)\/comments$/);
        if (match && request.method === 'POST') {
            return handlePostComment(context, authorId, match[1], request);
        }

        match = route.match(/^comments\/([^/]+)$/);
        if (match && request.method === 'DELETE') {
            return handleDeleteComment(context, authorId, match[1]);
        }
        if (match && request.method === 'PUT') {
            return handleUpdateComment(context, authorId, match[1], request);
        }
        match = route.match(/^comments\/([^/]+)\/vote$/);
        if (match && request.method === 'POST') {
            return handleVoteComment(context, authorId, match[1], request);
        }
        match = route.match(/^comments\/([^/]+)\/flag$/);
        if (match && request.method === 'POST') {
            return handleFlagComment(context, authorId, match[1], request);
        }

        console.warn(`[API Worker] Route not matched: ${route}`);
        return jsonResponse({ error: 'Route not found' }, 404);
    } catch (e) {
        return jsonResponse({ error: `Unhandled exception: ${e.message}` }, 500);
    }
}
