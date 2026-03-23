/**
 * Telegram Webhook Edge Function
 *
 * Handles incoming Telegram Bot API updates and responds to commands:
 *   /start  — link Telegram account to Volaura profile
 *   /aura   — show current AURA score
 *   /events — list upcoming open events
 *   /checkin <code> — check in to an event via QR code value
 */

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const BOT_TOKEN = Deno.env.get("TELEGRAM_BOT_TOKEN") ?? "";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SUPABASE_SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const API_URL = Deno.env.get("API_URL") ?? "http://localhost:8000";

const TG_API = `https://api.telegram.org/bot${BOT_TOKEN}`;

interface TelegramUpdate {
  update_id: number;
  message?: {
    message_id: number;
    from: { id: number; username?: string; first_name: string };
    chat: { id: number };
    text?: string;
  };
}

async function sendMessage(chatId: number, text: string): Promise<void> {
  await fetch(`${TG_API}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text, parse_mode: "Markdown" }),
  });
}

async function handleUpdate(update: TelegramUpdate, db: ReturnType<typeof createClient>): Promise<void> {
  const msg = update.message;
  if (!msg?.text) return;

  const chatId = msg.chat.id;
  const tgUserId = msg.from.id;
  const text = msg.text.trim();
  const [cmd, ...args] = text.split(/\s+/);

  switch (cmd.toLowerCase()) {
    case "/start": {
      const code = args[0];
      if (!code) {
        await sendMessage(chatId,
          "👋 *Welcome to Volaura Bot!*\n\nTo link your account, visit your profile settings and click *Connect Telegram*."
        );
        return;
      }
      // Link account via one-time code stored in profiles
      const { data, error } = await db
        .from("profiles")
        .update({ telegram_chat_id: chatId })
        .eq("telegram_link_code", code)
        .select("username")
        .single();

      if (error || !data) {
        await sendMessage(chatId, "❌ Invalid or expired link code. Please try again from your profile settings.");
        return;
      }
      await sendMessage(chatId, `✅ Account linked! Welcome, @${data.username}. Type /aura to see your score.`);
      break;
    }

    case "/aura": {
      const { data: profile } = await db
        .from("profiles")
        .select("id, username")
        .eq("telegram_chat_id", chatId)
        .single();

      if (!profile) {
        await sendMessage(chatId, "❌ Your Telegram is not linked to a Volaura account. Use /start <code> to link.");
        return;
      }

      const { data: aura } = await db
        .from("aura_scores")
        .select("overall_score, badge_tier, elite_status")
        .eq("volunteer_id", profile.id)
        .single();

      if (!aura) {
        await sendMessage(chatId, "📊 No AURA score yet. Complete an assessment at volaura.az to earn your score!");
        return;
      }

      const elite = aura.elite_status ? " ⭐ *Elite*" : "";
      await sendMessage(chatId,
        `📊 *Your AURA Score*\n\nScore: *${aura.overall_score.toFixed(1)}*\nBadge: *${aura.badge_tier.toUpperCase()}*${elite}\n\nView full breakdown: volaura.az/u/${profile.username}`
      );
      break;
    }

    case "/events": {
      const { data: events } = await db
        .from("events")
        .select("title_en, location, start_date, id")
        .eq("status", "open")
        .eq("is_public", true)
        .order("start_date")
        .limit(5);

      if (!events?.length) {
        await sendMessage(chatId, "📅 No upcoming events right now. Check volaura.az/events for updates.");
        return;
      }

      const list = events.map((e, i) => {
        const date = new Date(e.start_date).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
        return `${i + 1}. *${e.title_en}* — ${e.location ?? "TBD"} (${date})`;
      }).join("\n");

      await sendMessage(chatId, `📅 *Upcoming Events*\n\n${list}\n\nRegister at volaura.az/events`);
      break;
    }

    case "/checkin": {
      const code = args[0];
      if (!code) {
        await sendMessage(chatId, "Usage: /checkin <code>");
        return;
      }

      const { data: profile } = await db
        .from("profiles")
        .select("id")
        .eq("telegram_chat_id", chatId)
        .single();

      if (!profile) {
        await sendMessage(chatId, "❌ Account not linked. Use /start to link your Volaura account.");
        return;
      }

      const { data: reg, error } = await db
        .from("registrations")
        .select("id, event_id, checked_in_at")
        .eq("check_in_code", code)
        .eq("volunteer_id", profile.id)
        .single();

      if (error || !reg) {
        await sendMessage(chatId, "❌ Invalid check-in code or you are not registered for this event.");
        return;
      }

      if (reg.checked_in_at) {
        await sendMessage(chatId, "✅ You have already checked in to this event.");
        return;
      }

      await db.from("registrations").update({
        status: "approved",
        checked_in_at: new Date().toISOString(),
      }).eq("id", reg.id);

      await sendMessage(chatId, "✅ *Check-in successful!* Welcome to the event. Enjoy!");
      break;
    }

    default:
      await sendMessage(chatId,
        "Available commands:\n/aura — your AURA score\n/events — upcoming events\n/checkin <code> — check in to an event"
      );
  }
}

serve(async (req: Request) => {
  if (req.method !== "POST") {
    return new Response("Method not allowed", { status: 405 });
  }

  try {
    const update: TelegramUpdate = await req.json();
    const db = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);
    await handleUpdate(update, db);
    return new Response("ok", { status: 200 });
  } catch (err) {
    console.error("Webhook error:", err);
    return new Response("Internal error", { status: 500 });
  }
});
