// Logs a click on a store link in usage_events, then forwards the visitor to
// the store. Links are built by click_tracking.py, which signs each one with
// CLICK_SIGNING_SECRET; anything without a valid signature is refused, so the
// click numbers cannot be forged and this is not an open redirect.
//
// Deploy with JWT verification off, because a link click sends no auth header.

const EVENTS_TABLE = "usage_events";
const AUTOMATED_AGENT =
  /bot|crawl|spider|slurp|preview|facebookexternalhit|whatsapp|telegram/i;

function hexToBytes(hex) {
  if (!/^(?:[0-9a-f]{2})+$/i.test(hex)) return new Uint8Array();
  return Uint8Array.from(hex.match(/../g), (pair) => parseInt(pair, 16));
}

function decodeToken(token) {
  const base64 = token.replace(/-/g, "+").replace(/_/g, "/");
  const bytes = Uint8Array.from(atob(base64), (char) => char.charCodeAt(0));
  return JSON.parse(new TextDecoder().decode(bytes));
}

async function isValidSignature(token, signature, secret) {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["verify"],
  );
  return crypto.subtle.verify(
    "HMAC",
    key,
    hexToBytes(signature),
    encoder.encode(token),
  );
}

function serviceKey() {
  const legacyKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (legacyKey) return legacyKey;
  return JSON.parse(Deno.env.get("SUPABASE_SECRET_KEYS") ?? "{}").default;
}

async function logClick({ url, ...details }) {
  try {
    const key = serviceKey();
    const timestamp = new Date().toISOString().replace(/\.\d+Z$/, "Z");
    const headers = {
      apikey: key,
      "Content-Type": "application/json",
      Prefer: "return=minimal",
    };
    // Only the older JWT keys are valid as a bearer token.
    if (key.startsWith("eyJ")) headers.Authorization = `Bearer ${key}`;

    const response = await fetch(
      `${Deno.env.get("SUPABASE_URL")}/rest/v1/${EVENTS_TABLE}`,
      {
        method: "POST",
        headers,
        body: JSON.stringify({
          timestamp_utc: timestamp,
          event: "click",
          session_id: details.session_id || "unknown",
          query: details.query,
          payload: { timestamp_utc: timestamp, event: "click", url, ...details },
        }),
      },
    );
    if (!response.ok) console.error("click not logged:", response.status);
  } catch (error) {
    // Analytics must never stop the visitor from reaching the store.
    console.error("click not logged:", error);
  }
}

function isHumanClick(req) {
  const purpose = req.headers.get("sec-purpose") ?? req.headers.get("purpose");
  const userAgent = req.headers.get("user-agent") ?? "";
  return req.method === "GET" && !purpose?.includes("prefetch") &&
    !AUTOMATED_AGENT.test(userAgent);
}

async function handleRequest(req) {
  const secret = Deno.env.get("CLICK_SIGNING_SECRET");
  if (!secret) return new Response("Not configured", { status: 500 });
  if (req.method !== "GET" && req.method !== "HEAD") {
    return new Response("Method not allowed", { status: 405 });
  }

  const params = new URL(req.url).searchParams;
  const token = params.get("d") ?? "";
  const signature = params.get("sig") ?? "";
  if (!token || !(await isValidSignature(token, signature, secret))) {
    return new Response("Invalid link", { status: 400 });
  }

  const click = decodeToken(token);
  if (isHumanClick(req)) EdgeRuntime.waitUntil(logClick(click));

  // Some store URLs hold raw Greek text, which a header cannot carry as is.
  return new Response(null, {
    status: 302,
    headers: { Location: new URL(click.url).href, "Cache-Control": "no-store" },
  });
}

Deno.serve(handleRequest);
