/**
 * Send Notification Edge Function
 *
 * Sends Telegram messages to volunteers for:
 *   - assessment_reminder   — started but not completed after 24h
 *   - event_confirmation    — after registering for an event
 *   - event_reminder_24h    — 24h before event start
 *   - event_reminder_2h     — 2h before event start
 *   - aura_updated          — after AURA score recalculated
 *
 * Invoke via Supabase Edge Function HTTP call or scheduled cron.
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const BOT_TOKEN = Deno.env.get("TELEGRAM_BOT_TOKEN") ?? "";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SUPABASE_SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";

const TG_API = `https://api.telegram.org/bot${BOT_TOKEN}`;

interface NotificationPayload {
  type: "assessment_reminder" | "event_confirmation" | "event_reminder_24h" | "event_reminder_2h" | "aura_updated";
  volunteer_id: string;
  event_id?: string;
  session_id?: string;
  aura_score?: number;
  badge_tier?: string;
}

async function sendTelegram(chatId: number, text: string): Promise<boolean> {
  const r = await fetch(`${TG_API}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: "Markdown" }),
  });
  return r.ok;
}

async function getVolunteerChatId(db: ReturnType<typeof createClient>, volunteerId: string): Promise<number | null> {
  const { data } = await db
    .from("profiles")
    .select("telegram_chat_id, username")
    .eq("id", volunteerId)
    .single();
  return data?.telegram_chat_id ?? null;
}

async function buildMessage(
  db: ReturnType<typeof createClient>,
  payload: NotificationPayload
): Promise<string | null> {
  switch (payload.type) {
    case "assessment_reminder":
      return "⏰ *Reminder:* You started an assessment but didn't finish it. Complete it to update your AURA score! Visit volaura.az/assessment";

    case "event_confirmation": {
      if (!payload.event_id) return null;
      const { data: ev } = await db.from("events").select("title_en, start_date, location").eq("id", payload.event_id).single();
      if (!ev) return null;
      const date = new Date(ev.start_date).toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" });
      return `✅ *Registered!*\n\nEvent: *${ev.title_en}*\nDate: ${date}\nLocation: ${ev.location ?? "TBD"}\n\nYour check-in QR code is available in the app.`;
    }

    case "event_reminder_24h": {
      if (!payload.event_id) return null;
      const { data: ev } = await db.from("events").select("title_en, start_date, location").eq("id", payload.event_id).single();
      if (!ev) return null;
      return `📅 *Event tomorrow!*\n\n*${ev.title_en}*\n${ev.location ?? "TBD"}\n\nDon't forget to bring your check-in code!`;
    }

    case "event_reminder_2h": {
      if (!payload.event_id) return null;
      const { data: ev } = await db.from("events").select("title_en, location").eq("id", payload.event_id).single();
      if (!ev) return null;
      return `⏰ *Starting in 2 hours!*\n\n*${ev.title_en}* at ${ev.location ?? "TBD"}\n\nHead over now!`;
    }

    case "aura_updated": {
      const score = payload.aura_score?.toFixed(1) ?? "—";
      const tier = (payload.badge_tier ?? "none").toUpperCase();
      return `🏆 *AURA Score Updated!*\n\nNew score: *${score}*\nBadge: *${tier}*\n\nShare your achievement at volaura.az`;
    }

    default:
      return null;
  }
}

serve(async (req: Request) => {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  try {
    const payload: NotificationPayload = await req.json();
    const db = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

    const chatId = await getVolunteerChatId(db, payload.volunteer_id);
    if (!chatId) {
      return new Response(JSON.stringify({ sent: false, reason: "no_telegram" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    const message = await buildMessage(db, payload);
    if (!message) {
      return new Response(JSON.stringify({ sent: false, reason: "no_message" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    const sent = await sendTelegram(chatId, message);
    return new Response(JSON.stringify({ sent }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (err) {
    console.error("Send notification error:", err);
    return new Response("Internal error", { status: 500 });
  }
});
