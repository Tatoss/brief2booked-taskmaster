"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity, ArrowRight, Bot, CalendarDays, Check, CheckCircle2, ChevronDown,
  CircleDot, Clock3, Code2, FileText, Inbox, LayoutDashboard, Mail, Menu,
  MessageSquareText, Play, RotateCcw, Search, Settings, ShieldCheck, Sparkles,
  Users, X, Zap,
} from "lucide-react";

type RunState = "ready" | "running" | "complete" | "error";

type WorkflowResult = {
  run_id: string;
  status: "completed" | "needs_review" | "failed";
  decision: {
    service: string;
    summary: string;
    estimated_value_zar: number;
    delivery_weeks: number;
    fit_score: number;
    confidence: number;
    risks: string[];
    next_action: "qualify" | "request_clarification" | "decline";
    rationale: string;
  };
  actions: Array<{ action?: string; payload?: Record<string, unknown> }>;
};

const steps = [
  { icon: Mail, title: "Enquiry intercepted", detail: "New website enquiry from Naledi at Ubuntu Engineering", service: "Gmail", time: "00:00" },
  { icon: Sparkles, title: "Brief understood", detail: "Gemini identified a website redesign, 8-week timeline and R35k–R55k likely budget", service: "Gemini 3.5", time: "00:03" },
  { icon: Search, title: "Lead qualified", detail: "Matched against capability, capacity and past delivery patterns — score 92/100", service: "Firestore", time: "00:05" },
  { icon: FileText, title: "Proposal created", detail: "Personalised scope, milestones and estimate saved to the client workspace", service: "Drive", time: "00:09" },
  { icon: CalendarDays, title: "Follow-up reserved", detail: "30-minute discovery slot held for Wednesday at 10:30 SAST", service: "Calendar", time: "00:11" },
  { icon: CheckCircle2, title: "Pipeline updated", detail: "Lead, five delivery tasks and a review-ready reply were created", service: "Firestore", time: "00:13" },
];

const emptyStats = [
  { label: "Recent workflows", value: "0", delta: "Firestore", icon: Zap },
  { label: "Hours returned", value: "0", delta: "Estimated", icon: Clock3 },
  { label: "Qualified leads", value: "0", delta: "Completed", icon: Users },
  { label: "Success rate", value: "0%", delta: "Live", icon: Activity },
];

type Lead = { company: string; contact: string; service: string; value: string; score: number; status: string; tone: string };

export default function Home() {
  const [runState, setRunState] = useState<RunState>("ready");
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [error, setError] = useState("");
  const [mobileOpen, setMobileOpen] = useState(false);
  const [stats, setStats] = useState(emptyStats);
  const [leads, setLeads] = useState<Lead[]>([]);

  const visibleSteps = runState === "complete" ? steps.length : runState === "running" ? 1 : 0;
  const progress = runState === "complete" ? 100 : runState === "running" ? 18 : 0;
  const currentDate = useMemo(
    () => new Intl.DateTimeFormat("en-ZA", { dateStyle: "full" }).format(new Date()),
    [],
  );
  const score = result?.decision.fit_score ?? 0;
  const confidence = Math.round((result?.decision.confidence ?? 0) * 100);
  const workflowSteps = useMemo(() => {
    if (!result) return steps;
    return [
      steps[0],
      { ...steps[1], detail: `Gemini classified ${result.decision.service} with ${confidence}% confidence` },
      { ...steps[2], detail: `${result.decision.summary} — fit score ${score}/100` },
      { ...steps[3], detail: result.actions.some((item) => item.action === "proposal_created") ? "Proposal action completed and recorded" : "Proposal held for human review" },
      { ...steps[4], detail: result.actions.some((item) => item.action === "calendar_reserved") ? "Provisional discovery slot reserved" : "Calendar action was not authorised" },
      { ...steps[5], detail: `${result.actions.length} idempotent actions recorded for ${result.run_id}` },
    ];
  }, [confidence, result, score]);

  const loadOverview = useCallback(async () => {
    try {
      const response = await fetch("/v1/overview", { headers: { Accept: "application/json" } });
      if (!response.ok) return;
      const overview = await response.json() as {
        stats: { workflows: number; hours_returned: number; qualified_leads: number; success_rate: number };
        runs: Array<Record<string, unknown>>;
      };
      setStats([
        { ...emptyStats[0], value: String(overview.stats.workflows) },
        { ...emptyStats[1], value: String(overview.stats.hours_returned) },
        { ...emptyStats[2], value: String(overview.stats.qualified_leads) },
        { ...emptyStats[3], value: `${overview.stats.success_rate}%` },
      ]);
      setLeads(overview.runs.map((run) => ({
        company: String(run.company ?? "Unknown client"),
        contact: String(run.contact ?? run.sender_email ?? "Unknown contact"),
        service: String(run.service ?? run.subject ?? "Pending classification"),
        value: `R${Number(run.estimated_value_zar ?? 0).toLocaleString("en-ZA")}`,
        score: Number(run.fit_score ?? 0),
        status: run.status === "completed" ? "Proposal ready" : "Needs review",
        tone: run.status === "completed" ? "violet" : "amber",
      })));
    } catch {
      // Health and run controls remain available if overview loading is interrupted.
    }
  }, []);

  useEffect(() => {
    // Loading remote Firestore state is the intended external-system sync.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadOverview();
  }, [loadOverview]);

  async function startRun() {
    setResult(null);
    setError("");
    setRunState("running");
    try {
      const response = await fetch("/v1/demo", { method: "POST", headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error(`Agent returned HTTP ${response.status}`);
      const workflow = (await response.json()) as WorkflowResult;
      setResult(workflow);
      setRunState("complete");
      await loadOverview();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The agent could not be reached.");
      setRunState("error");
    }
  }
  function resetRun() { setResult(null); setError(""); setRunState("ready"); }

  return (
    <main className="min-h-screen bg-[#f6f7fb] text-[#14131a]">
      <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
        <div className="brand-row">
          <div className="brand-mark"><Zap size={18} fill="currentColor" /></div>
          <div><strong>Brief2Booked</strong><span>Agent console</span></div>
          <button className="mobile-close" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={20} /></button>
        </div>
        <nav aria-label="Main navigation">
          <a className="nav-item active" href="#dashboard"><LayoutDashboard size={18} />Overview</a>
          <a className="nav-item" href="#workflow"><Bot size={18} />Agent runs<span className="nav-count">{leads.length}</span></a>
          <a className="nav-item" href="#pipeline"><Users size={18} />Lead pipeline</a>
          <a className="nav-item" href="#architecture"><CircleDot size={18} />Integrations</a>
        </nav>
        <div className="sidebar-bottom">
          <div className="cloud-card">
            <div className="cloud-icon"><ShieldCheck size={18} /></div>
            <div><strong>Google Cloud</strong><span>All systems operational</span></div><i />
          </div>
          <a className="nav-item" href="#architecture"><Settings size={18} />Architecture</a>
          <a className="nav-item" href="#architecture"><Code2 size={18} />Source code</a>
          <div className="profile-row"><div className="avatar">TR</div><div><strong>Thato Ramoshaba</strong><span>Texcorp Solutions</span></div><ChevronDown size={16} /></div>
        </div>
      </aside>

      <section className="app-shell" id="dashboard">
        <header className="topbar">
          <button className="menu-button" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={21} /></button>
          <div className="top-title"><strong>Operations overview</strong><span>{currentDate}</span></div>
          <div className="header-actions">
            <div className="live-pill"><span /> LIVE</div>
            <button className="icon-button" aria-label="Messages"><MessageSquareText size={19} /></button>
            <button className="primary-button" onClick={runState === "running" ? undefined : startRun} disabled={runState === "running"}>
              {runState === "running" ? <Activity className="spin-soft" size={17} /> : <Play size={17} fill="currentColor" />}
              {runState === "running" ? "Agent working" : "Run demo"}
            </button>
          </div>
        </header>

        <div className="content-wrap">
          <section className="welcome-row">
            <div><p className="eyebrow">AUTONOMOUS FREELANCE OPERATIONS</p><h1>Your pipeline is moving<br />while you build.</h1><p>Brief2Booked turns messy enquiries into qualified, scheduled, proposal-ready opportunities — end to end.</p></div>
            <div className="agent-health"><div className="pulse-ring"><Bot size={25} /></div><div><span>Coordinator agent</span><strong>Watching for new work</strong></div><span className="status-dot" /></div>
          </section>

          <section className="stats-grid" aria-label="Performance summary">
            {stats.map(({ label, value, delta, icon: Icon }) => <article className="stat-card" key={label}><div className="stat-icon"><Icon size={19} /></div><div><span>{label}</span><strong>{value}</strong></div><em>{delta}</em></article>)}
          </section>

          <section className="workflow-grid" id="workflow">
            <article className="panel workflow-panel">
              <div className="panel-header"><div><p className="eyebrow">PROOF OF ACTION</p><h2>Live workflow execution</h2></div>{runState === "complete" && <button className="text-button" onClick={resetRun}><RotateCcw size={15} />Reset</button>}</div>
              {runState === "ready" || runState === "error" ? (
                <div className="ready-state">
                  <div className="mail-trigger"><Inbox size={28} /><span className="mail-badge">1</span></div>
                  <h3>{runState === "error" ? "The workflow needs attention" : "A new client enquiry just arrived"}</h3>
                  <p>{runState === "error" ? `${error} Please retry after checking the Cloud Run logs.` : "Run the live Cloud Run agent to watch Gemini understand, decide, route and complete the workflow."}</p>
                  <button className="run-button" onClick={startRun}><Play size={17} fill="currentColor" />{runState === "error" ? "Retry live agent" : "Start autonomous run"}</button>
                  <span className="demo-note">Live Gemini reasoning • Firestore audit • No emails are sent</span>
                </div>
              ) : (
                <div className="run-view">
                  <div className="run-meta"><div><span className={runState === "complete" ? "run-status done" : "run-status"}>{runState === "complete" ? <Check size={14} /> : <Activity size={14} />} {runState === "complete" ? "COMPLETED" : "RUNNING"}</span><strong>{result?.run_id ?? "Gemini is analysing the brief…"}</strong></div><span>{progress}%</span></div>
                  <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
                  <div className="timeline">
                    {workflowSteps.map(({ icon: Icon, title, detail, service, time }, index) => {
                      const visible = index < visibleSteps;
                      const active = runState === "running" && index === visibleSteps;
                      return <div className={`timeline-step ${visible ? "visible" : ""} ${active ? "active-step" : ""}`} key={title}>
                        <div className="step-rail"><div className="step-icon">{visible ? <Check size={15} /> : <Icon size={16} />}</div></div>
                        <div className="step-copy"><div><strong>{title}</strong><span>{time}</span></div><p>{detail}</p><em>{service}</em></div>
                      </div>;
                    })}
                  </div>
                </div>
              )}
            </article>

            <aside className="panel decision-panel">
              <div className="panel-header"><div><p className="eyebrow">LATEST DECISION</p><h2>Why the agent acted</h2></div><div className="gemini-chip"><Sparkles size={15} />Gemini 3.5</div></div>
              <div className="decision-score"><div className="score-ring"><strong>{score}</strong><span>/100</span></div><div><strong>{result ? result.decision.service : "High-fit opportunity"}</strong><span>{result?.status === "needs_review" ? "Human review required" : "Safe to continue autonomously"}</span></div></div>
              <blockquote>“{result?.decision.rationale ?? "Gemini’s validated decision and rationale will appear here after the live workflow runs."}”</blockquote>
              <div className="signal-list"><div><CheckCircle2 size={16} /><span>Service-capability match</span><strong>{score}%</strong></div><div><CheckCircle2 size={16} /><span>Model confidence</span><strong>{confidence}%</strong></div><div><CheckCircle2 size={16} /><span>Estimated engagement</span><strong>{result ? `R${result.decision.estimated_value_zar.toLocaleString("en-ZA")}` : "Pending"}</strong></div></div>
              <div className="safety-note"><ShieldCheck size={18} /><div><strong>Human boundary respected</strong><span>External reply saved as draft for review.</span></div></div>
            </aside>
          </section>

          <section className="panel pipeline-panel" id="pipeline">
            <div className="panel-header"><div><p className="eyebrow">OPPORTUNITY PIPELINE</p><h2>Work created by the agent</h2></div><button className="text-button">View pipeline <ArrowRight size={15} /></button></div>
            <div className="table-wrap"><table><thead><tr><th>CLIENT</th><th>REQUEST</th><th>EST. VALUE</th><th>FIT SCORE</th><th>STATUS</th></tr></thead><tbody>{leads.length === 0 ? <tr><td colSpan={5}>No production runs yet. Start the live agent to create the first audited workflow.</td></tr> : leads.map((lead) => <tr key={`${lead.company}-${lead.contact}`}><td><div className="client-cell"><div>{lead.company.slice(0,2).toUpperCase()}</div><span><strong>{lead.company}</strong><em>{lead.contact}</em></span></div></td><td>{lead.service}</td><td><strong>{lead.value}</strong></td><td><div className="score-bar"><span style={{width: `${lead.score}%`}} /><em>{lead.score}</em></div></td><td><span className={`status-pill ${lead.tone}`}>{lead.status}</span></td></tr>)}</tbody></table></div>
          </section>

          <section className="architecture-strip" id="architecture">
            <div><p className="eyebrow">BUILT FOR THE TASKMASTER TRACK</p><h2>Event in. Decisions made. Work completed.</h2></div>
            <div className="architecture-flow"><span>Gmail event</span><ArrowRight size={16}/><span>Pub/Sub</span><ArrowRight size={16}/><span>ADK + Gemini</span><ArrowRight size={16}/><span>Google tools</span></div>
          </section>
        </div>
      </section>
    </main>
  );
}
