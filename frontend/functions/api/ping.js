export async function onRequest(context) {
    const { env } = context;
    let allResult = null;
    let firstResult = null;
    let allJson = null;
    let firstJson = null;
    let error = null;
    try {
        allResult = env.DB.prepare('SELECT COUNT(*) as count FROM entries').all();
        allJson = JSON.parse(JSON.stringify(allResult));
        firstResult = env.DB.prepare('SELECT COUNT(*) as count FROM entries').first();
        firstJson = JSON.parse(JSON.stringify(firstResult));
    } catch (e) {
        error = { message: e.message };
    }
    return new Response(JSON.stringify({
        allResult,
        allJson,
        allKeys: allResult ? Object.getOwnPropertyNames(allResult) : null,
        firstResult,
        firstJson,
        firstKeys: firstResult ? Object.getOwnPropertyNames(firstResult) : null,
        firstVal: firstResult ? firstResult.count : null,
        dbType: typeof env.DB,
        dbKeys: Object.getOwnPropertyNames(env.DB),
        error,
    }), {
        headers: { 'Content-Type': 'application/json' },
    });
}
