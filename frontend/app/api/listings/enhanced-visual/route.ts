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
        const res = await fetch(`${API_BASE_URL}/listings/enhanced-fast`, {
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
        return new Response(JSON.stringify({ success: false, message: e?.message || "Proxy error" }), { status: 502, headers: { "Content-Type": "application/json" } })
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


