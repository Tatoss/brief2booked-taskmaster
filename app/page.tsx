"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity, ArrowRight, Bot, CalendarDays, Check, CheckCircle2, ChevronDown,
  CircleDot, Clock3, Code2, FileText, Inbox, LayoutDashboard, Mail, Menu,
  MessageSquareText, Play, RotateCcw, Search, Settings, ShieldCheck, Sparkles,
  Users, X, Zap,
} from "lucide-react";

type RunState = "ready" | "running" | "complete";

const steps = [
  { icon: Mail, title: "Enquiry intercepted", detail: "New website enquiry from Naledi at Ubuntu Engineering", service: "Gmail", time: "00:00" },
  { icon: Sparkles, title: "Brief understood", detail: "Gemini identified a website redesign, 8-week timeline and R35k–R55k likely budget", service: "Gemini 3.5", time: "00:03" },
  { icon: Search, title: "Lead qualified", detail: "Matched against capability, capacity and past delivery patterns — score 92/100", service: "Firestore", time: "00:05" },
  { icon: FileText, title: "Proposal created", detail: "Personalised scope, milestones and estimate saved to the client workspace", service: "Drive", time: "00:09" },
  { icon: CalendarDays, title: "Follow-up reserved", detail: "30-minute discovery slot held for Wednesday at 10:30 SAST", service: "Calendar", time: "00:11" },
  { icon: CheckCircle2, title: "Pipeline updated", detail: "Lead, five delivery tasks and a review-ready reply were created", service: "Firestore", time: "00:13" },
];

const stats = [
  { label: "Workflows this week", value: "24", delta: "+18%", icon: Zap },
  { label: "Hours returned", value: "11.6", delta: "≈ R6,960", icon: Clock3 },
  { label: "Qualified leads", value: "9", delta: "37.5%", icon: Users },
  { label: "Success rate", value: "98.2%", delta: "+2.1%", icon: Activity },
];

const leads = [
  { company: "Ubuntu Engineering", contact: "Naledi Mokoena", service: "Website redesign", value: "R45,000", score: 92, status: "Proposal ready", tone: "violet" },
  { company: "Mahlako Logistics", contact: "Peter Ndlovu", service: "Driver application", value: "R68,000", score: 87, status: "Call booked", tone: "blue" },
  { company: "Thuto Learning", contact: "Kgomotso Molefe", service: "School portal", value: "R52,000", score: 81, status: "Qualifying", tone: "amber" },
];

export default function Home() {
  const [runState, setRunState] = useState<RunState>("ready");
  const [visibleSteps, setVisibleSteps] = useState(0);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (runState !== "running") return;
    if (visibleSteps >= steps.length) {
      const done = window.setTimeout(() => setRunState("complete"), 500);
      return () => window.clearTimeout(done);
    }
    const next = window.setTimeout(() => setVisibleSteps((current) => current + 1), 800);
    return () => window.clearTimeout(next);
  }, [runState, visibleSteps]);

  const progress = useMemo(() => Math.round((visibleSteps / steps.length) * 100), [visibleSteps]);
  function startRun() { setVisibleSteps(0); setRunState("running"); }
  function resetRun() { setVisibleSteps(0); setRunState("ready"); }

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
          <a className="nav-item" href="#workflow"><Bot size={18} />Agent runs<span className="nav-count">6</span></a>
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
          <div className="top-title"><strong>Operations overview</strong><span>Monday, 31 August 2026</span></div>
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
              {runState === "ready" ? (
                <div className="ready-state">
                  <div className="mail-trigger"><Inbox size={28} /><span className="mail-badge">1</span></div>
                  <h3>A new client enquiry just arrived</h3>
                  <p>Run the agent to watch it understand, decide, route and complete the workflow without step-by-step guidance.</p>
                  <button className="run-button" onClick={startRun}><Play size={17} fill="currentColor" />Start autonomous run</button>
                  <span className="demo-note">Uses safe demo data • No emails are sent</span>
                </div>
              ) : (
                <div className="run-view">
                  <div className="run-meta"><div><span className={runState === "complete" ? "run-status done" : "run-status"}>{runState === "complete" ? <Check size={14} /> : <Activity size={14} />} {runState === "complete" ? "COMPLETED" : "RUNNING"}</span><strong>RUN-2026-0831-024</strong></div><span>{progress}%</span></div>
                  <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
                  <div className="timeline">
                    {steps.map(({ icon: Icon, title, detail, service, time }, index) => {
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
              <div className="decision-score"><div className="score-ring"><strong>92</strong><span>/100</span></div><div><strong>High-fit opportunity</strong><span>Safe to continue autonomously</span></div></div>
              <blockquote>“The client needs a technically straightforward redesign that matches Texcorp’s proven delivery history. Budget and timeline are realistic. No sensitive or irreversible action is required.”</blockquote>
              <div className="signal-list"><div><CheckCircle2 size={16} /><span>Service-capability match</span><strong>96%</strong></div><div><CheckCircle2 size={16} /><span>Budget confidence</span><strong>88%</strong></div><div><CheckCircle2 size={16} /><span>Capacity available</span><strong>Yes</strong></div></div>
              <div className="safety-note"><ShieldCheck size={18} /><div><strong>Human boundary respected</strong><span>External reply saved as draft for review.</span></div></div>
            </aside>
          </section>

          <section className="panel pipeline-panel" id="pipeline">
            <div className="panel-header"><div><p className="eyebrow">OPPORTUNITY PIPELINE</p><h2>Work created by the agent</h2></div><button className="text-button">View pipeline <ArrowRight size={15} /></button></div>
            <div className="table-wrap"><table><thead><tr><th>CLIENT</th><th>REQUEST</th><th>EST. VALUE</th><th>FIT SCORE</th><th>STATUS</th></tr></thead><tbody>{leads.map((lead) => <tr key={lead.company}><td><div className="client-cell"><div>{lead.company.slice(0,2).toUpperCase()}</div><span><strong>{lead.company}</strong><em>{lead.contact}</em></span></div></td><td>{lead.service}</td><td><strong>{lead.value}</strong></td><td><div className="score-bar"><span style={{width: `${lead.score}%`}} /><em>{lead.score}</em></div></td><td><span className={`status-pill ${lead.tone}`}>{lead.status}</span></td></tr>)}</tbody></table></div>
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
