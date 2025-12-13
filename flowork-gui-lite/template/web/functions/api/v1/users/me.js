//#######################################################################
//# WEBSITE https://flowork.cloud
//# File NAME : functions/api/v1/users/me.js
//# DESKRIPSI : Endpoint kelola profil pribadi (GET & PUT).
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
    if (isNaN(ts) || Math.abs(Date.now()/1000 - ts) > 600) return null; // Toleransi 10 menit

    const recovered = ethers.verifyMessage(msg, sig);
    return (recovered.toLowerCase() === addr.toLowerCase()) ? addr.toLowerCase() : null;
  } catch (e) { return null; }
}

export async function onRequest(context) {
  const { request, env } = context;
  const userAddr = await verify(request);
  if (!userAddr) {
    return new Response(JSON.stringify({ error: "Unauthorized" }), {
      status: 401, headers: { "Content-Type": "application/json" }
    });
  }

  await env.DB.exec(`
    CREATE TABLE IF NOT EXISTS users (
      addr TEXT PRIMARY KEY,
      name TEXT UNIQUE,
      bio TEXT,
      avatar TEXT,
      rep INT DEFAULT 0,
      ts INT
    )
  `);

  if (request.method === "GET") {
    const profile = await env.DB.prepare("SELECT * FROM users WHERE addr = ?").bind(userAddr).first();
    // Jika belum punya profil, kembalikan object dasar
    return new Response(JSON.stringify(profile || { addr: userAddr, is_new: true }), {
        status: 200, headers: { "Content-Type": "application/json" }
    });
  }

  if (request.method === "PUT") {
    try {
      const body = await request.json();
      const { name, bio, avatar } = body;

      if (name && !/^[a-zA-Z0-9_]{3,20}$/.test(name)) {
        return new Response(JSON.stringify({ error: "Username invalid (3-20 alphanumeric/_ only)" }), {
            status: 400, headers: { "Content-Type": "application/json" }
        });
      }

      await env.DB.prepare(`
        INSERT INTO users (addr, name, bio, avatar, ts)
        VALUES (?1, ?2, ?3, ?4, ?5)
        ON CONFLICT(addr) DO UPDATE SET
          name = excluded.name,
          bio = excluded.bio,
          avatar = excluded.avatar,
          ts = excluded.ts
      `).bind(userAddr, name || null, bio || null, avatar || null, Date.now()).run();

      return new Response(JSON.stringify({ success: true, message: "Profile saved" }), {
          status: 200, headers: { "Content-Type": "application/json" }
      });

    } catch (e) {
      if (e.message && e.message.includes("UNIQUE constraint failed")) {
         return new Response(JSON.stringify({ error: "Username already taken" }), {
             status: 409, headers: { "Content-Type": "application/json" }
         });
      }
      return new Response(JSON.stringify({ error: e.message }), {
          status: 500, headers: { "Content-Type": "application/json" }
      });
    }
  }

  return new Response(null, { status: 405 });
}