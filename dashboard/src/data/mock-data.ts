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
