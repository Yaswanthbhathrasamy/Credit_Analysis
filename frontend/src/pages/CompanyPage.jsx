import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createCompany } from '../services/api';
import {
  Building2, Save, AlertCircle, ChevronRight, ChevronLeft,
  FileText, IndianRupee, Info, CheckCircle, User,
} from 'lucide-react';

const STEPS = [
  { key: 'company', label: 'Company Info', icon: Building2 },
  { key: 'regulatory', label: 'Regulatory IDs', icon: FileText },
  { key: 'contact', label: 'Contact Details', icon: User },
  { key: 'loan', label: 'Loan Details', icon: IndianRupee },
  { key: 'review', label: 'Review & Submit', icon: CheckCircle },
];

const INDUSTRIES = [
  'Manufacturing', 'IT Services', 'Financial Services', 'Infrastructure',
  'Real Estate', 'Pharmaceuticals', 'FMCG', 'Textiles', 'Agriculture',
  'Automobiles', 'Chemicals', 'Energy & Power', 'Mining & Metals',
  'Telecommunications', 'Healthcare', 'Education', 'Logistics',
  'Media & Entertainment', 'Retail', 'Other',
];

const LOAN_TYPES = [
  'Term Loan', 'Working Capital', 'CC/OD (Cash Credit / Overdraft)',
  'Letter of Credit', 'Bank Guarantee', 'Project Finance',
  'Bill Discounting', 'Packing Credit', 'WCDL', 'Other',
];

export default function CompanyPage() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [form, setForm] = useState({
    name: '', industry: '', incorporation_date: '', registered_address: '',
    cin: '', pan: '', gst_number: '',
    contact_email: '', contact_phone: '',
    loan_amount_requested: '', loan_purpose: '', loan_type: '',
    loan_tenure_months: '', proposed_interest_rate: '', annual_turnover: '',
  });

  const validateStep = (step) => {
    const errs = {};
    if (step === 0) {
      if (!form.name.trim()) errs.name = 'Company name is required';
      if (!form.industry.trim()) errs.industry = 'Industry / sector is required';
    } else if (step === 1) {
      if (!form.pan.trim()) errs.pan = 'PAN is required';
      else if (!/^[A-Z]{5}[0-9]{4}[A-Z]$/.test(form.pan.toUpperCase()))
        errs.pan = 'Invalid PAN format (e.g., ABCDE1234F)';
      if (form.gst_number && !/^\d{2}[A-Z]{5}\d{4}[A-Z]\d[Z][A-Z\d]$/.test(form.gst_number.toUpperCase()))
        errs.gst_number = 'Invalid GST format (e.g., 27ABCDE1234F1Z5)';
      if (form.cin && form.cin.length > 0 && form.cin.length !== 21)
        errs.cin = 'CIN must be 21 characters';
    } else if (step === 2) {
      if (form.contact_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.contact_email))
        errs.contact_email = 'Invalid email format';
    } else if (step === 3) {
      if (!form.loan_amount_requested) errs.loan_amount_requested = 'Loan amount is required';
      else if (parseFloat(form.loan_amount_requested) <= 0)
        errs.loan_amount_requested = 'Loan amount must be positive';
      if (!form.loan_type) errs.loan_type = 'Loan type is required';
      if (form.loan_tenure_months && parseInt(form.loan_tenure_months) <= 0)
        errs.loan_tenure_months = 'Tenure must be positive';
      if (form.proposed_interest_rate && (parseFloat(form.proposed_interest_rate) < 0 || parseFloat(form.proposed_interest_rate) > 50))
        errs.proposed_interest_rate = 'Interest rate must be between 0% and 50%';
    }
    return errs;
  };

  const handleNext = () => {
    const errs = validateStep(currentStep);
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;
    setCurrentStep((s) => Math.min(s + 1, STEPS.length - 1));
  };

  const handleBack = () => setCurrentStep((s) => Math.max(s - 1, 0));

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
    if (errors[name]) setErrors({ ...errors, [name]: undefined });
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const payload = {
        ...form,
        pan: form.pan.toUpperCase(),
        gst_number: form.gst_number ? form.gst_number.toUpperCase() : '',
        cin: form.cin ? form.cin.toUpperCase() : '',
        loan_amount_requested: form.loan_amount_requested ? parseFloat(form.loan_amount_requested) : null,
        loan_tenure_months: form.loan_tenure_months ? parseInt(form.loan_tenure_months) : null,
        proposed_interest_rate: form.proposed_interest_rate ? parseFloat(form.proposed_interest_rate) : null,
        annual_turnover: form.annual_turnover ? parseFloat(form.annual_turnover) : null,
      };
      const res = await createCompany(payload);
      navigate(`/company/${res.data.id}`);
    } catch (err) {
      console.error('Failed to create company:', err);
      alert('Failed to create company. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {/* Header */}
      <section className="bg-white border-b border-navy-100 py-8 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-blue-50 rounded-xl">
              <Building2 className="h-7 w-7 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-navy-900">New Credit Analysis</h1>
              <p className="text-navy-500 text-sm mt-0.5">Complete the onboarding form to begin AI-powered credit assessment</p>
            </div>
          </div>
        </div>
      </section>

      {/* Step Indicator */}
      <div className="max-w-6xl mx-auto px-4 pt-6">
        <div className="flex items-center justify-between mb-8">
          {STEPS.map((step, idx) => {
            const Icon = step.icon;
            const isActive = idx === currentStep;
            const isComplete = idx < currentStep;
            return (
              <div key={step.key} className="flex items-center flex-1">
                <button
                  onClick={() => { if (idx < currentStep) setCurrentStep(idx); }}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition text-sm font-medium ${
                    isActive ? 'bg-blue-600 text-white' :
                    isComplete ? 'bg-green-100 text-green-700 hover:bg-green-200' :
                    'bg-gray-100 text-gray-400'
                  }`}
                >
                  {isComplete ? <CheckCircle className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                  <span className="hidden md:inline">{step.label}</span>
                  <span className="md:hidden">{idx + 1}</span>
                </button>
                {idx < STEPS.length - 1 && (
                  <div className={`flex-1 h-0.5 mx-2 ${idx < currentStep ? 'bg-green-400' : 'bg-gray-200'}`} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Step Content */}
      <div className="max-w-6xl mx-auto px-4 pb-12">
        {currentStep === 0 && (
          <StepCard title="Company Information" subtitle="Basic details about the corporate entity" icon={<Building2 className="h-5 w-5" />}>
            <div className="space-y-5">
              <FormField label="Company Name" name="name" value={form.name} onChange={handleChange} error={errors.name} required placeholder="Enter registered company name" />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <SelectField label="Industry / Sector" name="industry" value={form.industry} onChange={handleChange} error={errors.industry} required options={INDUSTRIES} placeholder="Select industry" />
                <FormField label="Annual Turnover (₹)" name="annual_turnover" type="number" value={form.annual_turnover} onChange={handleChange} placeholder="e.g., 500000000" hint="Amount in Indian Rupees" />
              </div>
              <FormField label="Incorporation Date" name="incorporation_date" value={form.incorporation_date} onChange={handleChange} placeholder="DD/MM/YYYY" />
              <FormField label="Registered Address" name="registered_address" value={form.registered_address} onChange={handleChange} placeholder="Full registered office address" multiline />
            </div>
          </StepCard>
        )}

        {currentStep === 1 && (
          <StepCard title="Regulatory Identifiers" subtitle="Government registration and tax identification numbers" icon={<FileText className="h-5 w-5" />}>
            <div className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <FormField label="CIN" name="cin" value={form.cin} onChange={handleChange} error={errors.cin} placeholder="L/U + 5 digits + ..." hint="Corporate Identity Number from MCA" />
                <FormField label="PAN" name="pan" value={form.pan} onChange={handleChange} error={errors.pan} required placeholder="ABCDE1234F" hint="Permanent Account Number" />
                <FormField label="GST Number" name="gst_number" value={form.gst_number} onChange={handleChange} error={errors.gst_number} placeholder="27ABCDE1234F1Z5" hint="15-digit GSTIN" />
              </div>
              <div className="flex items-center space-x-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <Info className="h-4 w-4 text-blue-600 flex-shrink-0" />
                <p className="text-xs text-blue-700">These identifiers will be used to cross-reference with MCA, GST Portal, and CIBIL databases for automated verification.</p>
              </div>
            </div>
          </StepCard>
        )}

        {currentStep === 2 && (
          <StepCard title="Contact Details" subtitle="Communication information for the company" icon={<User className="h-5 w-5" />}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <FormField label="Contact Email" name="contact_email" type="email" value={form.contact_email} onChange={handleChange} error={errors.contact_email} placeholder="company@example.com" />
              <FormField label="Contact Phone" name="contact_phone" value={form.contact_phone} onChange={handleChange} placeholder="+91 XXXXX XXXXX" />
            </div>
          </StepCard>
        )}

        {currentStep === 3 && (
          <StepCard title="Loan / Credit Facility" subtitle="Details of the credit facility being assessed" icon={<IndianRupee className="h-5 w-5" />}>
            <div className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <SelectField label="Loan Type" name="loan_type" value={form.loan_type} onChange={handleChange} error={errors.loan_type} required options={LOAN_TYPES} placeholder="Select loan type" />
                <FormField label="Loan Amount Requested (₹)" name="loan_amount_requested" type="number" value={form.loan_amount_requested} onChange={handleChange} error={errors.loan_amount_requested} required placeholder="e.g., 10000000" hint="Amount in Indian Rupees" />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <FormField label="Tenure (Months)" name="loan_tenure_months" type="number" value={form.loan_tenure_months} onChange={handleChange} error={errors.loan_tenure_months} placeholder="e.g., 60" hint="Loan tenure in months" />
                <FormField label="Proposed Interest Rate (%)" name="proposed_interest_rate" type="number" value={form.proposed_interest_rate} onChange={handleChange} error={errors.proposed_interest_rate} placeholder="e.g., 10.5" hint="Annual interest rate" />
              </div>
              <FormField label="Loan Purpose / Description" name="loan_purpose" value={form.loan_purpose} onChange={handleChange} placeholder="e.g., Expansion of manufacturing unit in Pune" multiline />
            </div>
          </StepCard>
        )}

        {currentStep === 4 && (
          <StepCard title="Review & Submit" subtitle="Verify all entered details before creating the analysis" icon={<CheckCircle className="h-5 w-5" />}>
            <div className="space-y-6">
              <ReviewSection title="Company Information" items={[
                { label: 'Name', value: form.name },
                { label: 'Industry', value: form.industry },
                { label: 'Annual Turnover', value: form.annual_turnover ? `₹${Number(form.annual_turnover).toLocaleString()}` : 'N/A' },
                { label: 'Incorporation Date', value: form.incorporation_date || 'N/A' },
                { label: 'Address', value: form.registered_address || 'N/A' },
              ]} />
              <ReviewSection title="Regulatory Identifiers" items={[
                { label: 'CIN', value: form.cin || 'N/A' },
                { label: 'PAN', value: form.pan.toUpperCase() },
                { label: 'GST', value: form.gst_number ? form.gst_number.toUpperCase() : 'N/A' },
              ]} />
              <ReviewSection title="Contact Details" items={[
                { label: 'Email', value: form.contact_email || 'N/A' },
                { label: 'Phone', value: form.contact_phone || 'N/A' },
              ]} />
              <ReviewSection title="Loan Details" items={[
                { label: 'Type', value: form.loan_type || 'N/A' },
                { label: 'Amount', value: form.loan_amount_requested ? `₹${Number(form.loan_amount_requested).toLocaleString()}` : 'N/A' },
                { label: 'Tenure', value: form.loan_tenure_months ? `${form.loan_tenure_months} months` : 'N/A' },
                { label: 'Interest Rate', value: form.proposed_interest_rate ? `${form.proposed_interest_rate}%` : 'N/A' },
                { label: 'Purpose', value: form.loan_purpose || 'N/A' },
              ]} />
            </div>
          </StepCard>
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between mt-8">
          <div>
            {currentStep > 0 && (
              <button onClick={handleBack} className="flex items-center space-x-2 px-5 py-2.5 border border-navy-200 text-navy-700 rounded-lg hover:bg-navy-50 transition text-sm font-medium">
                <ChevronLeft className="h-4 w-4" /><span>Back</span>
              </button>
            )}
          </div>
          <div className="flex items-center space-x-2">
            <p className="text-xs text-navy-400 mr-4">Step {currentStep + 1} of {STEPS.length}</p>
            {currentStep < STEPS.length - 1 ? (
              <button onClick={handleNext} className="btn-primary"><span>Next</span><ChevronRight className="h-4 w-4 ml-1" /></button>
            ) : (
              <button onClick={handleSubmit} disabled={loading} className="btn-primary">
                <Save className="h-5 w-5 mr-2" /><span>{loading ? 'Creating...' : 'Create & Start Analysis'}</span><ChevronRight className="h-4 w-4 ml-1" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StepCard({ title, subtitle, icon, children }) {
  return (
    <div className="card p-8">
      <div className="flex items-center space-x-3 pb-4 border-b border-navy-100 mb-6">
        <div className="p-2 bg-blue-50 rounded-lg text-blue-600">{icon}</div>
        <div>
          <h2 className="text-lg font-bold text-navy-900">{title}</h2>
          <p className="text-xs text-navy-500">{subtitle}</p>
        </div>
      </div>
      {children}
    </div>
  );
}

function ReviewSection({ title, items }) {
  return (
    <div className="bg-gray-50 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-navy-800 mb-3">{title}</h3>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {items.map((item) => (
          <div key={item.label} className="flex items-start">
            <span className="text-xs text-gray-500 w-32 flex-shrink-0">{item.label}:</span>
            <span className="text-sm text-navy-900 font-medium">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function FormField({ label, name, type = 'text', value, onChange, error, required, placeholder, hint, multiline }) {
  const Component = multiline ? 'textarea' : 'input';
  return (
    <div>
      <label className="form-label">{label}{required && <span className="form-required">*</span>}</label>
      <Component type={multiline ? undefined : type} name={name} value={value} onChange={onChange} rows={multiline ? 3 : undefined}
        className={`form-input text-base py-3 px-5 ${error ? 'border-red-400 ring-1 ring-red-400 focus:ring-red-400' : ''}`} placeholder={placeholder} />
      {hint && !error && <p className="text-navy-400 text-xs mt-1">{hint}</p>}
      {error && <p className="text-red-500 text-xs mt-1 flex items-center space-x-1"><AlertCircle className="h-3 w-3" /><span>{error}</span></p>}
    </div>
  );
}

function SelectField({ label, name, value, onChange, error, required, options, placeholder }) {
  return (
    <div>
      <label className="form-label">{label}{required && <span className="form-required">*</span>}</label>
      <select name={name} value={value} onChange={onChange} className={`form-input text-base py-3 px-5 ${error ? 'border-red-400 ring-1 ring-red-400 focus:ring-red-400' : ''}`}>
        <option value="">{placeholder}</option>
        {options.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
      </select>
      {error && <p className="text-red-500 text-xs mt-1 flex items-center space-x-1"><AlertCircle className="h-3 w-3" /><span>{error}</span></p>}
    </div>
  );
}
