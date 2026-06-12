export async function onRequest(context) {
    const { env } = context;
    const hasDb = typeof env.DB !== 'undefined';
    let dbResult = null;
    let error = null;
    try {
        if (hasDb) {
            dbResult = env.DB.prepare('SELECT COUNT(*) as count FROM entries').first();
        }
    } catch (e) {
        error = e.message;
    }
    return new Response(JSON.stringify({
        hasDb,
        dbType: typeof env.DB,
        dbResult,
        error,
        env: Object.keys(env).join(', '),
    }), {
        headers: { 'Content-Type': 'application/json' },
    });
}
