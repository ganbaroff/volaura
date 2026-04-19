"use client";

/**
 * EventShift — event detail page. MVP.
 *
 * People-first domain drill-down: Event → Department → Area → Unit.
 * Each tier has an inline "+ add" form (primitive, not a modal — single-form spirit).
 *
 * Constitution:
 * - Law 1 (no red): indent accent uses primary hue; cancelled/closed uses muted tokens.
 * - Law 2 (energy): low mode collapses to event header + single "add department" action only.
 * - Law 3 (shame-free): empty sections say "add the first…", not "no …".
 * - Law 4 (motion): framer-motion layout for expand, gated by useReducedMotion.
 * - Law 5 (one primary CTA): header has one CTA; inline adds are secondary.
 *
 * Server-side character_events fire on every mutation.
 */

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useTranslation } from "react-i18next";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  ChevronDown,
  ChevronRight,
  Plus,
  Layers,
  MapPin,
  Users,
  Building2,
} from "lucide-react";

import { TopBar } from "@/components/layout/top-bar";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import { useEnergyMode } from "@/hooks/use-energy-mode";
import { useMotionPreference } from "@/hooks/use-reduced-motion";
import {
  useEventShiftEvent,
  useDepartments,
  useCreateDepartment,
  useAreas,
  useCreateArea,
  useUnits,
  useCreateUnit,
  type EventShiftDepartment,
  type EventShiftArea,
  type EventShiftUnit,
} from "@/hooks/queries/use-eventshift";

const inlineInputClass =
  "w-full rounded-lg border border-outline-variant bg-surface-container px-3 py-1.5 text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 transition-all";

const inlineButtonClass =
  "inline-flex items-center gap-1.5 rounded-lg border border-outline-variant bg-surface-container px-3 py-1.5 text-xs font-medium text-on-surface transition-all hover:border-primary/40 hover:bg-surface-container-high focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40";

// ── Page ────────────────────────────────────────────────────────────────────

export default function EventShiftDetailPage() {
  const { t } = useTranslation();
  const params = useParams<{ locale: string; eventId: string }>();
  const locale = params?.locale ?? "en";
  const eventId = params?.eventId ?? "";
  const energy = useEnergyMode().energy;

  const eventQ = useEventShiftEvent(eventId);
  const ev = eventQ.data;

  return (
    <div className="flex min-h-screen flex-col">
      <TopBar
        title={ev?.name ?? t("eventshift.detail.loading", { defaultValue: "Loading event…" })}
      />

      <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-6 sm:px-6 md:py-10">
        <Link
          href={`/${locale}/eventshift`}
          className="mb-6 inline-flex items-center gap-1.5 text-sm text-on-surface-variant transition-colors hover:text-on-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 rounded-md"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          {t("eventshift.detail.back", { defaultValue: "Back to events" })}
        </Link>

        {/* Event loading */}
        {eventQ.isLoading && (
          <div className="space-y-3">
            <Skeleton className="h-[100px] w-full rounded-2xl" />
            <Skeleton className="h-[60px] w-full rounded-xl" />
            <Skeleton className="h-[60px] w-full rounded-xl" />
          </div>
        )}

        {/* Event error */}
        {eventQ.error && (
          <div className="rounded-2xl border border-outline-variant bg-surface-container p-6 text-sm text-on-surface-variant">
            {t("eventshift.detail.err.load", {
              defaultValue:
                "We couldn't load this event. It may have been cancelled or you may not have access.",
            })}
          </div>
        )}

        {/* Event happy path */}
        {ev && (
          <>
            {/* Event header card */}
            <section className="rounded-2xl border border-outline-variant bg-surface-container p-5 md:p-6">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h1 className="text-xl font-bold text-on-surface font-headline sm:text-2xl">
                    {ev.name}
                  </h1>
                  {ev.description && (
                    <p className="mt-2 text-sm text-on-surface-variant">
                      {ev.description}
                    </p>
                  )}
                </div>
              </div>

              <dl className="mt-4 grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
                <MetaCell
                  label={t("eventshift.detail.meta.start", {
                    defaultValue: "Start",
                  })}
                  value={new Date(ev.start_at).toLocaleString(locale, {
                    day: "numeric",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                />
                <MetaCell
                  label={t("eventshift.detail.meta.end", { defaultValue: "End" })}
                  value={new Date(ev.end_at).toLocaleString(locale, {
                    day: "numeric",
                    month: "short",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                />
                <MetaCell
                  label={t("eventshift.detail.meta.timezone", {
                    defaultValue: "Timezone",
                  })}
                  value={ev.timezone}
                />
                <MetaCell
                  label={t("eventshift.detail.meta.status", {
                    defaultValue: "Status",
                  })}
                  value={t(`eventshift.status.${ev.status}`, {
                    defaultValue: ev.status,
                  })}
                />
              </dl>
            </section>

            {/* Departments */}
            <section className="mt-8">
              <div className="mb-3 flex items-center gap-2">
                <Building2 className="h-4 w-4 text-primary" aria-hidden="true" />
                <h2 className="text-lg font-semibold text-on-surface font-headline">
                  {t("eventshift.detail.departments.heading", {
                    defaultValue: "Departments",
                  })}
                </h2>
              </div>
              <DepartmentList eventId={ev.id} energy={energy} />
            </section>
          </>
        )}
      </main>
    </div>
  );
}

// ── Departments ──────────────────────────────────────────────────────────────

function DepartmentList({
  eventId,
  energy,
}: {
  eventId: string;
  energy: "full" | "mid" | "low";
}) {
  const { t } = useTranslation();
  const depts = useDepartments(eventId);
  const createDept = useCreateDepartment(eventId);
  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState("");

  const onAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try {
      await createDept.mutateAsync({ name: newName.trim() });
      setNewName("");
      setShowAdd(false);
    } catch {
      // Surface via createDept.error below if needed — keep form open.
    }
  };

  if (depts.isLoading) {
    return (
      <div className="space-y-2">
        <Skeleton className="h-[56px] w-full rounded-xl" />
        <Skeleton className="h-[56px] w-full rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {depts.data && depts.data.length === 0 && (
        <EmptyState
          icon={<Building2 className="mx-auto h-10 w-10 text-on-surface-variant" aria-hidden="true" />}
          title={t("eventshift.detail.departments.empty.title", {
            defaultValue: "Start with one department",
          })}
          description={t("eventshift.detail.departments.empty.desc", {
            defaultValue:
              "Security, Registration, Catering — whatever groups people for this event.",
          })}
        />
      )}

      {depts.data?.map((d) => (
        <DepartmentRow key={d.id} dept={d} energy={energy} />
      ))}

      {/* Add department — inline form */}
      {!showAdd ? (
        <button
          type="button"
          onClick={() => setShowAdd(true)}
          className={inlineButtonClass}
          aria-label={t("eventshift.detail.departments.add", {
            defaultValue: "Add department",
          })}
        >
          <Plus className="h-3.5 w-3.5" aria-hidden="true" />
          {t("eventshift.detail.departments.add", {
            defaultValue: "Add department",
          })}
        </button>
      ) : (
        <form
          onSubmit={onAdd}
          className="flex flex-col gap-2 rounded-xl border border-outline-variant bg-surface-container p-3 sm:flex-row"
        >
          <input
            autoFocus
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder={t("eventshift.detail.departments.placeholder", {
              defaultValue: "Department name",
            })}
            className={inlineInputClass}
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={!newName.trim() || createDept.isPending}
              className="inline-flex items-center justify-center rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-on-primary disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
            >
              {createDept.isPending
                ? t("common.saving", { defaultValue: "Saving…" })
                : t("common.add", { defaultValue: "Add" })}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowAdd(false);
                setNewName("");
              }}
              className="inline-flex items-center justify-center rounded-lg border border-outline-variant px-3 py-1.5 text-xs font-medium text-on-surface-variant"
            >
              {t("common.cancel", { defaultValue: "Cancel" })}
            </button>
          </div>
          {createDept.error && (
            <p role="alert" aria-live="polite" className="text-sm text-[#D4B4FF] mt-1">{(createDept.error as Error).message || "Failed to create"}</p>
          )}
        </form>
      )}
    </div>
  );
}

function DepartmentRow({
  dept,
  energy,
}: {
  dept: EventShiftDepartment;
  energy: "full" | "mid" | "low";
}) {
  const [expanded, setExpanded] = useState(false);
  const { shouldReduceMotion } = useMotionPreference();
  const { t } = useTranslation();

  return (
    <div className="rounded-xl border border-outline-variant bg-surface-container">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        aria-controls={`dept-panel-${dept.id}`}
        className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 rounded-xl"
      >
        <div className="flex min-w-0 items-center gap-2">
          <Building2 className="h-4 w-4 shrink-0 text-primary" aria-hidden="true" />
          <span className="truncate text-sm font-medium text-on-surface">
            {dept.name}
          </span>
          {dept.description && (
            <span className="hidden truncate text-xs text-on-surface-variant sm:inline">
              — {dept.description}
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronDown className="h-4 w-4 shrink-0 text-on-surface-variant" aria-hidden="true" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0 text-on-surface-variant" aria-hidden="true" />
        )}
      </button>

      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            id={`dept-panel-${dept.id}`}
            initial={shouldReduceMotion ? false : { height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={shouldReduceMotion ? undefined : { height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden border-t border-outline-variant/60"
          >
            <div className="p-4 pl-8">
              {energy === "low" ? (
                <p className="text-xs text-on-surface-variant">
                  {t("eventshift.detail.low_energy.drilldown", {
                    defaultValue:
                      "Open the event in full-energy mode to manage areas and units.",
                  })}
                </p>
              ) : (
                <AreaList departmentId={dept.id} />
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Areas ────────────────────────────────────────────────────────────────────

function AreaList({ departmentId }: { departmentId: string }) {
  const { t } = useTranslation();
  const areas = useAreas(departmentId);
  const createArea = useCreateArea(departmentId);
  const [showAdd, setShowAdd] = useState(false);
  const [newName, setNewName] = useState("");

  const onAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;
    try {
      await createArea.mutateAsync({ name: newName.trim() });
      setNewName("");
      setShowAdd(false);
    } catch {
      /* kept open for retry */
    }
  };

  if (areas.isLoading) {
    return <Skeleton className="h-[40px] w-full rounded-lg" />;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
        <MapPin className="h-3 w-3" aria-hidden="true" />
        {t("eventshift.detail.areas.heading", { defaultValue: "Areas" })}
      </div>

      {areas.data?.map((a) => <AreaRow key={a.id} area={a} />)}

      {areas.data && areas.data.length === 0 && (
        <p className="text-xs text-on-surface-variant/80">
          {t("eventshift.detail.areas.empty", {
            defaultValue: "No areas yet — areas group units by physical location.",
          })}
        </p>
      )}

      {!showAdd ? (
        <button
          type="button"
          onClick={() => setShowAdd(true)}
          className={inlineButtonClass}
        >
          <Plus className="h-3 w-3" aria-hidden="true" />
          {t("eventshift.detail.areas.add", { defaultValue: "Add area" })}
        </button>
      ) : (
        <form onSubmit={onAdd} className="flex flex-col gap-2 sm:flex-row">
          <input
            autoFocus
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder={t("eventshift.detail.areas.placeholder", {
              defaultValue: "e.g. Main stage",
            })}
            className={inlineInputClass}
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={!newName.trim() || createArea.isPending}
              className="inline-flex items-center justify-center rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-on-primary disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
            >
              {createArea.isPending
                ? t("common.saving", { defaultValue: "Saving…" })
                : t("common.add", { defaultValue: "Add" })}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowAdd(false);
                setNewName("");
              }}
              className="inline-flex items-center justify-center rounded-lg border border-outline-variant px-3 py-1.5 text-xs font-medium text-on-surface-variant"
            >
              {t("common.cancel", { defaultValue: "Cancel" })}
            </button>
          </div>
          {createArea.error && (
            <p role="alert" aria-live="polite" className="text-sm text-[#D4B4FF] mt-1">{(createArea.error as Error).message || "Failed to create"}</p>
          )}
        </form>
      )}
    </div>
  );
}

function AreaRow({ area }: { area: EventShiftArea }) {
  const [expanded, setExpanded] = useState(false);
  const { shouldReduceMotion } = useMotionPreference();

  return (
    <div className="rounded-lg border border-outline-variant/60 bg-surface-container-high">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        aria-controls={`area-panel-${area.id}`}
        className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 rounded-lg"
      >
        <div className="flex min-w-0 items-center gap-2">
          <MapPin className="h-3.5 w-3.5 shrink-0 text-on-surface-variant" aria-hidden="true" />
          <span className="truncate text-sm text-on-surface">{area.name}</span>
        </div>
        {expanded ? (
          <ChevronDown className="h-3.5 w-3.5 text-on-surface-variant" aria-hidden="true" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 text-on-surface-variant" aria-hidden="true" />
        )}
      </button>

      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            id={`area-panel-${area.id}`}
            initial={shouldReduceMotion ? false : { height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={shouldReduceMotion ? undefined : { height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden border-t border-outline-variant/40"
          >
            <div className="p-3 pl-6">
              <UnitList areaId={area.id} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Units ────────────────────────────────────────────────────────────────────

function UnitList({ areaId }: { areaId: string }) {
  const { t } = useTranslation();
  const units = useUnits(areaId);
  const createUnit = useCreateUnit(areaId);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({
    name: "",
    shift_start: "",
    shift_end: "",
    required_headcount: 1,
  });

  const canSubmit =
    form.name.trim() && form.shift_start && form.shift_end && form.required_headcount > 0;

  const onAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    try {
      await createUnit.mutateAsync({
        name: form.name.trim(),
        shift_start: new Date(form.shift_start).toISOString(),
        shift_end: new Date(form.shift_end).toISOString(),
        required_headcount: form.required_headcount,
      });
      setForm({ name: "", shift_start: "", shift_end: "", required_headcount: 1 });
      setShowAdd(false);
    } catch {
      /* kept open */
    }
  };

  if (units.isLoading) {
    return <Skeleton className="h-[32px] w-full rounded-md" />;
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
        <Users className="h-3 w-3" aria-hidden="true" />
        {t("eventshift.detail.units.heading", { defaultValue: "Shift units" })}
      </div>

      {units.data?.map((u) => <UnitRow key={u.id} unit={u} />)}

      {units.data && units.data.length === 0 && (
        <p className="text-xs text-on-surface-variant/80">
          {t("eventshift.detail.units.empty", {
            defaultValue: "A unit is one shift slot — time window + headcount.",
          })}
        </p>
      )}

      {!showAdd ? (
        <button type="button" onClick={() => setShowAdd(true)} className={inlineButtonClass}>
          <Plus className="h-3 w-3" aria-hidden="true" />
          {t("eventshift.detail.units.add", { defaultValue: "Add unit" })}
        </button>
      ) : (
        <form
          onSubmit={onAdd}
          className="space-y-2 rounded-lg border border-outline-variant bg-surface-container p-2.5"
        >
          <input
            autoFocus
            type="text"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            placeholder={t("eventshift.detail.units.placeholder", {
              defaultValue: "e.g. Gate A — evening",
            })}
            className={inlineInputClass}
          />
          <div className="grid grid-cols-2 gap-2">
            <input
              type="datetime-local"
              value={form.shift_start}
              onChange={(e) => setForm((f) => ({ ...f, shift_start: e.target.value }))}
              className={inlineInputClass}
              aria-label={t("eventshift.detail.units.shift_start", {
                defaultValue: "Shift start",
              })}
            />
            <input
              type="datetime-local"
              value={form.shift_end}
              onChange={(e) => setForm((f) => ({ ...f, shift_end: e.target.value }))}
              className={inlineInputClass}
              aria-label={t("eventshift.detail.units.shift_end", {
                defaultValue: "Shift end",
              })}
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-on-surface-variant">
              {t("eventshift.detail.units.headcount", { defaultValue: "Headcount" })}
            </label>
            <input
              type="number"
              min={1}
              max={1000}
              value={form.required_headcount}
              onChange={(e) =>
                setForm((f) => ({ ...f, required_headcount: Number(e.target.value) }))
              }
              className="w-20 rounded-lg border border-outline-variant bg-surface-container px-2 py-1 text-sm text-on-surface focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
            />
            <div className="ml-auto flex gap-2">
              <button
                type="submit"
                disabled={!canSubmit || createUnit.isPending}
                className="inline-flex items-center justify-center rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-on-primary disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
              >
                {createUnit.isPending
                  ? t("common.saving", { defaultValue: "Saving…" })
                  : t("common.add", { defaultValue: "Add" })}
              </button>
              <button
                type="button"
                onClick={() => setShowAdd(false)}
                className="inline-flex items-center justify-center rounded-lg border border-outline-variant px-3 py-1.5 text-xs font-medium text-on-surface-variant"
              >
                {t("common.cancel", { defaultValue: "Cancel" })}
              </button>
            </div>
          </div>
          {createUnit.error && (
            <p role="alert" aria-live="polite" className="text-sm text-[#D4B4FF] mt-1">{(createUnit.error as Error).message || "Failed to create"}</p>
          )}
        </form>
      )}
    </div>
  );
}

function UnitRow({ unit }: { unit: EventShiftUnit }) {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-between gap-2 rounded-md border border-outline-variant/40 bg-surface-container px-3 py-2">
      <div className="flex min-w-0 items-center gap-2">
        <Layers className="h-3 w-3 text-on-surface-variant" aria-hidden="true" />
        <span className="truncate text-sm text-on-surface">{unit.name}</span>
      </div>
      <div className="flex items-center gap-3 text-[11px] text-on-surface-variant">
        <span>
          {new Date(unit.shift_start).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
          {" – "}
          {new Date(unit.shift_end).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
        <span className="inline-flex items-center gap-1 rounded-full bg-surface-container-high px-2 py-0.5">
          <Users className="h-3 w-3" aria-hidden="true" />
          {unit.required_headcount}
        </span>
        <span
          className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${
            unit.status === "live"
              ? "bg-success/10 text-success"
              : unit.status === "staffed"
                ? "bg-primary/10 text-primary"
                : unit.status === "closed"
                  ? "bg-surface-container-high text-on-surface-variant"
                  : "bg-secondary-container text-on-secondary-container"
          }`}
        >
          {t(`eventshift.unit_status.${unit.status}`, { defaultValue: unit.status })}
        </span>
      </div>
    </div>
  );
}

// ── Meta cell ────────────────────────────────────────────────────────────────

function MetaCell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[10px] font-semibold uppercase tracking-widest text-on-surface-variant">
        {label}
      </dt>
      <dd className="mt-0.5 text-sm font-medium text-on-surface">{value}</dd>
    </div>
  );
}
