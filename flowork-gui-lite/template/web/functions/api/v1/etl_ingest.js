//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\functions\api\v1\etl_ingest.js total lines 33 
//#######################################################################

export async function onRequestPost(context) {
  const { request, env } = context;
  const auth = request.headers.get("Authorization") || "";
  if (!env.ETL_API_KEY || !auth.includes(env.ETL_API_KEY)) {
    return new Response(JSON.stringify({ error: "Unauthorized" }), { status: 401 });
  }

  try {
    const body = await request.json();
    const events = body.events || [];
    if (!events.length) return new Response(JSON.stringify({ stored: 0 }), { status: 200 });
    await env.DB.exec(`CREATE TABLE IF NOT EXISTS etl_events (id TEXT PRIMARY KEY, topic TEXT, payload TEXT, gateway_ts INTEGER, ingested_at INTEGER)`);

    const stmt = env.DB.prepare(`INSERT OR IGNORE INTO etl_events (id, topic, payload, gateway_ts, ingested_at) VALUES (?1, ?2, ?3, ?4, ?5)`);
    const now = Date.now();
    let successCount = 0;
    for (const e of events) {
       const p = typeof e.payload === 'object' ? JSON.stringify(e.payload) : String(e.payload);
       await stmt.bind(e.id, e.topic, p, e.ts || now, now).run();
       successCount++;
    }

    return new Response(JSON.stringify({ success: true, stored: successCount }), { status: 200 });
  } catch (e) {
    return new Response(JSON.stringify({ error: e.message, type: "ETL_ERROR" }), { status: 500 });
  }
}
