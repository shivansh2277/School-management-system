import { useState } from "react";
import { Link } from "react-router-dom";

export function PublicDisclosurePage() {
  const [activeTab, setActiveTab] = useState<"general" | "docs" | "results" | "staff" | "infra" | "grievance">("general");

  return (
    <div className="bg-slate-50 min-h-screen py-10 lg:py-14">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Breadcrumb & Section Eyebrow */}
        <div className="space-y-2">
          <nav className="flex items-center text-xs text-slate-500 gap-2">
            <Link to="/" className="hover:text-primary transition-colors">Home</Link>
            <span>&rsaquo;</span>
            <span className="text-slate-900 font-semibold">Public Disclosure</span>
          </nav>
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 font-serif tracking-tight">
                Mandatory Public Disclosure
              </h1>
              <p className="text-slate-600 text-sm sm:text-base mt-1 max-w-2xl">
                Official institutional disclosure in compliance with CBSE regulatory guidelines (Appendix IX).
              </p>
            </div>
            <a
              href="/documents/public-disclosure-summary.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-[#042954] hover:bg-[#021b38] text-white text-xs sm:text-sm font-semibold px-4 py-2.5 rounded-lg shadow-sm transition-all shrink-0 self-start md:self-auto"
            >
              <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>Download Official Summary PDF (1 Page)</span>
            </a>
          </div>
        </div>

        {/* Institutional Demo Notice Banner */}
        <div className="rounded-xl border border-amber-200 bg-amber-50/80 p-4 text-xs text-amber-900 flex items-start gap-3">
          <span className="text-base leading-none">ℹ️</span>
          <div>
            <strong className="font-semibold block text-amber-950">Demonstration Disclosure Notice:</strong>
            Sunrise School is a demonstration institutional portal. Official statutory credentials, registration numbers, and regulatory certificates are marked as <em>"Demo information / To be configured"</em> to uphold institutional verification standards.
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-2 border-b border-slate-200 text-xs sm:text-sm font-semibold scrollbar-none">
          {[
            { id: "general", label: "A. General Information" },
            { id: "docs", label: "B. Documents & Information" },
            { id: "results", label: "C. Results & Academics" },
            { id: "staff", label: "D. Staff & Faculty" },
            { id: "infra", label: "E. Infrastructure" },
            { id: "grievance", label: "F. Student Support & Grievance" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`px-3.5 py-2 rounded-lg whitespace-nowrap transition-colors cursor-pointer ${
                activeTab === tab.id
                  ? "bg-[#042954] text-white shadow-xs"
                  : "bg-white text-slate-700 hover:bg-slate-100 hover:text-slate-900 border border-slate-200"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content Panels */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-xs">
          {/* TAB A: GENERAL INFORMATION */}
          {activeTab === "general" && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h2 className="text-lg sm:text-xl font-bold text-slate-900 font-serif">
                  A. General Institutional Information
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                  Core registration, leadership, and operational details of Sunrise School.
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs sm:text-sm border-collapse">
                  <thead>
                    <tr className="bg-slate-100 text-slate-700 border-b border-slate-200">
                      <th className="py-3 px-4 font-semibold w-16">S.No.</th>
                      <th className="py-3 px-4 font-semibold w-1/3">Information Parameter</th>
                      <th className="py-3 px-4 font-semibold">Institutional Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">1</td>
                      <td className="py-3 px-4 font-semibold text-slate-900">Name of the School</td>
                      <td className="py-3 px-4">Sunrise School (Sunrise Public School)</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">2</td>
                      <td className="py-3 px-4 font-semibold text-slate-900">Affiliation Status</td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-blue-50 text-blue-800 text-xs font-medium">
                          CBSE Senior Secondary (Demo information)
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">3</td>
                      <td className="py-3 px-4 font-semibold text-slate-900">Affiliation Number / School Code</td>
                      <td className="py-3 px-4 text-slate-500 italic">To be configured (Demo information)</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">4</td>
                      <td className="py-3 px-4 font-semibold text-slate-900">Complete Address & PIN Code</td>
                      <td className="py-3 px-4">Sector 4, Gomti Nagar, Lucknow, Uttar Pradesh — 226010</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">5</td>
                      <td className="py-3 px-4 font-semibold text-slate-900">Principal Name & Qualification</td>
                      <td className="py-3 px-4">Dr. Ananya Sengupta, M.Sc., M.Ed., Ph.D.</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">6</td>
                      <td className="py-3 px-4 font-semibold text-slate-900">School Email Address</td>
                      <td className="py-3 px-4 font-mono text-xs">info@sunrisepublic.edu</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">7</td>
                      <td className="py-3 px-4 font-semibold text-slate-900">Helpline / Contact Desk</td>
                      <td className="py-3 px-4">
                        <a href="tel:+915222990000" className="text-primary hover:underline font-semibold">
                          +91 522 299 0000
                        </a>
                      </td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">8</td>
                      <td className="py-3 px-4 font-semibold text-slate-900">Year of Establishment</td>
                      <td className="py-3 px-4">2011</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-medium text-slate-400">9</td>
                      <td className="py-3 px-4 font-semibold text-slate-900">Academic Session Duration</td>
                      <td className="py-3 px-4">1st April to 31st March</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB B: DOCUMENTS & INFORMATION */}
          {activeTab === "docs" && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h2 className="text-lg sm:text-xl font-bold text-slate-900 font-serif">
                  B. Documents & Information
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                  Official downloadable one-page demo summary documents and statutory certifications.
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs sm:text-sm border-collapse">
                  <thead>
                    <tr className="bg-slate-100 text-slate-700 border-b border-slate-200">
                      <th className="py-3 px-4 font-semibold w-12">S.No.</th>
                      <th className="py-3 px-4 font-semibold">Document Title</th>
                      <th className="py-3 px-4 font-semibold hidden md:table-cell">Regulatory Focus</th>
                      <th className="py-3 px-4 font-semibold text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    {[
                      {
                        no: 1,
                        title: "Mandatory Public Disclosure Summary (Appendix-IX)",
                        focus: "Complete institutional compliance checklist",
                        file: "/documents/public-disclosure-summary.pdf",
                      },
                      {
                        no: 2,
                        title: "School Profile, SMC & Governance Structure",
                        focus: "School Management Committee & society overview",
                        file: "/documents/school-information.pdf",
                      },
                      {
                        no: 3,
                        title: "Campus Infrastructure & Laboratories Specifications",
                        focus: "Built-up area, lab apparatus, and smart classrooms",
                        file: "/documents/infrastructure-overview.pdf",
                      },
                      {
                        no: 4,
                        title: "Faculty Qualifications & Teaching Cadre Overview",
                        focus: "100% certified PGT/TGT/PRT faculty roster",
                        file: "/documents/faculty-staff-overview.pdf",
                      },
                      {
                        no: 5,
                        title: "Approved Annual Fee Structure Schedule 2026–27",
                        focus: "Transparent wing-wise composite fee schedule",
                        file: "/documents/fee-structure.pdf",
                      },
                      {
                        no: 6,
                        title: "Academic Calendar & Examination Schedule 2026–27",
                        focus: "220 working days, term tests & vacation breaks",
                        file: "/documents/academic-calendar.pdf",
                      },
                    ].map((doc) => (
                      <tr key={doc.no} className="hover:bg-slate-50 transition-colors">
                        <td className="py-3 px-4 font-medium text-slate-400">{doc.no}</td>
                        <td className="py-3 px-4 font-semibold text-slate-900">{doc.title}</td>
                        <td className="py-3 px-4 text-slate-600 hidden md:table-cell">{doc.focus}</td>
                        <td className="py-3 px-4 text-right">
                          <a
                            href={doc.file}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 text-xs font-bold text-[#042954] hover:text-amber-600 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg transition-colors"
                          >
                            <span>Download PDF (1 Page)</span>
                            <span className="text-[10px]">&darr;</span>
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB C: RESULTS & ACADEMICS */}
          {activeTab === "results" && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h2 className="text-lg sm:text-xl font-bold text-slate-900 font-serif">
                  C. Academic Excellence & Board Results
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                  Three-year cumulative CBSE Board Examination results for Grade X and Grade XII.
                </p>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs sm:text-sm border-collapse">
                  <thead>
                    <tr className="bg-slate-100 text-slate-700 border-b border-slate-200">
                      <th className="py-3 px-4 font-semibold">Academic Session</th>
                      <th className="py-3 px-4 font-semibold">Class X Pass %</th>
                      <th className="py-3 px-4 font-semibold">Class X (&gt;90% Honors)</th>
                      <th className="py-3 px-4 font-semibold">Class XII Pass %</th>
                      <th className="py-3 px-4 font-semibold">Class XII (&gt;90% Honors)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    <tr>
                      <td className="py-3 px-4 font-bold text-slate-900">2024–2025 (Demo)</td>
                      <td className="py-3 px-4 font-semibold text-emerald-700">100%</td>
                      <td className="py-3 px-4">32.5% of students</td>
                      <td className="py-3 px-4 font-semibold text-emerald-700">99.2%</td>
                      <td className="py-3 px-4">28.4% of students</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-bold text-slate-900">2023–2024 (Demo)</td>
                      <td className="py-3 px-4 font-semibold text-emerald-700">100%</td>
                      <td className="py-3 px-4">30.8% of students</td>
                      <td className="py-3 px-4 font-semibold text-emerald-700">98.8%</td>
                      <td className="py-3 px-4">26.1% of students</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-bold text-slate-900">2022–2023 (Demo)</td>
                      <td className="py-3 px-4 font-semibold text-emerald-700">99.4%</td>
                      <td className="py-3 px-4">29.0% of students</td>
                      <td className="py-3 px-4 font-semibold text-emerald-700">98.5%</td>
                      <td className="py-3 px-4">25.0% of students</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="pt-2">
                <a
                  href="/documents/academic-information.pdf"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-[#042954] hover:text-amber-600 bg-slate-100 hover:bg-slate-200 px-3.5 py-2 rounded-lg transition-colors"
                >
                  <span>Download Complete Academic & Results Sheet (1 Page PDF)</span>
                  <span>&rarr;</span>
                </a>
              </div>
            </div>
          )}

          {/* TAB D: STAFF & FACULTY */}
          {activeTab === "staff" && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h2 className="text-lg sm:text-xl font-bold text-slate-900 font-serif">
                  D. Staff & Teaching Faculty Strength
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                  Qualified educators adhering strictly to CBSE and NCTE educator standards.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center">
                  <span className="text-2xl font-bold text-[#042954] block">1 : 20</span>
                  <span className="text-xs text-slate-500 font-medium uppercase tracking-wider">Teacher-Student Ratio</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center">
                  <span className="text-2xl font-bold text-[#042954] block">100%</span>
                  <span className="text-xs text-slate-500 font-medium uppercase tracking-wider">B.Ed / Certified</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center">
                  <span className="text-2xl font-bold text-[#042954] block">14</span>
                  <span className="text-xs text-slate-500 font-medium uppercase tracking-wider">PGT Instructors</span>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 text-center">
                  <span className="text-2xl font-bold text-[#042954] block">18</span>
                  <span className="text-xs text-slate-500 font-medium uppercase tracking-wider">TGT Instructors</span>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs sm:text-sm border-collapse">
                  <thead>
                    <tr className="bg-slate-100 text-slate-700 border-b border-slate-200">
                      <th className="py-3 px-4 font-semibold">Staff Designation</th>
                      <th className="py-3 px-4 font-semibold">Headcount</th>
                      <th className="py-3 px-4 font-semibold">Eligibility Qualification</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-700">
                    <tr>
                      <td className="py-3 px-4 font-semibold text-slate-900">Principal</td>
                      <td className="py-3 px-4">1</td>
                      <td className="py-3 px-4">M.Sc., M.Ed., Ph.D.</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-semibold text-slate-900">Post Graduate Teachers (PGT)</td>
                      <td className="py-3 px-4">14</td>
                      <td className="py-3 px-4">Post Graduate in Subject + B.Ed.</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-semibold text-slate-900">Trained Graduate Teachers (TGT)</td>
                      <td className="py-3 px-4">18</td>
                      <td className="py-3 px-4">Graduate in Subject + B.Ed.</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-semibold text-slate-900">Primary Teachers (PRT)</td>
                      <td className="py-3 px-4">16</td>
                      <td className="py-3 px-4">Graduate + B.Ed. / D.El.Ed.</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-semibold text-slate-900">Special Educator</td>
                      <td className="py-3 px-4">1</td>
                      <td className="py-3 px-4">B.Ed. Special Education (RCI Registered)</td>
                    </tr>
                    <tr>
                      <td className="py-3 px-4 font-semibold text-slate-900">Wellness & Adolescent Counsellor</td>
                      <td className="py-3 px-4">1</td>
                      <td className="py-3 px-4">M.A. Psychology / Child Guidance Diploma</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB E: INFRASTRUCTURE */}
          {activeTab === "infra" && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h2 className="text-lg sm:text-xl font-bold text-slate-900 font-serif">
                  E. Physical Infrastructure & Safety Norms
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                  Details of campus area, sports fields, laboratories, and safety measures.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <h3 className="font-bold text-slate-900 text-sm">Total Campus Area</h3>
                  <p className="text-xs text-slate-600 mt-1">14,200 sq. meters (~3.5 Acres) secure single-plot site.</p>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <h3 className="font-bold text-slate-900 text-sm">Outdoor Sports Turf</h3>
                  <p className="text-xs text-slate-600 mt-1">5,200 sq. meters 400m running track, football, and cricket nets.</p>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <h3 className="font-bold text-slate-900 text-sm">Central Library Hub</h3>
                  <p className="text-xs text-slate-600 mt-1">Over 10,500 titles, periodicals, and e-learning terminals.</p>
                </div>
              </div>

              <div className="pt-2">
                <a
                  href="/documents/infrastructure-overview.pdf"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-[#042954] hover:text-amber-600 bg-slate-100 hover:bg-slate-200 px-3.5 py-2 rounded-lg transition-colors"
                >
                  <span>Download Infrastructure Specifications (1 Page PDF)</span>
                  <span>&rarr;</span>
                </a>
              </div>
            </div>
          )}

          {/* TAB F: GRIEVANCE & SUPPORT */}
          {activeTab === "grievance" && (
            <div className="space-y-6 animate-fade-in">
              <div>
                <h2 className="text-lg sm:text-xl font-bold text-slate-900 font-serif">
                  F. Student Support, Safety & Grievance Mechanism
                </h2>
                <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
                  Constituted committees for child safety, prevention of harassment, and parent grievance redressal.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-5 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
                  <h3 className="font-bold text-slate-900 text-sm sm:text-base">
                    POCSO & Child Safety Committee
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Operates in accordance with the POCSO Act guidelines to safeguard student well-being. Includes female senior faculty, parent representatives, and external legal counselor.
                  </p>
                  <p className="text-xs font-medium text-slate-700">Contact: childprotection@sunrisepublic.edu</p>
                </div>

                <div className="p-5 rounded-xl border border-slate-200 bg-slate-50 space-y-2">
                  <h3 className="font-bold text-slate-900 text-sm sm:text-base">
                    Parent Grievance Redressal Cell
                  </h3>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Structured forum to address parent queries, academic feedback, and transportation concerns within a guaranteed 48-hour response protocol.
                  </p>
                  <p className="text-xs font-medium text-slate-700">Officer In-Charge: grievance@sunrisepublic.edu</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
