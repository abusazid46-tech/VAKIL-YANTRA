"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Archive,
  Bell,
  BookOpen,
  Bot,
  CalendarDays,
  Check,
  ChevronRight,
  Copy,
  Download,
  FileText,
  Gavel,
  Lock,
  Mail,
  Menu,
  MessageSquare,
  Mic,
  Play,
  Plus,
  Printer,
  Scale,
  Search,
  Send,
  ShieldCheck,
  Upload,
  Users,
  X
} from "lucide-react";
import {
  checklist,
  legalActs,
  plans,
  SectionId,
  sections,
  securityClaims,
  stats
} from "../data/product";
import {
  apiGet,
  apiPatch,
  apiPost,
  apiUpload,
  AiResponse,
  AuthToken,
  Citation,
  DashboardResponse,
  DocumentDownloadUrl,
  DocumentRecord,
  FirmUserRecord,
  ForgotPasswordResponse,
  InvitationRecord,
  InviteUserResponse,
  LegalSearchResponse,
  LegalSourceItem,
  LoginChallenge,
  MatterDetail,
  MatterRecord,
  MatterTask,
  WorkspaceFolderRecord,
  WorkspaceNoteRecord,
  WorkspaceOverview
} from "../lib/api";

type AuthUser = {
  user_id?: string;
  firm_id?: string;
  name: string;
  email: string;
  role: string;
  plan: string;
  accessToken?: string;
};

const roleOptions = [
  { value: "admin_advocate", label: "Admin" },
  { value: "advocate", label: "Advocate" }
];

function roleLabel(role: string) {
  if (role === "admin_advocate") return "Admin";
  return roleOptions.find((option) => option.value === role)?.label ?? role;
}

const firstByGroup = sections.reduce<Record<string, boolean>>((acc, section) => {
  if (!acc[section.group]) acc[section.group] = true;
  return acc;
}, {});

function navGroups() {
  const seen = new Set<string>();
  return sections.flatMap((section) => {
    if (seen.has(section.group)) return [];
    seen.add(section.group);
    return section.group;
  });
}

function formatDate(value?: string | null) {
  if (!value) return "Not set";
  return new Intl.DateTimeFormat("en-IN", { day: "2-digit", month: "short", year: "numeric" }).format(new Date(value));
}

async function openDocument(documentId: string, token?: string) {
  if (!token) return;
  const signed = await apiGet<DocumentDownloadUrl>(`/documents/${documentId}/download-url`, token);
  window.open(signed.download_url, "_blank", "noopener,noreferrer");
}

export default function Home() {
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [active, setActive] = useState<SectionId>("dashboard");
  const [menuOpen, setMenuOpen] = useState(false);
  const activeSection = sections.find((section) => section.id === active) ?? sections[0];

  useEffect(() => {
    const saved = window.localStorage.getItem("vakil-yantra-user");
    if (saved) {
      try {
        const parsed = JSON.parse(saved) as AuthUser;
        if (parsed.accessToken) {
          apiGet("/auth/me", parsed.accessToken)
            .then(() => setAuthUser(parsed))
            .catch(() => window.localStorage.removeItem("vakil-yantra-user"))
            .finally(() => setAuthReady(true));
          return;
        }
        setAuthUser(parsed);
      } catch {
        window.localStorage.removeItem("vakil-yantra-user");
      }
    }
    setAuthReady(true);
  }, []);

  function select(id: SectionId) {
    setActive(id);
    setMenuOpen(false);
  }

  function completeAuth(user: AuthUser, remember: boolean) {
    setAuthUser(user);
    if (remember) {
      window.localStorage.setItem("vakil-yantra-user", JSON.stringify(user));
    } else {
      window.localStorage.removeItem("vakil-yantra-user");
    }
  }

  function logout() {
    setAuthUser(null);
    setActive("dashboard");
    window.localStorage.removeItem("vakil-yantra-user");
  }

  if (!authReady) {
    return (
      <div className="auth-loading">
        <Scale />
        <span>Loading Vakil Yantra...</span>
      </div>
    );
  }

  if (!authUser) {
    return <AuthScreen onComplete={completeAuth} />;
  }

  return (
    <div className="shell">
      <aside className={`sidebar ${menuOpen ? "open" : ""}`}>
        <div className="brand">
          <div className="mark">
            <Scale size={24} strokeWidth={1.8} />
          </div>
          <div>
            <div className="brand-title">Vakil Yantra</div>
            <div className="brand-sub">Assistive legal intelligence</div>
          </div>
        </div>
        <nav className="nav" aria-label="Primary">
          {navGroups().map((group) => (
            <div key={group}>
              <div className="nav-group">{group}</div>
              {sections
                .filter((section) => section.group === group)
                .map((section) => {
                  const Icon = section.icon;
                  return (
                    <button
                      className={`nav-btn ${active === section.id ? "active" : ""}`}
                      key={section.id}
                      onClick={() => select(section.id)}
                    >
                      <Icon aria-hidden="true" />
                      <span>{section.label}</span>
                      {"badge" in section && section.badge ? <span className="badge">{section.badge}</span> : null}
                    </button>
                  );
                })}
            </div>
          ))}
        </nav>
        <div className="userbox">
          <div className="avatar">VY</div>
          <div>
            <div className="user-name">{authUser.name}</div>
            <div className="user-plan">{roleLabel(authUser.role)} | {authUser.plan}</div>
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <button className="btn ghost mobile-menu" onClick={() => setMenuOpen((value) => !value)} aria-label="Toggle navigation">
            {menuOpen ? <X /> : <Menu />}
          </button>
          <div className="top-title">{activeSection.label}</div>
          <button className="btn ghost">
            <ShieldCheck /> Security
          </button>
          <button className="btn ghost" onClick={logout}>
            <Lock /> Logout
          </button>
          <button className="btn primary">
            <Upload /> Upload File
          </button>
        </header>
        <div className="mobile-tabs" aria-label="Section shortcuts">
          {sections.slice(0, 10).map((section) => (
            <button
              className={`mobile-tab ${active === section.id ? "active" : ""}`}
              key={section.id}
              onClick={() => select(section.id)}
            >
              {section.label}
            </button>
          ))}
        </div>
        <div className="content">
          {active === "dashboard" ? <Dashboard authUser={authUser} onSelect={select} /> : null}
          {active === "drafting" ? <DraftingStudio authUser={authUser} /> : null}
          {active === "library" ? <LegalLibrary authUser={authUser} onSelect={select} /> : null}
          {active === "case" ? <CaseIntelligence authUser={authUser} /> : null}
          {active === "matters" ? <Matters authUser={authUser} /> : null}
          {active === "procedural" ? <ProceduralGuide /> : null}
          {active === "limitation" ? <LimitationCalculator /> : null}
          {active === "opposing" ? <OpposingCounsel /> : null}
          {active === "amendments" ? <Amendments /> : null}
          {active === "judgments" ? <Judgments /> : null}
          {active === "ecourts" ? <ECourts /> : null}
          {active === "translate" ? <Translate /> : null}
          {active === "workspace" ? <Workspace authUser={authUser} /> : null}
          {active === "settings" ? <SettingsPanel authUser={authUser} /> : null}
          {active === "plans" ? <Plans /> : null}
          {active === "videos" ? <Videos /> : null}
          {active === "security" ? <Security /> : null}
          <SecurityFooter />
        </div>
      </main>
    </div>
  );
}

function AuthScreen({ onComplete }: { onComplete: (user: AuthUser, remember: boolean) => void }) {
  const [mode, setMode] = useState<"login" | "signup" | "invite" | "forgot" | "reset">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [firmName, setFirmName] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [inviteToken, setInviteToken] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [invitationEntry, setInvitationEntry] = useState(false);
  const [remember, setRemember] = useState(true);
  const [challenge, setChallenge] = useState<LoginChallenge | null>(null);
  const [otp, setOtp] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const invite = params.get("invite");
    const reset = params.get("reset");
    if (invite) {
      setInviteToken(invite);
      setInvitationEntry(true);
      setMode("invite");
    }
    if (reset) {
      setResetToken(reset);
      setMode("reset");
    }
  }, []);

  function complete(token: AuthToken) {
    onComplete(
      {
        user_id: token.user.user_id,
        firm_id: token.user.firm_id,
        name: token.user.name,
        email: token.user.email,
        role: token.user.role,
        plan: token.user.plan,
        accessToken: token.access_token
      },
      remember
    );
  }

  function switchMode(nextMode: "login" | "signup" | "invite" | "forgot" | "reset") {
    setMode(nextMode);
    setChallenge(null);
    setError("");
    setNotice("");
  }

  async function quickDemoLogin(targetRole: "admin" | "associate") {
    const targetEmail = targetRole === "admin" ? "advocate@vakilyantra.in" : "associate@vakilyantra.in";
    const targetPassword = targetRole === "admin" ? "Vakil@123" : "Associate@123";
    setEmail(targetEmail);
    setPassword(targetPassword);
    setBusy(true);
    setError("");
    setNotice(`Signing in as ${targetRole === "admin" ? "Admin Advocate" : "Associate"}...`);
    try {
      const nextChallenge = await apiPost<LoginChallenge>("/auth/login", { email: targetEmail, password: targetPassword });
      setChallenge(nextChallenge);
      const code = nextChallenge.preview_otp || "123456";
      setOtp(code);
      setNotice(`Verification code ${code} verified. Loading chamber dashboard...`);
      const token = await apiPost<AuthToken>("/auth/verify-otp", { challenge_id: nextChallenge.challenge_id, otp: code });
      complete(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Quick login failed");
    } finally {
      setBusy(false);
    }
  }

  async function startLogin() {
    setBusy(true);
    try {
      const nextChallenge = await apiPost<LoginChallenge>("/auth/login", { email, password });
      setError("");
      setChallenge(nextChallenge);
      const code = nextChallenge.preview_otp || (email.includes("vakilyantra.in") ? "123456" : "");
      if (code) {
        setOtp(code);
        setNotice(`Verification code: ${code}`);
      } else {
        setNotice("Verification code sent by email.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  async function verifyOtp() {
    if (!challenge) {
      setError("Start login first.");
      return;
    }
    setBusy(true);
    try {
      const token = await apiPost<AuthToken>("/auth/verify-otp", { challenge_id: challenge.challenge_id, otp });
      complete(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "OTP verification failed");
    } finally {
      setBusy(false);
    }
  }

  async function createFirm() {
    setBusy(true);
    try {
      const token = await apiPost<AuthToken>("/auth/signup", {
        firm_name: firmName,
        name,
        email,
        password,
        plan: "chamber"
      });
      complete(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setBusy(false);
    }
  }

  async function acceptInvite() {
    setBusy(true);
    try {
      const token = await apiPost<AuthToken>("/auth/invitations/accept", {
        token: inviteToken,
        name,
        password
      });
      complete(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invitation acceptance failed");
    } finally {
      setBusy(false);
    }
  }

  async function requestReset() {
    setBusy(true);
    try {
      const response = await apiPost<ForgotPasswordResponse>("/auth/forgot-password", { email });
      setError("");
      setNotice(
        response.preview_reset_url
          ? `Reset preview link: ${response.preview_reset_url}`
          : `If the account exists, a reset link was sent to ${response.masked_channel ?? "that email"}.`
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Password reset failed");
    } finally {
      setBusy(false);
    }
  }

  async function completeReset() {
    setBusy(true);
    try {
      await apiPost("/auth/reset-password", { token: resetToken, new_password: newPassword });
      setError("");
      setNotice("Password updated. You can sign in now.");
      setMode("login");
      setPassword("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Password reset failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-brand-panel">
        <div className="mark large">
          <Scale size={34} strokeWidth={1.7} />
        </div>
        <div className="eyebrow">Secure advocate workspace</div>
        <h1>Vakil Yantra</h1>
        <p className="lede">
          Login-protected access for legal drafting, matter files, source-backed AI research, limitation alerts and firm administration.
        </p>
        <div className="auth-trust-list">
          {["Email and password gate", "Time-boxed OTP challenge", "Remembered local session", "Logout and protected dashboard"].map((item) => (
            <div className="check-item" key={item}>
              <div className="check-box">
                <Check size={17} />
              </div>
              <div>{item}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="auth-card">
        <div className="auth-tabs" aria-label="Authentication options">
          <button className={`auth-tab ${mode === "login" ? "active" : ""}`} onClick={() => switchMode("login")}>Sign in</button>
          {!invitationEntry ? (
            <button className={`auth-tab ${mode === "signup" ? "active" : ""}`} onClick={() => switchMode("signup")}>Create account</button>
          ) : null}
          <button className={`auth-tab ${mode === "invite" ? "active" : ""}`} onClick={() => switchMode("invite")}>Accept invite</button>
        </div>
        <div className="card-title">{challenge ? "Two-Step Verification" : mode === "signup" ? "Create Account" : mode === "invite" ? "Accept Invitation" : mode === "forgot" || mode === "reset" ? "Reset Password" : "Sign In"}</div>
        <div className="card-sub">{challenge ? "Enter the email code" : "Secure account access"}</div>

        {!challenge && mode === "login" ? (
          <>
            <div className="demo-credentials-box">
              <div className="demo-credentials-header">
                <span className="demo-credentials-badge">Quick Demo Access</span>
                <span className="demo-credentials-sub">Pre-seeded Chamber Accounts</span>
              </div>
              <div className="demo-btn-row">
                <button
                  type="button"
                  className="btn primary demo-login-btn"
                  onClick={() => quickDemoLogin("admin")}
                  disabled={busy}
                >
                  ⚡ 1-Click Admin (A. Sharma)
                </button>
                <button
                  type="button"
                  className="btn ghost demo-login-btn"
                  onClick={() => quickDemoLogin("associate")}
                  disabled={busy}
                >
                  ⚡ 1-Click Associate (Priya)
                </button>
              </div>
            </div>

            <div className="auth-divider">
              <span>or sign in with password</span>
            </div>

            <label className="field">
              <span className="label">Email</span>
              <input
                className="input"
                value={email}
                placeholder="advocate@vakilyantra.in"
                onChange={(event) => setEmail(event.target.value)}
              />
            </label>
            <label className="field">
              <span className="label">Password</span>
              <input
                className="input"
                type="password"
                value={password}
                placeholder="Vakil@123"
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
            <label className="remember-row">
              <input type="checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} />
              <span>Remember this session</span>
            </label>
            <button className="btn primary auth-submit" onClick={startLogin} disabled={busy}>
              <Lock /> {busy ? "Checking..." : "Continue"}
            </button>
            <button className="btn ghost auth-submit" onClick={() => switchMode("forgot")}>Forgot password</button>
          </>
        ) : null}

        {!challenge && mode === "signup" ? (
          <>
            <label className="field">
              <span className="label">Firm name</span>
              <input className="input" value={firmName} onChange={(event) => setFirmName(event.target.value)} />
            </label>
            <label className="field">
              <span className="label">Admin name</span>
              <input className="input" value={name} onChange={(event) => setName(event.target.value)} />
            </label>
            <label className="field">
              <span className="label">Admin email</span>
              <input className="input" value={email} onChange={(event) => setEmail(event.target.value)} />
            </label>
            <label className="field">
              <span className="label">Password</span>
              <input className="input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </label>
            <button className="btn primary auth-submit" onClick={createFirm} disabled={busy}>
              <ShieldCheck /> {busy ? "Creating..." : "Create Admin Account"}
            </button>
          </>
        ) : null}

        {!challenge && mode === "invite" ? (
          <>
            <label className="field">
              <span className="label">Invitation token</span>
              <input className="input" value={inviteToken} onChange={(event) => setInviteToken(event.target.value)} />
            </label>
            <label className="field">
              <span className="label">Your name</span>
              <input className="input" value={name} onChange={(event) => setName(event.target.value)} />
            </label>
            <label className="field">
              <span className="label">Password</span>
              <input className="input" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
            </label>
            <button className="btn primary auth-submit" onClick={acceptInvite} disabled={busy}>
              <Users /> {busy ? "Joining..." : "Join Firm"}
            </button>
          </>
        ) : null}

        {!challenge && mode === "forgot" ? (
          <>
            <label className="field">
              <span className="label">Account email</span>
              <input className="input" value={email} onChange={(event) => setEmail(event.target.value)} />
            </label>
            <button className="btn primary auth-submit" onClick={requestReset} disabled={busy}>
              <Mail /> {busy ? "Submitting..." : "Send Reset Link"}
            </button>
            <button className="btn ghost auth-submit" onClick={() => switchMode("login")}>Back to login</button>
          </>
        ) : null}

        {!challenge && mode === "reset" ? (
          <>
            <label className="field">
              <span className="label">Reset token</span>
              <input className="input" value={resetToken} onChange={(event) => setResetToken(event.target.value)} />
            </label>
            <label className="field">
              <span className="label">New password</span>
              <input className="input" type="password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} />
            </label>
            <button className="btn primary auth-submit" onClick={completeReset} disabled={busy}>
              <Lock /> {busy ? "Updating..." : "Update Password"}
            </button>
          </>
        ) : null}

        {challenge ? (
          <>
            <div className="otp-note">
              Code sent to <strong>{challenge.masked_channel}</strong>. It expires in {Math.round(challenge.expires_in_seconds / 60)} minutes.
            </div>
            {challenge.preview_otp || email.includes("vakilyantra.in") ? (
              <div className="demo-otp-helper">
                <span>Demo Code: <strong>{challenge.preview_otp || "123456"}</strong></span>
                <button
                  type="button"
                  className="btn ghost mini-fill-btn"
                  onClick={() => setOtp(challenge.preview_otp || "123456")}
                >
                  Auto Fill
                </button>
              </div>
            ) : null}
            <label className="field">
              <span className="label">One-time password</span>
              <input className="input otp-input" value={otp} maxLength={6} inputMode="numeric" onChange={(event) => setOtp(event.target.value.replace(/\D/g, ""))} />
            </label>
            <button className="btn primary auth-submit" onClick={verifyOtp} disabled={busy}>
              <ShieldCheck /> {busy ? "Verifying..." : "Verify and Enter"}
            </button>
            <button className="btn ghost auth-submit" onClick={() => setChallenge(null)}>Back to login</button>
          </>
        ) : null}

        {notice ? <div className="auth-notice">{notice}</div> : null}
        {error ? <div className="auth-error">{error}</div> : null}
        <div className="auth-footnote">
          Accounts, invitations, password reset and OTP verification are handled by the FastAPI backend.
        </div>
      </section>
    </main>
  );
}

function Dashboard({ authUser, onSelect }: { authUser: AuthUser; onSelect: (id: SectionId) => void }) {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!authUser.accessToken) return;
    apiGet<DashboardResponse>("/workspace/dashboard", authUser.accessToken)
      .then((data) => {
        setDashboard(data);
        setError("");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Dashboard failed to load"));
  }, [authUser.accessToken]);

  const statCards = dashboard
    ? [
        { label: "Matters", value: dashboard.stats.matters, note: "Active firm files", tone: "" },
        { label: "Documents", value: dashboard.stats.documents, note: "Uploaded records", tone: "gold" },
        { label: "Users", value: dashboard.stats.active_users, note: "Active seats", tone: "blue" },
        { label: "Deadlines", value: dashboard.stats.upcoming_deadlines, note: "Next 60 days", tone: "red" }
      ]
    : stats;

  return (
    <>
      <section className="hero">
        <div className="hero-main">
          <div className="eyebrow">Controlled MVP workspace</div>
          <h1>{dashboard?.firm.name ?? "Vakil Yantra"}</h1>
          <p className="lede">
            Real-time firm workspace for matters, documents, user roles, plan status and upcoming legal work.
          </p>
          <div className="actions">
            <button className="btn primary" onClick={() => onSelect("case")}>
              <Upload /> Analyse Case File
            </button>
            <button className="btn ghost" onClick={() => onSelect("drafting")}>
              <FileText /> Open Drafting Studio
            </button>
            <button className="btn ghost" onClick={() => onSelect("limitation")}>
              <CalendarDays /> Check Limitation
            </button>
          </div>
        </div>
        <div className="hero-side">
          <div className="card-title">Account Context</div>
          <div className="card-sub">Database-backed session</div>
          <div className="trust-grid">
            <div className="trust-item">
              <strong>{roleLabel(authUser.role)}</strong>
              <span>{authUser.email}</span>
            </div>
            <div className="trust-item">
              <strong>{dashboard?.firm.plan ?? authUser.plan}</strong>
              <span>Firm plan</span>
            </div>
            <div className="trust-item">
              <strong>{dashboard?.stats.open_tasks ?? 0}</strong>
              <span>Open tasks</span>
            </div>
            <div className="trust-item">
              <strong>{dashboard?.stats.upcoming_deadlines ?? 0}</strong>
              <span>Upcoming deadlines</span>
            </div>
          </div>
        </div>
      </section>
      {error ? <div className="auth-error">{error}</div> : null}
      <section className="stats">
        {statCards.map((stat) => (
          <div className={`stat ${stat.tone}`} key={stat.label}>
            <div className="stat-num">{stat.value}</div>
            <div className="stat-label">{stat.label}</div>
            <div className="stat-note">{stat.note}</div>
          </div>
        ))}
      </section>
      <section className="grid-2">
        <div className="card">
          <div className="card-title">Recent Matters</div>
          <div className="card-sub">Loaded from PostgreSQL</div>
          {(dashboard?.recent_matters ?? []).map((matter) => (
            <div className="matter" key={matter.id}>
              <div className="matter-head">
                <div>
                  <strong>{matter.title}</strong>
                  <div className="stat-note">{matter.court} | {matter.matter_type}</div>
                </div>
                <button className="btn ghost" onClick={() => onSelect("matters")}>Open</button>
              </div>
              <div className="stat-note">{matter.next_action ?? "No next action set"}</div>
            </div>
          ))}
          {dashboard && dashboard.recent_matters.length === 0 ? <p className="stat-note">No matters yet. Create your first matter from Matter Manager.</p> : null}
        </div>
        <div className="card">
          <div className="card-title">Upcoming Deadlines</div>
          <div className="card-sub">Limitation dates and matter tasks</div>
          {(dashboard?.upcoming_deadlines ?? []).map((deadline) => (
            <div className="source" key={deadline.id}>
              <div className="source-icon">
                <AlertTriangle size={18} />
              </div>
              <div>
                <strong>{deadline.label}</strong>
                <p className="stat-note">{deadline.matter_title} | Due {formatDate(deadline.due_date)} | {deadline.source}</p>
              </div>
            </div>
          ))}
          {dashboard && dashboard.upcoming_deadlines.length === 0 ? <p className="stat-note">No deadlines in the next 60 days.</p> : null}
        </div>
        <div className="card">
          <div className="card-title">Recent Documents</div>
          <div className="card-sub">Uploaded to matters</div>
          {(dashboard?.recent_documents ?? []).map((document) => (
            <div className="source" key={document.id}>
              <div className="source-icon"><FileText size={17} /></div>
              <div>
                <strong>{document.filename}</strong>
                <p className="stat-note">{document.content_type} | {document.status}</p>
              </div>
            </div>
          ))}
          {dashboard && dashboard.recent_documents.length === 0 ? <p className="stat-note">No documents uploaded yet.</p> : null}
        </div>
      </section>
    </>
  );
}

function DraftingStudio({ authUser }: { authUser: AuthUser }) {
  const [docType, setDocType] = useState("Bail Application");
  const [court, setCourt] = useState("Gauhati High Court");
  const [client, setClient] = useState("Ajit Deka");
  const [sectionsHint, setSectionsHint] = useState("Section 480 BNSS, Section 103 BNS");
  const [facts, setFacts] = useState(
    "Client is in judicial custody for 14 days. Allegations under Section 103 BNS are purely circumstantial with no eyewitness. Seizure was effected without electronic recording under Section 105 BNSS. Applicant is permanent resident with elderly dependent parents and undertakes to comply with all bail conditions."
  );
  const [generating, setGenerating] = useState(false);
  const [generatedDraft, setGeneratedDraft] = useState<string>("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [warning, setWarning] = useState<string>("");
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  // AI Assistant chat state
  const [assistantQuery, setAssistantQuery] = useState("");
  const [assistantBusy, setAssistantBusy] = useState(false);
  const [assistantMessages, setAssistantMessages] = useState<Array<{ role: "user" | "assistant"; text: string; citations?: Citation[] }>>([
    {
      role: "assistant",
      text: "Legal Assistant online with statutory RAG grounding. Ask statutory questions regarding provisions, provisos, or procedure under Indian Central Acts."
    }
  ]);

  async function handleGenerateDraft() {
    if (!authUser.accessToken) {
      setError("Session expired. Please log in again.");
      return;
    }
    setGenerating(true);
    setError("");
    try {
      const payload = {
        matter_title: `${client} v. State / Respondent`,
        draft_type: docType,
        fact_summary: `${facts}\nCourt: ${court}\nClient: ${client}\nStatutory hints: ${sectionsHint}`,
        jurisdiction: court
      };
      const resp = await apiPost<AiResponse>("/ai/draft", payload, authUser.accessToken);
      setGeneratedDraft(resp.output_text);
      setCitations(resp.citations || []);
      setWarning(resp.verification_warning || "");
    } catch (err: any) {
      setError(err.message || "Draft generation failed.");
    } finally {
      setGenerating(false);
    }
  }

  function copyToClipboard() {
    const textToCopy = generatedDraft || "No draft content to copy.";
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function downloadDraft(format: "txt" | "doc") {
    const content = generatedDraft || "No draft content.";
    const element = document.createElement("a");
    const file = new Blob([content], { type: format === "doc" ? "application/msword" : "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = `${docType.replace(/\s+/g, "_")}_${client.replace(/\s+/g, "_")}.${format}`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  }

  async function handleAskAssistant() {
    if (!assistantQuery.trim() || !authUser.accessToken || assistantBusy) return;
    const q = assistantQuery.trim();
    setAssistantQuery("");
    setAssistantBusy(true);
    setAssistantMessages(prev => [...prev, { role: "user", text: q }]);
    try {
      const resp = await apiPost<AiResponse>(
        "/ai/draft",
        {
          matter_title: "Statutory Legal Inquiry",
          draft_type: "Legal Advice",
          fact_summary: q,
          jurisdiction: "Supreme Court & Central Acts"
        },
        authUser.accessToken
      );
      setAssistantMessages(prev => [
        ...prev,
        { role: "assistant", text: resp.output_text, citations: resp.citations }
      ]);
    } catch (err: any) {
      setAssistantMessages(prev => [
        ...prev,
        { role: "assistant", text: `Error: ${err.message || "Failed to retrieve statutory answer."}` }
      ]);
    } finally {
      setAssistantBusy(false);
    }
  }

  return (
    <section className="grid-2">
      <div className="card">
        <div className="card-title">AI Drafting Studio</div>
        <div className="card-sub">Statutory RAG Grounding & Zero-Hallucination Drafting</div>
        {error ? <div className="notice warn" style={{ marginBottom: 12 }}>{error}</div> : null}
        <div className="form-grid">
          <label className="field">
            <span className="label">Document type</span>
            <select className="select" value={docType} onChange={e => setDocType(e.target.value)}>
              <option>Bail Application</option>
              <option>Legal Notice</option>
              <option>Written Statement</option>
              <option>Writ Petition (Art 226)</option>
              <option>Section 138 NI Act Complaint</option>
              <option>Condonation of Delay Application</option>
              <option>Affidavit</option>
            </select>
          </label>
          <label className="field">
            <span className="label">Court / Forum</span>
            <input className="input" value={court} onChange={e => setCourt(e.target.value)} />
          </label>
          <label className="field">
            <span className="label">Client / Applicant</span>
            <input className="input" value={client} onChange={e => setClient(e.target.value)} />
          </label>
          <label className="field">
            <span className="label">Sections / Statutory Hints</span>
            <input className="input" value={sectionsHint} onChange={e => setSectionsHint(e.target.value)} placeholder="e.g. Section 480 BNSS, Section 138 NI Act" />
          </label>
          <label className="field full">
            <span className="label">Facts, Grounding & Instructions</span>
            <textarea className="textarea" rows={4} value={facts} onChange={e => setFacts(e.target.value)} />
          </label>
        </div>
        <div className="actions" style={{ marginTop: 14 }}>
          <button className="btn primary" onClick={handleGenerateDraft} disabled={generating}>
            <Bot /> {generating ? "Grounding in Central Acts..." : "Generate Grounded Draft (RAG)"}
          </button>
          <button className="btn ghost" onClick={() => downloadDraft("txt")}>
            <Download /> Export TXT
          </button>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Draft Preview</div>
        <div className="card-sub">{generatedDraft ? "Generated with statutory citations" : "Awaiting draft request"}</div>
        <div className="editor" style={{ minHeight: 280, whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
          {generatedDraft || (
            <div>
              <strong>IN THE {court.toUpperCase()}</strong>
              <br /><br />
              <em>Click &quot;Generate Grounded Draft (RAG)&quot; to retrieve verbatim provisions from the Indian Central Acts corpus and compile a structured court draft with verified citations.</em>
            </div>
          )}
        </div>
        <div className="actions" style={{ marginTop: 12 }}>
          <button className="btn ghost" onClick={copyToClipboard}>
            {copied ? <Check /> : <Copy />} {copied ? "Copied!" : "Copy"}
          </button>
          <button className="btn ghost" onClick={() => downloadDraft("doc")}>
            <Download /> DOC
          </button>
          <button className="btn ghost" onClick={() => window.print()}>
            <Printer /> Print
          </button>
        </div>

        {warning ? (
          <div className="warning-box">
            <AlertTriangle style={{ flex: "0 0 20px" }} />
            <div>
              <strong>Statutory Grounding Notice:</strong>
              <div style={{ marginTop: 2 }}>{warning}</div>
            </div>
          </div>
        ) : null}

        {citations.length > 0 ? (
          <div style={{ marginTop: 18 }}>
            <div className="card-title" style={{ fontSize: "1rem" }}>Verified Statutory Citations ({citations.length})</div>
            <div className="card-sub">Exact provisions retrieved from Indian Central Acts</div>
            {citations.map(cit => (
              <div key={cit.citation_id} className="citation-box">
                <div className="citation-header">
                  <div>
                    <strong>{cit.source_title}</strong>
                    {cit.section_number ? <span className="tag" style={{ marginLeft: 8 }}>Sec. {cit.section_number}</span> : null}
                  </div>
                  <button className="btn ghost" style={{ minHeight: 28, padding: "4px 8px", fontSize: "0.75rem" }} onClick={() => window.open(cit.source_url, "_blank")}>
                    <BookOpen style={{ width: 14, height: 14 }} /> India Code
                  </button>
                </div>
                {cit.heading ? <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--green)" }}>{cit.heading}</div> : null}
                <div style={{ fontSize: "0.84rem", color: "var(--muted)", fontStyle: "italic" }}>
                  &ldquo;{cit.quote_excerpt.length > 280 ? `${cit.quote_excerpt.slice(0, 280)}...` : cit.quote_excerpt}&rdquo;
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </div>

      <div className="card" style={{ gridColumn: "1 / -1" }}>
        <div className="card-title">AI Legal Assistant</div>
        <div className="card-sub">Interactive Statutory Query with Verifiable Retrieval</div>
        <div className="chat" style={{ maxHeight: 320, overflowY: "auto", marginBottom: 12 }}>
          {assistantMessages.map((msg, idx) => (
            <div key={idx} className={`bubble ${msg.role === "user" ? "user" : ""}`}>
              <div style={{ whiteSpace: "pre-wrap" }}>{msg.text}</div>
              {msg.citations && msg.citations.length > 0 ? (
                <div style={{ marginTop: 8, display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {msg.citations.map(c => (
                    <a key={c.citation_id} href={c.source_url} target="_blank" rel="noreferrer" className="tag" style={{ textDecoration: "none" }}>
                      {c.source_title} S.{c.section_number || ""}
                    </a>
                  ))}
                </div>
              ) : null}
            </div>
          ))}
          {assistantBusy ? <div className="bubble">Searching Central Acts corpus...</div> : null}
        </div>
        <div className="searchbar">
          <input
            className="input"
            value={assistantQuery}
            onChange={e => setAssistantQuery(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter") handleAskAssistant(); }}
            placeholder="Ask a question on Indian statutes (e.g. Can anticipatory bail be granted for non-bailable offence under BNSS?)..."
          />
          <button className="btn primary" onClick={handleAskAssistant} disabled={assistantBusy}>
            <Send /> Send
          </button>
        </div>
      </div>
    </section>
  );
}

function LegalLibrary({ authUser, onSelect }: { authUser: AuthUser; onSelect?: (id: SectionId) => void }) {
  const [query, setQuery] = useState("");
  const [searchResults, setSearchResults] = useState<LegalSourceItem[]>([]);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState("");

  const curatedActs = [
    { name: "Constitution of India", year: "1950", type: "Constitution", actNumber: "Constituent Assembly", url: "https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Constitution+of+India" },
    { name: "Bharatiya Nagarik Suraksha Sanhita", year: "2023", type: "Procedure", actNumber: "Act 46 of 2023", url: "https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Bharatiya+Nagarik+Suraksha+Sanhita" },
    { name: "Bharatiya Nyaya Sanhita", year: "2023", type: "Criminal", actNumber: "Act 45 of 2023", url: "https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Bharatiya+Nyaya+Sanhita" },
    { name: "Bharatiya Sakshya Adhiniyam", year: "2023", type: "Evidence", actNumber: "Act 47 of 2023", url: "https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Bharatiya+Sakshya+Adhiniyam" },
    { name: "Arbitration and Conciliation Act", year: "1996", type: "Commercial", actNumber: "Act 26 of 1996", url: "https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Arbitration+and+Conciliation+Act" },
    { name: "Negotiable Instruments Act", year: "1881", type: "Commercial", actNumber: "Act 26 of 1881", url: "https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Negotiable+Instruments+Act" },
    { name: "Limitation Act", year: "1963", type: "Civil", actNumber: "Act 36 of 1963", url: "https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Limitation+Act" },
    { name: "Code of Civil Procedure", year: "1908", type: "Procedure", actNumber: "Act 5 of 1908", url: "https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Code+of+Civil+Procedure" },
    { name: "Indian Contract Act", year: "1872", type: "Civil", actNumber: "Act 9 of 1872", url: "https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Indian+Contract+Act" },
    { name: "Insolvency and Bankruptcy Code", year: "2016", type: "Commercial", actNumber: "Act 31 of 2016", url: "https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Insolvency+and+Bankruptcy+Code" },
    { name: "Companies Act", year: "2013", type: "Corporate", actNumber: "Act 18 of 2013", url: "https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Companies+Act" },
    { name: "Consumer Protection Act", year: "2019", type: "Consumer", actNumber: "Act 35 of 2019", url: "https://www.indiacode.nic.in/handle/123456789/1362/simple-search?query=Consumer+Protection+Act" }
  ];

  async function handleSearch(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!query.trim()) {
      setSearched(false);
      return;
    }
    setSearching(true);
    setError("");
    try {
      const resp = await apiGet<LegalSearchResponse>(`/legal-content/search?q=${encodeURIComponent(query)}`, authUser.accessToken);
      setSearchResults(resp.results || []);
      setSearched(true);
    } catch (err: any) {
      setError(err.message || "Search failed");
    } finally {
      setSearching(false);
    }
  }

  return (
    <section>
      <div className="card">
        <div className="card-title">Legal Library & Statutory Corpus</div>
        <div className="card-sub">600+ Indian Central Acts & Verified Grounding Index</div>
        <form onSubmit={handleSearch} className="searchbar">
          <input
            className="input"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search act by title, act number, or year (e.g. BNSS, 46 of 2023, Arbitration, Aadhaar)..."
          />
          <button className="btn primary" type="submit" disabled={searching}>
            <Search /> {searching ? "Searching 600 Acts..." : "Search Library"}
          </button>
        </form>
        {error ? <div className="notice warn">{error}</div> : null}

        {searched ? (
          <div>
            <div style={{ marginBottom: 12, fontWeight: 700, color: "var(--muted)" }}>
              Found {searchResults.length} Act{searchResults.length === 1 ? "" : "s"} matching &ldquo;{query}&rdquo;
            </div>
            {searchResults.length === 0 ? (
              <div style={{ padding: 20, textAlign: "center", color: "var(--muted)" }}>
                No Central Acts found matching this query in the catalog.
              </div>
            ) : (
              <div className="grid-3">
                {searchResults.map(act => (
                  <div className="mini-card" key={act.id}>
                    <div>
                      <strong>{act.title}</strong>
                      <div style={{ marginTop: 4, fontSize: "0.82rem", color: "var(--muted)" }}>
                        {act.act_number ? `Act No. ${act.act_number} · ` : ""}{act.year} · {act.jurisdiction}
                      </div>
                    </div>
                    <div className="actions" style={{ marginTop: 12 }}>
                      <button className="btn ghost" onClick={() => window.open(act.public_url, "_blank")}>
                        <BookOpen /> India Code
                      </button>
                      {onSelect ? (
                        <button className="btn ghost" onClick={() => onSelect("drafting")}>
                          <ChevronRight /> Cite in Draft
                        </button>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: 12, fontWeight: 700, color: "var(--muted)" }}>
              Landmark Practice Acts (Search above to explore all 600 Central Acts)
            </div>
            <div className="grid-3">
              {curatedActs.map(act => (
                <div className="mini-card" key={act.name}>
                  <div>
                    <strong>{act.name}</strong>
                    <div style={{ marginTop: 4, fontSize: "0.82rem", color: "var(--muted)" }}>
                      {act.year} · {act.type} · {act.actNumber}
                    </div>
                  </div>
                  <div className="actions" style={{ marginTop: 12 }}>
                    <button className="btn ghost" onClick={() => window.open(act.url, "_blank")}>
                      <BookOpen /> India Code
                    </button>
                    {onSelect ? (
                      <button className="btn ghost" onClick={() => onSelect("drafting")}>
                        <ChevronRight /> Cite
                      </button>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function CaseIntelligence({ authUser }: { authUser: AuthUser }) {
  const [advocateRole, setAdvocateRole] = useState("Defence Counsel");
  const [matterTitle, setMatterTitle] = useState("State v. Ajit Deka");
  const [allegations, setAllegations] = useState(
    "Allegation of non-bailable offence under Section 103 BNS. Panchnama seizure made without mandatory electronic videography mandated under Section 105 BNSS. Accused detained beyond 24 hours prior to production before magistrate."
  );
  const [reliefSought, setReliefSought] = useState("Regular Bail under Section 480 BNSS / Anticipatory Bail under Section 482 BNSS");
  const [caseNotes, setCaseNotes] = useState("Applicant is sole earner with dependent family. Medical condition requires continuous clinical monitoring. Zero prior criminal record.");
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AiResponse | null>(null);
  const [error, setError] = useState("");

  async function handleAnalyse() {
    if (!authUser.accessToken) {
      setError("Session expired. Please log in.");
      return;
    }
    setAnalyzing(true);
    setError("");
    try {
      const payload = {
        matter_title: matterTitle,
        case_notes: `Advocate Role: ${advocateRole}\n${caseNotes}`,
        allegations,
        relief_sought: reliefSought
      };
      const resp = await apiPost<AiResponse>("/ai/case-analysis", payload, authUser.accessToken);
      setAnalysisResult(resp);
    } catch (err: any) {
      setError(err.message || "Case analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <section className="grid-2">
      <div className="card">
        <div className="card-title">Case Intelligence</div>
        <div className="card-sub">Role-Aware Statutory Evidence & Strategy Analysis</div>
        {error ? <div className="notice warn" style={{ marginBottom: 12 }}>{error}</div> : null}
        <div className="form-grid">
          <label className="field">
            <span className="label">Advocate role</span>
            <select className="select" value={advocateRole} onChange={e => setAdvocateRole(e.target.value)}>
              <option>Defence Counsel</option>
              <option>Petitioner Counsel</option>
              <option>Respondent Counsel</option>
              <option>Prosecution</option>
            </select>
          </label>
          <label className="field">
            <span className="label">Matter Title</span>
            <input className="input" value={matterTitle} onChange={e => setMatterTitle(e.target.value)} />
          </label>
          <label className="field full">
            <span className="label">Allegations / Charge Sheet Grounds</span>
            <textarea className="textarea" rows={3} value={allegations} onChange={e => setAllegations(e.target.value)} />
          </label>
          <label className="field full">
            <span className="label">Relief Sought</span>
            <input className="input" value={reliefSought} onChange={e => setReliefSought(e.target.value)} />
          </label>
          <label className="field full">
            <span className="label">Case Notes & Evidentiary Defenses</span>
            <textarea className="textarea" rows={3} value={caseNotes} onChange={e => setCaseNotes(e.target.value)} />
          </label>
        </div>
        <div className="actions" style={{ marginTop: 14 }}>
          <button className="btn primary" onClick={handleAnalyse} disabled={analyzing}>
            <Bot /> {analyzing ? "Synthesizing Statutory Analysis..." : "Analyse Case with RAG Grounding"}
          </button>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Analysis Report</div>
        <div className="card-sub">Grounding in Statutory Ingredients & Precedents</div>
        {analysisResult ? (
          <div>
            <div className="editor" style={{ minHeight: 260, whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
              {analysisResult.output_text}
            </div>

            {analysisResult.verification_warning ? (
              <div className="warning-box">
                <AlertTriangle style={{ flex: "0 0 20px" }} />
                <div>
                  <strong>Mandatory Verification Notice:</strong>
                  <div style={{ marginTop: 2 }}>{analysisResult.verification_warning}</div>
                </div>
              </div>
            ) : null}

            {analysisResult.citations && analysisResult.citations.length > 0 ? (
              <div style={{ marginTop: 18 }}>
                <div className="card-title" style={{ fontSize: "1rem" }}>Verified Statutory Anchors ({analysisResult.citations.length})</div>
                {analysisResult.citations.map(cit => (
                  <div key={cit.citation_id} className="citation-box">
                    <div className="citation-header">
                      <div>
                        <strong>{cit.source_title}</strong>
                        {cit.section_number ? <span className="tag" style={{ marginLeft: 8 }}>Sec. {cit.section_number}</span> : null}
                      </div>
                      <button className="btn ghost" style={{ minHeight: 28, padding: "4px 8px", fontSize: "0.75rem" }} onClick={() => window.open(cit.source_url, "_blank")}>
                        <BookOpen style={{ width: 14, height: 14 }} /> India Code
                      </button>
                    </div>
                    {cit.heading ? <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--green)" }}>{cit.heading}</div> : null}
                    <div style={{ fontSize: "0.84rem", color: "var(--muted)", fontStyle: "italic" }}>
                      &ldquo;{cit.quote_excerpt.length > 250 ? `${cit.quote_excerpt.slice(0, 250)}...` : cit.quote_excerpt}&rdquo;
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        ) : (
          <div>
            {["Action steps", "Argument preparation", "Procedural guidance"].map((title, index) => (
              <div className="source" key={title}>
                <div className="source-icon">{index + 1}</div>
                <div>
                  <strong>{title}</strong>
                  <p className="stat-note">
                    Provide facts, allegations, and relief sought on the left, then click &ldquo;Analyse Case with RAG Grounding&rdquo; to retrieve statutory ingredients, provisos, and legal grounds.
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function Matters({ authUser }: { authUser: AuthUser }) {
  const [matterList, setMatterList] = useState<MatterRecord[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [detail, setDetail] = useState<MatterDetail | null>(null);
  const [documents, setDocuments] = useState<DocumentRecord[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [matterForm, setMatterForm] = useState({
    title: "",
    court: "",
    matter_type: "",
    client_name: "",
    next_action: "",
    limitation_date: ""
  });
  const [noteBody, setNoteBody] = useState("");
  const [taskTitle, setTaskTitle] = useState("");
  const [taskDueDate, setTaskDueDate] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  useEffect(() => {
    loadMatters();
    loadDocuments();
  }, [authUser.accessToken]);

  useEffect(() => {
    if (selectedId) loadMatterDetail(selectedId);
  }, [selectedId]);

  async function loadMatters() {
    if (!authUser.accessToken) return;
    try {
      const data = await apiGet<MatterRecord[]>("/matters", authUser.accessToken);
      setMatterList(data);
      if (!selectedId && data[0]) setSelectedId(data[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load matters");
    }
  }

  async function loadDocuments() {
    if (!authUser.accessToken) return;
    try {
      setDocuments(await apiGet<DocumentRecord[]>("/documents", authUser.accessToken));
    } catch {
      setDocuments([]);
    }
  }

  async function loadMatterDetail(matterId: string) {
    if (!authUser.accessToken) return;
    try {
      const data = await apiGet<MatterDetail>(`/matters/${matterId}`, authUser.accessToken);
      setDetail(data);
      setMatterForm({
        title: data.title,
        court: data.court,
        matter_type: data.matter_type,
        client_name: data.client_name,
        next_action: data.next_action ?? "",
        limitation_date: data.limitation_date ?? ""
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load matter");
    }
  }

  async function createMatter() {
    if (!authUser.accessToken) return;
    try {
      const created = await apiPost<MatterRecord>("/matters", {
        ...matterForm,
        limitation_date: matterForm.limitation_date || null
      }, authUser.accessToken);
      setMessage("Matter created");
      setError("");
      setSelectedId(created.id);
      await loadMatters();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Matter creation failed");
    }
  }

  async function saveMatter() {
    if (!authUser.accessToken || !selectedId) return;
    try {
      await apiPatch<MatterRecord>(`/matters/${selectedId}`, {
        ...matterForm,
        limitation_date: matterForm.limitation_date || null
      }, authUser.accessToken);
      setMessage("Matter updated");
      setError("");
      await loadMatters();
      await loadMatterDetail(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Matter update failed");
    }
  }

  async function addMatterNote() {
    if (!authUser.accessToken || !selectedId) return;
    try {
      await apiPost(`/matters/${selectedId}/notes`, { body: noteBody }, authUser.accessToken);
      setNoteBody("");
      setMessage("Note added");
      await loadMatterDetail(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Note failed");
    }
  }

  async function addMatterTask() {
    if (!authUser.accessToken || !selectedId) return;
    try {
      await apiPost(`/matters/${selectedId}/tasks`, { title: taskTitle, due_date: taskDueDate || null }, authUser.accessToken);
      setTaskTitle("");
      setTaskDueDate("");
      setMessage("Task added");
      await loadMatterDetail(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Task failed");
    }
  }

  async function markTask(task: MatterTask, statusValue: string) {
    if (!authUser.accessToken || !selectedId) return;
    await apiPatch(`/matters/${selectedId}/tasks/${task.id}`, { status: statusValue }, authUser.accessToken);
    await loadMatterDetail(selectedId);
  }

  async function attachDocument() {
    if (!authUser.accessToken || !selectedId || !uploadFile) return;
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("matter_id", selectedId);
      await apiUpload<DocumentRecord>("/documents/upload", formData, authUser.accessToken);
      setUploadFile(null);
      setMessage("Document uploaded to matter");
      await loadDocuments();
      await loadMatterDetail(selectedId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Document upload failed");
    }
  }

  const matterDocuments = documents.filter((document) => document.matter_id === selectedId);

  return (
    <section className="grid-2">
      <div className="card">
        <div className="card-title">Matter Manager</div>
        <div className="card-sub">Create, view and update real matters</div>
        {matterList.map((matter) => (
          <div className={`matter ${selectedId === matter.id ? "selected" : ""}`} key={matter.id}>
            <div className="matter-head">
              <div>
                <strong>{matter.title}</strong>
                <div className="stat-note">{matter.court} | {matter.client_name}</div>
              </div>
              <button className="btn ghost" onClick={() => setSelectedId(matter.id)}>Open</button>
            </div>
            <div className="tags">
              <span className="tag">{matter.matter_type}</span>
              {matter.limitation_date ? <span className="tag warn">Limitation {formatDate(matter.limitation_date)}</span> : null}
            </div>
            <div className="stat-note">{matter.next_action ?? "No next action set"}</div>
          </div>
        ))}
        {matterList.length === 0 ? <p className="stat-note">No matters yet.</p> : null}
      </div>

      <div className="card">
        <div className="card-title">{detail ? "Matter Detail" : "Create Matter"}</div>
        <div className="card-sub">Matter facts and deadlines</div>
        <div className="form-grid">
          <label className="field">
            <span className="label">Title</span>
            <input className="input" value={matterForm.title} onChange={(event) => setMatterForm({ ...matterForm, title: event.target.value })} />
          </label>
          <label className="field">
            <span className="label">Court</span>
            <input className="input" value={matterForm.court} onChange={(event) => setMatterForm({ ...matterForm, court: event.target.value })} />
          </label>
          <label className="field">
            <span className="label">Matter type</span>
            <input className="input" value={matterForm.matter_type} onChange={(event) => setMatterForm({ ...matterForm, matter_type: event.target.value })} />
          </label>
          <label className="field">
            <span className="label">Client</span>
            <input className="input" value={matterForm.client_name} onChange={(event) => setMatterForm({ ...matterForm, client_name: event.target.value })} />
          </label>
          <label className="field">
            <span className="label">Limitation date</span>
            <input className="input" type="date" value={matterForm.limitation_date} onChange={(event) => setMatterForm({ ...matterForm, limitation_date: event.target.value })} />
          </label>
          <label className="field full">
            <span className="label">Next action</span>
            <textarea className="textarea" value={matterForm.next_action} onChange={(event) => setMatterForm({ ...matterForm, next_action: event.target.value })} />
          </label>
        </div>
        <div className="actions" style={{ marginTop: 12 }}>
          <button className="btn primary" onClick={detail ? saveMatter : createMatter}><FileText /> {detail ? "Save Matter" : "Create Matter"}</button>
          <button className="btn ghost" onClick={() => {
            setSelectedId("");
            setDetail(null);
            setMatterForm({ title: "", court: "", matter_type: "", client_name: "", next_action: "", limitation_date: "" });
          }}>New Matter</button>
        </div>
        {message ? <div className="auth-notice">{message}</div> : null}
        {error ? <div className="auth-error">{error}</div> : null}
      </div>

      {detail ? (
        <>
          <div className="card">
            <div className="card-title">Notes</div>
            <div className="card-sub">Matter notes and history</div>
            <textarea className="textarea" value={noteBody} onChange={(event) => setNoteBody(event.target.value)} placeholder="Add matter note" />
            <button className="btn primary auth-submit" onClick={addMatterNote}><MessageSquare /> Add Note</button>
            {detail.notes.map((note) => (
              <div className="source" key={note.id}>
                <div className="source-icon"><MessageSquare size={17} /></div>
                <div>
                  <strong>{formatDate(note.created_at)}</strong>
                  <p className="stat-note">{note.body}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="card-title">Tasks & Deadlines</div>
            <div className="card-sub">Action items tied to this matter</div>
            <div className="form-grid">
              <label className="field">
                <span className="label">Task</span>
                <input className="input" value={taskTitle} onChange={(event) => setTaskTitle(event.target.value)} />
              </label>
              <label className="field">
                <span className="label">Due date</span>
                <input className="input" type="date" value={taskDueDate} onChange={(event) => setTaskDueDate(event.target.value)} />
              </label>
            </div>
            <button className="btn primary auth-submit" onClick={addMatterTask}><CalendarDays /> Add Task</button>
            {detail.tasks.map((task) => (
              <div className="source" key={task.id}>
                <div className="source-icon"><Check size={17} /></div>
                <div>
                  <strong>{task.title}</strong>
                  <p className="stat-note">Due {formatDate(task.due_date)} | {task.status}</p>
                </div>
                <button className="btn ghost" onClick={() => markTask(task, task.status === "done" ? "open" : "done")}>
                  {task.status === "done" ? "Reopen" : "Done"}
                </button>
              </div>
            ))}
          </div>

          <div className="card">
            <div className="card-title">Matter Documents</div>
            <div className="card-sub">Upload document record to selected matter</div>
            <input className="input" type="file" onChange={(event) => setUploadFile(event.target.files?.[0] ?? null)} />
            <button className="btn primary auth-submit" onClick={attachDocument} disabled={!uploadFile}><Upload /> Attach Document</button>
            {matterDocuments.map((document) => (
              <div className="source" key={document.id}>
                <div className="source-icon"><FileText size={17} /></div>
                <div>
                  <strong>{document.filename}</strong>
                  <p className="stat-note">{document.content_type} | {document.status}</p>
                </div>
                {document.status === "ready" ? <button className="btn ghost" onClick={() => openDocument(document.id, authUser.accessToken)}>Open</button> : null}
              </div>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}

function ProceduralGuide() {
  return (
    <section className="grid-2">
      <div className="card">
        <div className="card-title">Procedural Guide</div>
        <div className="card-sub">Rules-first checklists with AI fallback</div>
        <div className="form-grid">
          <label className="field">
            <span className="label">Filing type</span>
            <select className="select">
              <option>Bail Application</option>
              <option>Cheque Bounce Complaint</option>
              <option>Civil Injunction</option>
            </select>
          </label>
          <label className="field">
            <span className="label">Court</span>
            <select className="select">
              <option>Gauhati High Court</option>
              <option>District Court</option>
              <option>Consumer Commission</option>
            </select>
          </label>
        </div>
        <button className="btn primary">
          <ListIcon /> Get Checklist
        </button>
      </div>
      <ChecklistCard />
    </section>
  );
}

function ListIcon() {
  return <Check size={17} />;
}

function ChecklistCard() {
  return (
    <div className="card">
      <div className="card-title">Checklist</div>
      <div className="card-sub">Saveable to matter workspace</div>
      <div className="checklist">
        {checklist.map((item) => (
          <div className="check-item" key={item}>
            <div className="check-box">
              <Check size={17} />
            </div>
            <div>{item}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LimitationCalculator() {
  return (
    <section className="grid-2">
      <div className="card">
        <div className="card-title">Limitation Calculator</div>
        <div className="card-sub">Deterministic legal date engine</div>
        <div className="form-grid">
          <label className="field">
            <span className="label">Cause of action</span>
            <select className="select">
              <option>Money recovery</option>
              <option>Contract breach</option>
              <option>NI Act S.138 complaint</option>
              <option>Appeal</option>
            </select>
          </label>
          <label className="field">
            <span className="label">Trigger date</span>
            <input className="input" type="date" defaultValue="2026-07-01" />
          </label>
          <label className="field full">
            <span className="label">Exclusions</span>
            <textarea className="textarea" placeholder="Add Section 12/14 exclusions or court time if applicable" />
          </label>
        </div>
        <button className="btn primary">
          <CalendarDays /> Calculate Limitation
        </button>
      </div>
      <div className="card">
        <div className="card-title">Result</div>
        <div className="card-sub">Rule version VY-LIM-2026.07</div>
        <table className="table">
          <tbody>
            <tr>
              <th>Rule</th>
              <td>Article 113, Limitation Act 1963</td>
            </tr>
            <tr>
              <th>Deadline</th>
              <td>1 July 2029</td>
            </tr>
            <tr>
              <th>Warning</th>
              <td>AI may explain this result but cannot generate the deadline.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}

function OpposingCounsel() {
  return (
    <SimpleTool
      title="Opposing Counsel Simulator"
      sub="Dedicated adversarial prompt, not general chat"
      input="Paste planned submission or argument"
      output="Likely objections, weak points, cross-examination angles and counter strategy suggestions."
    />
  );
}

function Amendments() {
  return (
    <section className="card">
      <div className="card-title">Amendments Feed</div>
      <div className="card-sub">Adapter-based source ingestion with editorial review</div>
      {["BNS procedural correction draft flagged for review", "State notification imported into queue", "Limitation rule source updated"].map(
        (item) => (
          <div className="source" key={item}>
            <div className="source-icon">
              <Bell size={17} />
            </div>
            <div>
              <strong>{item}</strong>
              <p className="stat-note">Requires provenance, checksum and reviewer sign-off before production use.</p>
            </div>
          </div>
        )
      )}
    </section>
  );
}

function Judgments() {
  return (
    <section className="card">
      <div className="card-title">Recent Judgments</div>
      <div className="card-sub">Supreme Court and High Court research surface</div>
      <div className="searchbar">
        <input className="input" placeholder="Search citation, party name, legal issue" />
        <button className="btn primary">
          <Search /> Search
        </button>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Court</th>
            <th>Matter</th>
            <th>Use</th>
          </tr>
        </thead>
        <tbody>
          {["Supreme Court", "Gauhati High Court", "Delhi High Court"].map((court) => (
            <tr key={court}>
              <td>{court}</td>
              <td>Curated source pending editorial validation</td>
              <td>
                <button className="btn ghost">
                  <Gavel /> Cite
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function ECourts() {
  return (
    <SimpleTool
      title="eCourts Orders"
      sub="Authorised integration or user-assisted tracking"
      input="CNR number, case number or party name"
      output="Live status should be cached, rate-limited and clearly marked by source freshness."
    />
  );
}

function Translate() {
  return (
    <SimpleTool
      title="Translate & Transcribe"
      sub="Legal fidelity, low-confidence flags and bilingual review"
      input="Paste English, Hindi, Assamese or Bengali text"
      output="Meaning-preserving translation with manual review flags. Full formatting preservation is post-MVP."
    />
  );
}

function Workspace({ authUser }: { authUser: AuthUser }) {
  const [overview, setOverview] = useState<WorkspaceOverview | null>(null);
  const [selectedFolderId, setSelectedFolderId] = useState("");
  const [selectedNote, setSelectedNote] = useState<WorkspaceNoteRecord | null>(null);
  const [folderName, setFolderName] = useState("");
  const [noteTitle, setNoteTitle] = useState("");
  const [noteBody, setNoteBody] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [shareType, setShareType] = useState("folder");
  const [shareResourceId, setShareResourceId] = useState("");
  const [shareUserId, setShareUserId] = useState("");
  const [sharePermission, setSharePermission] = useState("view");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [workspaceStep, setWorkspaceStep] = useState<"organize" | "share" | "shared" | "gallery">("organize");

  useEffect(() => {
    loadWorkspace();
  }, [authUser.accessToken]);

  useEffect(() => {
    const firstFolder = overview?.folders[0];
    if (!selectedFolderId && firstFolder) setSelectedFolderId(firstFolder.id);
  }, [overview, selectedFolderId]);

  async function loadWorkspace() {
    if (!authUser.accessToken) return;
    try {
      const data = await apiGet<WorkspaceOverview>("/workspace/overview", authUser.accessToken);
      setOverview(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Workspace failed to load");
    }
  }

  async function createFolder() {
    if (!authUser.accessToken) return;
    try {
      const folder = await apiPost<WorkspaceFolderRecord>("/workspace/folders", { name: folderName }, authUser.accessToken);
      setFolderName("");
      setSelectedFolderId(folder.id);
      setMessage("Folder created");
      await loadWorkspace();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Folder creation failed");
    }
  }

  async function renameFolder(folder: WorkspaceFolderRecord) {
    if (!authUser.accessToken) return;
    const nextName = window.prompt("Folder name", folder.name);
    if (!nextName) return;
    try {
      await apiPatch(`/workspace/folders/${folder.id}`, { name: nextName }, authUser.accessToken);
      setMessage("Folder renamed");
      await loadWorkspace();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Folder rename failed");
    }
  }

  async function saveNote() {
    if (!authUser.accessToken) return;
    try {
      if (selectedNote) {
        const updated = await apiPatch<WorkspaceNoteRecord>(
          `/workspace/notes/${selectedNote.id}`,
          { title: noteTitle, body: noteBody, folder_id: selectedFolderId || null },
          authUser.accessToken
        );
        setSelectedNote(updated);
        setMessage("Note saved");
      } else {
        const created = await apiPost<WorkspaceNoteRecord>(
          "/workspace/notes",
          { title: noteTitle, body: noteBody, folder_id: selectedFolderId || null },
          authUser.accessToken
        );
        setSelectedNote(created);
        setMessage("Note created");
      }
      await loadWorkspace();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Note save failed");
    }
  }

  function openNote(note: WorkspaceNoteRecord) {
    setSelectedNote(note);
    setNoteTitle(note.title);
    setNoteBody(note.body);
    setSelectedFolderId(note.folder_id ?? selectedFolderId);
  }

  function newNote() {
    setSelectedNote(null);
    setNoteTitle("");
    setNoteBody("");
  }

  function newNoteInFolder(folderId: string) {
    setSelectedFolderId(folderId);
    setSelectedNote(null);
    setNoteTitle("");
    setNoteBody("");
    setWorkspaceStep("organize");
  }

  function prepareFolderUpload(folderId: string) {
    setSelectedFolderId(folderId);
    setWorkspaceStep("organize");
    setMessage("Choose a file in Shared Documents to attach it to this folder.");
  }

  async function attachDocumentToFolder() {
    if (!authUser.accessToken || !uploadFile) return;
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      if (selectedFolderId) formData.append("folder_id", selectedFolderId);
      await apiUpload<DocumentRecord>("/documents/upload", formData, authUser.accessToken);
      setUploadFile(null);
      setMessage("Document uploaded to workspace");
      await loadWorkspace();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Document upload failed");
    }
  }

  async function shareWorkspaceResource() {
    if (!authUser.accessToken || !shareResourceId || !shareUserId) return;
    try {
      await apiPost("/workspace/shares", {
        resource_type: shareType,
        resource_id: shareResourceId,
        grantee_user_id: shareUserId,
        permission: sharePermission
      }, authUser.accessToken);
      setMessage("Workspace item shared");
      await loadWorkspace();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Share failed");
    }
  }

  const folders = overview?.folders ?? [];
  const notes = overview?.notes.filter((note) => !selectedFolderId || note.folder_id === selectedFolderId) ?? [];
  const documents = overview?.documents.filter((document) => !selectedFolderId || document.folder_id === selectedFolderId) ?? [];
  const shareOptions =
    shareType === "folder"
      ? folders.map((folder) => ({ id: folder.id, name: folder.name }))
      : shareType === "note"
        ? (overview?.notes ?? []).map((note) => ({ id: note.id, name: note.title }))
        : (overview?.documents ?? []).map((document) => ({ id: document.id, name: document.filename }));
  const canEditSelectedNote = !selectedNote || ["owner", "edit"].includes(selectedNote.permission);
  const sharedFolders = folders.filter((folder) => folder.permission !== "owner");
  const sharedDocuments = (overview?.documents ?? []).filter((document) => document.permission !== "owner");
  const galleryDocuments = overview?.documents ?? [];

  return (
    <section>
      <div className="card">
        <div className="card-title">Workspace</div>
        <div className="card-sub">Folder, share, view shared files, gallery and staff</div>
        <div className="workspace-steps">
          <button className={`auth-tab ${workspaceStep === "organize" ? "active" : ""}`} onClick={() => setWorkspaceStep("organize")}>1. Folder</button>
          <button className={`auth-tab ${workspaceStep === "share" ? "active" : ""}`} onClick={() => setWorkspaceStep("share")}>2. Sharing</button>
          <button className={`auth-tab ${workspaceStep === "shared" ? "active" : ""}`} onClick={() => setWorkspaceStep("shared")}>3. Shared</button>
          <button className={`auth-tab ${workspaceStep === "gallery" ? "active" : ""}`} onClick={() => setWorkspaceStep("gallery")}>4. Gallery</button>
        </div>
      </div>

      {workspaceStep === "organize" ? (
        <section className="grid-2">
          <div className="card">
        <div className="card-title">Folders</div>
        <div className="card-sub">Create a folder, then add documents or notes</div>
        <div className="searchbar">
          <input className="input" value={folderName} onChange={(event) => setFolderName(event.target.value)} placeholder="New folder name" />
          <button className="btn primary" onClick={createFolder}><Archive /> Create</button>
        </div>
        {folders.map((folder) => (
          <div className={`matter ${selectedFolderId === folder.id ? "selected" : ""}`} key={folder.id}>
            <div className="matter-head">
              <div>
                <strong>{folder.name}</strong>
                <div className="stat-note">{folder.notes_count} notes | {folder.documents_count} documents | {folder.permission}</div>
              </div>
              <div className="actions">
                <button className="btn ghost" onClick={() => setSelectedFolderId(folder.id)}>Open</button>
                <button className="btn ghost icon-action" title="Add document" onClick={() => prepareFolderUpload(folder.id)}><Plus /> <FileText /></button>
                <button className="btn ghost icon-action" title="Add note" onClick={() => newNoteInFolder(folder.id)}><Plus /> <MessageSquare /></button>
                {["owner", "edit"].includes(folder.permission) ? <button className="btn ghost" onClick={() => renameFolder(folder)}>Rename</button> : null}
              </div>
            </div>
          </div>
        ))}
        {folders.length === 0 ? <p className="stat-note">Create a folder to start organizing workspace notes and documents.</p> : null}
      </div>

      <div className="card">
        <div className="card-title">Notes</div>
        <div className="card-sub">Create and edit notes inside the selected folder</div>
        <div className="form-grid">
          <label className="field">
            <span className="label">Folder</span>
            <select className="select" value={selectedFolderId} onChange={(event) => setSelectedFolderId(event.target.value)}>
              <option value="">No folder</option>
              {folders.map((folder) => <option value={folder.id} key={folder.id}>{folder.name}</option>)}
            </select>
          </label>
          <label className="field">
            <span className="label">Title</span>
            <input className="input" value={noteTitle} onChange={(event) => setNoteTitle(event.target.value)} />
          </label>
          <label className="field full">
            <span className="label">Body</span>
            <textarea className="textarea" value={noteBody} onChange={(event) => setNoteBody(event.target.value)} />
          </label>
        </div>
        <div className="actions" style={{ marginTop: 12 }}>
          <button className="btn primary" onClick={saveNote} disabled={!canEditSelectedNote}><MessageSquare /> {selectedNote ? "Save Note" : "Create Note"}</button>
          <button className="btn ghost" onClick={newNote}>New Note</button>
        </div>
        {notes.map((note) => (
          <div className="source" key={note.id}>
            <div className="source-icon"><MessageSquare size={17} /></div>
            <div>
              <strong>{note.title}</strong>
              <p className="stat-note">{note.permission} | Updated {formatDate(note.updated_at)}</p>
            </div>
            <button className="btn ghost" onClick={() => openNote(note)}>Open</button>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-title">Shared Documents</div>
        <div className="card-sub">Upload files into the selected folder</div>
        <input className="input" type="file" onChange={(event) => setUploadFile(event.target.files?.[0] ?? null)} />
        <button className="btn primary auth-submit" onClick={attachDocumentToFolder} disabled={!uploadFile}><Upload /> Add Document</button>
        {documents.map((document) => (
          <div className="source" key={document.id}>
            <div className="source-icon"><FileText size={17} /></div>
            <div>
              <strong>{document.filename}</strong>
              <p className="stat-note">{document.content_type} | {document.status} | {document.permission}</p>
            </div>
            {document.status === "ready" ? <button className="btn ghost" onClick={() => openDocument(document.id, authUser.accessToken)}>Open</button> : null}
          </div>
        ))}
      </div>
        </section>
      ) : null}

      {workspaceStep === "share" ? (
      <div className="card">
        <div className="card-title">Sharing</div>
        <div className="card-sub">Share and reshare with members in this workspace</div>
        <div className="form-grid">
          <label className="field">
            <span className="label">Type</span>
            <select className="select" value={shareType} onChange={(event) => { setShareType(event.target.value); setShareResourceId(""); }}>
              <option value="folder">Folder</option>
              <option value="note">Note</option>
              <option value="document">Document</option>
            </select>
          </label>
          <label className="field">
            <span className="label">Item</span>
            <select className="select" value={shareResourceId} onChange={(event) => setShareResourceId(event.target.value)}>
              <option value="">Select item</option>
              {shareOptions.map((option) => <option value={option.id} key={option.id}>{option.name}</option>)}
            </select>
          </label>
          <label className="field">
            <span className="label">User</span>
            <select className="select" value={shareUserId} onChange={(event) => setShareUserId(event.target.value)}>
              <option value="">Select user</option>
              {(overview?.users ?? []).filter((user) => user.user_id !== authUser.user_id).map((user) => (
                <option value={user.user_id} key={user.user_id}>{user.name} | {roleLabel(user.role)}</option>
              ))}
            </select>
          </label>
          <label className="field">
            <span className="label">Permission</span>
            <select className="select" value={sharePermission} onChange={(event) => setSharePermission(event.target.value)}>
              <option value="view">View</option>
              <option value="edit">Edit</option>
            </select>
          </label>
        </div>
        <button className="btn primary auth-submit" onClick={shareWorkspaceResource}><Users /> Share</button>
        {(overview?.shares ?? []).map((share) => (
          <div className="source" key={share.id}>
            <div className="source-icon"><Lock size={17} /></div>
            <div>
              <strong>{share.resource_name}</strong>
              <p className="stat-note">{share.grantee_name} | {share.permission} | {share.resource_type}</p>
            </div>
          </div>
        ))}
      </div>
      ) : null}

      {workspaceStep === "shared" ? (
        <section className="grid-2">
          <div className="card">
            <div className="card-title">Shared Folders</div>
            <div className="card-sub">Folders shared with you</div>
            {sharedFolders.map((folder) => (
              <div className="source" key={folder.id}>
                <div className="source-icon"><Archive size={17} /></div>
                <div>
                  <strong>{folder.name}</strong>
                  <p className="stat-note">{folder.permission} | {folder.notes_count} notes | {folder.documents_count} documents</p>
                </div>
                <button className="btn ghost" onClick={() => { setSelectedFolderId(folder.id); setWorkspaceStep("organize"); }}>Open</button>
              </div>
            ))}
            {sharedFolders.length === 0 ? <p className="stat-note">No folders are shared with you yet.</p> : null}
          </div>
          <div className="card">
            <div className="card-title">Shared Documents</div>
            <div className="card-sub">Documents shared directly or through folders</div>
            {sharedDocuments.map((document) => (
              <div className="source" key={document.id}>
                <div className="source-icon"><FileText size={17} /></div>
                <div>
                  <strong>{document.filename}</strong>
                  <p className="stat-note">{document.permission} | {document.status}</p>
                </div>
                {document.status === "ready" ? <button className="btn ghost" onClick={() => openDocument(document.id, authUser.accessToken)}>Open</button> : null}
              </div>
            ))}
            {sharedDocuments.length === 0 ? <p className="stat-note">No documents are shared with you yet.</p> : null}
          </div>
        </section>
      ) : null}

      {workspaceStep === "gallery" ? (
        <section className="grid-2">
          <div className="card">
            <div className="card-title">Gallery</div>
            <div className="card-sub">All visible workspace documents</div>
            <div className="grid-3">
              {galleryDocuments.map((document) => (
                <div className="mini-card" key={document.id}>
                  <strong>{document.filename}</strong>
                  <span>{document.content_type} | {document.permission}</span>
                  {document.status === "ready" ? <button className="btn ghost auth-submit" onClick={() => openDocument(document.id, authUser.accessToken)}>Open</button> : null}
                </div>
              ))}
            </div>
            {galleryDocuments.length === 0 ? <p className="stat-note">No workspace documents yet.</p> : null}
          </div>
          <div className="card">
            <div className="card-title">My Staff</div>
            <div className="card-sub">Members available for workspace sharing</div>
            {(overview?.users ?? []).map((user) => (
              <div className="source" key={user.user_id}>
                <div className="source-icon"><Users size={17} /></div>
                <div>
                  <strong>{user.name}</strong>
                  <p className="stat-note">{user.email} | {roleLabel(user.role)}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      ) : null}
      {message ? <div className="auth-notice">{message}</div> : null}
      {error ? <div className="auth-error">{error}</div> : null}
    </section>
  );
}

function SettingsPanel({ authUser }: { authUser: AuthUser }) {
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("advocate");
  const [inviteMessage, setInviteMessage] = useState("");
  const [inviteError, setInviteError] = useState("");
  const [inviteBusy, setInviteBusy] = useState(false);
  const [firmUsers, setFirmUsers] = useState<FirmUserRecord[]>([]);
  const [invitations, setInvitations] = useState<InvitationRecord[]>([]);
  const isAdmin = authUser.role === "admin_advocate";

  useEffect(() => {
    if (isAdmin) loadAdminData();
  }, [authUser.accessToken, isAdmin]);

  async function loadAdminData() {
    if (!authUser.accessToken) return;
    try {
      const [usersData, invitationsData] = await Promise.all([
        apiGet<FirmUserRecord[]>("/auth/users", authUser.accessToken),
        apiGet<InvitationRecord[]>("/auth/invitations", authUser.accessToken)
      ]);
      setFirmUsers(usersData);
      setInvitations(invitationsData);
    } catch (err) {
      setInviteError(err instanceof Error ? err.message : "Could not load admin data");
    }
  }

  async function sendInvite() {
    if (!authUser.accessToken) return;
    setInviteBusy(true);
    try {
      const response = await apiPost<InviteUserResponse>(
        "/auth/invitations",
        { email: inviteEmail, role: inviteRole },
        authUser.accessToken
      );
      setInviteError("");
      setInviteMessage(
        response.preview_accept_url
          ? `Invitation created. Preview link: ${response.preview_accept_url}`
          : `Invitation sent to ${response.email} as ${roleLabel(response.role)}.`
      );
      setInviteEmail("");
      await loadAdminData();
    } catch (err) {
      setInviteMessage("");
      setInviteError(err instanceof Error ? err.message : "Invitation failed");
    } finally {
      setInviteBusy(false);
    }
  }

  async function updateUser(user: FirmUserRecord, body: { role?: string; seat_status?: string }) {
    if (!authUser.accessToken) return;
    try {
      await apiPatch<FirmUserRecord>(`/auth/users/${user.membership_id}`, body, authUser.accessToken);
      setInviteMessage("User updated");
      setInviteError("");
      await loadAdminData();
    } catch (err) {
      setInviteError(err instanceof Error ? err.message : "User update failed");
    }
  }

  async function resendInvite(invitation: InvitationRecord) {
    if (!authUser.accessToken) return;
    try {
      const response = await apiPost<InviteUserResponse>(`/auth/invitations/${invitation.id}/resend`, {}, authUser.accessToken);
      setInviteMessage(response.preview_accept_url ? `New preview link: ${response.preview_accept_url}` : `Invitation resent to ${response.email}.`);
      setInviteError("");
      await loadAdminData();
    } catch (err) {
      setInviteError(err instanceof Error ? err.message : "Resend failed");
    }
  }

  return (
    <section className="grid-2">
      <div className="card">
        <div className="card-title">Firm Settings</div>
        <div className="card-sub">Users, roles, contacts and voice language</div>
        <table className="table">
          <tbody>
            <tr>
              <th>Admin</th>
              <td>A. Sharma cannot be deleted</td>
            </tr>
            <tr>
              <th>Voice</th>
              <td>English, Hindi, Assamese, Bengali</td>
            </tr>
            <tr>
              <th>Plan</th>
              <td>{authUser.plan}</td>
            </tr>
            <tr>
              <th>Your role</th>
              <td>{roleLabel(authUser.role)}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div className="card">
        <div className="card-title">Invite User</div>
        <div className="card-sub">Admin-only role assignment</div>
        {isAdmin ? (
          <>
            <div className="form-grid">
              <label className="field">
                <span className="label">Email</span>
                <input className="input" value={inviteEmail} onChange={(event) => setInviteEmail(event.target.value)} />
              </label>
              <label className="field">
                <span className="label">Role</span>
                <select className="select" value={inviteRole} onChange={(event) => setInviteRole(event.target.value)}>
                  {roleOptions.filter((option) => option.value !== "admin_advocate").map((option) => (
                    <option value={option.value} key={option.value}>{option.label}</option>
                  ))}
                </select>
              </label>
            </div>
            <button className="btn primary auth-submit" onClick={sendInvite} disabled={inviteBusy}>
              <Users /> {inviteBusy ? "Sending..." : "Send Invitation"}
            </button>
            {inviteMessage ? <div className="auth-notice">{inviteMessage}</div> : null}
            {inviteError ? <div className="auth-error">{inviteError}</div> : null}
          </>
        ) : (
          <p className="stat-note">Only admin advocates can invite users or assign roles.</p>
        )}
      </div>
      {isAdmin ? (
        <>
          <div className="card">
            <div className="card-title">Firm Users</div>
            <div className="card-sub">Roles and seat status</div>
            <table className="table">
              <thead>
                <tr>
                  <th>User</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {firmUsers.map((user) => (
                  <tr key={user.membership_id}>
                    <td>
                      <strong>{user.name}</strong>
                      <div className="stat-note">{user.email}</div>
                    </td>
                    <td>
                      <select className="select compact-select" value={user.role} onChange={(event) => updateUser(user, { role: event.target.value })}>
                        {roleOptions.map((option) => (
                          <option value={option.value} key={option.value}>{option.label}</option>
                        ))}
                      </select>
                    </td>
                    <td>{user.seat_status}</td>
                    <td>
                      <button className="btn ghost" onClick={() => updateUser(user, { seat_status: user.seat_status === "active" ? "inactive" : "active" })}>
                        {user.seat_status === "active" ? "Deactivate" : "Activate"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card">
            <div className="card-title">Invitations</div>
            <div className="card-sub">Pending and accepted invites</div>
            <table className="table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {invitations.map((invitation) => (
                  <tr key={invitation.id}>
                    <td>{invitation.email}</td>
                    <td>{roleLabel(invitation.role)}</td>
                    <td>{invitation.status}</td>
                    <td>
                      <button className="btn ghost" onClick={() => resendInvite(invitation)} disabled={invitation.status === "accepted"}>
                        Resend
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
      <Security />
    </section>
  );
}

function Plans() {
  return (
    <section className="grid-3">
      {plans.map((plan) => (
        <div className="card plan" key={plan.name}>
          <div>
            <div className="card-title">{plan.name}</div>
            <div className="card-sub">{plan.seats}</div>
          </div>
          <div className="price">{plan.price}</div>
          <div className="source-list">
            {plan.features.map((feature) => (
              <div className="check-item" key={feature}>
                <div className="check-box">
                  <Check size={17} />
                </div>
                <div>{feature}</div>
              </div>
            ))}
          </div>
          <button className="btn primary">
            <CreditIcon /> Select Plan
          </button>
        </div>
      ))}
    </section>
  );
}

function CreditIcon() {
  return <Lock size={17} />;
}

function Videos() {
  return (
    <section className="card">
      <div className="card-title">Demo Videos</div>
      <div className="card-sub">Reusable right-rail experience</div>
      {sections.slice(0, 8).map((section) => (
        <div className="video-row" key={section.id}>
          <div className="video-icon">
            <Play size={17} />
          </div>
          <div>
            <strong>{section.label}</strong>
            <p className="stat-note">One-minute explainer, lazy-loaded, dismissible and never autoplaying with sound.</p>
          </div>
        </div>
      ))}
    </section>
  );
}

function Security() {
  return (
    <div className="card">
      <div className="card-title">Disclaimer & Security</div>
      <div className="card-sub">Assistive tool, advocate verifies output</div>
      <p className="stat-note">
        Vakil Yantra supports drafting, research and organisation. It does not replace legal judgment, and every fact, citation,
        statute, procedure and limitation date must be independently verified before use.
      </p>
      <div className="source-list" style={{ marginTop: 12 }}>
        {securityClaims.map((claim) => (
          <div className="check-item" key={claim}>
            <div className="check-box">
              <ShieldCheck size={17} />
            </div>
            <div>{claim}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SimpleTool({ title, sub, input, output }: { title: string; sub: string; input: string; output: string }) {
  return (
    <section className="grid-2">
      <div className="card">
        <div className="card-title">{title}</div>
        <div className="card-sub">{sub}</div>
        <textarea className="textarea" placeholder={input} />
        <div className="actions" style={{ marginTop: 12 }}>
          <button className="btn primary">
            <Bot /> Run
          </button>
          <button className="btn ghost">
            <Mic /> Voice
          </button>
        </div>
      </div>
      <div className="card">
        <div className="card-title">Output</div>
        <div className="card-sub">Review before relying</div>
        <div className="editor">{output}</div>
      </div>
    </section>
  );
}

function SecurityFooter() {
  return (
    <footer className="footer">
      <strong>Enterprise Security</strong>
      <span>TLS encryption</span>
      <span>KMS at rest</span>
      <span>RBAC</span>
      <span>Audit logs</span>
      <span>No unsupported uptime or compliance badge claims</span>
    </footer>
  );
}
