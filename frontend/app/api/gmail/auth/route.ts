export const runtime = "nodejs"
export const dynamic = "force-dynamic"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://listing-bot-api-production.up.railway.app"

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const redirect = searchParams.get("redirect") || "false"
  const url = `${API_BASE_URL}/gmail/auth?redirect=${encodeURIComponent(redirect)}`
  return Response.redirect(url, 302)
}


