export async function onRequest(context) {
    const { env } = context;
    let result = null;
    let error = null;
    try {
        result = await env.DB.prepare('SELECT COUNT(*) as count FROM entries').all();
    } catch (e) {
        error = { message: e.message, stack: e.stack?.substring(0, 500) };
    }
    return new Response(JSON.stringify({
        hasDb: typeof env.DB !== 'undefined',
        dbType: typeof env.DB,
        result,
        error,
    }), {
        headers: { 'Content-Type': 'application/json' },
    });
}
