// Mock data matching the fertility-sense FastAPI response shapes

export interface PipelineStage {
  stage: string;
  count: number;
  value: number;
  color: string;
}

export const pipelineStages: PipelineStage[] = [
  { stage: "Cold", count: 14, value: 420000, color: "#94a3b8" },
  { stage: "Warm", count: 9, value: 630000, color: "#06b6d4" },
  { stage: "Evaluating", count: 6, value: 780000, color: "#f5a623" },
  { stage: "Negotiating", count: 3, value: 510000, color: "#8b5cf6" },
  { stage: "Won", count: 2, value: 340000, color: "#10b981" },
];

export interface PipelineSummary {
  totalPipelineValue: number;
  dealsInPipeline: number;
  weightedValue: number;
  staleDeals: number;
  winRate: number;
  avgDealSize: number;
}

export const pipelineSummary: PipelineSummary = {
  totalPipelineValue: 2680000,
  dealsInPipeline: 34,
  weightedValue: 1240000,
  staleDeals: 5,
  winRate: 28,
  avgDealSize: 78800,
};

export interface BuyerType {
  type: string;
  count: number;
  value: number;
}

export const buyerTypes: BuyerType[] = [
  { type: "CHRO / VP HR", count: 12, value: 960000 },
  { type: "Benefits Broker", count: 8, value: 640000 },
  { type: "SMB Direct", count: 6, value: 420000 },
  { type: "Union / Trust", count: 4, value: 380000 },
  { type: "TPA", count: 4, value: 280000 },
];

export interface Prospect {
  id: string;
  name: string;
  company: string;
  buyerType: string;
  dealStage: string;
  dealScore: number;
  dealValue: number;
  lastContact: string;
  nextAction: string;
}

export const prospects: Prospect[] = [
  {
    id: "p1",
    name: "Sarah Mitchell",
    company: "Acme Corp (4,200 EEs)",
    buyerType: "CHRO / VP HR",
    dealStage: "Negotiating",
    dealScore: 92,
    dealValue: 185000,
    lastContact: "2026-04-06",
    nextAction: "Send revised proposal",
  },
  {
    id: "p2",
    name: "David Chen",
    company: "TechForward Inc (1,800 EEs)",
    buyerType: "Benefits Broker",
    dealStage: "Evaluating",
    dealScore: 85,
    dealValue: 120000,
    lastContact: "2026-04-05",
    nextAction: "Schedule clinical outcomes call",
  },
  {
    id: "p3",
    name: "Lisa Rodriguez",
    company: "Pacific Manufacturing (3,100 EEs)",
    buyerType: "CHRO / VP HR",
    dealStage: "Evaluating",
    dealScore: 78,
    dealValue: 155000,
    lastContact: "2026-04-03",
    nextAction: "ROI analysis presentation",
  },
  {
    id: "p4",
    name: "James Park",
    company: "Midwest Teachers Union",
    buyerType: "Union / Trust",
    dealStage: "Warm",
    dealScore: 72,
    dealValue: 210000,
    lastContact: "2026-04-01",
    nextAction: "Board presentation prep",
  },
  {
    id: "p5",
    name: "Rachel Thompson",
    company: "GreenLeaf Biotech (680 EEs)",
    buyerType: "SMB Direct",
    dealStage: "Negotiating",
    dealScore: 88,
    dealValue: 65000,
    lastContact: "2026-04-07",
    nextAction: "Final contract review",
  },
  {
    id: "p6",
    name: "Mark Williams",
    company: "Atlas Benefits Group",
    buyerType: "TPA",
    dealStage: "Cold",
    dealScore: 45,
    dealValue: 95000,
    lastContact: "2026-03-22",
    nextAction: "Initial discovery call",
  },
  {
    id: "p7",
    name: "Jennifer Adams",
    company: "Skyline Logistics (2,400 EEs)",
    buyerType: "CHRO / VP HR",
    dealStage: "Evaluating",
    dealScore: 81,
    dealValue: 140000,
    lastContact: "2026-04-04",
    nextAction: "Send case study packet",
  },
  {
    id: "p8",
    name: "Robert Kim",
    company: "NexGen Financial (950 EEs)",
    buyerType: "Benefits Broker",
    dealStage: "Warm",
    dealScore: 63,
    dealValue: 78000,
    lastContact: "2026-03-29",
    nextAction: "Follow-up webinar invite",
  },
];

export interface StaleDeal {
  company: string;
  stage: string;
  daysSinceContact: number;
  value: number;
  owner: string;
}

export const staleDeals: StaleDeal[] = [
  { company: "Atlas Benefits Group", stage: "Cold", daysSinceContact: 17, value: 95000, owner: "Mark W." },
  { company: "Pinnacle HR Solutions", stage: "Warm", daysSinceContact: 14, value: 110000, owner: "Sarah M." },
  { company: "Coast Healthcare Admin", stage: "Evaluating", daysSinceContact: 12, value: 175000, owner: "David C." },
  { company: "Metro Workers Union", stage: "Cold", daysSinceContact: 21, value: 88000, owner: "James P." },
  { company: "Summit Corp", stage: "Warm", daysSinceContact: 10, value: 130000, owner: "Lisa R." },
];

export interface TOSScore {
  topic: string;
  score: number;
  trend: "up" | "down" | "flat";
  category: string;
}

export const tosScores: TOSScore[] = [
  { topic: "IVF coverage mandate expansion", score: 94, trend: "up", category: "Regulatory" },
  { topic: "Employer fertility benefit demand", score: 91, trend: "up", category: "Market" },
  { topic: "Fertility benefit cost containment", score: 87, trend: "up", category: "Market" },
  { topic: "State mandate tracking (IL, CO, NY)", score: 85, trend: "up", category: "Regulatory" },
  { topic: "LGBTQ+ family building coverage", score: 82, trend: "up", category: "DE&I" },
  { topic: "Egg freezing as standard benefit", score: 79, trend: "flat", category: "Market" },
  { topic: "Fertility benefit ROI studies", score: 76, trend: "up", category: "Research" },
  { topic: "Surrogacy coverage frameworks", score: 73, trend: "flat", category: "Market" },
  { topic: "Menopause benefit bundling", score: 68, trend: "up", category: "Adjacent" },
  { topic: "Adoption assistance integration", score: 64, trend: "flat", category: "Adjacent" },
];

export interface VelocityAlert {
  signal: string;
  change: number;
  period: string;
  source: string;
}

export const velocityAlerts: VelocityAlert[] = [
  { signal: "IVF mandate Google searches", change: 47, period: "7d", source: "Google Trends" },
  { signal: "Fertility benefit job postings", change: 32, period: "30d", source: "Indeed/LinkedIn" },
  { signal: "Progyny competitor mentions", change: 28, period: "7d", source: "News/Social" },
  { signal: "Employer benefits RFP activity", change: 19, period: "14d", source: "BidSignal" },
  { signal: "State legislature fertility bills", change: 15, period: "30d", source: "LegiScan" },
];

export interface RegulatorySignal {
  state: string;
  bill: string;
  status: string;
  impact: "high" | "medium" | "low";
  effectiveDate: string;
}

export const regulatorySignals: RegulatorySignal[] = [
  { state: "Colorado", bill: "HB 26-1187", status: "Committee hearing", impact: "high", effectiveDate: "2027-01-01" },
  { state: "Illinois", bill: "SB 2841", status: "Passed senate", impact: "high", effectiveDate: "2026-07-01" },
  { state: "New York", bill: "A.4533", status: "In committee", impact: "medium", effectiveDate: "2027-01-01" },
  { state: "California", bill: "AB 1294", status: "Enrolled", impact: "high", effectiveDate: "2026-10-01" },
  { state: "Massachusetts", bill: "H.1208", status: "Hearing scheduled", impact: "medium", effectiveDate: "2027-07-01" },
];

export interface FeedHealth {
  name: string;
  status: "healthy" | "degraded" | "down";
  lastRun: string;
  recordsProcessed: number;
  errorRate: number;
}

export const feedHealth: FeedHealth[] = [
  { name: "Google Trends Scout", status: "healthy", lastRun: "2026-04-08T06:00:00Z", recordsProcessed: 342, errorRate: 0 },
  { name: "News & PR Monitor", status: "healthy", lastRun: "2026-04-08T05:30:00Z", recordsProcessed: 128, errorRate: 0.02 },
  { name: "LegiScan Regulatory Feed", status: "degraded", lastRun: "2026-04-07T22:00:00Z", recordsProcessed: 47, errorRate: 0.08 },
];

export interface Competitor {
  name: string;
  revenue: string;
  clients: string;
  strengths: string[];
  weaknesses: string[];
  winPositioning: string;
  recentMoves: string[];
}

export const competitors: Competitor[] = [
  {
    name: "Progyny",
    revenue: "$1.1B (2025)",
    clients: "500+ employers",
    strengths: ["Market leader brand", "Smart Cycle bundled pricing", "Outcomes data at scale"],
    weaknesses: ["Premium pricing", "Limited international", "LGBTQ+ coverage gaps"],
    winPositioning: "WIN offers broader family-building spectrum at competitive rates with superior clinical navigation",
    recentMoves: ["Expanded surrogacy network", "Launched menopause module", "Q4 earnings beat"],
  },
  {
    name: "Carrot Fertility",
    revenue: "$200M+ (est.)",
    clients: "1,000+ employers",
    strengths: ["Global coverage (80+ countries)", "Tech-forward UX", "Broad benefit spectrum"],
    weaknesses: ["Thin clinical network in US", "High churn in SMB", "Limited outcomes reporting"],
    winPositioning: "WIN delivers deeper clinical expertise and US network density vs. Carrot's breadth-first approach",
    recentMoves: ["Series D funding $75M", "Added adoption benefits", "UK expansion"],
  },
  {
    name: "Maven Clinic",
    revenue: "$300M+ (est.)",
    clients: "2,000+ employers",
    strengths: ["Virtual-first model", "Maternity + fertility bundle", "Strong brand with millennials"],
    weaknesses: ["Virtual-only limits complex care", "No direct clinic network", "High per-member cost"],
    winPositioning: "WIN combines virtual convenience with direct clinic access for complex fertility cases",
    recentMoves: ["IPO rumors", "Launched fertility pharmacy", "Partnership with Cleveland Clinic"],
  },
  {
    name: "Kindbody",
    revenue: "$150M+ (est.)",
    clients: "200+ employers",
    strengths: ["Own clinics (40+ locations)", "Vertically integrated", "Transparent pricing"],
    weaknesses: ["Limited geographic reach", "Small employer base", "Capacity constraints"],
    winPositioning: "WIN's nationwide network of 900+ clinics vs. Kindbody's 40 owned locations",
    recentMoves: ["Opened 8 new clinics", "Launched genetic testing", "New CFO hire"],
  },
];

export interface EmailSequence {
  id: string;
  name: string;
  buyerType: string;
  enrolled: number;
  active: number;
  completed: number;
  paused: number;
  openRate: number;
  replyRate: number;
}

export const emailSequences: EmailSequence[] = [
  { id: "seq1", name: "CHRO Cold Outreach", buyerType: "CHRO / VP HR", enrolled: 85, active: 42, completed: 31, paused: 12, openRate: 34, replyRate: 8 },
  { id: "seq2", name: "Broker Partnership Intro", buyerType: "Benefits Broker", enrolled: 62, active: 28, completed: 22, paused: 12, openRate: 41, replyRate: 12 },
  { id: "seq3", name: "SMB Fertility Benefit Pitch", buyerType: "SMB Direct", enrolled: 120, active: 67, completed: 38, paused: 15, openRate: 29, replyRate: 6 },
  { id: "seq4", name: "Union Trust Engagement", buyerType: "Union / Trust", enrolled: 35, active: 18, completed: 10, paused: 7, openRate: 38, replyRate: 11 },
  { id: "seq5", name: "TPA Integration Partner", buyerType: "TPA", enrolled: 28, active: 14, completed: 8, paused: 6, openRate: 32, replyRate: 7 },
  { id: "seq6", name: "Re-engagement (Stale Leads)", buyerType: "Mixed", enrolled: 45, active: 45, completed: 0, paused: 0, openRate: 22, replyRate: 4 },
];

export interface RecentSend {
  timestamp: string;
  sequence: string;
  recipient: string;
  subject: string;
  status: "delivered" | "opened" | "replied" | "bounced";
}

export const recentSends: RecentSend[] = [
  { timestamp: "2026-04-08T09:15:00Z", sequence: "CHRO Cold Outreach", recipient: "j.hernandez@acmecorp.com", subject: "Fertility benefits that reduce turnover by 22%", status: "opened" },
  { timestamp: "2026-04-08T09:00:00Z", sequence: "Broker Partnership Intro", recipient: "m.chang@atlasbenefits.com", subject: "Partner opportunity: fertility benefit demand is surging", status: "delivered" },
  { timestamp: "2026-04-08T08:45:00Z", sequence: "SMB Fertility Benefit Pitch", recipient: "ceo@greenleafbio.com", subject: "How companies under 1K employees offer fertility benefits", status: "replied" },
  { timestamp: "2026-04-08T08:30:00Z", sequence: "Re-engagement (Stale Leads)", recipient: "hr@summitcorp.com", subject: "3 things changed since we last spoke about fertility benefits", status: "delivered" },
  { timestamp: "2026-04-07T16:00:00Z", sequence: "Union Trust Engagement", recipient: "benefits@midwestteachers.org", subject: "How 12 unions added fertility coverage in 2025", status: "opened" },
];

export interface ContentItem {
  id: string;
  title: string;
  type: "blog" | "case_study" | "whitepaper" | "email" | "social";
  status: "draft" | "review" | "scheduled" | "published";
  targetBuyer: string;
  dueDate: string;
  author: string;
}

export const contentQueue: ContentItem[] = [
  { id: "c1", title: "2026 State Fertility Mandate Tracker", type: "whitepaper", status: "review", targetBuyer: "CHRO / VP HR", dueDate: "2026-04-12", author: "Content AI" },
  { id: "c2", title: "ROI of Fertility Benefits: 5 Employer Case Studies", type: "case_study", status: "draft", targetBuyer: "Benefits Broker", dueDate: "2026-04-15", author: "Content AI" },
  { id: "c3", title: "Why Egg Freezing Is the New 401(k) Match", type: "blog", status: "scheduled", targetBuyer: "SMB Direct", dueDate: "2026-04-10", author: "Content AI" },
  { id: "c4", title: "Union Negotiation Playbook: Fertility Benefits", type: "whitepaper", status: "draft", targetBuyer: "Union / Trust", dueDate: "2026-04-18", author: "Content AI" },
  { id: "c5", title: "LinkedIn: 3 fertility benefit stats that will surprise your CFO", type: "social", status: "scheduled", targetBuyer: "CHRO / VP HR", dueDate: "2026-04-09", author: "Content AI" },
  { id: "c6", title: "TPA Integration Guide: Adding Fertility Benefits", type: "whitepaper", status: "review", targetBuyer: "TPA", dueDate: "2026-04-14", author: "Content AI" },
];

export interface AgentStatus {
  name: string;
  status: "running" | "idle" | "error";
  lastRun: string;
  nextRun: string;
  runsToday: number;
  successRate: number;
  description: string;
}

export const agentStatuses: AgentStatus[] = [
  { name: "Scout Agent", status: "idle", lastRun: "2026-04-08T06:00:00Z", nextRun: "2026-04-08T12:00:00Z", runsToday: 2, successRate: 100, description: "Scans Google Trends, news, and job boards for demand signals" },
  { name: "Sequence Runner", status: "running", lastRun: "2026-04-08T09:00:00Z", nextRun: "2026-04-08T09:30:00Z", runsToday: 18, successRate: 97, description: "Executes email sequences and tracks engagement" },
  { name: "Content Generator", status: "idle", lastRun: "2026-04-07T22:00:00Z", nextRun: "2026-04-08T22:00:00Z", runsToday: 1, successRate: 100, description: "Generates blog posts, case studies, and social content" },
  { name: "Digest Builder", status: "idle", lastRun: "2026-04-08T07:00:00Z", nextRun: "2026-04-09T07:00:00Z", runsToday: 1, successRate: 100, description: "Compiles daily and weekly intelligence digests" },
  { name: "Pipeline Scorer", status: "idle", lastRun: "2026-04-08T06:30:00Z", nextRun: "2026-04-08T12:30:00Z", runsToday: 2, successRate: 100, description: "Recalculates deal scores based on latest signals" },
];

// ─── Executive View ──────────────────────────────────────────────────

export interface ExecutiveFocus {
  headline: string;
  badges: { label: string; variant: "amber" | "blue" | "emerald" | "purple" }[];
}

export const executiveFocus: ExecutiveFocus = {
  headline: "5 stale deals worth $420K need attention this week",
  badges: [
    { label: "3 RFPs due", variant: "amber" },
    { label: "$1.2M weighted pipeline", variant: "blue" },
    { label: "2 new mandates", variant: "emerald" },
  ],
};

export interface ExecutiveKPI {
  label: string;
  value: string;
  trend?: number;
  target?: string;
}

export const executiveKPIs: ExecutiveKPI[] = [
  { label: "Total Pipeline", value: "$2.7M", trend: 12 },
  { label: "Win Rate", value: "28%", target: "35%" },
  { label: "Avg Cycle", value: "45 days", trend: -5 },
  { label: "Emails Sent (7d)", value: "47", trend: 22 },
  { label: "Meetings Booked (7d)", value: "3" },
  { label: "Active Sequences", value: "4" },
];

export interface ActionStep {
  step: string;
  status: "pending" | "done" | "overdue";
}

export interface ActionItem {
  title: string;
  detail: string;
  priority: "high" | "medium" | "low";
  type: "followup" | "sequence" | "regulatory" | "competitive" | "new_prospect";
  prospect?: {
    name: string;
    company: string;
    email: string;
    buyerType: string;
    dealStage: string;
    dealValue: string;
    daysSilent?: number;
    currentSequence?: string;
    sequenceStep?: number;
  };
  context: string;
  steps: ActionStep[];
  timeline: string;
  impact: string;
}

export const weeklyActions: ActionItem[] = [
  {
    title: "Follow up with Disney",
    detail: "Evaluating stage, 12 days silent — $500K deal at risk",
    priority: "high",
    type: "followup",
    prospect: {
      name: "Jane Smith",
      company: "Disney",
      email: "jane.smith@disney.com",
      buyerType: "CHRO",
      dealStage: "Evaluating",
      dealValue: "$500K ARR",
      daysSilent: 12,
      currentSequence: "chro_outbound",
      sequenceStep: 3,
    },
    context: "Jane downloaded the ROI calculator 3 weeks ago and had a 30-min intro call. She requested a case study for media/entertainment companies. We sent chro_outbound step 3 but no response in 12 days. Disney has 180K employees and currently uses no managed fertility benefit — massive greenfield opportunity.",
    steps: [
      { step: "Send personalized follow-up referencing media industry case study", status: "pending" },
      { step: "Connect Jane with WIN's client success lead for Disney-scale reference", status: "pending" },
      { step: "Prepare custom ROI model for 180K employee base", status: "done" },
      { step: "Schedule 15-min check-in call (suggest Thu/Fri)", status: "pending" },
      { step: "If no response by Friday, escalate to VP of Sales for executive intro", status: "pending" },
    ],
    timeline: "Action needed by Friday — deal goes stale at 14 days",
    impact: "$500K ARR at risk. Disney would be WIN's largest client and flagship reference.",
  },
  {
    title: "Send broker_education step 3 to AON",
    detail: "Sequence step overdue by 2 days — broker channel activation",
    priority: "high",
    type: "sequence",
    prospect: {
      name: "Michael Torres",
      company: "AON",
      email: "michael.torres@aon.com",
      buyerType: "Broker",
      dealStage: "Warm",
      dealValue: "$200K+ (channel)",
      daysSilent: 5,
      currentSequence: "broker_education",
      sequenceStep: 2,
    },
    context: "Michael is a senior producer at AON's health & benefits practice. He opened emails 1 and 2 (both within 2 hours of send). Step 3 covers WIN's commission structure and co-sell playbook. AON has 150+ enterprise clients who could be referred to WIN — this is a channel multiplier, not just one deal.",
    steps: [
      { step: "Send broker_education step 3 (commission structure + co-sell playbook)", status: "overdue" },
      { step: "Include link to broker partner portal (when ready)", status: "pending" },
      { step: "Propose 30-min call to walk through first co-sell target", status: "pending" },
      { step: "Identify 3 AON clients in mandate states (CA, NY, IL) as co-sell candidates", status: "pending" },
    ],
    timeline: "Send today — Michael has shown high engagement (opened both prior emails)",
    impact: "$200K+ direct, but AON channel could drive $2M+ in referred deals over 12 months.",
  },
  {
    title: "New Colorado mandate — prospect 15 companies",
    detail: "HB 22-1008 creates window for employers with 100+ employees in CO",
    priority: "medium",
    type: "regulatory",
    context: "Colorado's Building Families Act (HB 22-1008) mandates fertility coverage including IVF for employers with 100+ employees. This creates a compliance trigger: employers in CO who don't yet have a managed fertility benefit need one. Our state mandate feed identified 15 Fortune 1000 companies headquartered or with major operations in CO.",
    steps: [
      { step: "Pull list of 15 target companies from CO employer database", status: "done" },
      { step: "Cross-reference against existing WIN clients (exclude current)", status: "pending" },
      { step: "Check which are already using Progyny/Carrot/Maven (competitive intel)", status: "pending" },
      { step: "Create CO-specific outreach email (reference HB 22-1008 compliance deadline)", status: "pending" },
      { step: "Add qualified prospects to pipeline and assign chro_outbound sequence", status: "pending" },
      { step: "Brief AON/Willis producers in CO region for co-sell", status: "pending" },
    ],
    timeline: "Complete prospecting by end of week — compliance deadline creates urgency",
    impact: "15 prospects × $100K avg = $1.5M potential pipeline from one regulatory trigger.",
  },
];

export interface CompetitiveAlert {
  text: string;
}

export const competitiveAlerts: CompetitiveAlert[] = [
  { text: "Progyny Q1 earnings next week" },
  { text: "Carrot expanding to EMEA" },
  { text: "Kindbody opened 3 new clinics in TX" },
  { text: "Maven Clinic IPO filing expected Q2" },
];

// ─── Queue HITL Items ───────────────────────────────────────────────

export type QueueItemStatus = "pending" | "approved" | "sent" | "rejected";
export type QueueChannel = "sales_email" | "linkedin" | "case_study" | "blog" | "social";

export interface QueueItem {
  id: string;
  title: string;
  body: string;
  channel: QueueChannel;
  evidenceCount: number;
  riskTier: "low" | "medium" | "high";
  status: QueueItemStatus;
  rejectReason?: string;
  targetCompany: string;
  createdAt: string;
}

export const queueItems: QueueItem[] = [
  {
    id: "q1",
    title: "Cold outreach to Acme Corp CHRO",
    body: "Hi Sarah, I noticed Acme Corp recently posted 3 fertility-related benefit roles on LinkedIn. With 4,200 employees, companies your size typically see 22% reduction in turnover after adding fertility benefits. I'd love to share how WIN Fertility can help...",
    channel: "sales_email",
    evidenceCount: 4,
    riskTier: "low",
    status: "pending",
    targetCompany: "Acme Corp",
    createdAt: "2026-04-08T08:30:00Z",
  },
  {
    id: "q2",
    title: "LinkedIn connection request to David Chen",
    body: "Hi David, as a Benefits Broker at TechForward, you're likely fielding more fertility benefit questions from clients. Our broker partnership program offers white-labeled resources and co-selling support...",
    channel: "linkedin",
    evidenceCount: 2,
    riskTier: "low",
    status: "pending",
    targetCompany: "TechForward Inc",
    createdAt: "2026-04-08T08:15:00Z",
  },
  {
    id: "q3",
    title: "Case study: Pacific Manufacturing ROI analysis",
    body: "Pacific Manufacturing (3,100 EEs) saw a 31% reduction in fertility-related medical claims and 18% improvement in employee retention after implementing WIN Fertility benefits. Total first-year ROI: 2.4x...",
    channel: "case_study",
    evidenceCount: 7,
    riskTier: "medium",
    status: "approved",
    targetCompany: "Pacific Manufacturing",
    createdAt: "2026-04-07T14:00:00Z",
  },
  {
    id: "q4",
    title: "Blog: Why Egg Freezing Is the New 401(k) Match",
    body: "In 2026, egg freezing benefits have moved from Silicon Valley perk to mainstream expectation. Here are 5 data points that show why forward-thinking employers are adding egg freezing to their benefits package...",
    channel: "blog",
    evidenceCount: 5,
    riskTier: "low",
    status: "sent",
    targetCompany: "General",
    createdAt: "2026-04-07T10:00:00Z",
  },
  {
    id: "q5",
    title: "Follow-up email to Midwest Teachers Union",
    body: "Hi James, following up on our conversation about fertility benefits for union members. I've attached the playbook showing how 12 unions successfully negotiated fertility coverage in their 2025 contracts...",
    channel: "sales_email",
    evidenceCount: 3,
    riskTier: "medium",
    status: "pending",
    targetCompany: "Midwest Teachers Union",
    createdAt: "2026-04-08T07:45:00Z",
  },
  {
    id: "q6",
    title: "Social post: 3 fertility stats for CFOs",
    body: "Did you know? 1) Companies with fertility benefits see 22% lower turnover. 2) The average IVF cycle costs $23K out-of-pocket. 3) Fertility benefits have a 3.2x ROI in the first year. #FertilityBenefits #HR",
    channel: "social",
    evidenceCount: 3,
    riskTier: "low",
    status: "rejected",
    rejectReason: "Stats need updated sources for Q2 2026",
    targetCompany: "General",
    createdAt: "2026-04-06T16:00:00Z",
  },
  {
    id: "q7",
    title: "Re-engagement email to Summit Corp",
    body: "Hi there, it's been a while since we connected about fertility benefits for Summit Corp. Since then, 3 things have changed: Colorado's new mandate (HB 26-1187), your competitor added fertility benefits, and our pricing model now includes...",
    channel: "sales_email",
    evidenceCount: 4,
    riskTier: "high",
    status: "pending",
    targetCompany: "Summit Corp",
    createdAt: "2026-04-08T09:00:00Z",
  },
  {
    id: "q8",
    title: "LinkedIn thought leadership post",
    body: "The fertility benefits landscape is shifting fast. In the last 30 days: 4 new state mandates introduced, Progyny expanded surrogacy coverage, and employer demand signals are up 47% on Google Trends. Here's what smart HR leaders are doing about it...",
    channel: "linkedin",
    evidenceCount: 6,
    riskTier: "low",
    status: "approved",
    targetCompany: "General",
    createdAt: "2026-04-07T11:00:00Z",
  },
];

// ─── Intelligence / Feeds ────────────────────────────────────────────

export interface FeedSource {
  source: string;
  recordCount: number;
  topicsCovered: number;
  grades: Record<string, number>;
  latestDate: string | null;
  type: "evidence" | "regulatory" | "intelligence" | "demand";
}

export const feedSources: FeedSource[] = [
  { source: "mother_to_baby", recordCount: 20, topicsCovered: 26, grades: { D: 20 }, latestDate: "2026-04-09", type: "evidence" },
  { source: "state_mandates", recordCount: 20, topicsCovered: 3, grades: { B: 20 }, latestDate: "2026-04-09", type: "regulatory" },
  { source: "nih_nichd", recordCount: 5, topicsCovered: 11, grades: { A: 1, B: 3, C: 1 }, latestDate: "2024-02-01", type: "evidence" },
  { source: "competitor_intel", recordCount: 4, topicsCovered: 3, grades: { C: 4 }, latestDate: "2026-04-09", type: "intelligence" },
  { source: "cdc_art", recordCount: 1, topicsCovered: 2, grades: { A: 1 }, latestDate: "2024-10-01", type: "evidence" },
  { source: "cdc_prams", recordCount: 1, topicsCovered: 2, grades: { A: 1 }, latestDate: "2024-06-15", type: "evidence" },
  { source: "acog", recordCount: 1, topicsCovered: 2, grades: { B: 1 }, latestDate: null, type: "evidence" },
  { source: "cochrane", recordCount: 1, topicsCovered: 3, grades: { C: 1 }, latestDate: null, type: "evidence" },
  { source: "mothertobaby", recordCount: 1, topicsCovered: 1, grades: { B: 1 }, latestDate: null, type: "evidence" },
];

export const gradeDistribution = [
  { grade: "A", count: 3, color: "#10b981" },
  { grade: "B", count: 25, color: "#3b82f6" },
  { grade: "C", count: 6, color: "#f5a623" },
  { grade: "D", count: 20, color: "#94a3b8" },
];

export interface TopicCoverage {
  topicId: string;
  displayName: string;
  riskTier: string;
  evidenceCount: number;
}

export const coveredTopics: TopicCoverage[] = [
  { topicId: "medication-pregnancy-safety", displayName: "Medication Safety", riskTier: "red", evidenceCount: 8 },
  { topicId: "ivf", displayName: "IVF", riskTier: "yellow", evidenceCount: 5 },
  { topicId: "pcos-symptoms", displayName: "PCOS Symptoms", riskTier: "yellow", evidenceCount: 4 },
  { topicId: "prenatal-vitamins", displayName: "Prenatal Vitamins", riskTier: "yellow", evidenceCount: 4 },
  { topicId: "egg-quality", displayName: "Egg Quality", riskTier: "yellow", evidenceCount: 3 },
  { topicId: "fertility-supplements", displayName: "Fertility Supplements", riskTier: "green", evidenceCount: 3 },
  { topicId: "postpartum-depression", displayName: "Postpartum Depression", riskTier: "yellow", evidenceCount: 3 },
  { topicId: "fertility-diet", displayName: "Fertility Diet", riskTier: "green", evidenceCount: 2 },
  { topicId: "miscarriage-risk", displayName: "Miscarriage Risk", riskTier: "yellow", evidenceCount: 2 },
  { topicId: "breastfeeding-problems", displayName: "Breastfeeding", riskTier: "green", evidenceCount: 2 },
];

export const uncoveredTopics: TopicCoverage[] = [
  { topicId: "iui", displayName: "IUI", riskTier: "yellow", evidenceCount: 0 },
  { topicId: "egg-freezing", displayName: "Egg Freezing", riskTier: "yellow", evidenceCount: 0 },
  { topicId: "donor-eggs-sperm", displayName: "Donor Eggs & Sperm", riskTier: "yellow", evidenceCount: 0 },
  { topicId: "surrogacy", displayName: "Surrogacy", riskTier: "red", evidenceCount: 0 },
  { topicId: "clomid", displayName: "Clomid", riskTier: "red", evidenceCount: 0 },
  { topicId: "letrozole", displayName: "Letrozole", riskTier: "red", evidenceCount: 0 },
  { topicId: "semen-analysis", displayName: "Semen Analysis", riskTier: "yellow", evidenceCount: 0 },
  { topicId: "hsg-test", displayName: "HSG Test", riskTier: "yellow", evidenceCount: 0 },
  { topicId: "fertility-anxiety", displayName: "Fertility Anxiety", riskTier: "green", evidenceCount: 0 },
  { topicId: "sperm-health", displayName: "Sperm Health", riskTier: "yellow", evidenceCount: 0 },
];

export interface EvidenceRecord {
  evidenceId: string;
  title: string;
  source: string;
  grade: string;
  topics: string[];
  publicationDate: string | null;
  keyFindings: string[];
  url: string;
}

export const sampleEvidence: EvidenceRecord[] = [
  { evidenceId: "seed-003", title: "CDC ART National Summary Report", source: "cdc_art", grade: "A", topics: ["ivf", "fertility-clinic-selection"], publicationDate: "2024-10-01", keyFindings: ["Live birth rate 31.7% for patients under 35", "Cumulative rate 51.3% including frozen transfers"], url: "https://www.cdc.gov/art/reports/" },
  { evidenceId: "seed-001", title: "Folic Acid Supplementation and NTD Prevention", source: "cdc_prams", grade: "A", topics: ["prenatal-vitamins", "fertility-supplements"], publicationDate: "2024-06-15", keyFindings: ["0.4-0.8 mg/day reduces NTD risk by 50-70%"], url: "https://www.cdc.gov/prams/" },
  { evidenceId: "seed-005", title: "Screening and Treatment of PPD", source: "nih_nichd", grade: "A", topics: ["postpartum-depression"], publicationDate: "2024-02-01", keyFindings: ["CBT reduces PPD symptoms by 50-60%"], url: "https://pubmed.ncbi.nlm.nih.gov/" },
  { evidenceId: "comp-001", title: "Progyny Market Position Analysis", source: "competitor_intel", grade: "C", topics: ["ivf", "fertility-clinic-selection"], publicationDate: "2026-04-09", keyFindings: ["$1.1B revenue", "400+ employer clients", "Network managed model"], url: "" },
  { evidenceId: "mandate-ca", title: "California SB 729 Fertility Mandate", source: "state_mandates", grade: "B", topics: ["fertility-insurance"], publicationDate: "2024-01-01", keyFindings: ["Comprehensive IVF coverage required for insured employers"], url: "" },
];

export const intelligenceSummary = {
  totalRecords: 54,
  sourcesActive: 9,
  topicCoveragePct: 57,
  topicsCovered: 52,
  topicsTotal: 91,
  feedsRegistered: 3,
};
