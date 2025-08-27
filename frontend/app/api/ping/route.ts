export const runtime = "nodejs"
export const dynamic = "force-dynamic"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://listing-bot-api-production.up.railway.app"

export async function GET() {
    try {
        const res = await fetch(`${API_BASE_URL}/`, { cache: "no-store" })
        const text = await res.text()
        return new Response(text, { status: res.status, headers: { "Content-Type": res.headers.get("content-type") || "text/plain" } })
    } catch (e: any) {
        return new Response(JSON.stringify({ ok: false, message: e?.message || "ping failed" }), { status: 200, headers: { "Content-Type": "application/json" } })
    }
}


