import { Link } from "react-router-dom";

interface ResourceItem {
  id: string;
  title: string;
  category: string;
  description: string;
  filename: string;
  pages: string;
  fileSize: string;
  docRef: string;
}

const APPROVED_RESOURCES: ResourceItem[] = [
  {
    id: "prospectus",
    title: "School Prospectus 2026–27",
    category: "General & Admissions",
    description: "Executive institutional summary highlighting academic ethos, foundational stage care, Atal Tinkering STEM initiatives, and athletic infrastructure.",
    filename: "/documents/school-prospectus.pdf",
    pages: "1 Page (A4)",
    fileSize: "4.1 KB",
    docRef: "PROSP-2026-06",
  },
  {
    id: "calendar",
    title: "Academic Calendar 2026–27",
    category: "Academics",
    description: "Detailed term dates, periodic test windows, half-yearly and pre-board examinations, gazetted holidays, and vacation schedules for 220 working days.",
    filename: "/documents/academic-calendar.pdf",
    pages: "1 Page (A4)",
    fileSize: "4.0 KB",
    docRef: "CAL-2026-07",
  },
  {
    id: "guidelines",
    title: "Admission Guidelines & Age Norms",
    category: "Admissions",
    description: "Step-by-step intake procedure, age eligibility as on 31st March 2026, required document verification checklist, and online application portal instructions.",
    filename: "/documents/admission-guidelines.pdf",
    pages: "1 Page (A4)",
    fileSize: "4.0 KB",
    docRef: "ADM-GUIDE-2026-08",
  },
  {
    id: "fees",
    title: "Approved Fee Structure 2026–27",
    category: "Admissions & Finance",
    description: "School Management Committee approved annual composite fee schedule across Pre-Primary, Primary, Middle, Secondary, and Senior Secondary streams.",
    filename: "/documents/fee-structure.pdf",
    pages: "1 Page (A4)",
    fileSize: "4.2 KB",
    docRef: "FEE-2026-09",
  },
  {
    id: "syllabus",
    title: "Curriculum & Syllabus Overview",
    category: "Academics",
    description: "Comprehensive CBSE and NEP 2020 curriculum matrix detailing core subject frameworks and electives across Grades 1 through 12.",
    filename: "/documents/syllabus-overview.pdf",
    pages: "1 Page (A4)",
    fileSize: "4.1 KB",
    docRef: "SYLL-2026-10",
  },
  {
    id: "disclosure",
    title: "Mandatory Public Disclosure (Appendix-IX)",
    category: "Compliance & Governance",
    description: "Official statutory information table covering CBSE affiliation status, infrastructure parameters, faculty roster headcount, and safety compliance.",
    filename: "/documents/public-disclosure-summary.pdf",
    pages: "1 Page (A4)",
    fileSize: "4.1 KB",
    docRef: "PUB-DISC-2026-01",
  },
];

export function ResourcesPage() {
  return (
    <div className="bg-slate-50 min-h-screen py-10 lg:py-14">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Breadcrumb & Section Eyebrow */}
        <div className="space-y-2">
          <nav className="flex items-center text-xs text-slate-500 gap-2">
            <Link to="/" className="hover:text-primary transition-colors">Home</Link>
            <span>&rsaquo;</span>
            <span className="text-slate-900 font-semibold">Resources & Downloads</span>
          </nav>
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 font-serif tracking-tight">
                Resources & Downloads Hub
              </h1>
              <p className="text-slate-600 text-sm sm:text-base mt-1 max-w-2xl">
                Download official school prospectuses, academic calendars, curriculum guides, and fee circulars for the 2026–27 academic session.
              </p>
            </div>
            <Link
              to="/apply"
              className="inline-flex items-center gap-1.5 bg-amber-400 hover:bg-amber-300 text-slate-900 text-xs sm:text-sm font-bold px-4 py-2.5 rounded-lg shadow-sm transition-all shrink-0 self-start md:self-auto"
            >
              <span>Apply Online for 2026–27</span>
              <span>&rarr;</span>
            </Link>
          </div>
        </div>

        {/* Demo Standards Notice */}
        <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs text-slate-600 flex items-start gap-3 shadow-xs">
          <span className="text-base leading-none text-[#042954]">📄</span>
          <div>
            <strong className="font-semibold text-slate-900 block">Single-Page Institutional Format:</strong>
            In accordance with digital accessibility norms, all official download summaries provided below are formatted as concise, professional <strong>one-page A4 PDF documents</strong> containing key institutional metrics and policies.
          </div>
        </div>

        {/* Resource Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {APPROVED_RESOURCES.map((item) => (
            <div
              key={item.id}
              className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col justify-between shadow-xs hover:shadow-md hover:border-slate-300 transition-all duration-200 group"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="inline-block text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-700">
                    {item.category}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">{item.docRef}</span>
                </div>

                <div>
                  <h2 className="text-lg font-bold text-slate-900 font-serif group-hover:text-primary transition-colors leading-snug">
                    {item.title}
                  </h2>
                  <p className="text-xs text-slate-600 mt-2 leading-relaxed line-clamp-3">
                    {item.description}
                  </p>
                </div>
              </div>

              <div className="pt-5 mt-4 border-t border-slate-100 flex items-center justify-between gap-3 text-xs">
                <div className="text-slate-400 text-[11px] space-y-0.5">
                  <span className="font-medium text-slate-600 block">{item.pages}</span>
                  <span>PDF Document • {item.fileSize}</span>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  <a
                    href={item.filename}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 bg-[#042954] hover:bg-[#021b38] text-white text-xs font-semibold px-3 py-1.5 rounded-lg shadow-xs transition-colors"
                    title={`Download ${item.title}`}
                  >
                    <span>Download</span>
                    <svg className="w-3.5 h-3.5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Additional Guidance Footer Callout */}
        <div className="rounded-2xl border border-slate-200 bg-slate-100/70 p-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-600">
          <div className="space-y-1 text-center sm:text-left">
            <h3 className="font-bold text-slate-900 text-sm">Need customized academic or fee details?</h3>
            <p className="text-slate-500">Contact the Admissions & Student Records desk at our Gomti Nagar campus.</p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to="/contact"
              className="bg-white hover:bg-slate-50 text-slate-900 border border-slate-300 font-semibold px-4 py-2 rounded-lg transition-colors whitespace-nowrap"
            >
              Contact Office
            </Link>
            <a
              href="tel:+915222990000"
              className="bg-[#042954] hover:bg-[#021b38] text-white font-semibold px-4 py-2 rounded-lg transition-colors whitespace-nowrap"
            >
              Call Helpline
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
