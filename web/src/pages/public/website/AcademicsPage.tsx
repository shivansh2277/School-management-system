import { Link } from "react-router-dom";

export function AcademicsPage() {
  return (
    <div className="space-y-16 sm:space-y-20 pb-16">
      {/* 1. HERO BANNER */}
      <section className="bg-gradient-to-b from-indigo-50/80 via-ground to-white py-14 sm:py-20 border-b border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
            Scholastic Excellence
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
            Academics at Sunrise School
          </h1>
          <p className="text-base sm:text-lg text-ink-soft max-w-2xl mx-auto leading-relaxed">
            A comprehensive, NEP 2020-aligned CBSE curriculum cultivating critical discernment, scientific curiosity, and lifelong love for learning.
          </p>
        </div>
      </section>

      {/* 2. ACADEMIC APPROACH & METHODOLOGY */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-6 space-y-4">
            <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
              Our Pedagogical Philosophy
            </span>
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight">
              Moving Beyond Rote to Conceptual Mastery
            </h2>
            <p className="text-sm sm:text-base text-ink-soft leading-relaxed">
              At Sunrise School, classroom learning is dynamic and participatory. We reject monotonous rote memorization in favor of inquiry, experimentation, and meaningful peer discourse.
            </p>
            <div className="space-y-3 pt-2">
              <div className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                  ✓
                </span>
                <div>
                  <h4 className="font-bold text-sm text-slate-900">Experiential & Project-Based</h4>
                  <p className="text-xs text-ink-soft mt-0.5">Students engage in hands-on science experiments, field observations, and interdisciplinary theme projects.</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                  ✓
                </span>
                <div>
                  <h4 className="font-bold text-sm text-slate-900">Bilingual Fluency & Communication</h4>
                  <p className="text-xs text-ink-soft mt-0.5">Equal emphasis on English articulation, Hindi literature appreciation, and classical/foreign language exposure.</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">
                  ✓
                </span>
                <div>
                  <h4 className="font-bold text-sm text-slate-900">Personalized Mentorship</h4>
                  <p className="text-xs text-ink-soft mt-0.5">With a 1:18 faculty ratio, our teachers tailor guidance to the specific pace and strengths of each student.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-6">
            <div className="bg-surface rounded-2xl border border-rule shadow-card p-6 sm:p-8 space-y-5">
              <h3 className="font-bold text-lg text-slate-900 border-b border-rule pb-3">
                Core Academic Pillars
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-ground border border-rule/70 space-y-1">
                  <span className="text-xl">🔬</span>
                  <div className="font-bold text-sm text-slate-900">STEM & Robotics</div>
                  <div className="text-xs text-ink-soft">Atal Tinkering style hands-on experimentation from Class 3.</div>
                </div>
                <div className="p-4 rounded-xl bg-ground border border-rule/70 space-y-1">
                  <span className="text-xl">📐</span>
                  <div className="font-bold text-sm text-slate-900">Mathematics Lab</div>
                  <div className="text-xs text-ink-soft">Geometry kits, algebraic puzzles, and visual model reasoning.</div>
                </div>
                <div className="p-4 rounded-xl bg-ground border border-rule/70 space-y-1">
                  <span className="text-xl">📖</span>
                  <div className="font-bold text-sm text-slate-900">Reading Circles</div>
                  <div className="text-xs text-ink-soft">Daily library reading hours, book reviews, and creative writing.</div>
                </div>
                <div className="p-4 rounded-xl bg-ground border border-rule/70 space-y-1">
                  <span className="text-xl">🎙️</span>
                  <div className="font-bold text-sm text-slate-900">Debate & Elocution</div>
                  <div className="text-xs text-ink-soft">Fostering public speaking, parliamentary debate, and MUN training.</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. THREE-TIER WING STRUCTURE */}
      <section className="bg-ground py-16 border-y border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
              Wing Structure
            </span>
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight">
              Progressive Learning Across Grades
            </h2>
            <p className="text-sm text-ink-soft">
              Each developmental milestone receives tailored curriculum design, age-appropriate infrastructure, and specialized educators.
            </p>
          </div>

          <div className="space-y-8">
            {/* Wing 1 */}
            <div className="bg-white rounded-2xl p-6 sm:p-8 border border-rule shadow-sm grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-4 space-y-2">
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-100 text-amber-800">
                  Nursery, LKG, UKG, Class I & II
                </span>
                <h3 className="text-2xl font-bold text-slate-900">Foundational Stage</h3>
                <p className="text-xs text-ink-soft leading-relaxed">
                  Focusing on joyful early childhood education where play, phonics, sensorial discovery, and foundational literacy create a loving bridge between home and school.
                </p>
              </div>
              <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-ground border border-rule/80">
                  <div className="font-bold text-slate-900 mb-1">Key Focus</div>
                  <div className="text-ink-soft">Motor coordination, bilingual phonics, sensorial exploration, social habits.</div>
                </div>
                <div className="lg:col-span-1 p-4 rounded-xl bg-ground border border-rule/80">
                  <div className="font-bold text-slate-900 mb-1">Methodology</div>
                  <div className="text-ink-soft">Montessori-inspired activity stations, storytelling, puppet play, music.</div>
                </div>
                <div className="p-4 rounded-xl bg-ground border border-rule/80">
                  <div className="font-bold text-slate-900 mb-1">Assessment</div>
                  <div className="text-ink-soft">Continuous observation portfolios; zero formal exam stress.</div>
                </div>
              </div>
            </div>

            {/* Wing 2 */}
            <div className="bg-white rounded-2xl p-6 sm:p-8 border border-rule shadow-sm grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-4 space-y-2">
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-100 text-indigo-800">
                  Class III to VIII
                </span>
                <h3 className="text-2xl font-bold text-slate-900">Preparatory & Middle Stage</h3>
                <p className="text-xs text-ink-soft leading-relaxed">
                  Deepening subject understanding through inquiry, structured lab experiments, computational thinking, and artistic enrichment.
                </p>
              </div>
              <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-ground border border-rule/80">
                  <div className="font-bold text-slate-900 mb-1">Subjects</div>
                  <div className="text-ink-soft">English, Hindi, Sanskrit/French, Mathematics, Integrated Science, Social Sciences, Computer/AI.</div>
                </div>
                <div className="p-4 rounded-xl bg-ground border border-rule/80">
                  <div className="font-bold text-slate-900 mb-1">Enrichment</div>
                  <div className="text-ink-soft">Science exhibitions, coding competitions, math olympiads, weekly clubs.</div>
                </div>
                <div className="p-4 rounded-xl bg-ground border border-rule/80">
                  <div className="font-bold text-slate-900 mb-1">Assessment</div>
                  <div className="text-ink-soft">Periodic tests, project presentations, subject enrichment assessments.</div>
                </div>
              </div>
            </div>

            {/* Wing 3 */}
            <div className="bg-white rounded-2xl p-6 sm:p-8 border border-rule shadow-sm grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
              <div className="lg:col-span-4 space-y-2">
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800">
                  Class IX to XII
                </span>
                <h3 className="text-2xl font-bold text-slate-900">Secondary & Senior Secondary</h3>
                <p className="text-xs text-ink-soft leading-relaxed">
                  Rigorous academic streams preparing students for CBSE All-India Senior School Certificate Examination (AISSCE) and prestigious university entrances.
                </p>
              </div>
              <div className="lg:col-span-8 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-ground border border-rule/80">
                  <div className="font-bold text-slate-900 mb-1">Stream Options</div>
                  <div className="text-ink-soft">
                    • Science: Physics, Chem, Math / Biology, CS<br />
                    • Commerce: Accountancy, Business, Economics, Math/IP<br />
                    • Humanities: Pol Sci, History, Psychology, Economics
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-ground border border-rule/80">
                  <div className="font-bold text-slate-900 mb-1">Competitive Mentoring</div>
                  <div className="text-ink-soft">Doubt-clearing clinics, regular mock tests, JEE/NEET/CUET foundation support.</div>
                </div>
                <div className="p-4 rounded-xl bg-ground border border-rule/80">
                  <div className="font-bold text-slate-900 mb-1">Board Prep</div>
                  <div className="text-ink-soft">CBSE sample paper analysis, timed test series, individualized feedback.</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. TECHNOLOGY & ASSESSMENT APPROACH */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Tech in Education */}
          <div className="bg-surface rounded-2xl border border-rule p-8 space-y-4">
            <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center text-xl font-bold">
              💻
            </div>
            <h3 className="text-xl font-bold text-slate-900">Technology-Enabled Learning</h3>
            <p className="text-xs sm:text-sm text-ink-soft leading-relaxed">
              We leverage digital tools to enhance comprehension, not to replace the human touch of great teachers.
            </p>
            <ul className="text-xs text-slate-600 space-y-2">
              <li className="flex items-center gap-2">
                <span className="text-primary font-bold">•</span>
                <span>Interactive smart panels in all 40+ instructional rooms</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-primary font-bold">•</span>
                <span>60-seat high-speed Computer and Artificial Intelligence lab</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-primary font-bold">•</span>
                <span>Curated digital learning modules and e-library access</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-primary font-bold">•</span>
                <span>Cloud-based ERP for tracking grades, assignments, and attendance</span>
              </li>
            </ul>
          </div>

          {/* Assessment Approach */}
          <div className="bg-surface rounded-2xl border border-rule p-8 space-y-4">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center text-xl font-bold">
              📊
            </div>
            <h3 className="text-xl font-bold text-slate-900">CBSE Assessment Architecture</h3>
            <p className="text-xs sm:text-sm text-ink-soft leading-relaxed">
              Assessment at Sunrise is formative, diagnostic, and progress-oriented, designed to identify learning gaps and celebrate student growth.
            </p>
            <ul className="text-xs text-slate-600 space-y-2">
              <li className="flex items-center gap-2">
                <span className="text-emerald-600 font-bold">•</span>
                <span>Periodic Tests (PT-1, PT-2, PT-3) spaced across academic terms</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-emerald-600 font-bold">•</span>
                <span>Subject Enrichment activities (Lab practicals, speaking & listening assessments)</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-emerald-600 font-bold">•</span>
                <span>Regular parent-teacher review sessions with actionable feedback</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="text-emerald-600 font-bold">•</span>
                <span>Diagnostic analytics ensuring every learner receives remedial intervention</span>
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* 5. CALL TO ACTION STRIP */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-primary to-indigo-900 text-white rounded-2xl p-8 sm:p-10 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-card">
          <div className="space-y-1 text-center sm:text-left">
            <h3 className="font-bold text-xl sm:text-2xl">Want to know more about our syllabus & streams?</h3>
            <p className="text-sm text-indigo-100">Schedule an academic counseling session or speak with our admissions dean.</p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/admissions"
              className="bg-white text-primary hover:bg-slate-50 text-sm font-semibold px-6 py-3 rounded-lg shadow-sm transition-all"
            >
              Admissions 2025–26
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
