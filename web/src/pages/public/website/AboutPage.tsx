import { Link } from "react-router-dom";

export function AboutPage() {
  return (
    <div className="space-y-16 sm:space-y-20 pb-16">
      {/* 1. HERO BANNER */}
      <section className="bg-gradient-to-b from-indigo-50/80 via-ground to-white py-14 sm:py-20 border-b border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
            Our Identity & Heritage
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
            About Sunrise School
          </h1>
          <p className="text-base sm:text-lg text-ink-soft max-w-2xl mx-auto leading-relaxed">
            Fostering intellectual vigor, moral purpose, and creative curiosity since 2011 in Lucknow, Uttar Pradesh.
          </p>
        </div>
      </section>

      {/* 2. THE SCHOOL STORY */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-6 space-y-4">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-700 bg-amber-100 px-3 py-1 rounded-full">
              Our Journey
            </span>
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight">
              A Legacy of Child-Centric Learning
            </h2>
            <p className="text-sm sm:text-base text-ink-soft leading-relaxed">
              Founded in 2011 by a consortium of visionary educationists in Lucknow, Sunrise School began with a humble conviction: that modern education must nurture both the analytical mind and the compassionate heart.
            </p>
            <p className="text-sm sm:text-base text-ink-soft leading-relaxed">
              Over the past decade and a half, Sunrise School has grown from a fledgling primary academy into one of Lucknow's most respected CBSE-affiliated institutions, serving over 1,200 learners across Pre-Primary to Class XII.
            </p>
            <p className="text-sm sm:text-base text-ink-soft leading-relaxed">
              Our campus in Gomti Nagar provides an idyllic sanctuary from urban frenzy—equipped with expansive sports grounds, advanced STEM labs, and creative studios where students discover their authentic callings.
            </p>
          </div>

          <div className="lg:col-span-6">
            <div className="bg-surface rounded-2xl border border-rule shadow-card p-6 sm:p-8 space-y-6">
              <h3 className="font-bold text-lg text-slate-900 border-b border-rule pb-3">
                Key Institutional Milestones
              </h3>
              <div className="space-y-4">
                <div className="flex gap-4">
                  <span className="w-12 font-mono font-bold text-sm text-primary shrink-0">2011</span>
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">Foundation Stone Laid</h4>
                    <p className="text-xs text-ink-soft mt-0.5">Commenced with 150 foundational students and 12 devoted educators.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <span className="w-12 font-mono font-bold text-sm text-primary shrink-0">2016</span>
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">CBSE Secondary Affiliation</h4>
                    <p className="text-xs text-ink-soft mt-0.5">Expanded to Class X with state-of-the-art physics, chemistry, and biology labs.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <span className="w-12 font-mono font-bold text-sm text-primary shrink-0">2019</span>
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">Senior Secondary Accreditation</h4>
                    <p className="text-xs text-ink-soft mt-0.5">Inaugurated dedicated Science, Commerce, and Humanities wings for Classes XI & XII.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <span className="w-12 font-mono font-bold text-sm text-primary shrink-0">2023</span>
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">Smart Campus & ERP Integration</h4>
                    <p className="text-xs text-ink-soft mt-0.5">Deployed interactive digital panels in all classrooms and unified ERP for transparency.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. VISION & MISSION */}
      <section className="bg-ground py-16 border-y border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Vision */}
            <div className="bg-white rounded-2xl p-8 sm:p-10 border border-rule shadow-sm space-y-4">
              <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center text-2xl font-bold">
                👁️
              </div>
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-600 block">
                Our Vision
              </span>
              <h3 className="text-2xl font-bold text-slate-900">
                Cultivating Visionary & Empathetic Global Citizens
              </h3>
              <p className="text-sm text-ink-soft leading-relaxed">
                To be an inspiring lighthouse of holistic education that nurtures intellectually fearless, morally grounded, and culturally rooted individuals equipped to navigate and enrich a complex global society.
              </p>
            </div>

            {/* Mission */}
            <div className="bg-white rounded-2xl p-8 sm:p-10 border border-rule shadow-sm space-y-4">
              <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center text-2xl font-bold">
                🎯
              </div>
              <span className="text-xs font-bold uppercase tracking-wider text-amber-600 block">
                Our Mission
              </span>
              <h3 className="text-2xl font-bold text-slate-900">
                Empowering Every Learner to Excel with Integrity
              </h3>
              <ul className="text-sm text-ink-soft space-y-2.5">
                <li className="flex items-start gap-2">
                  <span className="text-primary font-bold">•</span>
                  <span>Deliver engaging, experiential pedagogy aligned with NEP 2020 guidelines.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary font-bold">•</span>
                  <span>Foster physical vitality, artistic expression, and ethical character alongside academics.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-primary font-bold">•</span>
                  <span>Provide an inclusive, emotionally secure learning sanctuary that values every child's voice.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* 4. CORE VALUES (PANCH TATTVA) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12 space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
            Our Guiding Compass
          </span>
          <h2 className="text-3xl font-bold text-slate-900 tracking-tight">
            The Five Core Values of Sunrise
          </h2>
          <p className="text-sm text-ink-soft">
            These foundational principles shape every morning assembly, classroom interaction, and sports field endeavor.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
          <div className="bg-surface rounded-card p-5 border border-rule shadow-sm space-y-2 text-center">
            <div className="text-2xl">⚖️</div>
            <h3 className="font-bold text-base text-slate-900">Satya (Integrity)</h3>
            <p className="text-xs text-ink-soft leading-relaxed">
              Uncompromising honesty, moral clarity, and ethical courage in thought, word, and deed.
            </p>
          </div>

          <div className="bg-surface rounded-card p-5 border border-rule shadow-sm space-y-2 text-center">
            <div className="text-2xl">🌱</div>
            <h3 className="font-bold text-base text-slate-900">Karmanya (Diligence)</h3>
            <p className="text-xs text-ink-soft leading-relaxed">
              Sincere dedication to duty, perseverance through setbacks, and pride in honest labor.
            </p>
          </div>

          <div className="bg-surface rounded-card p-5 border border-rule shadow-sm space-y-2 text-center">
            <div className="text-2xl">🤝</div>
            <h3 className="font-bold text-base text-slate-900">Karuna (Empathy)</h3>
            <p className="text-xs text-ink-soft leading-relaxed">
              Compassionate awareness of others, service to community, and respect for all life.
            </p>
          </div>

          <div className="bg-surface rounded-card p-5 border border-rule shadow-sm space-y-2 text-center">
            <div className="text-2xl">🏆</div>
            <h3 className="font-bold text-base text-slate-900">Utkarsh (Excellence)</h3>
            <p className="text-xs text-ink-soft leading-relaxed">
              Striving constantly for highest standards in scholarship, creativity, and conduct.
            </p>
          </div>

          <div className="bg-surface rounded-card p-5 border border-rule shadow-sm space-y-2 text-center">
            <div className="text-2xl">🔍</div>
            <h3 className="font-bold text-base text-slate-900">Jigyasa (Curiosity)</h3>
            <p className="text-xs text-ink-soft leading-relaxed">
              Lifelong passion for questioning, scientific inquiry, and adventurous learning.
            </p>
          </div>
        </div>
      </section>

      {/* 5. LEADERSHIP SECTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12 space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
            School Governance
          </span>
          <h2 className="text-3xl font-bold text-slate-900 tracking-tight">
            Academic Leadership & Mentorship
          </h2>
          <p className="text-sm text-ink-soft">
            Guided by dedicated educators with decades of frontline experience in leading national and international curricula.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-surface rounded-2xl border border-rule p-6 shadow-sm text-center space-y-4">
            <div className="w-20 h-20 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center mx-auto text-2xl font-bold font-serif">
              AS
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-900">Dr. Ananya Sengupta</h3>
              <p className="text-xs text-primary font-semibold">Principal & Head of School</p>
              <p className="text-[11px] text-ink-faint mt-1">M.Sc., B.Ed., Ph.D. in Education</p>
            </div>
            <p className="text-xs text-ink-soft leading-relaxed">
              Passionate educationist with 22 years of experience championing progressive CBSE pedagogy, faculty development, and value-based schooling.
            </p>
          </div>

          <div className="bg-surface rounded-2xl border border-rule p-6 shadow-sm text-center space-y-4">
            <div className="w-20 h-20 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center mx-auto text-2xl font-bold font-serif">
              RK
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-900">Prof. R. K. Srivastava</h3>
              <p className="text-xs text-amber-700 font-semibold">Dean of Academics</p>
              <p className="text-[11px] text-ink-faint mt-1">M.A., M.Ed., Former CBSE Regional Advisor</p>
            </div>
            <p className="text-xs text-ink-soft leading-relaxed">
              Guides curriculum integration, continuous assessment frameworks, and senior secondary stream specializations across science and commerce.
            </p>
          </div>

          <div className="bg-surface rounded-2xl border border-rule p-6 shadow-sm text-center space-y-4">
            <div className="w-20 h-20 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center mx-auto text-2xl font-bold font-serif">
              SM
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-900">Mrs. Shalini Mishra</h3>
              <p className="text-xs text-emerald-700 font-semibold">Head of Student Welfare</p>
              <p className="text-[11px] text-ink-faint mt-1">M.Sc. (Child Psychology), B.Ed.</p>
            </div>
            <p className="text-xs text-ink-soft leading-relaxed">
              Leads pastoral care, inclusive education, adolescent counseling, and parent-teacher collaboration initiatives.
            </p>
          </div>
        </div>
      </section>

      {/* 6. CALL TO ACTION STRIP */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-ground border border-rule rounded-2xl p-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="space-y-1 text-center sm:text-left">
            <h3 className="font-bold text-xl text-slate-900">Want to see our classrooms in action?</h3>
            <p className="text-sm text-ink-soft">We welcome parents for personalized campus tours on all working days.</p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/facilities"
              className="bg-white border border-rule hover:bg-slate-50 text-slate-800 text-sm font-semibold px-5 py-2.5 rounded-lg shadow-xs transition-all"
            >
              Explore Campus Facilities
            </Link>
            <Link
              to="/admissions"
              className="bg-primary hover:bg-primary-dark text-white text-sm font-semibold px-5 py-2.5 rounded-lg shadow-sm transition-all"
            >
              Admissions Info
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
