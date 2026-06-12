export async function onRequest(context) {
    const { env } = context;
    let allResult = null;
    let error = null;
    try {
        allResult = await env.DB.prepare('SELECT COUNT(*) as count FROM entries').all();
    } catch (e) {
        error = { message: e.message, stack: e.stack?.substring(0, 500) };
    }
    return new Response(JSON.stringify({ allResult, error, server: 'new' }), {
        headers: { 'Content-Type': 'application/json' },
    });
}
