import { NextRequest, NextResponse } from "next/server"

export const runtime = "nodejs"
export const dynamic = "force-dynamic"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://listing-bot-api-production.up.railway.app"

export async function GET(req: NextRequest, { params }: { params: { jobId: string } }) {
    const { jobId } = params

    try {
        const res = await fetch(`${API_BASE_URL}/listings/enhanced-visual/status/${jobId}`, {
            method: "GET",
            headers: { "Accept": "application/json" },
            cache: "no-store"
        })

        const data = await res.json()

        return NextResponse.json(data, {
            status: res.status,
            headers: {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "Content-Type"
            }
        })
    } catch (error) {
        return NextResponse.json(
            { error: "Failed to fetch job status" },
            { status: 500 }
        )
    }
}
