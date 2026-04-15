/**
 * Atlas ecosystem memory interface — Node filesystem stub.
 *
 * Each product calls recordEcosystemEvent() to drop a signal into
 * Atlas's canonical memory. A cron elsewhere ingests the inbox into
 * memory/atlas/journal.md later.
 *
 * In Next.js this runs server-side only. In Expo it should be swapped
 * for an HTTP POST to a stub endpoint (not implemented here) — this
 * module throws a clear error if `fs` is unavailable.
 *
 * Atomic write via writeFile to tmp + rename.
 */
import { z } from "zod";
import { randomUUID } from "node:crypto";
import { mkdir, rename, writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

export const SourceProductSchema = z.enum([
  "volaura",
  "mindshift",
  "lifesim",
  "brandedby",
  "zeus",
]);
export type SourceProduct = z.infer<typeof SourceProductSchema>;

export const EcosystemEventSchema = z
  .object({
    source_product: SourceProductSchema,
    event_type: z.string().min(1),
    user_id: z.string().min(1),
    content: z.record(z.unknown()),
    emotional_intensity: z.number().int().min(0).max(5),
    timestamp: z.string(),
    event_id: z.string(),
  })
  .strict();
export type EcosystemEvent = z.infer<typeof EcosystemEventSchema>;

const INBOX_SUBPATH = join("memory", "atlas", "ecosystem-inbox");

function slugify(s: string): string {
  return (
    s
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "event"
  );
}

/** Walk up from startDir looking for memory/atlas. Returns inbox dir or null. */
function findInboxDir(startDir: string = process.cwd()): string | null {
  let current = resolve(startDir);
  while (true) {
    const marker = join(current, "memory", "atlas");
    if (existsSync(marker)) {
      return join(current, INBOX_SUBPATH);
    }
    const parent = dirname(current);
    if (parent === current) return null;
    current = parent;
  }
}

async function atomicWrite(target: string, payload: string): Promise<void> {
  await mkdir(dirname(target), { recursive: true });
  const tmp = `${target}.${randomUUID().slice(0, 8)}.tmp`;
  await writeFile(tmp, payload, { encoding: "utf-8" });
  await rename(tmp, target);
}

function formatMarkdown(event: EcosystemEvent): string {
  const front = JSON.stringify(event, null, 2);
  const content = JSON.stringify(event.content, null, 2);
  return (
    `---\n${front}\n---\n\n` +
    `Event from **${event.source_product}** — \`${event.event_type}\`.\n\n` +
    `User \`${event.user_id}\` at ${event.timestamp}. ` +
    `Emotional intensity: ${event.emotional_intensity}/5 ` +
    `(0=routine, 5=definitional).\n\n` +
    `Content:\n\n\`\`\`json\n${content}\n\`\`\`\n`
  );
}

export interface RecordEventInput {
  source_product: SourceProduct;
  event_type: string;
  user_id: string;
  content: Record<string, unknown>;
  emotional_intensity: number;
  inboxDir?: string;
}

/**
 * Record a cross-product event into Atlas's ecosystem inbox.
 * Returns the path written, or null if no inbox directory was resolvable
 * (e.g. running in production outside the monorepo).
 */
export async function recordEcosystemEvent(
  input: RecordEventInput,
): Promise<string | null> {
  const now = new Date();
  const event = EcosystemEventSchema.parse({
    source_product: input.source_product,
    event_type: input.event_type,
    user_id: input.user_id,
    content: input.content,
    emotional_intensity: input.emotional_intensity,
    timestamp: now.toISOString(),
    event_id: randomUUID(),
  });

  const targetDir = input.inboxDir ?? findInboxDir();
  if (!targetDir) {
    // eslint-disable-next-line no-console
    console.warn(
      "[atlas-core.memory] memory/atlas/ not found from cwd. " +
        "Event dropped locally; future HTTP stub will forward to prod inbox.",
      { event },
    );
    return null;
  }

  const ts = now
    .toISOString()
    .replace(/[-:]/g, "")
    .replace(/\.\d+Z$/, "Z");
  const shortId = event.event_id.split("-")[0];
  const filename = `${ts}-${event.source_product}-${slugify(
    event.event_type,
  )}-${shortId}.md`;
  const path = join(targetDir, filename);

  await atomicWrite(path, formatMarkdown(event));
  return path;
}
