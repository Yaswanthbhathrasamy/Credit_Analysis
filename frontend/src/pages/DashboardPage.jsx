import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import {
  getCompany, getDashboardSummary, uploadDocuments, extractFinancialData,
  getFinancials, runResearchAgent, getResearch, runPromoterAnalysis,
  getPromoters, detectEarlyWarning, getRiskFlags, calculateRiskScore,
  getRiskScore, updateDueDiligence, downloadCAMReport,
  runAgentPipeline, runSingleAgent, getDocuments, approveClassification,
  getDefaultSchemas, setExtractionSchema, generateSWOT, getSWOT,
} from '../services/api';
import {
  Upload, FileText, Brain, Search, Users, AlertTriangle,
  BarChart3, FileDown, CheckCircle, XCircle, Loader2,
  ChevronDown, ChevronUp, Shield, TrendingUp, TrendingDown,
  ClipboardList, BookOpen, Bot, Zap, PlayCircle, Activity,
  Check, X, Edit3, Settings, Target,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, RadarChart,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from 'recharts';

const COLORS = ['#102a43', '#243b53', '#2563eb', '#3b82f6', '#60a5fa'];

const DOC_TYPE_OPTIONS = [
  { value: 'annual_report', label: 'Annual Report (P&L, Cashflow, Balance Sheet)' },
  { value: 'alm', label: 'ALM (Asset-Liability Management)' },
  { value: 'shareholding_pattern', label: 'Shareholding Pattern' },
  { value: 'borrowing_profile', label: 'Borrowing Profile' },
  { value: 'portfolio_performance', label: 'Portfolio Cuts / Performance Data' },
  { value: 'gst_return', label: 'GST Returns' },
  { value: 'cibil_report', label: 'CIBIL / Credit Report' },
  { value: 'financial_statement', label: 'Financial Statement' },
  { value: 'bank_statement', label: 'Bank Statement' },
  { value: 'itr_form', label: 'ITR Form' },
  { value: 'mca_filing', label: 'MCA Filing' },
  { value: 'other', label: 'Other' },
];

export default function DashboardPage() {
  const { id } = useParams();
  const [company, setCompany] = useState(null);
  const [summary, setSummary] = useState(null);
  const [financials, setFinancials] = useState([]);
  const [research, setResearch] = useState([]);
  const [promoters, setPromoters] = useState([]);
  const [riskFlags, setRiskFlags] = useState([]);
  const [riskScore, setRiskScore] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [swotData, setSwotData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [actionLoading, setActionLoading] = useState({});
  const [dueDiligenceNotes, setDueDiligenceNotes] = useState('');
  const [agentResults, setAgentResults] = useState(null);
  const [agentLogs, setAgentLogs] = useState([]);

  const loadData = useCallback(async () => {
    try {
      const [companyRes, summaryRes] = await Promise.all([
        getCompany(id), getDashboardSummary(id),
      ]);
      setCompany(companyRes.data);
      setSummary(summaryRes.data);

      const [finRes, researchRes, promoterRes, flagsRes, scoreRes, docsRes, swotRes] = await Promise.allSettled([
        getFinancials(id), getResearch(id), getPromoters(id),
        getRiskFlags(id), getRiskScore(id), getDocuments(id), getSWOT(id),
      ]);

      if (finRes.status === 'fulfilled' && finRes.value?.data) setFinancials(finRes.value.data);
      if (researchRes.status === 'fulfilled' && researchRes.value?.data) setResearch(researchRes.value.data);
      if (promoterRes.status === 'fulfilled' && promoterRes.value?.data) setPromoters(promoterRes.value.data);
      if (flagsRes.status === 'fulfilled' && flagsRes.value?.data) setRiskFlags(flagsRes.value.data);
      if (scoreRes.status === 'fulfilled' && scoreRes.value?.data) {
        setRiskScore(scoreRes.value.data);
        if (scoreRes.value.data?.due_diligence_notes)
          setDueDiligenceNotes(scoreRes.value.data.due_diligence_notes);
      }
      if (docsRes.status === 'fulfilled' && docsRes.value?.data) setDocuments(docsRes.value.data);
      if (swotRes.status === 'fulfilled' && swotRes.value?.data?.length > 0)
        setSwotData(swotRes.value.data[0]);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { loadData(); }, [loadData]);

  const runAction = async (key, action) => {
    setActionLoading((prev) => ({ ...prev, [key]: true }));
    try {
      await action();
      await loadData();
    } catch (err) {
      console.error(`Action ${key} failed:`, err);
      alert(`${key} failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setActionLoading((prev) => ({ ...prev, [key]: false }));
    }
  };

  const handleDownloadCAM = async () => {
    setActionLoading((prev) => ({ ...prev, cam: true }));
    try {
      const res = await downloadCAMReport(id);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `CAM_${company?.name || 'report'}.docx`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('CAM generation failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setActionLoading((prev) => ({ ...prev, cam: false }));
    }
  };

  const handleRunAllAgents = async () => {
    await runAction('agents', async () => {
      const res = await runAgentPipeline(id);
      setAgentResults(res.data?.data || null);
      setAgentLogs(res.data?.data?.agent_logs || []);
    });
  };

  const handleRunSingleAgent = async (agentName) => {
    await runAction(`agent_${agentName}`, async () => {
      const res = await runSingleAgent(id, agentName);
      const data = res.data?.data || {};
      setAgentLogs((prev) => [...prev, ...(data.agent_logs || [])]);
      setAgentResults((prev) => prev ? { ...prev, ...data } : data);
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="h-12 w-12 text-blue-600 animate-spin" />
      </div>
    );
  }

  if (!company) {
    return <div className="text-center py-16 text-navy-500">Company not found.</div>;
  }

  const tabs = [
    { key: 'overview', label: 'Overview', icon: BarChart3 },
    { key: 'agents', label: 'AI Agents', icon: Bot },
    { key: 'documents', label: 'Documents', icon: FileText },
    { key: 'financials', label: 'Financials', icon: TrendingUp },
    { key: 'research', label: 'Research', icon: Search },
    { key: 'promoters', label: 'Promoters', icon: Users },
    { key: 'warnings', label: 'Warnings', icon: AlertTriangle },
    { key: 'swot', label: 'SWOT', icon: Target },
    { key: 'risk', label: 'Risk Score', icon: Shield },
    { key: 'report', label: 'CAM Report', icon: FileDown },
  ];

  return (
    <div>
      {/* Company Header */}
      <div className="bg-white rounded-xl shadow-sm border border-navy-100 p-6 mb-6 max-w-[90rem] mx-auto mt-8 px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-navy-900">{company.name}</h1>
            <p className="text-navy-500 mt-1 text-base">
              {company.industry || 'Industry N/A'} •
              {company.loan_type ? ` ${company.loan_type} •` : ''}
              {' '}Loan: {company.loan_amount_requested
                ? `₹${Number(company.loan_amount_requested).toLocaleString()}`
                : 'TBD'}
              {company.loan_tenure_months ? ` • ${company.loan_tenure_months}mo` : ''}
            </p>
          </div>
          {riskScore && (
            <div className={`text-center px-6 py-3 rounded-lg ${
              riskScore.decision === 'approve' ? 'bg-green-100 text-green-800' :
              riskScore.decision === 'approve_with_conditions' ? 'bg-amber-100 text-amber-800' :
              'bg-red-100 text-red-800'
            }`}>
              <p className="text-sm font-medium uppercase">Decision</p>
              <p className="text-xl font-bold">
                {riskScore.decision?.replace(/_/g, ' ').toUpperCase() || 'Pending'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 bg-white rounded-xl shadow-sm border border-navy-100 p-1 mb-6 overflow-x-auto max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center space-x-1.5 px-5 py-3 rounded-lg text-base font-medium transition whitespace-nowrap ${
                activeTab === tab.key
                  ? 'bg-blue-600 text-white'
                  : 'text-navy-600 hover:bg-blue-50'
              }`}
            >
              <Icon className="h-5 w-5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 pb-12">
      {activeTab === 'overview' && <OverviewTab summary={summary} riskScore={riskScore} financials={financials} company={company} />}
      {activeTab === 'agents' && (
        <AgentsTab agentResults={agentResults} agentLogs={agentLogs} onRunAll={handleRunAllAgents}
          onRunSingle={handleRunSingleAgent} loadingAll={actionLoading.agents} loadingSingle={actionLoading} />
      )}
      {activeTab === 'documents' && (
        <DocumentsTab companyId={id} documents={documents} onRefresh={loadData}
          actionLoading={actionLoading} setActionLoading={setActionLoading} />
      )}
      {activeTab === 'financials' && (
        <FinancialsTab financials={financials}
          onExtract={() => runAction('extract', () => extractFinancialData(id))} loading={actionLoading.extract} />
      )}
      {activeTab === 'research' && (
        <ResearchTab research={research}
          onRun={() => runAction('research', () => runResearchAgent(id))} loading={actionLoading.research} />
      )}
      {activeTab === 'promoters' && (
        <PromoterTab promoters={promoters}
          onRun={() => runAction('promoter', () => runPromoterAnalysis(id))} loading={actionLoading.promoter} />
      )}
      {activeTab === 'warnings' && (
        <WarningsTab flags={riskFlags}
          onDetect={() => runAction('warning', () => detectEarlyWarning(id))} loading={actionLoading.warning} />
      )}
      {activeTab === 'swot' && (
        <SWOTTab swotData={swotData}
          onGenerate={() => runAction('swot', () => generateSWOT(id))} loading={actionLoading.swot} />
      )}
      {activeTab === 'risk' && (
        <RiskTab riskScore={riskScore}
          onCalculate={() => runAction('risk', () => calculateRiskScore(id))} loading={actionLoading.risk}
          dueDiligenceNotes={dueDiligenceNotes}
          onSaveNotes={(notes) => runAction('notes', () => updateDueDiligence(id, notes))}
          setDueDiligenceNotes={setDueDiligenceNotes} />
      )}
      {activeTab === 'report' && (
        <ReportTab onDownload={handleDownloadCAM} loading={actionLoading.cam} summary={summary} swotData={swotData} />
      )}
      </div>
    </div>
  );
}

// ─── AI Agents Tab ───
const AGENT_DEFINITIONS = [
  { key: 'documents', name: 'Document Agent', icon: FileText, color: 'blue', description: 'Verifies document completeness and quality for credit appraisal' },
  { key: 'financials', name: 'Financial Agent', icon: TrendingUp, color: 'emerald', description: 'Analyzes financial health using Ind-AS, ratios, and Tandon Committee norms' },
  { key: 'research', name: 'Research Agent', icon: Search, color: 'purple', description: 'Synthesizes web intelligence — NCLT, SEBI, RBI, media, fraud signals' },
  { key: 'promoters', name: 'Promoter Agent', icon: Users, color: 'amber', description: 'Verifies promoter backgrounds — bankruptcies, fraud, regulatory actions' },
  { key: 'warnings', name: 'Warning Agent', icon: AlertTriangle, color: 'orange', description: 'Detects early warning signals using RBI IRAC norms (SMA classification)' },
  { key: 'risk', name: 'Risk Verdict Agent', icon: Shield, color: 'red', description: 'Delivers final credit verdict using Five Cs framework' },
];

function AgentsTab({ agentResults, agentLogs, onRunAll, onRunSingle, loadingAll, loadingSingle }) {
  const getAgentLog = (agentKey) => {
    const map = { documents: 'DocumentAgent', financials: 'FinancialAgent', research: 'ResearchAgent',
      promoters: 'PromoterAgent', warnings: 'WarningAgent', risk: 'RiskVerdictAgent' };
    return agentLogs.filter((l) => l.agent === map[agentKey]);
  };
  const getAgentSummary = (agentKey) => {
    if (!agentResults) return null;
    const map = { documents: agentResults.document_summary, financials: agentResults.financial_summary,
      research: agentResults.research_summary, promoters: agentResults.promoter_summary,
      warnings: agentResults.warning_summary, risk: agentResults.risk_summary };
    return map[agentKey];
  };
  const colorMap = { blue: 'border-blue-500 bg-blue-50', emerald: 'border-emerald-500 bg-emerald-50',
    purple: 'border-purple-500 bg-purple-50', amber: 'border-amber-500 bg-amber-50',
    orange: 'border-orange-500 bg-orange-50', red: 'border-red-500 bg-red-50' };
  const iconColorMap = { blue: 'text-blue-600', emerald: 'text-emerald-600', purple: 'text-purple-600',
    amber: 'text-amber-600', orange: 'text-orange-600', red: 'text-red-600' };

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-navy-900 via-navy-800 to-navy-900 rounded-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-xl font-bold flex items-center"><Bot className="h-6 w-6 mr-2" /> LangGraph Agent Pipeline</h3>
            <p className="text-navy-200 mt-1 text-sm">6 specialized AI agents powered by OpenAI + LangChain verify and analyze every aspect of the credit application</p>
          </div>
          <button onClick={onRunAll} disabled={loadingAll}
            className="flex items-center space-x-2 px-6 py-3 bg-white text-navy-900 rounded-lg hover:bg-navy-50 disabled:opacity-50 transition font-semibold">
            {loadingAll ? <Loader2 className="h-5 w-5 animate-spin" /> : <Zap className="h-5 w-5" />}
            <span>{loadingAll ? 'Running Pipeline...' : 'Run All Agents'}</span>
          </button>
        </div>
        {agentLogs.length > 0 && (
          <div className="mt-4 flex items-center space-x-1">
            {AGENT_DEFINITIONS.map((agent, idx) => {
              const logs = getAgentLog(agent.key);
              const done = logs.length > 0 && logs[logs.length - 1].status === 'complete';
              const errored = logs.length > 0 && logs[logs.length - 1].status === 'error';
              return (
                <React.Fragment key={agent.key}>
                  <div className={`flex items-center space-x-1 px-2 py-1 rounded text-xs font-medium ${
                    done ? 'bg-green-500/20 text-green-200' : errored ? 'bg-red-500/20 text-red-200' : 'bg-white/10 text-white/50'
                  }`}>
                    {done ? <CheckCircle className="h-3 w-3" /> : errored ? <XCircle className="h-3 w-3" /> : <Activity className="h-3 w-3" />}
                    <span>{agent.name.split(' ')[0]}</span>
                  </div>
                  {idx < AGENT_DEFINITIONS.length - 1 && <div className={`w-4 h-0.5 ${done ? 'bg-green-400' : 'bg-white/20'}`} />}
                </React.Fragment>
              );
            })}
          </div>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {AGENT_DEFINITIONS.map((agent) => {
          const Icon = agent.icon;
          const logs = getAgentLog(agent.key);
          const summary = getAgentSummary(agent.key);
          const lastLog = logs.length > 0 ? logs[logs.length - 1] : null;
          const isRunning = loadingSingle[`agent_${agent.key}`];
          return (
            <div key={agent.key} className={`rounded-xl border-l-4 p-5 bg-white shadow-sm ${colorMap[agent.color]} transition hover:shadow-md`}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Icon className={`h-5 w-5 ${iconColorMap[agent.color]}`} />
                  <h4 className="font-semibold text-gray-900">{agent.name}</h4>
                </div>
                {lastLog && (
                  <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                    lastLog.status === 'complete' ? 'bg-green-100 text-green-700' : lastLog.status === 'error' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                  }`}>{lastLog.status === 'complete' ? 'Done' : lastLog.status === 'error' ? 'Error' : 'Pending'}</span>
                )}
              </div>
              <p className="text-xs text-gray-500 mb-3">{agent.description}</p>
              {lastLog && <div className="bg-gray-50 rounded-lg p-2 mb-3 text-xs text-gray-600">{lastLog.message}</div>}
              {summary && summary.overall_assessment && (
                <div className="bg-white border rounded-lg p-2 mb-3 text-xs text-gray-700 max-h-24 overflow-y-auto">{summary.overall_assessment}</div>
              )}
              <button onClick={() => onRunSingle(agent.key)} disabled={isRunning || loadingAll}
                className={`w-full flex items-center justify-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium transition ${
                  isRunning || loadingAll ? 'bg-gray-100 text-gray-400' : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}>
                {isRunning ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <PlayCircle className="h-3.5 w-3.5" />}
                <span>{isRunning ? 'Running...' : 'Run Agent'}</span>
              </button>
            </div>
          );
        })}
      </div>
      {agentLogs.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h4 className="font-semibold mb-4 flex items-center"><Activity className="h-5 w-5 mr-2 text-blue-600" /> Agent Execution Log</h4>
          <div className="space-y-3">
            {agentLogs.map((log, idx) => (
              <div key={idx} className="flex items-start space-x-3">
                <div className={`mt-1 h-2.5 w-2.5 rounded-full flex-shrink-0 ${
                  log.status === 'complete' ? 'bg-green-500' : log.status === 'error' ? 'bg-red-500' : 'bg-amber-500'
                }`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-900">{log.agent}</span>
                    <span className="text-xs text-gray-400">{log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ''}</span>
                  </div>
                  <p className="text-sm text-gray-600 truncate">{log.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      {agentResults?.risk_summary?.credit_verdict && (
        <div className={`rounded-xl p-6 ${
          agentResults.risk_summary.credit_verdict === 'approve' ? 'bg-green-50 border border-green-200' :
          agentResults.risk_summary.credit_verdict === 'approve_with_conditions' ? 'bg-amber-50 border border-amber-200' :
          'bg-red-50 border border-red-200'
        }`}>
          <h4 className="font-bold text-lg mb-2">Agent Verdict: {agentResults.risk_summary.credit_verdict.replace(/_/g, ' ').toUpperCase()}</h4>
          {agentResults.risk_summary.confidence_level != null && <p className="text-sm mb-2">Confidence: {agentResults.risk_summary.confidence_level}%</p>}
          {agentResults.risk_summary.key_strengths?.length > 0 && (
            <div className="mb-2"><p className="text-sm font-medium text-green-800">Strengths:</p>
              <ul className="list-disc list-inside text-sm text-gray-700">{agentResults.risk_summary.key_strengths.map((s, i) => <li key={i}>{s}</li>)}</ul></div>
          )}
          {agentResults.risk_summary.key_concerns?.length > 0 && (
            <div className="mb-2"><p className="text-sm font-medium text-red-800">Concerns:</p>
              <ul className="list-disc list-inside text-sm text-gray-700">{agentResults.risk_summary.key_concerns.map((c, i) => <li key={i}>{c}</li>)}</ul></div>
          )}
          {agentResults.risk_summary.reasoning_walkthrough && (
            <div className="mt-3 bg-white/60 rounded-lg p-4">
              <p className="text-xs font-medium text-gray-500 mb-1">AI Reasoning Walkthrough:</p>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{agentResults.risk_summary.reasoning_walkthrough}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Overview Tab ───
function OverviewTab({ summary, riskScore, financials, company }) {
  const fiveCsData = riskScore?.five_cs_evaluation
    ? Object.entries(riskScore.five_cs_evaluation).map(([key, val]) => ({
        subject: key.charAt(0).toUpperCase() + key.slice(1), score: val.score, fullMark: val.max,
      })) : [];
  return (
    <div className="space-y-6">
      {/* Company Quick Info */}
      <div className="bg-white rounded-xl shadow-sm border p-8">
        <h3 className="text-xl font-semibold mb-5">Entity Details</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-x-8 gap-y-5 text-base">
          <div><span className="text-gray-500">PAN:</span> <span className="font-medium ml-1">{company.pan || 'N/A'}</span></div>
          <div><span className="text-gray-500">CIN:</span> <span className="font-medium ml-1">{company.cin || 'N/A'}</span></div>
          <div><span className="text-gray-500">GST:</span> <span className="font-medium ml-1">{company.gst_number || 'N/A'}</span></div>
          <div><span className="text-gray-500">Turnover:</span> <span className="font-medium ml-1">{company.annual_turnover ? `₹${Number(company.annual_turnover).toLocaleString()}` : 'N/A'}</span></div>
          <div><span className="text-gray-500">Loan Type:</span> <span className="font-medium ml-1">{company.loan_type || 'N/A'}</span></div>
          <div><span className="text-gray-500">Tenure:</span> <span className="font-medium ml-1">{company.loan_tenure_months ? `${company.loan_tenure_months} months` : 'N/A'}</span></div>
          <div><span className="text-gray-500">Interest:</span> <span className="font-medium ml-1">{company.proposed_interest_rate ? `${company.proposed_interest_rate}%` : 'N/A'}</span></div>
          <div><span className="text-gray-500">Purpose:</span> <span className="font-medium ml-1">{company.loan_purpose || 'N/A'}</span></div>
        </div>
      </div>
      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <QuickStat label="Documents" value={summary?.documents_count || 0} color="blue" />
        <QuickStat label="Risk Flags" value={summary?.risk_flags_count || 0} color="amber" />
        <QuickStat label="Research Items" value={summary?.research_findings_count || 0} color="purple" />
        <QuickStat label="Default Prob." value={riskScore ? `${(riskScore.probability_of_default * 100).toFixed(1)}%` : 'N/A'} color={riskScore?.probability_of_default > 0.35 ? 'red' : 'green'} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {fiveCsData.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-4">Five Cs Evaluation</h3>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={fiveCsData}>
                <PolarGrid /><PolarAngleAxis dataKey="subject" /><PolarRadiusAxis angle={30} domain={[0, 10]} />
                <Radar name="Score" dataKey="score" stroke="#2563eb" fill="#2563eb" fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}
        {riskScore?.feature_importance && (
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-4">Risk Factor Importance</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={Object.entries(riskScore.feature_importance).slice(0, 8).map(([k, v]) => ({ name: k.replace(/_/g, ' '), value: v }))} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" /><XAxis type="number" /><YAxis dataKey="name" type="category" width={120} fontSize={12} />
                <Tooltip /><Bar dataKey="value" fill="#2563eb" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
      {financials.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold mb-4">Key Financial Metrics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard label="Revenue" value={financials[0].revenue} prefix="₹" />
            <MetricCard label="Net Profit" value={financials[0].net_profit} prefix="₹" />
            <MetricCard label="Debt Ratio" value={financials[0].debt_ratio} format="pct" />
            <MetricCard label="Current Ratio" value={financials[0].current_ratio} format="ratio" />
          </div>
        </div>
      )}
    </div>
  );
}

function QuickStat({ label, value, color }) {
  const colorMap = { blue: 'bg-blue-50 text-blue-700', amber: 'bg-amber-50 text-amber-700',
    purple: 'bg-purple-50 text-purple-700', green: 'bg-green-50 text-green-700', red: 'bg-red-50 text-red-700' };
  return (
    <div className={`${colorMap[color]} rounded-xl p-5 text-center`}>
      <p className="text-3xl font-bold">{value}</p><p className="text-base mt-1">{label}</p>
    </div>
  );
}

function MetricCard({ label, value, prefix = '', format }) {
  let display = 'N/A';
  if (value != null) {
    if (format === 'pct') display = `${(value * 100).toFixed(1)}%`;
    else if (format === 'ratio') display = value.toFixed(2);
    else display = `${prefix}${Number(value).toLocaleString()}`;
  }
  return (
    <div className="bg-gray-50 rounded-lg p-4 text-center">
      <p className="text-xl font-bold text-gray-900">{display}</p><p className="text-sm text-gray-500">{label}</p>
    </div>
  );
}

// ─── Enhanced Documents Tab with 5 types, Classification, Schema ───
function DocumentsTab({ companyId, documents, onRefresh, actionLoading, setActionLoading }) {
  const [selectedType, setSelectedType] = useState('other');
  const [uploading, setUploading] = useState(false);
  const [editingDoc, setEditingDoc] = useState(null);
  const [correctedType, setCorrectedType] = useState('');

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    setUploading(true);
    try {
      await uploadDocuments(companyId, selectedType, files);
      await onRefresh();
    } catch (err) {
      alert('Upload failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
    }
  };

  const handleApprove = async (docId) => {
    try {
      await approveClassification(docId, true);
      await onRefresh();
    } catch (err) {
      alert('Approval failed');
    }
  };

  const handleCorrect = async (docId) => {
    if (!correctedType) return;
    try {
      await approveClassification(docId, true, correctedType);
      setEditingDoc(null);
      setCorrectedType('');
      await onRefresh();
    } catch (err) {
      alert('Correction failed');
    }
  };

  const requiredTypes = [
    { type: 'alm', label: 'ALM', desc: 'Asset-Liability Management' },
    { type: 'shareholding_pattern', label: 'Shareholding', desc: 'Shareholding Pattern' },
    { type: 'borrowing_profile', label: 'Borrowing', desc: 'Borrowing Profile' },
    { type: 'annual_report', label: 'Annual Report', desc: 'P&L, Cashflow, Balance Sheet' },
    { type: 'portfolio_performance', label: 'Portfolio', desc: 'Performance Data' },
  ];

  const uploadedTypes = documents.map(d => d.document_type);

  return (
    <div className="space-y-6">
      {/* Required Documents Checklist */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <h3 className="text-lg font-semibold mb-4">Required Documents Checklist</h3>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
          {requiredTypes.map((rt) => {
            const uploaded = uploadedTypes.includes(rt.type);
            return (
              <div key={rt.type} className={`rounded-lg p-3 border-2 text-center ${
                uploaded ? 'border-green-400 bg-green-50' : 'border-dashed border-gray-300 bg-gray-50'
              }`}>
                {uploaded ? <CheckCircle className="h-6 w-6 text-green-500 mx-auto mb-1" /> : <Upload className="h-6 w-6 text-gray-400 mx-auto mb-1" />}
                <p className={`text-sm font-medium ${uploaded ? 'text-green-700' : 'text-gray-600'}`}>{rt.label}</p>
                <p className="text-xs text-gray-400">{rt.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Upload Documents</h3>
          <span className="text-sm text-gray-500">{documents.filter(d => d.processing_status === 'processed').length} / {documents.length} processed</span>
        </div>
        <div className="flex items-center space-x-4 mb-4">
          <label className="text-sm font-medium text-gray-700">Document Type:</label>
          <select value={selectedType} onChange={(e) => setSelectedType(e.target.value)}
            className="rounded-lg border-gray-300 border px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500">
            {DOC_TYPE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-400 transition">
          <Upload className="h-10 w-10 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600 mb-2">Drag & drop or click to upload documents</p>
          <p className="text-sm text-gray-400 mb-4">Supports: PDF, PNG, JPG — Annual Reports, ALM, Shareholding, Borrowing Profile, Portfolio Data</p>
          <label className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer transition">
            {uploading ? <Loader2 className="h-5 w-5 animate-spin mr-2" /> : <Upload className="h-5 w-5 mr-2" />}
            <span>{uploading ? 'Uploading...' : 'Select Files'}</span>
            <input type="file" multiple accept=".pdf,.png,.jpg,.jpeg" onChange={handleFileUpload} className="hidden" disabled={uploading} />
          </label>
        </div>
      </div>

      {/* Document List with Classification Approval */}
      {documents.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold mb-4">Uploaded Documents — Classification Review</h3>
          <div className="space-y-3">
            {documents.map((doc) => (
              <div key={doc.id} className={`rounded-lg border p-4 ${doc.classification_approved ? 'border-green-200 bg-green-50/30' : 'border-amber-200 bg-amber-50/30'}`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <FileText className="h-4 w-4 text-gray-500" />
                      <span className="font-medium text-gray-900 text-sm">{doc.original_filename}</span>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${
                        doc.processing_status === 'processed' ? 'bg-green-100 text-green-700' : doc.processing_status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                      }`}>{doc.processing_status}</span>
                    </div>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>Auto-classified: <strong className="text-gray-700">{doc.detected_doc_type || doc.document_type}</strong></span>
                      {doc.user_corrected_type && <span>User corrected: <strong className="text-blue-700">{doc.user_corrected_type}</strong></span>}
                      {doc.confidence_score != null && <span>Confidence: {(doc.confidence_score * 100).toFixed(0)}%</span>}
                      {doc.ocr_used && <span className="text-amber-600">OCR Used</span>}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {doc.classification_approved ? (
                      <span className="flex items-center text-green-600 text-xs font-medium"><CheckCircle className="h-4 w-4 mr-1" />Approved</span>
                    ) : (
                      <>
                        <button onClick={() => handleApprove(doc.id)} className="flex items-center px-3 py-1.5 bg-green-600 text-white rounded-lg text-xs hover:bg-green-700 transition">
                          <Check className="h-3 w-3 mr-1" />Approve
                        </button>
                        <button onClick={() => { setEditingDoc(doc.id); setCorrectedType(doc.document_type); }}
                          className="flex items-center px-3 py-1.5 bg-amber-600 text-white rounded-lg text-xs hover:bg-amber-700 transition">
                          <Edit3 className="h-3 w-3 mr-1" />Edit Type
                        </button>
                      </>
                    )}
                  </div>
                </div>
                {editingDoc === doc.id && (
                  <div className="mt-3 flex items-center space-x-3 p-3 bg-white rounded-lg border">
                    <select value={correctedType} onChange={(e) => setCorrectedType(e.target.value)}
                      className="rounded-lg border-gray-300 border px-3 py-1.5 text-sm flex-1">
                      {DOC_TYPE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
                    <button onClick={() => handleCorrect(doc.id)} className="px-4 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">Save</button>
                    <button onClick={() => setEditingDoc(null)} className="px-4 py-1.5 bg-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-300">Cancel</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Financials Tab ───
function FinancialsTab({ financials, onExtract, loading }) {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Financial Metrics</h3>
        <ActionButton onClick={onExtract} loading={loading} icon={Brain} label="Extract with AI" />
      </div>
      {financials.length === 0 ? (
        <EmptyState message="No financial data extracted yet. Upload documents and click 'Extract with AI'." />
      ) : (
        financials.map((metric, idx) => (
          <div key={metric.id || idx} className="bg-white rounded-xl shadow-sm border p-6">
            <h4 className="font-medium text-gray-700 mb-4">Fiscal Year: {metric.fiscal_year || 'N/A'}</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard label="Revenue" value={metric.revenue} prefix="₹" />
              <MetricCard label="Net Profit" value={metric.net_profit} prefix="₹" />
              <MetricCard label="Total Assets" value={metric.total_assets} prefix="₹" />
              <MetricCard label="Total Debt" value={metric.total_debt} prefix="₹" />
              <MetricCard label="Debt Ratio" value={metric.debt_ratio} format="pct" />
              <MetricCard label="Current Ratio" value={metric.current_ratio} format="ratio" />
              <MetricCard label="Interest Coverage" value={metric.interest_coverage} format="ratio" />
              <MetricCard label="Profit Margin" value={metric.profit_margin} format="pct" />
            </div>
            {metric.director_names?.length > 0 && (
              <div className="mt-4"><p className="text-sm text-gray-600"><strong>Directors:</strong> {metric.director_names.join(', ')}</p></div>
            )}
          </div>
        ))
      )}
    </div>
  );
}

// ─── Research Tab ───
function ResearchTab({ research, onRun, loading }) {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Research Intelligence</h3>
        <ActionButton onClick={onRun} loading={loading} icon={Search} label="Run Research Agent" />
      </div>
      {research.length === 0 ? (
        <EmptyState message="No research findings yet. Click 'Run Research Agent' to gather web intelligence." />
      ) : (
        research.map((finding, idx) => (
          <div key={finding.id || idx} className="bg-white rounded-xl shadow-sm border p-5">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center space-x-2 mb-1">
                  <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${
                    finding.sentiment === 'positive' ? 'bg-green-100 text-green-700' :
                    finding.sentiment === 'negative' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                  }`}>{finding.sentiment || 'neutral'}</span>
                  <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700">{finding.category}</span>
                </div>
                <h4 className="font-medium text-gray-900">{finding.title}</h4>
              </div>
            </div>
            <p className="text-sm text-gray-600 mt-2">{finding.summary}</p>
            {finding.source_url && <a href={finding.source_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline mt-2 block">View Source</a>}
          </div>
        ))
      )}
    </div>
  );
}

// ─── Promoter Tab ───
function PromoterTab({ promoters, onRun, loading }) {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Promoter Risk Analysis</h3>
        <ActionButton onClick={onRun} loading={loading} icon={Users} label="Analyze Promoters" />
      </div>
      {promoters.length === 0 ? (
        <EmptyState message="No promoter analysis yet. Extract financials first, then click 'Analyze Promoters'." />
      ) : (
        promoters.map((p, idx) => (
          <div key={p.id || idx} className="bg-white rounded-xl shadow-sm border p-6">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-lg font-medium">{p.promoter_name}</h4>
              <span className={`px-3 py-1 text-sm font-medium rounded-full ${
                p.risk_level === 'low' ? 'bg-green-100 text-green-700' :
                p.risk_level === 'medium' ? 'bg-amber-100 text-amber-700' :
                p.risk_level === 'high' ? 'bg-red-100 text-red-700' : 'bg-red-200 text-red-800'
              }`}>{p.risk_level?.toUpperCase()} RISK</span>
            </div>
            <p className="text-sm text-gray-500 mb-3">{p.designation || 'Role unknown'}</p>
            <div className="flex space-x-4 mb-3">
              <FlagBadge label="Bankruptcy" active={p.bankruptcy_flag} />
              <FlagBadge label="Fraud" active={p.fraud_flag} />
              <FlagBadge label="Regulatory" active={p.regulatory_violation_flag} />
            </div>
            {p.background_summary && <p className="text-sm text-gray-600">{p.background_summary}</p>}
            {p.risk_summary && <p className="text-sm text-gray-700 mt-2 font-medium">Risk: {p.risk_summary}</p>}
          </div>
        ))
      )}
    </div>
  );
}

function FlagBadge({ label, active }) {
  return (
    <span className={`flex items-center space-x-1 text-xs ${active ? 'text-red-600' : 'text-green-600'}`}>
      {active ? <XCircle className="h-3.5 w-3.5" /> : <CheckCircle className="h-3.5 w-3.5" />}<span>{label}</span>
    </span>
  );
}

// ─── Warnings Tab ───
function WarningsTab({ flags, onDetect, loading }) {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Early Warning Signals</h3>
        <ActionButton onClick={onDetect} loading={loading} icon={AlertTriangle} label="Detect Warnings" />
      </div>
      {flags.length === 0 ? (
        <EmptyState message="No risk flags detected. Extract financials first to run validation." />
      ) : (
        flags.map((flag, idx) => (
          <div key={flag.id || idx} className={`rounded-xl border-l-4 p-5 bg-white shadow-sm ${
            flag.severity === 'critical' ? 'border-l-red-600' : flag.severity === 'high' ? 'border-l-orange-500' :
            flag.severity === 'medium' ? 'border-l-amber-400' : 'border-l-blue-400'
          }`}>
            <div className="flex items-center space-x-2 mb-1">
              <span className={`px-2 py-0.5 text-xs font-bold rounded ${
                flag.severity === 'critical' ? 'bg-red-100 text-red-700' : flag.severity === 'high' ? 'bg-orange-100 text-orange-700' :
                flag.severity === 'medium' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'
              }`}>{flag.severity?.toUpperCase()}</span>
              <span className="text-xs text-gray-500">{flag.flag_type?.replace(/_/g, ' ')}</span>
            </div>
            <p className="text-sm text-gray-700">{flag.description}</p>
            {flag.discrepancy_pct != null && <p className="text-xs text-gray-500 mt-1">Discrepancy: {flag.discrepancy_pct}%</p>}
          </div>
        ))
      )}
    </div>
  );
}

// ─── SWOT Tab ───
function SWOTTab({ swotData, onGenerate, loading }) {
  const swotSections = swotData ? [
    { title: 'Strengths', items: swotData.strengths || [], color: 'green', icon: TrendingUp },
    { title: 'Weaknesses', items: swotData.weaknesses || [], color: 'red', icon: TrendingDown },
    { title: 'Opportunities', items: swotData.opportunities || [], color: 'blue', icon: Target },
    { title: 'Threats', items: swotData.threats || [], color: 'orange', icon: AlertTriangle },
  ] : [];

  const colorMap = {
    green: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700', icon: 'text-green-600', bullet: 'bg-green-500' },
    red: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-700', icon: 'text-red-600', bullet: 'bg-red-500' },
    blue: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700', icon: 'text-blue-600', bullet: 'bg-blue-500' },
    orange: { bg: 'bg-orange-50', border: 'border-orange-200', text: 'text-orange-700', icon: 'text-orange-600', bullet: 'bg-orange-500' },
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h3 className="text-lg font-semibold">SWOT Analysis</h3>
          <p className="text-sm text-gray-500 mt-0.5">AI-generated analysis triangulating financial data, research, promoter analysis, and risk flags</p>
        </div>
        <ActionButton onClick={onGenerate} loading={loading} icon={Target} label="Generate SWOT" />
      </div>

      {!swotData ? (
        <EmptyState message="No SWOT analysis generated yet. Ensure data is extracted and research is run, then click 'Generate SWOT'." />
      ) : (
        <>
          {swotData.summary && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h4 className="font-semibold text-gray-900 mb-2">Executive Summary</h4>
              <p className="text-sm text-gray-700">{swotData.summary}</p>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {swotSections.map((section) => {
              const Icon = section.icon;
              const c = colorMap[section.color];
              return (
                <div key={section.title} className={`rounded-xl border ${c.border} ${c.bg} p-6`}>
                  <h4 className={`font-semibold ${c.text} mb-4 flex items-center`}>
                    <Icon className={`h-5 w-5 mr-2 ${c.icon}`} />{section.title}
                  </h4>
                  {section.items.length > 0 ? (
                    <ul className="space-y-2">
                      {section.items.map((item, i) => (
                        <li key={i} className="flex items-start">
                          <div className={`h-2 w-2 rounded-full ${c.bullet} mt-1.5 mr-3 flex-shrink-0`} />
                          <span className="text-sm text-gray-700">{item}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-gray-400 italic">No items identified</p>
                  )}
                </div>
              );
            })}
          </div>
          {swotData.data_sources && (
            <div className="bg-white rounded-xl shadow-sm border p-4">
              <p className="text-xs text-gray-500">
                <strong>Data Sources:</strong>{' '}
                {Object.entries(swotData.data_sources).map(([k, v]) => `${k.replace(/_/g, ' ')}: ${v}`).join(' • ')}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ─── Risk Tab ───
function RiskTab({ riskScore, onCalculate, loading, dueDiligenceNotes, onSaveNotes, setDueDiligenceNotes }) {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Credit Risk Assessment</h3>
        <ActionButton onClick={onCalculate} loading={loading} icon={BarChart3} label="Calculate Risk Score" />
      </div>
      {!riskScore ? (
        <EmptyState message="No risk score calculated. Ensure financials are extracted first." />
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white rounded-xl shadow-sm border p-6 text-center">
              <p className="text-sm text-gray-500 mb-2">Probability of Default</p>
              <p className={`text-4xl font-bold ${
                riskScore.probability_of_default < 0.15 ? 'text-green-600' :
                riskScore.probability_of_default < 0.35 ? 'text-amber-600' : 'text-red-600'
              }`}>{(riskScore.probability_of_default * 100).toFixed(1)}%</p>
              <p className={`mt-2 text-sm font-medium uppercase ${
                riskScore.risk_level === 'low' ? 'text-green-600' : riskScore.risk_level === 'medium' ? 'text-amber-600' : 'text-red-600'
              }`}>{riskScore.risk_level} Risk</p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border p-6 text-center">
              <p className="text-sm text-gray-500 mb-2">Loan Decision</p>
              <p className={`text-xl font-bold ${
                riskScore.decision === 'approve' ? 'text-green-600' : riskScore.decision === 'approve_with_conditions' ? 'text-amber-600' : 'text-red-600'
              }`}>{riskScore.decision?.replace(/_/g, ' ').toUpperCase()}</p>
              {riskScore.recommended_loan_limit > 0 && <p className="text-sm text-gray-500 mt-2">Limit: ₹{Number(riskScore.recommended_loan_limit).toLocaleString()}</p>}
            </div>
            <div className="bg-white rounded-xl shadow-sm border p-6 text-center">
              <p className="text-sm text-gray-500 mb-2">Suggested Interest Rate</p>
              <p className="text-4xl font-bold text-blue-600">{riskScore.suggested_interest_rate ? `${riskScore.suggested_interest_rate}%` : 'N/A'}</p>
              <p className="text-sm text-gray-500 mt-2">Per Annum</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {riskScore.positive_factors?.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h4 className="font-semibold text-green-700 mb-3 flex items-center"><TrendingUp className="h-5 w-5 mr-2" /> Positive Factors</h4>
                <ul className="space-y-2">{riskScore.positive_factors.map((f, i) => (
                  <li key={i} className="text-sm text-gray-700 flex items-start"><CheckCircle className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />{f}</li>
                ))}</ul>
              </div>
            )}
            {riskScore.negative_factors?.length > 0 && (
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h4 className="font-semibold text-red-700 mb-3 flex items-center"><TrendingDown className="h-5 w-5 mr-2" /> Negative Factors</h4>
                <ul className="space-y-2">{riskScore.negative_factors.map((f, i) => (
                  <li key={i} className="text-sm text-gray-700 flex items-start"><XCircle className="h-4 w-4 text-red-500 mr-2 mt-0.5 flex-shrink-0" />{f}</li>
                ))}</ul>
              </div>
            )}
          </div>

          {riskScore.five_cs_evaluation && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h4 className="font-semibold mb-4 flex items-center"><Shield className="h-5 w-5 mr-2 text-blue-600" /> Five Cs Credit Evaluation</h4>
              <div className="space-y-4">
                {['character', 'capacity', 'capital', 'collateral', 'conditions'].map((cs) => {
                  const data = riskScore.five_cs_evaluation[cs];
                  if (!data) return null;
                  const pct = ((data.score / (data.max || 10)) * 100).toFixed(0);
                  return (
                    <div key={cs} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-gray-800 capitalize">{cs}</span>
                        <span className={`text-sm font-bold ${pct >= 70 ? 'text-green-600' : pct >= 40 ? 'text-amber-600' : 'text-red-600'}`}>{data.score}/{data.max || 10}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                        <div className={`h-2 rounded-full ${pct >= 70 ? 'bg-green-500' : pct >= 40 ? 'bg-amber-500' : 'bg-red-500'}`} style={{ width: `${pct}%` }} />
                      </div>
                      <p className="text-sm text-gray-600 mb-1">{data.assessment}</p>
                      {data.reasoning?.length > 0 && (
                        <ul className="mt-2 space-y-1">{data.reasoning.map((r, i) => (
                          <li key={i} className="text-xs text-gray-500 flex items-start"><span className="mr-1.5 mt-0.5 text-blue-400">•</span>{r}</li>
                        ))}</ul>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {riskScore.reasoning_narrative && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h4 className="font-semibold mb-3 flex items-center"><BookOpen className="h-5 w-5 mr-2 text-blue-600" /> AI Reasoning Narrative</h4>
              <p className="text-xs text-gray-400 mb-4">Step-by-step walkthrough of the credit decision logic</p>
              <div className="prose prose-sm max-w-none text-gray-700">
                {riskScore.reasoning_narrative.split('\n').map((line, i) => {
                  const trimmed = line.trim();
                  if (!trimmed) return <br key={i} />;
                  if (trimmed.startsWith('## ')) return <h3 key={i} className="text-base font-semibold text-gray-800 mt-4 mb-2">{trimmed.slice(3)}</h3>;
                  if (trimmed.startsWith('# ')) return <h2 key={i} className="text-lg font-bold text-gray-900 mt-4 mb-2">{trimmed.slice(2)}</h2>;
                  if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) return <li key={i} className="ml-4 text-sm">{trimmed.slice(2)}</li>;
                  if (trimmed.startsWith('**') && trimmed.endsWith('**')) return <p key={i} className="font-semibold text-sm">{trimmed.slice(2, -2)}</p>;
                  return <p key={i} className="text-sm mb-1">{trimmed}</p>;
                })}
              </div>
            </div>
          )}

          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h4 className="font-semibold mb-3 flex items-center"><ClipboardList className="h-5 w-5 mr-2" /> Due Diligence Notes</h4>
            <textarea value={dueDiligenceNotes} onChange={(e) => setDueDiligenceNotes(e.target.value)} rows={4}
              className="w-full rounded-lg border-gray-300 border px-4 py-2.5 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Enter your due diligence notes here..." />
            <button onClick={() => onSaveNotes(dueDiligenceNotes)} className="mt-3 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition text-sm">Save Notes</button>
          </div>
        </>
      )}
    </div>
  );
}

// ─── Report Tab ───
function ReportTab({ onDownload, loading, summary, swotData }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-8 text-center">
      <FileDown className="h-16 w-16 text-blue-600 mx-auto mb-4" />
      <h3 className="text-xl font-semibold mb-2">Credit Appraisal Memorandum</h3>
      <p className="text-gray-500 mb-6 max-w-lg mx-auto">
        Generate a comprehensive CAM report including company overview, financial summary,
        research intelligence, SWOT analysis, promoter analysis, risk score, and loan recommendation.
      </p>
      <div className="flex flex-wrap justify-center gap-3 mb-6">
        <ReportCheckItem label="Company Data" ready={true} />
        <ReportCheckItem label="Financials" ready={summary?.has_financials} />
        <ReportCheckItem label="Research" ready={summary?.research_findings_count > 0} />
        <ReportCheckItem label="SWOT Analysis" ready={!!swotData} />
        <ReportCheckItem label="Promoter Analysis" ready={summary?.promoters_analyzed > 0} />
        <ReportCheckItem label="Risk Score" ready={summary?.has_risk_score} />
      </div>
      <button onClick={onDownload} disabled={loading}
        className="inline-flex items-center px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition font-medium text-lg">
        {loading ? <Loader2 className="h-5 w-5 animate-spin mr-2" /> : <FileDown className="h-5 w-5 mr-2" />}
        <span>{loading ? 'Generating...' : 'Download CAM Report (.docx)'}</span>
      </button>
    </div>
  );
}

function ReportCheckItem({ label, ready }) {
  return (
    <span className={`flex items-center space-x-1 text-sm ${ready ? 'text-green-600' : 'text-gray-400'}`}>
      {ready ? <CheckCircle className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}<span>{label}</span>
    </span>
  );
}

// ─── Shared Components ───
function ActionButton({ onClick, loading, icon: Icon, label }) {
  return (
    <button onClick={onClick} disabled={loading}
      className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition text-sm font-medium">
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Icon className="h-4 w-4" />}<span>{loading ? 'Processing...' : label}</span>
    </button>
  );
}

function EmptyState({ message }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
      <FileText className="h-12 w-12 text-gray-300 mx-auto mb-3" /><p className="text-gray-500">{message}</p>
    </div>
  );
}
