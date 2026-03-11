import React from 'react';
import {
  Shield, FileSearch, Globe, Brain, Landmark, CheckCircle,
  BarChart3, Lock, Cpu, Database, Layers, ArrowRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export default function AboutPage() {
  return (
    <div>
      {/* Hero */}
      <section className="gradient-hero text-white py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl font-bold mb-4">About Intelli-Credit</h1>
          <p className="text-lg text-navy-200 max-w-2xl mx-auto leading-relaxed">
            An AI-powered Corporate Credit Decisioning Engine built for Indian mid-sized corporates.
            We automate Credit Appraisal Memos by combining multi-source data ingestion,
            web-scale research, and ML-based lending recommendations.
          </p>
        </div>
      </section>

      {/* Mission */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-teal-600 mb-2 block">Our Mission</span>
            <h2 className="text-3xl font-bold text-navy-900 mb-4">
              Transforming Corporate Credit Assessment in India
            </h2>
            <p className="text-navy-600 leading-relaxed mb-6">
              Traditional credit appraisal for Indian mid-sized corporates is manual, slow, and
              prone to human bias. Intelli-Credit leverages cutting-edge AI to analyze financial
              documents, conduct web-scale research across Indian regulatory databases, and
              produce explainable ML-driven risk assessments — all within minutes.
            </p>
            <div className="space-y-3">
              {[
                'RBI IRAC norms compliant risk classification',
                'Hindi + English OCR for Indian financial documents',
                'CIBIL Commercial score integration',
                'GST reconciliation (GSTR-2A vs 3B)',
                'SHAP-based explainable AI decisions',
              ].map((item, i) => (
                <div key={i} className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-emerald-500 flex-shrink-0" />
                  <span className="text-navy-700 text-sm font-medium">{item}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <InfoCard icon={<FileSearch />} title="Data Ingestor" desc="PyMuPDF + PaddleOCR for Indian PDFs with confidence scoring" />
            <InfoCard icon={<Globe />} title="Research Agent" desc="CrewAI-powered intelligence from NCLT, SEBI, MCA, IndianKanoon" />
            <InfoCard icon={<Brain />} title="ML Engine" desc="scikit-learn ensemble (RF/LR/GBT) with SHAP explainability" />
            <InfoCard icon={<Landmark />} title="CAM Generator" desc="Automated Credit Appraisal Memo with Five Cs reasoning" />
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="bg-navy-900 text-white py-16 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Technology Stack</h2>
            <p className="text-navy-300 max-w-xl mx-auto">
              Built with modern, production-grade tools and frameworks
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <TechCard icon={<Cpu />} category="Backend" items={['FastAPI', 'SQLAlchemy', 'PostgreSQL', 'Docker']} />
            <TechCard icon={<Layers />} category="Frontend" items={['React 18', 'Vite', 'Tailwind CSS', 'Recharts']} />
            <TechCard icon={<Brain />} category="AI/ML" items={['GPT-4o-mini', 'LangChain', 'CrewAI', 'scikit-learn']} />
            <TechCard icon={<Database />} category="Processing" items={['PyMuPDF', 'PaddleOCR', 'SHAP', 'python-docx']} />
          </div>
        </div>
      </section>

      {/* Indian Context */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-navy-900 mb-4">Indian Context Awareness</h2>
          <p className="text-navy-500 max-w-2xl mx-auto">
            Purpose-built for the Indian corporate credit landscape with deep understanding
            of local regulations, accounting standards, and compliance frameworks.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <ContextCard
            title="Regulatory Compliance"
            items={['RBI IRAC NPA Classification (SMA-0/1/2)', 'SEBI Order Monitoring', 'MCA/ROC Filing Analysis', 'FEMA Compliance Checks']}
          />
          <ContextCard
            title="Financial Standards"
            items={['Ind-AS Accounting (not US GAAP)', 'Amounts in ₹ Lakhs/Crores', 'FY April–March (e.g., FY 2024-25)', 'Tandon Committee Norms']}
          />
          <ContextCard
            title="Tax & GST"
            items={['GSTR-1, 2A, 2B, 3B Reconciliation', 'Rule 36(4) ITC Validation', 'DGGI Investigation Monitoring', 'CGST Act Compliance']}
          />
        </div>
      </section>

      {/* CTA */}
      <section className="bg-navy-50 border-t border-navy-100 py-12 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold text-navy-900 mb-4">Ready to Start?</h2>
          <p className="text-navy-600 mb-6">
            Begin your first AI-powered credit analysis in minutes.
          </p>
          <Link to="/new-company" className="btn-primary">
            <span>Start New Analysis</span>
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </div>
      </section>
    </div>
  );
}

function InfoCard({ icon, title, desc }) {
  return (
    <div className="card p-6 hover:shadow-md transition">
      <div className="text-navy-600 mb-3">{icon}</div>
      <h3 className="font-semibold text-navy-900 mb-1">{title}</h3>
      <p className="text-sm text-navy-500 leading-relaxed">{desc}</p>
    </div>
  );
}

function TechCard({ icon, category, items }) {
  return (
    <div className="bg-navy-800/50 rounded-xl p-6 border border-teal-800/30">
      <div className="text-teal-400 mb-3">{icon}</div>
      <h3 className="font-bold text-lg mb-3">{category}</h3>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className="text-sm text-navy-300 flex items-center space-x-2">
            <div className="h-1.5 w-1.5 rounded-full bg-teal-400"></div>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ContextCard({ title, items }) {
  return (
    <div className="card p-6">
      <h3 className="font-bold text-navy-900 mb-4 text-lg">{title}</h3>
      <ul className="space-y-3">
        {items.map((item, i) => (
          <li key={i} className="flex items-start space-x-2 text-sm">
            <CheckCircle className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
            <span className="text-navy-600">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
