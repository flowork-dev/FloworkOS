//#######################################################################
//# WEBSITE https://flowork.cloud
//# File NAME : functions/api/v1/users/[address].js
//# DESKRIPSI : Endpoint publik untuk melihat profil user lain.
//#######################################################################

export async function onRequestGet(context) {
  const { env, params } = context;
  const targetAddr = params.address;

  try {
    const profile = await env.DB.prepare("SELECT addr, name, bio, avatar, rep, ts FROM users WHERE addr = ? COLLATE NOCASE").bind(targetAddr).first();

    if (!profile) {
      return new Response(JSON.stringify({ error: "User not found" }), {
          status: 404, headers: { "Content-Type": "application/json" }
      });
    }

    return new Response(JSON.stringify(profile), {
      status: 200,
      headers: {
          "Content-Type": "application/json",
          "Cache-Control": "public, max-age=300"
      }
    });

  } catch (e) {
    if (e.message && e.message.includes("no such table")) {
        return new Response(JSON.stringify({ error: "User system inactive" }), {
            status: 404, headers: { "Content-Type": "application/json" }
        });
    }
    return new Response(JSON.stringify({ error: e.message }), {
        status: 500, headers: { "Content-Type": "application/json" }
    });
  }
}