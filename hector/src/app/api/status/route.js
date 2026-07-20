const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8001";
const API_KEY = process.env.HECTOR_API_KEY || "";

export async function GET() {
  try {
    const res = await fetch(`${BACKEND_URL}/status`, {
      headers: { "X-API-Key": API_KEY },
    });

    if (!res.ok) {
      return Response.json({ status: "offline" }, { status: 502 });
    }

    const data = await res.json();
    return Response.json(data);
  } catch {
    return Response.json({ status: "offline" }, { status: 502 });
  }
}
