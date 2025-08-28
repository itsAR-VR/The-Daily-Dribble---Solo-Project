import { NextRequest } from "next/server"

export const runtime = "nodejs"
export const dynamic = "force-dynamic"
export const maxDuration = 300

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://listing-bot-api-production.up.railway.app"

export async function GET() {
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 15000)
    try {
        const res = await fetch(`${API_BASE_URL}/`, { cache: "no-store", signal: controller.signal })
        const text = await res.text()
        return new Response(text, { status: res.status, headers: { "Content-Type": res.headers.get("content-type") || "text/plain" } })
    } catch (e: any) {
        return new Response(JSON.stringify({ ok: false, message: e?.message || "Warmup failed" }), { status: 502, headers: { "Content-Type": "application/json" } })
    } finally {
        clearTimeout(timeout)
    }
}

// Retain route for compatibility, but immediately call the new fast endpoint to avoid 504s
export async function POST(req: NextRequest) {
    const body = await req.text()
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 60000)
    try {
        let lastErr: any = null
        for (let attempt = 0; attempt < 3; attempt++) {
            try {
                const res = await fetch(`${API_BASE_URL}/listings/enhanced-fast`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "Accept": "application/json" },
                    cache: "no-store",
                    body,
                    signal: controller.signal,
                })
                const text = await res.text()
                const contentType = res.headers.get("content-type") || "application/json"
                if (res.ok) {
                    // Normalize success to 200 for stability
                    return new Response(text, { status: 200, headers: { "Content-Type": contentType } })
                }
                // Retry only on transient 5xx
                if (res.status === 502 || res.status === 504 || res.status === 500) {
                    await new Promise(r => setTimeout(r, 300 * (attempt + 1)))
                    continue
                }
                // Non-5xx: return normalized JSON with success=false but HTTP 200 to avoid Next.js 502
                let json: any
                try { json = text ? JSON.parse(text) : {} } catch { json = {} }
                if (!json || typeof json !== 'object') json = {}
                if (json.success === undefined) json.success = false
                if (!json.message) json.message = `Upstream HTTP ${res.status}`
                // Include platform context when possible (for easier debugging in UI logs)
                try {
                    const parsed = JSON.parse(body || '{}')
                    if (parsed && typeof parsed === 'object' && parsed.platform && !json.platform) {
                        json.platform = parsed.platform
                    }
                } catch {}
                return new Response(JSON.stringify(json), { status: 200, headers: { "Content-Type": "application/json" } })
            } catch (e: any) {
                lastErr = e
                await new Promise(r => setTimeout(r, 300 * (attempt + 1)))
            }
        }
        // Final normalized error after retries
        return new Response(JSON.stringify({ success: false, message: `Proxy upstream error${lastErr?.message ? ": " + lastErr.message : ''}` }), { status: 200, headers: { "Content-Type": "application/json" } })
    } finally {
        clearTimeout(timeout)
    }
}

// Fire-and-poll endpoints
export async function PUT(req: NextRequest) {
    // Start background job upstream
    const body = await req.text()
    const controller = new AbortController()
    const timeout = setTimeout(() => controller.abort(), 60000)
    try {
        const res = await fetch(`${API_BASE_URL}/listings/enhanced-visual/start`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Accept": "application/json" },
            cache: "no-store",
            body,
            signal: controller.signal,
        })
        const text = await res.text()
        const contentType = res.headers.get("content-type") || "application/json"
        return new Response(text, { status: res.status, headers: { "Content-Type": contentType } })
    } catch (e: any) {
        return new Response(JSON.stringify({ ok: false, message: e?.message || "start failed" }), { status: 502, headers: { "Content-Type": "application/json" } })
    } finally {
        clearTimeout(timeout)
    }
}


