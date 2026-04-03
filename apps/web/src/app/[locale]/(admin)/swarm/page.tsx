"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Bot, AlertTriangle, CheckCircle, Clock, XCircle, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  useSwarmAgents,
  useSwarmProposals,
  useDecideProposal,
  type SwarmAgent,
  type SwarmProposal,
} from "@/hooks/queries/use-admin";

const STATUS_DOT: Record<string, string> = {
  idle: "bg-emerald-400",
  new: "bg-slate-400",
  blocked: "bg-red-400",
  unknown: "bg-slate-600",
};

const SEVERITY_BADGE: Record<string, string> = {
  critical: "bg-red-500/20 text-red-400 border-red-500/30",
  high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  low: "bg-slate-500/20 text-slate-400 border-slate-500/30",
};

function timeAgo(iso: string | null): string {
  if (!iso) return "never";
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.floor(diff / 60000);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  return `${Math.floor(hr / 24)}d ago`;
}

function AgentCard({ agent }: { agent: SwarmAgent }) {
  const dotColor = agent.blockers.length > 0 ? STATUS_DOT.blocked : STATUS_DOT[agent.status] ?? STATUS_DOT.unknown;

  return (
    <div className="rounded-lg border border-border bg-surface-container p-3 space-y-1.5">
      <div className="flex items-center gap-2">
        <span className={`size-2.5 rounded-full ${dotColor}`} />
        <span className="text-sm font-medium text-foreground truncate">{agent.display_name}</span>
        <span className="text-xs text-muted-foreground ml-auto">{timeAgo(agent.last_run)}</span>
      </div>
      <p className="text-xs text-muted-foreground line-clamp-1">{agent.last_task || "No tasks yet"}</p>
      {agent.blockers.length > 0 && (
        <div className="flex items-center gap-1 text-xs text-red-400">
          <AlertTriangle className="size-3" />
          <span className="truncate">{agent.blockers[0]}</span>
        </div>
      )}
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span>{agent.tasks_completed} done</span>
        {agent.tasks_failed > 0 && <span className="text-red-400">{agent.tasks_failed} failed</span>}
      </div>
    </div>
  );
}

function ProposalRow({ proposal, onDecide }: { proposal: SwarmProposal; onDecide: (id: string, action: string) => void }) {
  const [expanded, setExpanded] = useState(false);
  const badgeClass = SEVERITY_BADGE[proposal.severity] ?? SEVERITY_BADGE.low;

  return (
    <div className="rounded-lg border border-border bg-surface-container p-3 space-y-2">
      <div className="flex items-start gap-2">
        <span className={`text-[10px] uppercase px-1.5 py-0.5 rounded border ${badgeClass}`}>
          {proposal.severity}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-foreground">{proposal.title}</p>
          <p className="text-xs text-muted-foreground">{proposal.agent} · {timeAgo(proposal.timestamp)}</p>
        </div>
        {proposal.content && (
          <button onClick={() => setExpanded(!expanded)} className="text-muted-foreground">
            <ChevronDown className={`size-4 transition-transform ${expanded ? "rotate-180" : ""}`} />
          </button>
        )}
      </div>
      {expanded && proposal.content && (
        <p className="text-xs text-muted-foreground bg-surface-dim rounded p-2 whitespace-pre-wrap">
          {proposal.content.slice(0, 500)}
        </p>
      )}
      {proposal.status === "pending" && (
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={() => onDecide(proposal.id, "approve")} className="text-xs gap-1">
            <CheckCircle className="size-3" /> Approve
          </Button>
          <Button size="sm" variant="outline" onClick={() => onDecide(proposal.id, "dismiss")} className="text-xs gap-1">
            <XCircle className="size-3" /> Dismiss
          </Button>
        </div>
      )}
      {proposal.status !== "pending" && (
        <span className="text-xs text-muted-foreground">{proposal.status} {proposal.ceo_decision ? `· ${proposal.ceo_decision}` : ""}</span>
      )}
    </div>
  );
}

export default function SwarmPage() {
  const { t } = useTranslation();
  const { data: agentData, isLoading: agentsLoading } = useSwarmAgents();
  const { data: proposalData, isLoading: proposalsLoading } = useSwarmProposals();
  const decideMutation = useDecideProposal();

  const agents = agentData?.agents ?? [];
  const proposals = proposalData?.proposals ?? [];
  const summary = proposalData?.summary ?? { pending: 0, approved: 0, rejected: 0 };
  const totalTracked = agentData?.total_tracked ?? 0;
  const totalUntracked = agentData?.total_untracked ?? 0;

  const activeCount = agents.filter((a) => a.status === "idle" && a.last_run).length;
  const blockedCount = agents.filter((a) => a.blockers.length > 0).length;
  const newCount = agents.filter((a) => a.status === "new").length;

  function handleDecide(proposalId: string, action: string) {
    decideMutation.mutate({ proposalId, action });
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Bot className="size-5 text-primary" />
        <h1 className="text-lg font-bold">AI Office</h1>
        <span className="text-xs text-muted-foreground ml-auto">
          {totalTracked} tracked · {totalUntracked} untracked
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <div className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3 text-center">
          <div className="text-2xl font-bold text-emerald-400">{activeCount}</div>
          <div className="text-xs text-muted-foreground">Active</div>
        </div>
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3 text-center">
          <div className="text-2xl font-bold text-red-400">{blockedCount}</div>
          <div className="text-xs text-muted-foreground">Blocked</div>
        </div>
        <div className="rounded-lg border border-slate-500/20 bg-slate-500/5 p-3 text-center">
          <div className="text-2xl font-bold text-slate-400">{newCount}</div>
          <div className="text-xs text-muted-foreground">New</div>
        </div>
      </div>

      {/* Agent Grid */}
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
          <Clock className="size-4 text-muted-foreground" />
          Agents ({agents.length})
        </h2>
        {agentsLoading ? (
          <div className="text-sm text-muted-foreground">Loading agents...</div>
        ) : agents.length === 0 ? (
          <div className="text-sm text-muted-foreground">No agents tracked yet.</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {agents.map((a) => (
              <AgentCard key={a.name} agent={a} />
            ))}
          </div>
        )}
      </div>

      {/* Proposals */}
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
          <AlertTriangle className="size-4 text-muted-foreground" />
          Proposals ({summary.pending} pending)
        </h2>
        {proposalsLoading ? (
          <div className="text-sm text-muted-foreground">Loading proposals...</div>
        ) : proposals.length === 0 ? (
          <div className="text-sm text-muted-foreground">No proposals.</div>
        ) : (
          <div className="space-y-2">
            {proposals.slice(0, 10).map((p) => (
              <ProposalRow key={p.id} proposal={p} onDecide={handleDecide} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
