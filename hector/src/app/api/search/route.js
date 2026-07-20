const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8001";
const API_KEY = process.env.HECTOR_API_KEY || "";

export async function POST(request) {
  try {
    const body = await request.json();

    const res = await fetch(`${BACKEND_URL}/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
      },
      body: JSON.stringify({
        query: body.query,
        page: 1,
        page_size: 5,
        verify: true,
        format: "summary",
        include_related: true,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      return new Response(text || `Backend error: ${res.status}`, {
        status: res.status,
      });
    }

    const data = await res.json();
    return Response.json(data);
  } catch (err) {
    return new Response(
      JSON.stringify({ error: err.message || "Backend unavailable" }),
      { status: 502, headers: { "Content-Type": "application/json" } }
    );
  }
}
