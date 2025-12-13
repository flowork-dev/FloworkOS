//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\functions\api\v1\idem\global.js total lines 31 
//#######################################################################

export async function onRequestPost(context) {
  const { request, env } = context;
  const keyHeader = request.headers.get("X-API-Key");
  if (!env.IDEM_API_KEY || keyHeader !== env.IDEM_API_KEY) {
    return new Response(JSON.stringify({ error: "Unauthorized IDEM" }), { status: 401 });
  }
  try {
    const { key, job_id, ttl = 3600 } = await request.json();
    if (!key || !job_id) return new Response(JSON.stringify({ error: "Missing params" }), { status: 400 });
    await env.DB.exec(`CREATE TABLE IF NOT EXISTS global_locks (key TEXT PRIMARY KEY, job_id TEXT, created_at INTEGER, expires_at INTEGER)`);
    const now = Math.floor(Date.now() / 1000);
    await env.DB.prepare("DELETE FROM global_locks WHERE expires_at < ?").bind(now).run();
    await env.DB.prepare(`INSERT OR IGNORE INTO global_locks (key, job_id, created_at, expires_at) VALUES (?1, ?2, ?3, ?4)`).bind(key, job_id, now, now + ttl).run();
    const winner = await env.DB.prepare("SELECT job_id FROM global_locks WHERE key = ?").bind(key).first();
    if (!winner) {
        throw new Error("Fatal: Lock verified but not found");
    }
    return new Response(JSON.stringify({
      claimed: (winner.job_id === job_id),
      winner_job_id: winner.job_id
    }), { status: 200, headers: { "Content-Type": "application/json" } });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message, type: "IDEM_ERROR" }), { status: 500 });
  }
}
