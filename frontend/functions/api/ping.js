export async function onRequest(context) {
    const { env } = context;
    let result = null;
    let result2 = null;
    let error = null;
    try {
        const r = env.DB.prepare('SELECT COUNT(*) as count FROM entries').all();
        result = r;
        const r2 = env.DB.prepare('SELECT COUNT(*) as count FROM entries').first();
        result2 = r2;
    } catch (e) {
        error = e.message + ' | ' + e.stack;
    }
    return new Response(JSON.stringify({
        result,
        result2,
        error,
        keys: result ? Object.keys(result) : null,
    }), {
        headers: { 'Content-Type': 'application/json' },
    });
}
