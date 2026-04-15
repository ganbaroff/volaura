/**
 * @volaura/atlas-core — canonical Atlas identity + voice + memory interface.
 *
 * Consumed by all 5 VOLAURA ecosystem products: volaura (Next.js),
 * mindshift (Expo), lifesim (Expo/Godot bridge), brandedby (Next.js), zeus (Next.js).
 *
 * The identity.json file at package root is the machine-readable source
 * of truth, shared with the Python sibling so the two runtimes never drift.
 */
export {
  AtlasIdentitySchema,
  IDENTITY,
  loadIdentity,
} from "./identity.js";
export type { AtlasIdentity } from "./identity.js";

export {
  BreachSchema,
  VoiceCheckResultSchema,
  validateVoice,
} from "./voice.js";
export type { Breach, VoiceCheckResult } from "./voice.js";

export {
  EcosystemEventSchema,
  SourceProductSchema,
  recordEcosystemEvent,
} from "./memory.js";
export type { EcosystemEvent, SourceProduct } from "./memory.js";
