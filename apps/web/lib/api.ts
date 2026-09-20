export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function extractErrorMessage(body: unknown): string {
  if (
    body &&
    typeof body === "object" &&
    "detail" in body &&
    Array.isArray((body as { detail: unknown }).detail)
  ) {
    const detail = (body as { detail: { msg?: string }[] }).detail;
    const msg = detail[0]?.msg ?? "Request failed";
    return msg.replace(/^Value error,\s*/, "");
  }
  if (body && typeof body === "object" && "detail" in body) {
    return String((body as { detail: unknown }).detail);
  }
  return "Request failed";
}
