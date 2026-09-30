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
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight font-serif">
            Academics at Sunrise School
          </h1>
          <p className="text-base sm:text-lg text-ink-soft max-w-2xl mx-auto leading-relaxed">
            A comprehensive, NEP 2020-aligned CBSE curriculum cultivating critical discernment, scientific curiosity, and lifelong love for learning.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <a
              href="/documents/syllabus-overview.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 bg-[#042954] hover:bg-[#021b38] text-white text-xs sm:text-sm font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors"
            >
              <span>Download Syllabus Overview (1 Page PDF)</span>
              <span>&darr;</span>
            </a>
            <a
              href="/documents/academic-calendar.pdf"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 bg-white hover:bg-slate-50 text-slate-800 border border-slate-300 text-xs sm:text-sm font-semibold px-4 py-2 rounded-lg shadow-sm transition-colors"
            >
              <span>Academic Calendar 2026–27</span>
              <span>&darr;</span>
            </a>
          </div>
        </div>
      </section>

      {/* 2. ACADEMIC APPROACH & METHODOLOGY */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          <div className="lg:col-span-6 space-y-4">
            <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
              Our Pedagogical Philosophy
            </span>
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight font-serif">
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
                  <p className="text-xs text-ink-soft mt-0.5">With an optimal 1:20 faculty ratio, our teachers tailor guidance to the specific pace and strengths of each student.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-6">
            <div className="bg-surface rounded-2xl border border-rule shadow-card p-6 sm:p-8 space-y-5">
              <h3 className="font-bold text-lg text-slate-900 border-b border-rule pb-3 font-serif">
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

      {/* 3. FOUR-TIER NEP 2020 ACADEMIC STAGES */}
      <section className="bg-ground py-16 border-y border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
              NEP 2020 Framework
            </span>
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight font-serif">
              Progressive Learning Across Academic Stages
            </h2>
            <p className="text-sm text-ink-soft">
              Aligned with the 5+3+3+4 pedagogical structure, each developmental milestone receives tailored curriculum design and specialized educators.
            </p>
          </div>

          <div className="space-y-8">
            {/* Stage 1: Foundational */}
            <div className="bg-white rounded-2xl overflow-hidden border border-rule shadow-sm grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
              <div className="lg:col-span-4 h-48 lg:h-full min-h-[180px] bg-slate-900 relative">
                <img
                  src="/images/school/modern_classroom_learning.jpg"
                  alt="Foundational Smart Classroom Learning"
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
                <div className="absolute top-3 left-3">
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-100/95 text-amber-900 backdrop-blur-xs shadow-xs">
                    Foundational (Nursery – Grade 2)
                  </span>
                </div>
              </div>
              <div className="lg:col-span-8 p-6 lg:p-6 lg:pl-0 space-y-4">
                <div>
                  <h3 className="text-2xl font-bold text-slate-900 font-serif">Foundational Stage (Ages 3–8)</h3>
                  <p className="text-xs text-ink-soft leading-relaxed mt-1">
                    Focusing on joyful early childhood education where play, phonics, sensorial discovery, and foundational numeracy create a loving bridge between home and school.
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                  <div className="p-3.5 rounded-xl bg-ground border border-rule/80">
                    <div className="font-bold text-slate-900 mb-0.5">Key Focus</div>
                    <div className="text-ink-soft text-[11px]">Motor coordination, bilingual phonics, sensorial exploration, social habits.</div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-ground border border-rule/80">
                    <div className="font-bold text-slate-900 mb-0.5">Methodology</div>
                    <div className="text-ink-soft text-[11px]">Montessori-inspired activity stations, storytelling, puppet play, music.</div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-ground border border-rule/80">
                    <div className="font-bold text-slate-900 mb-0.5">Assessment</div>
                    <div className="text-ink-soft text-[11px]">Continuous observation portfolios; zero formal exam stress.</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Stage 2: Preparatory & Middle */}
            <div className="bg-white rounded-2xl overflow-hidden border border-rule shadow-sm grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
              <div className="lg:col-span-4 h-48 lg:h-full min-h-[180px] bg-slate-900 relative">
                <img
                  src="/images/school/stem_robotics_activity.jpg"
                  alt="Preparatory and Middle Stage STEM Tinkering"
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
                <div className="absolute top-3 left-3">
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-100/95 text-indigo-900 backdrop-blur-xs shadow-xs">
                    Preparatory & Middle (Grades 3–8)
                  </span>
                </div>
              </div>
              <div className="lg:col-span-8 p-6 lg:p-6 lg:pl-0 space-y-4">
                <div>
                  <h3 className="text-2xl font-bold text-slate-900 font-serif">Preparatory & Middle Stages (Ages 8–14)</h3>
                  <p className="text-xs text-ink-soft leading-relaxed mt-1">
                    Deepening subject understanding through inquiry, structured lab experiments, computational thinking, and artistic enrichment.
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                  <div className="p-3.5 rounded-xl bg-ground border border-rule/80">
                    <div className="font-bold text-slate-900 mb-0.5">Subjects</div>
                    <div className="text-ink-soft text-[11px]">English, Hindi, Sanskrit/French, Mathematics, Integrated Science, Social Sciences, Computer/AI.</div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-ground border border-rule/80">
                    <div className="font-bold text-slate-900 mb-0.5">Enrichment</div>
                    <div className="text-ink-soft text-[11px]">Science exhibitions, coding competitions, math olympiads, weekly clubs.</div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-ground border border-rule/80">
                    <div className="font-bold text-slate-900 mb-0.5">Assessment</div>
                    <div className="text-ink-soft text-[11px]">Periodic tests, project presentations, subject enrichment assessments.</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Stage 3: Secondary & Senior Secondary */}
            <div className="bg-white rounded-2xl overflow-hidden border border-rule shadow-sm grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
              <div className="lg:col-span-4 h-48 lg:h-full min-h-[180px] bg-slate-900 relative">
                <img
                  src="/images/school/science_lab_practical.jpg"
                  alt="Secondary and Senior Secondary Laboratory Practicals"
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
                <div className="absolute top-3 left-3">
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100/95 text-emerald-900 backdrop-blur-xs shadow-xs">
                    Secondary & Senior Secondary (Grades 9–12)
                  </span>
                </div>
              </div>
              <div className="lg:col-span-8 p-6 lg:p-6 lg:pl-0 space-y-4">
                <div>
                  <h3 className="text-2xl font-bold text-slate-900 font-serif">Secondary & Senior Secondary (Ages 14–18)</h3>
                  <p className="text-xs text-ink-soft leading-relaxed mt-1">
                    Rigorous academic streams preparing students for CBSE All-India Senior School Certificate Examination (AISSCE) and prestigious university entrances.
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                  <div className="p-3.5 rounded-xl bg-ground border border-rule/80">
                    <div className="font-bold text-slate-900 mb-0.5">Curriculum</div>
                    <div className="text-ink-soft text-[11px]">CBSE All-India Secondary (AISSE) and Senior Secondary (AISSCE) Board Syllabi.</div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-ground border border-rule/80">
                    <div className="font-bold text-slate-900 mb-0.5">Competitive Foundation</div>
                    <div className="text-ink-soft text-[11px]">Integrated preparatory modules for CUET, JEE, NEET, and CLAT with specialized faculty.</div>
                  </div>
                  <div className="p-3.5 rounded-xl bg-ground border border-rule/80">
                    <div className="font-bold text-slate-900 mb-0.5">Laboratories</div>
                    <div className="text-ink-soft text-[11px]">Dedicated practical sessions in Physics, Chemistry, Biology, and Computer Science suites.</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. SENIOR SECONDARY STREAMS MATRIX */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
            Senior Secondary Pathways
          </span>
          <h2 className="text-3xl font-bold text-slate-900 tracking-tight font-serif">
            Three Specialized Academic Streams
          </h2>
          <p className="text-sm text-ink-soft">
            Grades XI & XII offer targeted academic specializations led by experienced PGT subject matter experts.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Science Stream */}
          <div className="bg-surface rounded-2xl border border-rule p-6 space-y-4 shadow-sm flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-md bg-blue-100 text-blue-800">
                  Science Stream
                </span>
                <span className="text-lg">🔬</span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 font-serif">PCM / PCB Specialization</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Comprehensive training for engineering, medical, scientific research, and technological careers.
              </p>
              <div className="space-y-1.5 text-xs text-slate-700 pt-2 border-t border-rule">
                <div><strong>Compulsory:</strong> English Core, Physics, Chemistry</div>
                <div><strong>Electives:</strong> Mathematics, Biology, Computer Science (Python), Physical Education</div>
              </div>
            </div>
            <div className="pt-3 border-t border-rule text-xs text-slate-500">
              Lab Practical: 30 Marks • Theory: 70 Marks
            </div>
          </div>

          {/* Commerce Stream */}
          <div className="bg-surface rounded-2xl border border-rule p-6 space-y-4 shadow-sm flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-md bg-amber-100 text-amber-800">
                  Commerce Stream
                </span>
                <span className="text-lg">📈</span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 font-serif">Commerce & Finance</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Empowering future business leaders, chartered accountants, financial analysts, and entrepreneurs.
              </p>
              <div className="space-y-1.5 text-xs text-slate-700 pt-2 border-t border-rule">
                <div><strong>Compulsory:</strong> English Core, Accountancy, Business Studies, Economics</div>
                <div><strong>Electives:</strong> Applied Mathematics, Informatics Practices, Physical Education</div>
              </div>
            </div>
            <div className="pt-3 border-t border-rule text-xs text-slate-500">
              Case Study Projects • Stock Market Simulation
            </div>
          </div>

          {/* Humanities Stream */}
          <div className="bg-surface rounded-2xl border border-rule p-6 space-y-4 shadow-sm flex flex-col justify-between">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-md bg-purple-100 text-purple-800">
                  Humanities Stream
                </span>
                <span className="text-lg">🏛️</span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 font-serif">Liberal Arts & Social Sciences</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Rigorous preparation for law, civil services, international diplomacy, psychology, and public policy.
              </p>
              <div className="space-y-1.5 text-xs text-slate-700 pt-2 border-t border-rule">
                <div><strong>Compulsory:</strong> English Core, History, Political Science</div>
                <div><strong>Electives:</strong> Psychology, Economics, Sociology, Geography, Legal Studies</div>
              </div>
            </div>
            <div className="pt-3 border-t border-rule text-xs text-slate-500">
              Policy Research Papers • Model UN Mentorship
            </div>
          </div>
        </div>
      </section>

      {/* 5. TECHNOLOGY & ASSESSMENT APPROACH */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Tech in Education */}
          <div className="bg-surface rounded-2xl border border-rule overflow-hidden shadow-sm flex flex-col justify-between">
            <div className="h-48 w-full bg-slate-900 relative">
              <img
                src="/images/school/computer_lab_coding.jpg"
                alt="Sunrise School Computer and AI Laboratory"
                className="w-full h-full object-cover"
                loading="lazy"
              />
              <div className="absolute top-3 left-3">
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-black/60 text-white backdrop-blur-xs">
                  Coding & Computational Thinking
                </span>
              </div>
            </div>
            <div className="p-6 sm:p-8 space-y-3">
              <h3 className="text-xl font-bold text-slate-900 font-serif">Digital Fluency & AI Education</h3>
              <p className="text-xs sm:text-sm text-ink-soft leading-relaxed">
                Every learner from Grade 3 onwards interacts with our 60-seat high-speed computer programming lab, exploring block-based coding, Python programming, and ethical AI applications.
              </p>
              <div className="pt-2">
                <Link to="/facilities" className="text-xs font-bold text-primary hover:underline">
                  Tour our computing and robotics facilities &rarr;
                </Link>
              </div>
            </div>
          </div>

          {/* Assessment Approach */}
          <div className="bg-surface rounded-2xl border border-rule p-6 sm:p-8 space-y-4 shadow-sm flex flex-col justify-between">
            <div>
              <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center text-xl font-bold mb-3">
                📊
              </div>
              <h3 className="text-xl font-bold text-slate-900 font-serif">CBSE Assessment Architecture</h3>
              <p className="text-xs sm:text-sm text-ink-soft leading-relaxed mt-1">
                Assessment at Sunrise is formative, diagnostic, and progress-oriented, designed to identify learning gaps and celebrate individual student growth.
              </p>
              <ul className="text-xs text-slate-600 space-y-2 mt-4">
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

            <div className="pt-4 border-t border-rule flex items-center justify-between">
              <span className="text-xs text-slate-500">Academic Year 2026–27 Schedule</span>
              <a
                href="/documents/academic-calendar.pdf"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs font-bold text-[#042954] hover:text-amber-600 transition-colors"
              >
                View Academic Calendar PDF &rarr;
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* 6. CALL TO ACTION STRIP */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-primary to-indigo-900 text-white rounded-2xl p-8 sm:p-10 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-card">
          <div className="space-y-1 text-center sm:text-left">
            <h3 className="font-bold text-xl sm:text-2xl font-serif">Want to know more about our syllabus & streams?</h3>
            <p className="text-sm text-indigo-100">Download syllabus guides or schedule an academic counseling session with our admissions dean.</p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <Link
              to="/resources"
              className="bg-white text-primary hover:bg-slate-50 text-xs sm:text-sm font-semibold px-5 py-2.5 rounded-lg shadow-sm transition-all"
            >
              Downloads & Syllabus
            </Link>
            <Link
              to="/apply"
              className="bg-amber-400 hover:bg-amber-300 text-slate-900 text-xs sm:text-sm font-bold px-5 py-2.5 rounded-lg shadow-sm transition-all"
            >
              Apply Online
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
