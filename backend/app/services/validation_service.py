"""
Financial Validation Service
Cross-verifies financial indicators across multiple document sources and detects discrepancies.
Enhanced with India-specific validations: GSTR-2A vs 3B reconciliation, NPA/SMA classification,
RBI prudential norms, and Ind-AS consistency checks.
"""

import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import FinancialMetric, RiskFlag, RiskLevel, Document

logger = logging.getLogger(__name__)

# Threshold for flagging discrepancies (percentage)
DISCREPANCY_THRESHOLD = 15.0


class FinancialValidationService:
    """Cross-verifies financial data across multiple document sources.
    Includes India-specific GST, CIBIL, and RBI norm validations."""

    def validate_financials(self, company_id: str, db: Session) -> List[Dict[str, Any]]:
        """
        Run validation checks on all financial metrics for a company.
        Returns a list of detected risk flags with reasoning trail.
        """
        metrics = (
            db.query(FinancialMetric)
            .filter(FinancialMetric.company_id == company_id)
            .all()
        )

        if len(metrics) < 1:
            logger.info(f"No metrics found for company {company_id}")
            return []

        flags = []

        # Cross-source validation (needs 2+ sources)
        if len(metrics) >= 2:
            flags.extend(self._check_metric_consistency(
                metrics, "revenue", "Revenue", company_id
            ))
            flags.extend(self._check_metric_consistency(
                metrics, "net_profit", "Net Profit", company_id
            ))

        # Balance sheet sanity checks
        flags.extend(self._check_balance_sheet_sanity(metrics, company_id))

        # Ratio anomaly checks
        flags.extend(self._check_ratio_anomalies(metrics, company_id))

        # India-specific: GST reconciliation
        flags.extend(self._check_gst_reconciliation(metrics, company_id))

        # India-specific: CIBIL/credit discipline
        flags.extend(self._check_cibil_flags(metrics, company_id))

        # India-specific: NPA/SMA classification
        flags.extend(self._check_npa_classification(metrics, company_id))

        # India-specific: Revenue vs GST turnover
        flags.extend(self._check_revenue_gst_consistency(metrics, company_id))

        # India-specific: Auditor qualification flags
        flags.extend(self._check_auditor_qualifications(metrics, company_id))

        # India-specific: Related party and contingent liability checks
        flags.extend(self._check_related_party_contingent(metrics, company_id))

        # India-specific: RBI prudential norms for lending
        flags.extend(self._check_rbi_prudential_norms(metrics, company_id))

        # Store flags in database
        for flag_data in flags:
            risk_flag = RiskFlag(
                company_id=company_id,
                flag_type=flag_data["flag_type"],
                description=flag_data["description"],
                severity=flag_data["severity"],
                source_a=flag_data.get("source_a"),
                source_b=flag_data.get("source_b"),
                value_a=flag_data.get("value_a"),
                value_b=flag_data.get("value_b"),
                discrepancy_pct=flag_data.get("discrepancy_pct"),
            )
            db.add(risk_flag)

        db.commit()
        return flags

    def _check_metric_consistency(
        self,
        metrics: List[FinancialMetric],
        field: str,
        label: str,
        company_id: str,
    ) -> List[Dict[str, Any]]:
        """Compare a metric across multiple document sources."""
        flags = []
        values = []

        for m in metrics:
            val = getattr(m, field, None)
            if val is not None:
                values.append((m, val))

        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                m1, v1 = values[i]
                m2, v2 = values[j]

                if v1 == 0 and v2 == 0:
                    continue

                avg = (abs(v1) + abs(v2)) / 2
                if avg == 0:
                    continue

                discrepancy = abs(v1 - v2) / avg * 100

                if discrepancy > DISCREPANCY_THRESHOLD:
                    severity = RiskLevel.HIGH if discrepancy > 30 else RiskLevel.MEDIUM
                    flags.append({
                        "flag_type": f"{field}_discrepancy",
                        "description": (
                            f"{label} discrepancy of {discrepancy:.1f}% detected between "
                            f"documents. Source A: ₹{v1:,.2f}, Source B: ₹{v2:,.2f}. "
                            f"This may indicate data manipulation or different reporting periods."
                        ),
                        "severity": severity,
                        "source_a": str(m1.source_document_id or m1.fiscal_year),
                        "source_b": str(m2.source_document_id or m2.fiscal_year),
                        "value_a": v1,
                        "value_b": v2,
                        "discrepancy_pct": round(discrepancy, 2),
                    })

        return flags

    def _check_balance_sheet_sanity(
        self, metrics: List[FinancialMetric], company_id: str
    ) -> List[Dict[str, Any]]:
        """Check if balance sheet items are internally consistent per Ind-AS/Schedule III."""
        flags = []

        for m in metrics:
            # Total assets should roughly equal total liabilities + equity (Ind-AS Schedule III)
            if m.total_assets and m.total_liabilities and m.shareholders_equity:
                expected = m.total_liabilities + m.shareholders_equity
                diff_pct = abs(m.total_assets - expected) / m.total_assets * 100
                if diff_pct > 5:
                    flags.append({
                        "flag_type": "balance_sheet_mismatch",
                        "description": (
                            f"Balance sheet mismatch per Ind-AS Schedule III: "
                            f"Assets (₹{m.total_assets:,.2f}) ≠ "
                            f"Liabilities (₹{m.total_liabilities:,.2f}) + Equity (₹{m.shareholders_equity:,.2f}). "
                            f"Difference: {diff_pct:.1f}%. Verify if non-current liabilities or "
                            f"deferred tax liabilities are excluded."
                        ),
                        "severity": RiskLevel.HIGH,
                        "value_a": m.total_assets,
                        "value_b": expected,
                        "discrepancy_pct": round(diff_pct, 2),
                    })

            # Negative equity warning (Section 271 of Companies Act trigger)
            if m.shareholders_equity is not None and m.shareholders_equity < 0:
                flags.append({
                    "flag_type": "negative_equity",
                    "description": (
                        f"Negative shareholders' equity of ₹{m.shareholders_equity:,.2f} detected. "
                        f"Under Companies Act 2013, net worth erosion may trigger Section 271 "
                        f"(winding up) if accumulated losses exceed 50% of peak net worth."
                    ),
                    "severity": RiskLevel.CRITICAL,
                    "value_a": m.shareholders_equity,
                })

        return flags

    def _check_ratio_anomalies(
        self, metrics: List[FinancialMetric], company_id: str
    ) -> List[Dict[str, Any]]:
        """Check for anomalous financial ratios against Indian lending benchmarks."""
        flags = []

        for m in metrics:
            if m.debt_ratio is not None and m.debt_ratio > 0.8:
                flags.append({
                    "flag_type": "high_debt_ratio",
                    "description": (
                        f"Debt ratio of {m.debt_ratio:.2%} exceeds the comfortable threshold of 60-70% "
                        f"per RBI guidelines. Company is heavily leveraged and may face difficulty "
                        f"in securing additional credit facilities."
                    ),
                    "severity": RiskLevel.HIGH,
                    "value_a": m.debt_ratio,
                })

            if m.current_ratio is not None and m.current_ratio < 1.0:
                flags.append({
                    "flag_type": "low_current_ratio",
                    "description": (
                        f"Current ratio of {m.current_ratio:.2f} is below 1.0. "
                        f"RBI's working capital assessment (Tandon Committee norms) expects "
                        f"a minimum current ratio of 1.33. Liquidity risk is significant."
                    ),
                    "severity": RiskLevel.MEDIUM if m.current_ratio > 0.75 else RiskLevel.HIGH,
                    "value_a": m.current_ratio,
                })

            if m.interest_coverage is not None and m.interest_coverage < 1.5:
                flags.append({
                    "flag_type": "low_interest_coverage",
                    "description": (
                        f"Interest coverage ratio of {m.interest_coverage:.2f} indicates "
                        f"difficulty in servicing debt. Banks typically require DSCR > 1.5x "
                        f"for term loans per RBI prudential norms."
                    ),
                    "severity": RiskLevel.HIGH,
                    "value_a": m.interest_coverage,
                })

            if m.profit_margin is not None and m.profit_margin < 0:
                flags.append({
                    "flag_type": "negative_profit_margin",
                    "description": (
                        f"Negative profit margin of {m.profit_margin:.2%}. Company is loss-making. "
                        f"Continuous losses may lead to SMA/NPA classification per RBI's "
                        f"Income Recognition and Asset Classification (IRAC) norms."
                    ),
                    "severity": RiskLevel.HIGH,
                    "value_a": m.profit_margin,
                })

            # DSCR check (important for Indian bank lending)
            dscr = getattr(m, 'raw_extraction', {}) or {}
            if isinstance(dscr, dict) and dscr.get("dscr") is not None:
                dscr_val = dscr["dscr"]
                if dscr_val < 1.25:
                    flags.append({
                        "flag_type": "low_dscr",
                        "description": (
                            f"Debt Service Coverage Ratio (DSCR) of {dscr_val:.2f}x is below "
                            f"the RBI minimum of 1.25x for term loans. This means the company "
                            f"cannot comfortably meet its annual debt obligations from operating cash flows."
                        ),
                        "severity": RiskLevel.HIGH,
                        "value_a": dscr_val,
                    })

        return flags

    # ─── India-Specific Validation Checks ───

    def _check_gst_reconciliation(
        self, metrics: List[FinancialMetric], company_id: str
    ) -> List[Dict[str, Any]]:
        """Check GSTR-2A vs GSTR-3B ITC reconciliation — a key Indian tax risk indicator."""
        flags = []

        for m in metrics:
            raw = m.raw_extraction or {}
            if not isinstance(raw, dict):
                continue

            itc_2a = raw.get("gstr2a_itc_claimed")
            itc_3b = raw.get("gstr3b_itc_claimed")

            if itc_2a is not None and itc_3b is not None and itc_2a > 0:
                excess_pct = ((itc_3b - itc_2a) / itc_2a) * 100

                if excess_pct > 10:
                    severity = RiskLevel.CRITICAL if excess_pct > 30 else RiskLevel.HIGH
                    flags.append({
                        "flag_type": "gst_itc_mismatch",
                        "description": (
                            f"GSTR-3B ITC (₹{itc_3b:,.2f}) exceeds GSTR-2A/2B ITC (₹{itc_2a:,.2f}) "
                            f"by {excess_pct:.1f}%. Under Rule 36(4) of CGST Rules, ITC claim cannot "
                            f"exceed GSTR-2B amount by more than prescribed limits. "
                            f"This indicates potential excess ITC availed, which may attract "
                            f"GST demand notice under Section 73/74 of CGST Act."
                        ),
                        "severity": severity,
                        "value_a": itc_3b,
                        "value_b": itc_2a,
                        "discrepancy_pct": round(excess_pct, 2),
                    })

            # GST filing regularity
            gst_count = raw.get("gst_filings_count")
            if gst_count is not None and gst_count < 10:
                flags.append({
                    "flag_type": "irregular_gst_filing",
                    "description": (
                        f"Only {gst_count}/12 GST returns filed in the year. "
                        f"Irregular GST filing may indicate: business disruption, "
                        f"cash flow issues, or deliberate non-compliance. "
                        f"Government restricts e-way bill generation for non-filers."
                    ),
                    "severity": RiskLevel.MEDIUM if gst_count >= 8 else RiskLevel.HIGH,
                    "value_a": gst_count,
                })

        return flags

    def _check_cibil_flags(
        self, metrics: List[FinancialMetric], company_id: str
    ) -> List[Dict[str, Any]]:
        """Check CIBIL score and credit discipline indicators."""
        flags = []

        for m in metrics:
            raw = m.raw_extraction or {}
            if not isinstance(raw, dict):
                continue

            # CIBIL Score check
            cibil_score = raw.get("cibil_score")
            if cibil_score is not None:
                if cibil_score < 600:
                    flags.append({
                        "flag_type": "poor_cibil_score",
                        "description": (
                            f"CIBIL score of {cibil_score} is classified as 'Poor' (below 600). "
                            f"Most banks require a minimum CIBIL score of 650-700 for commercial lending. "
                            f"This significantly reduces creditworthiness and may attract higher interest rates."
                        ),
                        "severity": RiskLevel.CRITICAL,
                        "value_a": float(cibil_score),
                    })
                elif cibil_score < 700:
                    flags.append({
                        "flag_type": "below_avg_cibil_score",
                        "description": (
                            f"CIBIL score of {cibil_score} is below average for commercial lending (< 700). "
                            f"May face higher interest rates and stricter lending terms."
                        ),
                        "severity": RiskLevel.MEDIUM,
                        "value_a": float(cibil_score),
                    })

            # CIBIL Rank check (Commercial reports: 1=best, 10=worst)
            cibil_rank = raw.get("cibil_rank")
            if cibil_rank is not None and cibil_rank > 4:
                severity = RiskLevel.CRITICAL if cibil_rank >= 7 else RiskLevel.HIGH
                flags.append({
                    "flag_type": "poor_cibil_rank",
                    "description": (
                        f"CIBIL Commercial Rank of {cibil_rank}/10 (1=best, 10=worst). "
                        f"Ranks above 4 indicate deteriorating credit profile. "
                        f"Banks use this for early warning under RBI's SMA framework."
                    ),
                    "severity": severity,
                    "value_a": float(cibil_rank),
                })

            # DPD (Days Past Due) check
            dpd_instances = raw.get("dpd_instances")
            if dpd_instances is not None and dpd_instances > 0:
                severity = RiskLevel.CRITICAL if dpd_instances > 3 else RiskLevel.HIGH
                flags.append({
                    "flag_type": "dpd_detected",
                    "description": (
                        f"Found {dpd_instances} Days Past Due (DPD) instance(s) in credit report. "
                        f"Any DPD > 0 triggers SMA classification per RBI norms: "
                        f"SMA-0 (1-30 days), SMA-1 (31-60 days), SMA-2 (61-90 days). "
                        f"DPD history remains on credit bureau records for 7 years."
                    ),
                    "severity": severity,
                    "value_a": float(dpd_instances),
                })

        return flags

    def _check_npa_classification(
        self, metrics: List[FinancialMetric], company_id: str
    ) -> List[Dict[str, Any]]:
        """Check NPA/SMA classification per RBI's IRAC norms."""
        flags = []

        for m in metrics:
            raw = m.raw_extraction or {}
            if not isinstance(raw, dict):
                continue

            npa_class = raw.get("npa_classification")
            if not npa_class or npa_class == "standard":
                continue

            npa_class_lower = npa_class.lower()
            severity_map = {
                "sma-0": (RiskLevel.MEDIUM, "Account overdue 1-30 days. Early stress signal under RBI circular dated 7-Jun-2019."),
                "sma-1": (RiskLevel.HIGH, "Account overdue 31-60 days. Banks must report to CRILC (Central Repository of Information on Large Credits)."),
                "sma-2": (RiskLevel.CRITICAL, "Account overdue 61-90 days. Triggers mandatory referral to IBC/NCLT if aggregate exposure > ₹5 Cr."),
                "substandard": (RiskLevel.CRITICAL, "Asset classified as NPA (overdue > 90 days). Minimum provisioning of 15% required by banks."),
                "doubtful": (RiskLevel.CRITICAL, "Doubtful asset — NPA for > 12 months. Provisioning 25-100% of outstanding."),
                "loss": (RiskLevel.CRITICAL, "Loss asset — identified as uncollectable. 100% provisioning required."),
            }

            severity, detail = severity_map.get(npa_class_lower, (RiskLevel.HIGH, "Non-standard asset classification detected."))
            flags.append({
                "flag_type": "npa_sma_classification",
                "description": (
                    f"Account classified as '{npa_class.upper()}' per RBI's Income Recognition "
                    f"and Asset Classification (IRAC) norms. {detail}"
                ),
                "severity": severity,
            })

        return flags

    def _check_revenue_gst_consistency(
        self, metrics: List[FinancialMetric], company_id: str
    ) -> List[Dict[str, Any]]:
        """Cross-verify reported revenue against GST turnover."""
        flags = []

        for m in metrics:
            raw = m.raw_extraction or {}
            if not isinstance(raw, dict):
                continue

            gst_turnover = raw.get("gst_turnover")
            book_revenue = m.revenue

            if gst_turnover and book_revenue and book_revenue > 0:
                diff_pct = abs(gst_turnover - book_revenue) / book_revenue * 100
                if diff_pct > 15:
                    flags.append({
                        "flag_type": "revenue_gst_mismatch",
                        "description": (
                            f"GST-reported turnover (₹{gst_turnover:,.2f}) differs from "
                            f"books revenue (₹{book_revenue:,.2f}) by {diff_pct:.1f}%. "
                            f"This discrepancy may indicate: under-reporting in GST returns, "
                            f"exempt supplies not captured, or revenue inflation in financial statements. "
                            f"GST authorities use this mismatch for audit selection."
                        ),
                        "severity": RiskLevel.HIGH if diff_pct > 30 else RiskLevel.MEDIUM,
                        "value_a": gst_turnover,
                        "value_b": book_revenue,
                        "discrepancy_pct": round(diff_pct, 2),
                    })

        return flags

    def _check_auditor_qualifications(
        self, metrics: List[FinancialMetric], company_id: str
    ) -> List[Dict[str, Any]]:
        """Flag auditor qualifications and emphasis of matter paragraphs."""
        flags = []

        for m in metrics:
            raw = m.raw_extraction or {}
            if not isinstance(raw, dict):
                continue

            qualifications = raw.get("auditor_qualifications", [])
            if qualifications:
                flags.append({
                    "flag_type": "auditor_qualification",
                    "description": (
                        f"Auditor has raised {len(qualifications)} qualification(s)/emphasis of matter: "
                        f"{'; '.join(str(q)[:100] for q in qualifications[:3])}. "
                        f"Qualified audit reports are a significant red flag under RBI's "
                        f"credit appraisal guidelines and SEBI LODR regulations."
                    ),
                    "severity": RiskLevel.HIGH,
                })

        return flags

    def _check_related_party_contingent(
        self, metrics: List[FinancialMetric], company_id: str
    ) -> List[Dict[str, Any]]:
        """Check related party transactions and contingent liabilities."""
        flags = []

        for m in metrics:
            raw = m.raw_extraction or {}
            if not isinstance(raw, dict):
                continue

            # Related party transactions (Ind-AS 24)
            rpt = raw.get("related_party_transactions")
            if rpt and m.revenue and m.revenue > 0:
                rpt_pct = (rpt / m.revenue) * 100
                if rpt_pct > 25:
                    flags.append({
                        "flag_type": "high_related_party_transactions",
                        "description": (
                            f"Related party transactions of ₹{rpt:,.2f} constitute {rpt_pct:.1f}% "
                            f"of revenue. Per Ind-AS 24 and Section 188 of Companies Act 2013, "
                            f"high RPT concentration may indicate fund diversion or "
                            f"non-arm's length pricing. Requires Board/shareholder approval."
                        ),
                        "severity": RiskLevel.HIGH if rpt_pct > 50 else RiskLevel.MEDIUM,
                        "value_a": rpt,
                    })

            # Contingent liabilities (Ind-AS 37)
            contingent = raw.get("contingent_liabilities")
            if contingent and m.shareholders_equity and m.shareholders_equity > 0:
                cl_pct = (contingent / m.shareholders_equity) * 100
                if cl_pct > 50:
                    flags.append({
                        "flag_type": "high_contingent_liabilities",
                        "description": (
                            f"Contingent liabilities of ₹{contingent:,.2f} are {cl_pct:.1f}% "
                            f"of net worth. Per Ind-AS 37, these represent possible obligations "
                            f"whose outcome depends on future events. High contingent liabilities "
                            f"may include tax demands, legal claims, or guarantees that could "
                            f"crystallize and erode net worth."
                        ),
                        "severity": RiskLevel.HIGH if cl_pct > 100 else RiskLevel.MEDIUM,
                        "value_a": contingent,
                    })

        return flags

    def _check_rbi_prudential_norms(
        self, metrics: List[FinancialMetric], company_id: str
    ) -> List[Dict[str, Any]]:
        """Check against RBI prudential lending norms and Tandon Committee recommendations."""
        flags = []

        for m in metrics:
            # Debt-to-Equity per RBI norms (typically max 2:1 for manufacturing)
            if m.debt_to_equity is not None and m.debt_to_equity > 3:
                flags.append({
                    "flag_type": "excessive_leverage",
                    "description": (
                        f"Debt-to-Equity ratio of {m.debt_to_equity:.2f}x exceeds "
                        f"the typical RBI guideline of 2:1 to 3:1 for term lending. "
                        f"High leverage reduces the cushion for lenders and may trigger "
                        f"covenant breaches in existing loan agreements."
                    ),
                    "severity": RiskLevel.HIGH,
                    "value_a": m.debt_to_equity,
                })

            # Check if Turnover is adequate relative to working capital
            if m.revenue and m.current_assets and m.current_liabilities:
                net_working_capital = m.current_assets - m.current_liabilities
                if m.revenue > 0 and net_working_capital < 0:
                    flags.append({
                        "flag_type": "negative_working_capital",
                        "description": (
                            f"Negative net working capital of ₹{net_working_capital:,.2f}. "
                            f"Per Tandon Committee norms, working capital should be financed "
                            f"with a minimum 25% from long-term sources (Method II). "
                            f"Negative NWC indicates heavy reliance on short-term borrowings."
                        ),
                        "severity": RiskLevel.HIGH,
                        "value_a": net_working_capital,
                    })

        return flags


financial_validation_service = FinancialValidationService()
