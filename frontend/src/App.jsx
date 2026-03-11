import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import CompanyPage from './pages/CompanyPage';
import DashboardPage from './pages/DashboardPage';
import AboutPage from './pages/AboutPage';
import TeamPage from './pages/TeamPage';
import AnalyzerPage from './pages/AnalyzerPage';
import ContactPage from './pages/ContactPage';

function App() {
  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/company/:id" element={<DashboardPage />} />
          <Route path="/new-company" element={<CompanyPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/team" element={<TeamPage />} />
          <Route path="/analyzer" element={<AnalyzerPage />} />
          <Route path="/contact" element={<ContactPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
