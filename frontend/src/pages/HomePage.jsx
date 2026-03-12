import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getCompanies } from '../services/api';
import {
  Building2, ArrowRight, AlertTriangle, CheckCircle,
  Clock, TrendingUp, Shield, BarChart3, FileSearch,
  Brain, Landmark, ChevronRight, Zap, Globe,
} from 'lucide-react';

export default function HomePage() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      const res = await getCompanies();
      setCompanies(res.data);
    } catch (err) {
      console.error('Failed to load companies:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Hero Section */}
      <section className="gradient-hero text-white py-20 px-4 relative overflow-hidden">
        {/* Decorative bg elements */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-24 -right-24 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-32 -left-32 w-80 h-80 bg-blue-400/10 rounded-full blur-3xl"></div>
        </div>
        <div className="max-w-7xl mx-auto relative">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center space-x-2 bg-blue-500/15 ring-1 ring-blue-500/30 rounded-full px-4 py-1.5 mb-6">
                <Zap className="h-4 w-4 text-blue-300" />
                <span className="text-sm font-medium text-blue-200">AI-Powered Credit Decisioning</span>
              </div>
              <h1 className="text-4xl lg:text-5xl font-bold leading-tight mb-6">
                Intelligent Corporate
                <span className="bg-gradient-to-r from-blue-300 to-white bg-clip-text text-transparent"> Credit Analysis</span>
              </h1>
              <p className="text-lg text-navy-200 mb-8 leading-relaxed max-w-xl">
                Automate Credit Appraisal Memos (CAM) for Indian mid-sized corporates.
                Multi-source data ingestion, AI research, and ML-driven lending recommendations
                — all compliant with RBI IRAC norms.
              </p>
              <div className="flex flex-wrap gap-4">
                <Link to="/new-company" className="btn-accent">
                  <span>Start New Analysis</span>
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
                <Link to="/analyzer" className="btn-secondary !bg-transparent !text-white !border-blue-400/30 hover:!bg-blue-500/10">
                  <span>View Dashboard</span>
                  <ChevronRight className="ml-1 h-4 w-4" />
                </Link>
              </div>
            </div>
            <div className="hidden lg:grid grid-cols-2 gap-4">
              <FeatureCard
                icon={<FileSearch className="h-6 w-6" />}
                title="Data Ingestor"
                desc="OCR + NLP extraction from Indian financial documents"
              />
              <FeatureCard
                icon={<Globe className="h-6 w-6" />}
                title="Research Agent"
                desc="Web-scale intelligence from NCLT, SEBI, MCA sources"
              />
              <FeatureCard
                icon={<Brain className="h-6 w-6" />}
                title="Risk Engine"
                desc="ML ensemble with SHAP explainability"
              />
              <FeatureCard
                icon={<Landmark className="h-6 w-6" />}
                title="Indian Context"
                desc="RBI norms, GST, CIBIL, Ind-AS compliant"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="bg-white border-b border-navy-100 py-6 px-4">
        <div className="max-w-7xl mx-auto">
          {loading ? (
            <div className="flex justify-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <StatCard
                icon={<Building2 className="h-5 w-5 text-blue-600" />}
                label="Total Companies"
                value={companies.length}
                color="teal"
              />
              <StatCard
                icon={<Clock className="h-5 w-5 text-amber-600" />}
                label="Pending Analysis"
                value={companies.filter((c) => !c.loan_amount_requested).length}
                color="amber"
              />
              <StatCard
                icon={<CheckCircle className="h-5 w-5 text-green-600" />}
                label="Completed"
                value={companies.filter((c) => c.loan_amount_requested).length}
                color="emerald"
              />
              <StatCard
                icon={<TrendingUp className="h-5 w-5 text-blue-600" />}
                label="Active Reviews"
                value={companies.length}
                color="cyan"
              />
            </div>
          )}
        </div>
      </section>

      {/* Recent Companies */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-navy-900">Recent Analyses</h2>
            <p className="text-navy-500 mt-1">Companies under credit evaluation</p>
          </div>
          <Link
            to="/new-company"
            className="btn-primary text-sm"
          >
            <Building2 className="h-4 w-4 mr-2" />
            New Analysis
          </Link>
        </div>

        {!loading && companies.length === 0 ? (
          <div className="text-center py-20 card rounded-2xl">
            <Building2 className="h-16 w-16 text-navy-200 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-navy-900">No companies yet</h3>
            <p className="text-navy-500 mt-2 mb-6">
              Start by creating a new credit analysis for an Indian corporate.
            </p>
            <Link to="/new-company" className="btn-primary">
              <span>Create First Analysis</span>
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {companies.map((company) => (
              <CompanyCard key={company.id} company={company} />
            ))}
          </div>
        )}
      </section>

      {/* Three Pillars Section */}
      <section className="bg-navy-900 text-white py-16 px-4 relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 right-1/4 w-64 h-64 bg-blue-500/5 rounded-full blur-3xl"></div>
        </div>
        <div className="max-w-7xl mx-auto text-center mb-12 relative">
          <h2 className="text-3xl font-bold mb-4">Three Pillars of Analysis</h2>
          <p className="text-navy-300 max-w-2xl mx-auto">
            Our platform combines three critical dimensions to deliver comprehensive
            credit assessments for Indian corporates.
          </p>
        </div>
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 relative">
          <PillarCard
            number="01"
            title="Data Ingestor"
            items={['PDF/OCR Hindi+English extraction', 'GSTR, CIBIL, ITR parsing', 'Cross-source validation', 'Confidence scoring']}
          />
          <PillarCard
            number="02"
            title="Research Agent"
            items={['CrewAI-powered intelligence', 'NCLT, SEBI, IndianKanoon', 'Promoter background checks', 'Sector & reputation analysis']}
          />
          <PillarCard
            number="03"
            title="Risk Engine"
            items={['Five Cs evaluation', 'ML ensemble (RF/LR/GBT)', 'SHAP explainability', 'RBI IRAC compliance']}
          />
        </div>
      </section>
    </div>
  );
}

function FeatureCard({ icon, title, desc }) {
  return (
    <div className="bg-blue-500/10 backdrop-blur-sm rounded-xl p-5 border border-blue-500/20 hover:bg-blue-500/15 transition">
      <div className="text-blue-300 mb-3">{icon}</div>
      <h3 className="font-semibold text-sm mb-1">{title}</h3>
      <p className="text-navy-300 text-xs leading-relaxed">{desc}</p>
    </div>
  );
}

function StatCard({ icon, label, value, color }) {
  const bgMap = {
    teal: 'bg-blue-50',
    amber: 'bg-amber-50',
    emerald: 'bg-green-50',
    cyan: 'bg-blue-50',
  };
  return (
    <div className={`${bgMap[color]} rounded-xl p-5 border border-navy-100`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-navy-500 uppercase tracking-wider">{label}</p>
          <p className="text-2xl font-bold text-navy-900 mt-1">{value}</p>
        </div>
        <div className="p-2 bg-white rounded-lg shadow-sm">{icon}</div>
      </div>
    </div>
  );
}

function CompanyCard({ company }) {
  return (
    <Link
      to={`/company/${company.id}`}
      className="card p-6 card-hover block group"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-50 rounded-lg">
            <Building2 className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-navy-900 group-hover:text-blue-700">
              {company.name}
            </h3>
            <p className="text-sm text-navy-500">
              {company.industry || 'Industry not specified'}
            </p>
          </div>
        </div>
        <ArrowRight className="h-5 w-5 text-navy-300 group-hover:text-blue-600 transition" />
      </div>
      <div className="mt-4 pt-4 border-t border-navy-100 flex items-center justify-between text-sm">
        <span className="font-medium text-navy-700">
          {company.loan_amount_requested
            ? `₹${Number(company.loan_amount_requested).toLocaleString('en-IN')}`
            : 'Loan TBD'}
        </span>
        <span className="text-xs text-navy-400">
          {new Date(company.created_at).toLocaleDateString('en-IN')}
        </span>
      </div>
    </Link>
  );
}

function PillarCard({ number, title, items }) {
  return (
    <div className="bg-navy-800/50 rounded-2xl p-8 border border-navy-700/30 hover:border-blue-500/40 transition">
      <span className="text-blue-400 text-4xl font-bold opacity-40">{number}</span>
      <h3 className="text-xl font-bold mt-2 mb-4">{title}</h3>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className="flex items-start space-x-2 text-sm text-navy-300">
            <CheckCircle className="h-4 w-4 text-blue-400 mt-0.5 flex-shrink-0" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
