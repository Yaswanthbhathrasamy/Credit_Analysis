import React from 'react';
import { Code, Brain, Database, Globe } from 'lucide-react';

const TEAM_MEMBERS = [
  {
    name: 'CrewX',
    role: 'Full Stack Developer, Ai Architect Ai Engineer AI Security Engineer',
    category: 'developer',
    desc: 'Architected the end-to-end platform — FastAPI backend, React frontend, Docker infrastructure, and CI/CD pipeline.',
    skills: ['FastAPI', 'React', 'PostgreSQL', 'Docker'],
    icon: Code,
  },
  {
    name: 'AI Research Agent',
    role: 'Intelligence Analyst',
    category: 'analyzer',
    desc: 'CrewAI-powered autonomous research agent that gathers intelligence from NCLT, SEBI, MCA, IndianKanoon, and news sources.',
    skills: ['CrewAI', 'LangChain', 'SerpAPI', 'NLP'],
    icon: Globe,
  },
  {
    name: 'ML Risk Engine',
    role: 'Risk Scoring Analyst',
    category: 'analyzer',
    desc: 'Ensemble ML model (Random Forest, Logistic Regression, GBT) with SHAP explainability for Five Cs credit evaluation.',
    skills: ['scikit-learn', 'SHAP', 'Feature Engineering', 'RBI Norms'],
    icon: Brain,
  },
  {
    name: 'Data Ingestor',
    role: 'Document Analyst',
    category: 'analyzer',
    desc: 'OCR-powered document processing pipeline handling Hindi+English PDFs with confidence scoring and Indian document auto-detection.',
    skills: ['PaddleOCR', 'PyMuPDF', 'GPT-4o-mini', 'Ind-AS'],
    icon: Database,
  },
];

export default function TeamPage() {
  const developers = TEAM_MEMBERS.filter((m) => m.category === 'developer');
  const analyzers = TEAM_MEMBERS.filter((m) => m.category === 'analyzer');

  return (
    <div>
      {/* Hero */}
      <section className="gradient-hero text-white py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl font-bold mb-4">Our Team</h1>
          <p className="text-lg text-navy-200 max-w-2xl mx-auto leading-relaxed">
            A blend of human expertise and AI-powered agents working together
            to deliver intelligent credit decisioning.
          </p>
        </div>
      </section>

      {/* Developers */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="mb-12">
          <span className="text-xs font-bold uppercase tracking-wider text-teal-600 mb-2 block">Human Team</span>
          <h2 className="text-3xl font-bold text-navy-900">Developers</h2>
          <p className="text-navy-500 mt-2">The engineers behind the platform</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {developers.map((member, i) => (
            <TeamCard key={i} member={member} />
          ))}
        </div>
      </section>

      {/* AI Analyzers */}
      <section className="bg-navy-50 border-t border-navy-100 py-16 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="mb-12">
            <span className="text-xs font-bold uppercase tracking-wider text-teal-600 mb-2 block">AI Agents</span>
            <h2 className="text-3xl font-bold text-navy-900">Analyzers</h2>
            <p className="text-navy-500 mt-2">
              Autonomous AI agents that power the credit analysis pipeline
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {analyzers.map((member, i) => (
              <TeamCard key={i} member={member} isAI />
            ))}
          </div>
        </div>
      </section>

      {/* LangSmith Monitoring */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="card-elevated p-8 text-center">
          <div className="inline-flex items-center justify-center p-3 bg-teal-50 rounded-xl mb-4">
            <Brain className="h-8 w-8 text-teal-600" />
          </div>
          <h3 className="text-2xl font-bold text-navy-900 mb-2">AI Monitoring with LangSmith</h3>
          <p className="text-navy-500 max-w-xl mx-auto mb-6">
            All AI agent workflows are monitored and traced via LangSmith for
            full transparency, debugging, and performance optimization.
          </p>
          <div className="flex justify-center gap-4 flex-wrap">
            <div className="bg-navy-50 rounded-lg px-4 py-2 text-sm font-medium text-navy-700">
              Trace Logging
            </div>
            <div className="bg-navy-50 rounded-lg px-4 py-2 text-sm font-medium text-navy-700">
              Latency Monitoring
            </div>
            <div className="bg-navy-50 rounded-lg px-4 py-2 text-sm font-medium text-navy-700">
              Token Usage Tracking
            </div>
            <div className="bg-navy-50 rounded-lg px-4 py-2 text-sm font-medium text-navy-700">
              Error Diagnostics
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

function TeamCard({ member, isAI = false }) {
  const Icon = member.icon;
  return (
    <div className="card p-6 hover:shadow-lg transition-all duration-300">
      <div className="flex items-start space-x-4">
        <div className={`p-3 rounded-xl ${isAI ? 'bg-teal-50' : 'bg-navy-50'}`}>
          <Icon className={`h-6 w-6 ${isAI ? 'text-teal-600' : 'text-navy-600'}`} />
        </div>
        <div className="flex-1">
          <div className="flex items-center space-x-2">
            <h3 className="font-bold text-navy-900">{member.name}</h3>
            {isAI && (
              <span className="text-[10px] font-bold uppercase bg-teal-100 text-teal-700 px-2 py-0.5 rounded-full">
                AI Agent
              </span>
            )}
          </div>
          <p className="text-sm font-medium text-navy-500">{member.role}</p>
        </div>
      </div>
      <p className="text-sm text-navy-600 mt-4 leading-relaxed">{member.desc}</p>
      <div className="flex flex-wrap gap-2 mt-4">
        {member.skills.map((skill, i) => (
          <span
            key={i}
            className="text-xs font-medium bg-navy-50 text-navy-600 px-2.5 py-1 rounded-md"
          >
            {skill}
          </span>
        ))}
      </div>
    </div>
  );
}
