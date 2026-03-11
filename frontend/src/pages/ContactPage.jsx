import React, { useState } from 'react';
import { Mail, Phone, MapPin, Send, CheckCircle, Shield } from 'lucide-react';

export default function ContactPage() {
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' });
  const [submitted, setSubmitted] = useState(false);
  const [errors, setErrors] = useState({});

  const validate = () => {
    const errs = {};
    if (!form.name.trim()) errs.name = 'Name is required';
    if (!form.email.trim()) errs.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errs.email = 'Invalid email format';
    if (!form.message.trim()) errs.message = 'Message is required';
    return errs;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length === 0) {
      setSubmitted(true);
    }
  };

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    if (errors[e.target.name]) {
      setErrors({ ...errors, [e.target.name]: undefined });
    }
  };

  return (
    <div>
      {/* Hero */}
      <section className="gradient-hero text-white py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl font-bold mb-4">Contact Us</h1>
          <p className="text-lg text-navy-200 max-w-2xl mx-auto leading-relaxed">
            Have questions about Intelli-Credit? We'd love to hear from you.
          </p>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Contact Info */}
          <div className="space-y-8">
            <div>
              <h2 className="text-xl font-bold text-navy-900 mb-6">Get in Touch</h2>
              <div className="space-y-6">
                <ContactInfo
                  icon={<Mail className="h-5 w-5" />}
                  title="Email"
                  detail="crewx011@gmail.com"
                />
                <ContactInfo
                  icon={<Phone className="h-5 w-5" />}
                  title="Phone"
                  detail="+91 90 XXXX XXXX"
                />
                <ContactInfo
                  icon={<MapPin className="h-5 w-5" />}
                  title="Address"
                  detail="Coimbatore, Tamil Nadu, India"
                />
              </div>
            </div>

            {/* Office Hours */}
            <div className="card p-6">
              <h3 className="font-bold text-navy-900 mb-3">Support Hours</h3>
              <div className="space-y-2 text-sm text-navy-600">
                <div className="flex justify-between">
                  <span>Monday — Friday</span>
                  <span className="font-medium">9:00 AM — 6:00 PM IST</span>
                </div>
                <div className="flex justify-between">
                  <span>Saturday</span>
                  <span className="font-medium">10:00 AM — 2:00 PM IST</span>
                </div>
                <div className="flex justify-between">
                  <span>Sunday</span>
                  <span className="font-medium text-navy-400">Closed</span>
                </div>
              </div>
            </div>
          </div>

          {/* Contact Form */}
          <div className="lg:col-span-2">
            {submitted ? (
              <div className="card p-12 text-center">
                <div className="inline-flex items-center justify-center p-3 bg-emerald-50 rounded-full mb-4">
                  <CheckCircle className="h-10 w-10 text-emerald-500" />
                </div>
                <h3 className="text-2xl font-bold text-navy-900 mb-2">Message Sent!</h3>
                <p className="text-navy-500 mb-6">
                  Thank you for reaching out. We'll get back to you within 24 hours.
                </p>
                <button
                  onClick={() => {
                    setSubmitted(false);
                    setForm({ name: '', email: '', subject: '', message: '' });
                  }}
                  className="btn-secondary text-sm"
                >
                  Send Another Message
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="card p-8 space-y-6">
                <h3 className="text-xl font-bold text-navy-900 mb-2">Send us a Message</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <FormField
                    label="Full Name"
                    name="name"
                    value={form.name}
                    onChange={handleChange}
                    error={errors.name}
                    required
                    placeholder="Your full name"
                  />
                  <FormField
                    label="Email Address"
                    name="email"
                    type="email"
                    value={form.email}
                    onChange={handleChange}
                    error={errors.email}
                    required
                    placeholder="you@example.com"
                  />
                </div>

                <FormField
                  label="Subject"
                  name="subject"
                  value={form.subject}
                  onChange={handleChange}
                  placeholder="What is this about?"
                />

                <div>
                  <label className="form-label">
                    Message <span className="form-required">*</span>
                  </label>
                  <textarea
                    name="message"
                    value={form.message}
                    onChange={handleChange}
                    rows={5}
                    className={`form-input ${errors.message ? 'border-red-400 focus:ring-red-400' : ''}`}
                    placeholder="Tell us more about your inquiry..."
                  />
                  {errors.message && (
                    <p className="text-red-500 text-xs mt-1">{errors.message}</p>
                  )}
                </div>

                <div className="flex justify-end pt-2">
                  <button type="submit" className="btn-primary">
                    <Send className="h-4 w-4 mr-2" />
                    Send Message
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function ContactInfo({ icon, title, detail }) {
  return (
    <div className="flex items-start space-x-4">
      <div className="p-2.5 bg-navy-50 rounded-lg text-navy-600 flex-shrink-0">
        {icon}
      </div>
      <div>
        <p className="text-sm font-medium text-navy-500">{title}</p>
        <p className="text-navy-800 font-medium">{detail}</p>
      </div>
    </div>
  );
}

function FormField({ label, name, type = 'text', value, onChange, error, required, placeholder }) {
  return (
    <div>
      <label className="form-label">
        {label} {required && <span className="form-required">*</span>}
      </label>
      <input
        type={type}
        name={name}
        value={value}
        onChange={onChange}
        className={`form-input ${error ? 'border-red-400 focus:ring-red-400' : ''}`}
        placeholder={placeholder}
      />
      {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
    </div>
  );
}
