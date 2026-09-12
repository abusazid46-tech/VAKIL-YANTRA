import {
  Archive,
  Bell,
  BookOpen,
  Bot,
  Briefcase,
  CalendarClock,
  CreditCard,
  FileSearch,
  FileText,
  Gavel,
  Languages,
  LayoutDashboard,
  Library,
  ListChecks,
  PlaySquare,
  Scale,
  Settings,
  ShieldCheck,
  Users
} from "lucide-react";

export type SectionId =
  | "dashboard"
  | "drafting"
  | "library"
  | "case"
  | "matters"
  | "procedural"
  | "limitation"
  | "opposing"
  | "amendments"
  | "judgments"
  | "ecourts"
  | "translate"
  | "workspace"
  | "settings"
  | "plans"
  | "videos"
  | "security";

export const sections = [
  { id: "dashboard", label: "Dashboard", group: "Daily Work", icon: LayoutDashboard },
  { id: "drafting", label: "AI Drafting Studio", group: "Daily Work", icon: FileText },
  { id: "case", label: "Case Intelligence", group: "Daily Work", icon: FileSearch },
  { id: "matters", label: "Matter Manager", group: "Daily Work", icon: Briefcase },
  { id: "library", label: "Legal Library", group: "Research", icon: Library },
  { id: "judgments", label: "Recent Judgments", group: "Research", icon: Gavel },
  { id: "amendments", label: "Amendments Feed", group: "Research", icon: Bell, badge: "3" },
  { id: "ecourts", label: "eCourts Orders", group: "Research", icon: Scale, badge: "Live" },
  { id: "procedural", label: "Procedural Guide", group: "Tools", icon: ListChecks },
  { id: "limitation", label: "Limitation Calculator", group: "Tools", icon: CalendarClock },
  { id: "opposing", label: "Counsel Simulator", group: "Tools", icon: Bot },
  { id: "translate", label: "Translate & Transcribe", group: "Tools", icon: Languages },
  { id: "workspace", label: "Workspace", group: "Firm", icon: Archive },
  { id: "settings", label: "Settings", group: "Firm", icon: Settings },
  { id: "plans", label: "Plans & Payment", group: "Firm", icon: CreditCard },
  { id: "videos", label: "Demo Videos", group: "Trust", icon: PlaySquare },
  { id: "security", label: "Disclaimer & Security", group: "Trust", icon: ShieldCheck }
] as const;

export const stats = [
  { label: "Active Matters", value: "28", note: "6 updated this week", tone: "gold" },
  { label: "Drafts Prepared", value: "146", note: "12 awaiting review", tone: "green" },
  { label: "Legal Sources", value: "132", note: "Curated MVP corpus", tone: "blue" },
  { label: "Limitation Alerts", value: "2", note: "Immediate attention", tone: "red" }
];

export const matters = [
  {
    title: "Rahman v. Barua Traders",
    court: "District Court, Kamrup",
    tags: ["NI Act S.138", "Limitation 14d"],
    next: "Draft rejoinder and verify service proof"
  },
  {
    title: "State v. Ajit Deka",
    court: "Gauhati High Court",
    tags: ["BNS 103", "Bail Prep"],
    next: "Upload certified FIR copy"
  },
  {
    title: "Das Family Partition",
    court: "Civil Judge Senior Division",
    tags: ["Property", "Evidence"],
    next: "Prepare issue matrix"
  }
];

export const legalActs = [
  { name: "Constitution of India", year: "1950", type: "Constitution", sections: "395 Articles" },
  { name: "Bharatiya Nyaya Sanhita", year: "2023", type: "Criminal", sections: "358 Sections" },
  { name: "Bharatiya Nagarik Suraksha Sanhita", year: "2023", type: "Procedure", sections: "531 Sections" },
  { name: "Bharatiya Sakshya Adhiniyam", year: "2023", type: "Evidence", sections: "170 Sections" },
  { name: "Limitation Act", year: "1963", type: "Civil", sections: "137 Articles" },
  { name: "Negotiable Instruments Act", year: "1881", type: "Commercial", sections: "147 Sections" }
];

export const plans = [
  {
    name: "Individual",
    price: "₹1,499",
    seats: "1 advocate",
    features: ["AI drafting", "Matter workspace", "Legal search", "Limitation alerts"]
  },
  {
    name: "Chamber",
    price: "₹4,999",
    seats: "2-5 users",
    features: ["Shared folders", "Role permissions", "Billing controls", "Priority support"]
  },
  {
    name: "Firm",
    price: "₹8,999",
    seats: "6-10 users",
    features: ["Admin dashboard", "Audit events", "Seat enforcement", "Advanced exports"]
  }
];

export const checklist = [
  "Confirm filing type and court jurisdiction",
  "Verify limitation period and exclusions",
  "Attach authority letter, vakalatnama, affidavits and annexures",
  "Generate draft checklist and assign owners",
  "Save final checklist to the matter workspace"
];

export const securityClaims = [
  "Managed authentication with MFA",
  "Firm-level RBAC plus PostgreSQL RLS",
  "Short-lived signed document URLs",
  "KMS-backed encryption at rest",
  "Prompt-injection checks for uploaded documents",
  "Tamper-evident audit events"
];
