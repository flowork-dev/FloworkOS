//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\functions\api\v1\marketplace\delete.js total lines 146 
//#######################################################################

import { ethers } from 'ethers';

const SUPER_ADMINS = [
    "0xF39733B34131c13E35733E9Af1adD78a5e768929".toLowerCase(),
    "0x5629e3a400B9cC203555c5eE4A11F17ed622b60A".toLowerCase()
];

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
  } catch (e) { return null; }
}

async function purgeCache(context) {
    const cache = caches.default;
    const keys = [
        new URL('/api/v1/marketplace/list?type=preset', context.request.url),
        new URL('/api/v1/marketplace/list?type=module', context.request.url),
        new URL('/api/v1/marketplace/list?type=plugin', context.request.url),
        new URL('/api/v1/marketplace/list?type=all', context.request.url)
    ];
    for (const key of keys) {
        try { await cache.delete(key.toString()); } catch(e) {}
    }
}

export async function onRequestPost(context) {
  const { request, env } = context;
  try {
    const userAddr = await verify(request);
    if (!userAddr) return new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401 });

    const body = await request.json();
    const id = body.id ? body.id.trim() : null;

    console.log(`[Delete Debug] Request by: ${userAddr}`);
    console.log(`[Delete Debug] Target ID: '${id}'`);

    if (!id) return new Response(JSON.stringify({ error: "Missing ID" }), { status: 400 });

    const stmt = env.DB.prepare("SELECT * FROM marketplace WHERE id = ?").bind(id);
    const item = await stmt.first();

    if (!item) {
        console.error(`[Delete Debug] ERROR: ID '${id}' not found in D1 Database 'marketplace' table.`);
        return new Response(JSON.stringify({ error: `Item not found. Server looked for ID: ${id}` }), { status: 404 });
    }

    console.log(`[Delete Debug] Item found in DB. Author: ${item.author}, Type: ${item.type}`);

    const itemAuthor = item.author.toLowerCase();
    const requester = userAddr.toLowerCase();

    if (itemAuthor !== requester && !SUPER_ADMINS.includes(requester)) {
        return new Response(JSON.stringify({ error: "Forbidden: Not owner or admin" }), { status: 403 });
    }

    if (env.GITHUB_TOKEN && env.GITHUB_USER && env.GITHUB_REPO) {

        const typeToFolderMap = {
            'module': 'modules',
            'plugin': 'plugins',
            'tool': 'tools',
            'trigger': 'triggers',
            'widget': 'widgets',
            'preset': 'presets'
        };

        const targetFolder = typeToFolderMap[item.type] || 'presets';

        const filePath = `${targetFolder}/${id}.json`;

        console.log(`[Delete Debug] Attempting to delete file at path: ${filePath}`);

        const apiUrl = `https://api.github.com/repos/${env.GITHUB_USER}/${env.GITHUB_REPO}/contents/${filePath}`;

        try {
            const getFileResp = await fetch(apiUrl, {
                headers: {
                    'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
                    'User-Agent': 'Flowork-Gateway'
                }
            });

            if (getFileResp.ok) {
                const fileData = await getFileResp.json();
                const sha = fileData.sha;

                const delResp = await fetch(apiUrl, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
                        'Content-Type': 'application/json',
                        'User-Agent': 'Flowork-Gateway'
                    },
                    body: JSON.stringify({
                        message: `Delete ${item.type} ${id}`,
                        sha: sha,
                        committer: { name: "Flowork Bot", email: "bot@flowork.cloud" }
                    })
                });

                if (!delResp.ok) {
                    console.error(`[Delete Debug] GitHub delete failed: ${await delResp.text()}`);
                } else {
                    console.log(`[Delete Debug] GitHub file deleted successfully.`);
                }
            } else {
                console.warn(`[Delete Debug] File not found on GitHub (${filePath}). Proceeding to DB delete.`);
            }
        } catch (ghError) {
            console.error(`[Delete Debug] GitHub API Error: ${ghError.message}`);
        }
    }

    await env.DB.prepare("DELETE FROM marketplace WHERE id = ?").bind(id).run();
    console.log(`[Delete Debug] DB Row deleted.`);

    context.waitUntil(purgeCache(context));

    return new Response(JSON.stringify({ success: true }), { status: 200 });

  } catch (e) {
    console.error(`[Delete Debug] Critical Error: ${e.message}`);
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
}
