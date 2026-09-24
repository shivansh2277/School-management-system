import { Link } from "react-router-dom";

export function AdmissionsPage() {
  return (
    <div className="space-y-16 sm:space-y-20 pb-16">
      {/* 1. HERO BANNER */}
      <section className="bg-gradient-to-b from-indigo-50/80 via-ground to-white py-14 sm:py-20 border-b border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Admissions Open for Academic Session 2025–26</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
            Admissions at Sunrise School
          </h1>
          <p className="text-base sm:text-lg text-ink-soft max-w-2xl mx-auto leading-relaxed">
            Join an enriching learning community where every student is encouraged to discover their passions, think deeply, and thrive.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <Link
              to="/apply"
              className="bg-primary hover:bg-primary-dark text-white font-semibold px-7 py-3 rounded-input shadow-md transition-all text-sm"
            >
              Fill Online Application Form &rarr;
            </Link>
            <a
              href="#process"
              className="bg-white hover:bg-slate-50 text-slate-800 font-semibold px-6 py-3 rounded-input border border-slate-300 shadow-sm transition-all text-sm"
            >
              View Admission Steps
            </a>
          </div>
        </div>
      </section>

      {/* 2. ADMISSION OVERVIEW & TRANSPARENCY NOTICE */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-7 space-y-4">
            <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
              Welcoming New Learners
            </span>
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight">
              A Transparent, Child-Friendly Admission Process
            </h2>
            <p className="text-sm sm:text-base text-ink-soft leading-relaxed">
              We welcome prospective parents and guardians to explore admissions for Nursery through Class XI for the 2025–26 academic year. Our admission criteria are fair, merit-guided, and in full compliance with CBSE and Right to Education (RTE) guidelines.
            </p>
            <p className="text-sm sm:text-base text-ink-soft leading-relaxed">
              For foundational classes (Nursery to Class 2), there is <strong>no formal entrance exam</strong>. Instead, we arrange an informal interactive session with parents and the child to understand their developmental milestones and ensure a harmonious transition.
            </p>
            <div className="pt-2 flex flex-wrap gap-4 text-xs font-medium text-slate-700">
              <span className="flex items-center gap-1.5 bg-ground px-3 py-1.5 rounded-lg border border-rule">
                <span>📅</span> Application Window: Open Now
              </span>
              <span className="flex items-center gap-1.5 bg-ground px-3 py-1.5 rounded-lg border border-rule">
                <span>🏫</span> Campus Visits: Mon–Sat 9:00 AM – 2:00 PM
              </span>
            </div>
          </div>

          <div className="lg:col-span-5">
            <div className="bg-surface rounded-2xl border border-rule shadow-card p-6 sm:p-8 space-y-4">
              <div className="flex items-center justify-between border-b border-rule pb-3">
                <h3 className="font-bold text-base text-slate-900">Online Admission Portal</h3>
                <span className="text-xs bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded">
                  Live
                </span>
              </div>
              <p className="text-xs text-ink-soft leading-relaxed">
                Parents can submit admission applications, upload student details, and track application status entirely online through our admissions engine.
              </p>
              <div className="space-y-2.5 pt-2">
                <Link
                  to="/apply"
                  className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary-dark text-white font-semibold py-2.5 px-4 rounded-input text-xs shadow-sm transition-all"
                >
                  <span>Start New Application</span>
                  <span>&rarr;</span>
                </Link>
                <Link
                  to="/apply"
                  className="w-full flex items-center justify-center gap-2 bg-ground hover:bg-slate-100 text-slate-700 font-semibold py-2.5 px-4 rounded-input text-xs border border-rule transition-all"
                >
                  <span>Track Application Status</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. STEP-BY-STEP ADMISSION PROCESS */}
      <section id="process" className="bg-ground py-16 border-y border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
              Five-Step Pathway
            </span>
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight">
              How to Secure Admission
            </h2>
            <p className="text-sm text-ink-soft">
              A smooth, step-by-step enrollment pathway designed for parent convenience.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {/* Step 1 */}
            <div className="bg-white rounded-2xl p-5 border border-rule shadow-sm space-y-3 relative">
              <span className="w-8 h-8 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center">
                1
              </span>
              <h3 className="font-bold text-sm text-slate-900">Registration</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Submit the online application form with student details or purchase an enquiry prospectus from the school reception.
              </p>
            </div>

            {/* Step 2 */}
            <div className="bg-white rounded-2xl p-5 border border-rule shadow-sm space-y-3 relative">
              <span className="w-8 h-8 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center">
                2
              </span>
              <h3 className="font-bold text-sm text-slate-900">Campus Interaction</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Visit the campus for an informal interaction (Classes Nur–II) or a diagnostic aptitude test (Classes III–XI).
              </p>
            </div>

            {/* Step 3 */}
            <div className="bg-white rounded-2xl p-5 border border-rule shadow-sm space-y-3 relative">
              <span className="w-8 h-8 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center">
                3
              </span>
              <h3 className="font-bold text-sm text-slate-900">Verification</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Submit self-attested copies of birth certificate, previous school report card, and residential address proof.
              </p>
            </div>

            {/* Step 4 */}
            <div className="bg-white rounded-2xl p-5 border border-rule shadow-sm space-y-3 relative">
              <span className="w-8 h-8 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center">
                4
              </span>
              <h3 className="font-bold text-sm text-slate-900">Seat Offer</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Formal provisional admission offer is intimated via SMS and Email within 3 working days of interaction.
              </p>
            </div>

            {/* Step 5 */}
            <div className="bg-white rounded-2xl p-5 border border-rule shadow-sm space-y-3 relative">
              <span className="w-8 h-8 rounded-full bg-emerald-600 text-white text-xs font-bold flex items-center justify-center">
                5
              </span>
              <h3 className="font-bold text-sm text-slate-900">Fee & Enrollment</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Complete admission fee payment at the fee counter or via online banking, receive scholar number and uniform kit.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. AGE CRITERIA & REQUIRED DOCUMENTS */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          {/* Age Eligibility Table */}
          <div className="lg:col-span-7 space-y-4">
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
                Eligibility Guidelines
              </span>
              <h3 className="text-2xl font-bold text-slate-900">Age Criteria (as of 31st March 2025)</h3>
              <p className="text-xs text-ink-soft">Calculated strictly in accordance with NEP & Uttar Pradesh government regulations.</p>
            </div>

            <div className="overflow-x-auto rounded-xl border border-rule shadow-sm">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-100 text-slate-700 font-bold uppercase tracking-wider border-b border-rule">
                  <tr>
                    <th className="px-4 py-3">Class</th>
                    <th className="px-4 py-3">Minimum Age</th>
                    <th className="px-4 py-3">Maximum Age</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-rule bg-white">
                  <tr>
                    <td className="px-4 py-2.5 font-semibold text-slate-900">Nursery / Pre-School</td>
                    <td className="px-4 py-2.5 text-slate-600">3 Years</td>
                    <td className="px-4 py-2.5 text-slate-600">4 Years</td>
                  </tr>
                  <tr className="bg-slate-50/50">
                    <td className="px-4 py-2.5 font-semibold text-slate-900">LKG (Lower KG)</td>
                    <td className="px-4 py-2.5 text-slate-600">4 Years</td>
                    <td className="px-4 py-2.5 text-slate-600">5 Years</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2.5 font-semibold text-slate-900">UKG (Upper KG)</td>
                    <td className="px-4 py-2.5 text-slate-600">5 Years</td>
                    <td className="px-4 py-2.5 text-slate-600">6 Years</td>
                  </tr>
                  <tr className="bg-slate-50/50">
                    <td className="px-4 py-2.5 font-semibold text-slate-900">Class I</td>
                    <td className="px-4 py-2.5 text-slate-600">6 Years</td>
                    <td className="px-4 py-2.5 text-slate-600">7 Years</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2.5 font-semibold text-slate-900">Class II to V</td>
                    <td className="px-4 py-2.5 text-slate-600">7 – 10 Years</td>
                    <td className="px-4 py-2.5 text-slate-600">Corresponding progression</td>
                  </tr>
                  <tr className="bg-slate-50/50">
                    <td className="px-4 py-2.5 font-semibold text-slate-900">Class VI to IX</td>
                    <td className="px-4 py-2.5 text-slate-600">11 – 14 Years</td>
                    <td className="px-4 py-2.5 text-slate-600">Subject to previous report card</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-2.5 font-semibold text-slate-900">Class XI</td>
                    <td className="px-4 py-2.5 text-slate-600">15 – 17 Years</td>
                    <td className="px-4 py-2.5 text-slate-600">Based on Class X Board Marks</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Required Documents Checklist */}
          <div className="lg:col-span-5 space-y-4">
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-700 bg-amber-100 px-3 py-1 rounded-full">
                Verification Checklist
              </span>
              <h3 className="text-2xl font-bold text-slate-900">Required Documents</h3>
              <p className="text-xs text-ink-soft">Please keep photocopies and originals ready at the time of interaction.</p>
            </div>

            <div className="bg-surface rounded-2xl border border-rule shadow-sm p-6 space-y-3 text-xs text-slate-700">
              <div className="flex items-start gap-2.5">
                <span className="text-primary font-bold text-sm">📄</span>
                <div>
                  <span className="font-semibold block text-slate-900">Birth Certificate</span>
                  <span>Issued by Municipal Corporation / Nagar Nigam (Mandatory for all).</span>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <span className="text-primary font-bold text-sm">📷</span>
                <div>
                  <span className="font-semibold block text-slate-900">Passport Photos</span>
                  <span>4 passport-sized color photos of student and 2 each of parents.</span>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <span className="text-primary font-bold text-sm">📜</span>
                <div>
                  <span className="font-semibold block text-slate-900">Previous School Report Card</span>
                  <span>Previous year's annual marksheet (for Class 1 and above).</span>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <span className="text-primary font-bold text-sm">🏫</span>
                <div>
                  <span className="font-semibold block text-slate-900">Transfer Certificate (TC)</span>
                  <span>Original counter-signed TC required from last school attended.</span>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <span className="text-primary font-bold text-sm">🏠</span>
                <div>
                  <span className="font-semibold block text-slate-900">Address Proof</span>
                  <span>Aadhaar Card, Passport, or Electricity bill of parent.</span>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <span className="text-primary font-bold text-sm">💉</span>
                <div>
                  <span className="font-semibold block text-slate-900">Medical Record & Blood Group</span>
                  <span>Vaccination chart and blood group certificate.</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. CONTACT ADMISSIONS DESK */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-slate-900 text-white rounded-2xl p-8 sm:p-12 shadow-card grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-8 space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-400">
              Need Assistance?
            </span>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Connect with Our Admissions Counselor
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed max-w-xl">
              Have questions regarding fee structure, bus routes, or subject stream eligibility? Our counseling team is available throughout the week to assist your family.
            </p>
            <div className="pt-2 flex flex-wrap gap-6 text-xs text-slate-300">
              <div>
                <span className="block text-slate-400">Helpline:</span>
                <span className="font-bold text-white text-sm">+91 522 299 0000</span>
              </div>
              <div>
                <span className="block text-slate-400">Email:</span>
                <span className="font-bold text-white text-sm">admissions@sunrisepublic.edu</span>
              </div>
              <div>
                <span className="block text-slate-400">Visiting Hours:</span>
                <span className="font-bold text-white text-sm">Mon–Sat 9:00 AM – 2:00 PM</span>
              </div>
            </div>
          </div>

          <div className="lg:col-span-4 flex flex-col gap-3">
            <Link
              to="/apply"
              className="bg-primary hover:bg-primary-dark text-white font-bold py-3.5 px-6 rounded-input text-center text-sm shadow-md transition-all"
            >
              Fill Online Application Form &rarr;
            </Link>
            <Link
              to="/facilities"
              className="bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold py-3 px-6 rounded-input text-center text-xs border border-slate-700 transition-all"
            >
              View Campus Facilities
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
