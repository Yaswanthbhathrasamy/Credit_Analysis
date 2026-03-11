import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ─── Company APIs ───

export const createCompany = (data) => api.post('/companies', data);
export const getCompanies = () => api.get('/companies');
export const getCompany = (id) => api.get(`/companies/${id}`);

// ─── Document APIs ───

export const uploadDocuments = (companyId, documentType, files) => {
  const formData = new FormData();
  formData.append('company_id', companyId);
  formData.append('document_type', documentType);
  files.forEach((file) => formData.append('files', file));
  return api.post('/upload-documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

// ─── Financial Extraction ───

export const extractFinancialData = (companyId) =>
  api.post('/extract-financial-data', { company_id: companyId });

export const getFinancials = (companyId) =>
  api.get(`/companies/${companyId}/financials`);

// ─── Research Intelligence ───

export const runResearchAgent = (companyId) =>
  api.post('/run-research-agent', { company_id: companyId });

export const getResearch = (companyId) =>
  api.get(`/companies/${companyId}/research`);

// ─── CrewAI Research Intelligence ───

export const runCrewResearch = (companyId) =>
  api.post('/run-crew-research', { company_id: companyId });

// ─── Agent Orchestrator ───

export const runAgentPipeline = (companyId) =>
  api.post('/run-agent-pipeline', { company_id: companyId });

export const runSingleAgent = (companyId, agentName) =>
  api.post(`/run-single-agent?agent_name=${agentName}`, { company_id: companyId });

// ─── Promoter Analysis ───

export const runPromoterAnalysis = (companyId, promoterNames = []) =>
  api.post('/run-promoter-analysis', {
    company_id: companyId,
    promoter_names: promoterNames,
  });

export const getPromoters = (companyId) =>
  api.get(`/companies/${companyId}/promoters`);

// ─── Early Warning ───

export const detectEarlyWarning = (companyId) =>
  api.post('/detect-early-warning', { company_id: companyId });

export const getRiskFlags = (companyId) =>
  api.get(`/companies/${companyId}/risk-flags`);

// ─── Risk Score ───

export const calculateRiskScore = (companyId) =>
  api.post('/calculate-risk-score', { company_id: companyId });

export const getRiskScore = (companyId) =>
  api.get(`/companies/${companyId}/risk-score`);

// ─── Due Diligence ───

export const updateDueDiligence = (companyId, notes) =>
  api.post(`/companies/${companyId}/due-diligence`, {
    company_id: companyId,
    notes,
  });

// ─── CAM Report ───

export const downloadCAMReport = (companyId) =>
  api.get(`/generate-cam-report?company_id=${companyId}`, {
    responseType: 'blob',
  });

// ─── Dashboard Summary ───

export const getDashboardSummary = (companyId) =>
  api.get(`/companies/${companyId}/dashboard-summary`);

// ─── Document Management ───

export const getDocuments = (companyId) =>
  api.get(`/companies/${companyId}/documents`);

export const approveClassification = (documentId, approved, correctedType = null) =>
  api.post('/approve-classification', {
    document_id: documentId,
    approved,
    corrected_type: correctedType,
  });

export const setExtractionSchema = (documentId, schema) =>
  api.post('/set-extraction-schema', {
    document_id: documentId,
    schema,
  });

export const getDefaultSchemas = () =>
  api.get('/default-schemas');

// ─── SWOT Analysis ───

export const generateSWOT = (companyId) =>
  api.post('/generate-swot', { company_id: companyId });

export const getSWOT = (companyId) =>
  api.get(`/companies/${companyId}/swot`);

export default api;
