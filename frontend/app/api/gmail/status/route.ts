export const runtime = "nodejs"
export const dynamic = "force-dynamic"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://listing-bot-api-production.up.railway.app"

export async function GET() {
  try {
    const res = await fetch(`${API_BASE_URL}/gmail/status`, { cache: "no-store" })
    const text = await res.text()
    const contentType = res.headers.get("content-type") || "application/json"
    return new Response(text, { status: res.status, headers: { "Content-Type": contentType } })
  } catch (e: any) {
    return new Response(JSON.stringify({ status: "unknown", ok: false, message: e?.message || "status proxy error" }), { status: 200, headers: { "Content-Type": "application/json" } })
  }
}


