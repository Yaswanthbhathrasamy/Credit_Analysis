import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getCompanies } from '../services/api';
import {
  Building2, ArrowRight, Search, Filter, Clock,
  CheckCircle, AlertTriangle, TrendingUp, BarChart3,
} from 'lucide-react';

export default function AnalyzerPage() {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');

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

  const filtered = companies.filter((c) => {
    const matchSearch = c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.industry || '').toLowerCase().includes(search.toLowerCase());
    if (filter === 'pending') return matchSearch && !c.loan_amount_requested;
    if (filter === 'completed') return matchSearch && c.loan_amount_requested;
    return matchSearch;
  });

  return (
    <div>
      {/* Header */}
      <section className="bg-white border-b border-navy-100 py-8 px-4">
        <div className="max-w-[90rem] mx-auto">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-navy-900 flex items-center space-x-3">
                <BarChart3 className="h-7 w-7 text-teal-600" />
                <span>Credit Analyzer</span>
              </h1>
              <p className="text-navy-500 mt-1">Manage and track all company credit analyses</p>
            </div>
            <Link to="/new-company" className="btn-primary text-sm self-start">
              <Building2 className="h-4 w-4 mr-2" />
              New Analysis
            </Link>
          </div>

          {/* Search & Filter */}
          <div className="flex flex-col sm:flex-row gap-3 mt-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-navy-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by company name or industry..."
                className="form-input pl-10 text-base py-3"
              />
            </div>
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-navy-400" />
              {['all', 'pending', 'completed'].map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
                    filter === f
                      ? 'bg-teal-600 text-white'
                      : 'bg-navy-50 text-navy-600 hover:bg-navy-100'
                  }`}
                >
                  {f.charAt(0).toUpperCase() + f.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Results */}
      <section className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="flex justify-center py-16">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-teal-600"></div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20 card rounded-2xl">
            <Search className="h-12 w-12 text-navy-200 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-navy-900">No companies found</h3>
            <p className="text-navy-500 mt-2">
              {search ? 'Try adjusting your search terms.' : 'Start by creating a new credit analysis.'}
            </p>
          </div>
        ) : (
          <>
            <p className="text-sm text-navy-500 mb-4">
              Showing {filtered.length} of {companies.length} companies
            </p>
            <div className="space-y-3">
              {filtered.map((company) => (
                <AnalyzerRow key={company.id} company={company} />
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}

function AnalyzerRow({ company }) {
  const hasLoan = !!company.loan_amount_requested;
  return (
    <Link
      to={`/company/${company.id}`}
      className="card p-6 flex items-center justify-between hover:shadow-md transition group block"
    >
      <div className="flex items-center space-x-4 flex-1 min-w-0">
        <div className="p-2.5 bg-teal-50 rounded-lg flex-shrink-0">
          <Building2 className="h-5 w-5 text-teal-600" />
        </div>
        <div className="min-w-0">
          <h3 className="font-semibold text-navy-900 truncate group-hover:text-navy-700">
            {company.name}
          </h3>
          <p className="text-sm text-navy-500 truncate">
            {company.industry || 'Industry not specified'}
          </p>
        </div>
      </div>
      <div className="hidden md:flex items-center space-x-8">
        <div className="text-right">
          <p className="text-xs text-navy-400 uppercase tracking-wider">Loan Amount</p>
          <p className="font-semibold text-navy-800">
            {hasLoan
              ? `₹${Number(company.loan_amount_requested).toLocaleString('en-IN')}`
              : '—'}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-navy-400 uppercase tracking-wider">Status</p>
          <div className="flex items-center space-x-1.5 mt-0.5">
            {hasLoan ? (
              <>
                <CheckCircle className="h-4 w-4 text-emerald-500" />
                <span className="text-sm font-medium text-emerald-700">Completed</span>
              </>
            ) : (
              <>
                <Clock className="h-4 w-4 text-amber-500" />
                <span className="text-sm font-medium text-amber-700">Pending</span>
              </>
            )}
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs text-navy-400 uppercase tracking-wider">Date</p>
          <p className="text-sm text-navy-600">
            {new Date(company.created_at).toLocaleDateString('en-IN')}
          </p>
        </div>
      </div>
      <ArrowRight className="h-5 w-5 text-navy-300 ml-4 group-hover:text-navy-600 transition flex-shrink-0" />
    </Link>
  );
}
