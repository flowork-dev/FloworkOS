//#######################################################################
// WEBSITE https://flowork.cloud
// File NAME : C:\ORGINAL\flowork-gui-lite\template\web\functions\[[catchall]].js total lines 19 
//#######################################################################

/**
 * Handles all routes that are not explicitly caught by other function handlers.
 * This is the standard "SPA (Single Page Application) Mode" handler for Cloudflare Pages.
 * It fetches the static index.html file, allowing Vue Router to take over routing on the client-side.
 */
export async function onRequest(context) {
  try {
    return await context.next();
  } catch (err) {
    console.error("SPA Fallback Error:", err);
    return new Response(err.message || "Server Error", { status: 500 });
  }
}
