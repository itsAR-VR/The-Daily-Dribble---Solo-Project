export const runtime = "nodejs"
export const dynamic = "force-dynamic"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://listing-bot-api-production.up.railway.app"

export async function GET() {
    try {
        const res = await fetch(`${API_BASE_URL}/gmail/status`, { cache: "no-store" })
        const ct = res.headers.get("content-type") || "application/json"
        if (ct.includes("application/json")) {
            const data = await res.json()
            const raw = (data?.status || data?.state || data?.auth_status || "").toString().toLowerCase()
            const boolAuth = [data?.authenticated, data?.isAuthenticated, data?.auth].some((v: any) => v === true || v === "true")
            const status = raw === "authenticated" || raw === "ok" || boolAuth
                ? "authenticated"
                : raw === "requires_auth" || raw === "needs_auth" || raw === "reauth"
                    ? "requires_auth"
                    : "not_configured"
            return new Response(JSON.stringify({ status }), { status: 200, headers: { "Content-Type": "application/json" } })
        }
        const text = await res.text()
        const status = text?.toLowerCase().includes("ok") ? "authenticated" : "not_configured"
        return new Response(JSON.stringify({ status }), { status: 200, headers: { "Content-Type": "application/json" } })
    } catch (e: any) {
        return new Response(JSON.stringify({ status: "not_configured", ok: false, message: e?.message || "status proxy error" }), { status: 200, headers: { "Content-Type": "application/json" } })
    }
}


