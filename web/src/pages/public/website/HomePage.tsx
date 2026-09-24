import { Link } from "react-router-dom";
import heroCampusImage from "../../../assets/hero-campus.jpg";

export function HomePage() {
  return (
    <div className="space-y-16 sm:space-y-24 pb-16">
      {/* 1. HERO SECTION */}
      <section className="relative overflow-hidden bg-gradient-to-b from-indigo-50/50 via-ground to-white pt-8 pb-12 sm:pt-12 sm:pb-16 border-b border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
          {/* Top Announcement & Action Bar */}
          <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
            <div className="space-y-2.5 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold tracking-wide">
                <span className="w-2 h-2 rounded-full bg-primary animate-ping" />
                <span>Admissions Open for Session 2025–26 • CBSE Affiliated (Estd. 2011)</span>
              </div>
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight">
                Sunrise School
              </h1>
              <p className="text-base sm:text-lg text-ink-soft leading-relaxed font-normal">
                Nurturing curious minds and building confident futures in Gomti Nagar, Lucknow through academic excellence, ethical character, and joyful discovery.
              </p>
            </div>

            {/* Clean Functional CTAs */}
            <div className="flex flex-wrap items-center gap-3 sm:gap-4 shrink-0">
              <Link
                to="/about"
                className="bg-primary hover:bg-primary-dark text-white font-semibold px-6 py-3 rounded-input shadow-md hover:shadow-lg transition-all duration-150 text-sm sm:text-base"
              >
                Explore Our School
              </Link>
              <Link
                to="/admissions"
                className="bg-white hover:bg-slate-50 text-slate-800 font-semibold px-6 py-3 rounded-input border border-slate-300 shadow-sm transition-all duration-150 text-sm sm:text-base"
              >
                Admissions
              </Link>
              <Link
                to="/apply"
                className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:text-primary-dark px-2 py-2 transition-colors"
              >
                <span>Apply Online</span>
                <span>&rarr;</span>
              </Link>
            </div>
          </div>

          {/* Hero Visual Centerpiece */}
          <div className="relative rounded-2xl sm:rounded-3xl overflow-hidden shadow-2xl border border-slate-200/90 bg-slate-900">
            <img
              src={heroCampusImage}
              alt="Sunrise School Campus - Nurturing Brighter Tomorrows"
              className="w-full h-[280px] sm:h-[400px] md:h-[500px] lg:h-[600px] object-cover object-[32%_center] sm:object-center block transition-transform duration-700 hover:scale-[1.01]"
              loading="eager"
            />
          </div>

          {/* Trust Highlights Bar */}
          <div className="pt-2 flex flex-wrap items-center justify-between gap-4 text-xs sm:text-sm text-ink-soft border-t border-slate-200/60">
            <div className="flex items-center gap-2">
              <span className="text-emerald-600 font-bold text-base">✓</span>
              <span className="font-medium text-slate-800">100% CBSE Board Pass Rate</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-600 font-bold text-base">✓</span>
              <span className="font-medium text-slate-800">1:18 Faculty-Student Ratio</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-600 font-bold text-base">✓</span>
              <span className="font-medium text-slate-800">Lush 5-Acre Eco-Campus</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-600 font-bold text-base">✓</span>
              <span className="font-medium text-slate-800">GPS-Tracked Safe Transport</span>
            </div>
          </div>
        </div>
      </section>

      {/* 2. STATS & KEY DEMO HIGHLIGHTS */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 lg:gap-6">
          <div className="bg-surface rounded-card p-5 border border-rule shadow-sm text-center">
            <div className="text-3xl sm:text-4xl font-extrabold text-primary font-mono">1,200+</div>
            <div className="text-xs font-semibold uppercase tracking-wider text-ink-soft mt-1">Students Enrolled</div>
            <div className="text-[11px] text-ink-faint mt-0.5">Pre-Primary to Class XII</div>
          </div>
          <div className="bg-surface rounded-card p-5 border border-rule shadow-sm text-center">
            <div className="text-3xl sm:text-4xl font-extrabold text-indigo-600 font-mono">75+</div>
            <div className="text-xs font-semibold uppercase tracking-wider text-ink-soft mt-1">Qualified Faculty</div>
            <div className="text-[11px] text-ink-faint mt-0.5">100% Trained Mentors</div>
          </div>
          <div className="bg-surface rounded-card p-5 border border-rule shadow-sm text-center">
            <div className="text-3xl sm:text-4xl font-extrabold text-amber-600 font-mono">15+</div>
            <div className="text-xs font-semibold uppercase tracking-wider text-ink-soft mt-1">Years of Legacy</div>
            <div className="text-[11px] text-ink-faint mt-0.5">Established in 2011</div>
          </div>
          <div className="bg-surface rounded-card p-5 border border-rule shadow-sm text-center">
            <div className="text-3xl sm:text-4xl font-extrabold text-emerald-600 font-mono">25+</div>
            <div className="text-xs font-semibold uppercase tracking-wider text-ink-soft mt-1">Clubs & Sports</div>
            <div className="text-[11px] text-ink-faint mt-0.5">Beyond Academics</div>
          </div>
          <div className="col-span-2 md:col-span-1 bg-surface rounded-card p-5 border border-rule shadow-sm text-center">
            <div className="text-3xl sm:text-4xl font-extrabold text-slate-800 font-mono">100%</div>
            <div className="text-xs font-semibold uppercase tracking-wider text-ink-soft mt-1">CBSE Pass Rate</div>
            <div className="text-[11px] text-ink-faint mt-0.5">Continuous Board Honors</div>
          </div>
        </div>
      </section>

      {/* 3. SCHOOL INTRODUCTION & EDUCATIONAL PHILOSOPHY */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-surface rounded-2xl border border-rule shadow-sm p-8 sm:p-12 lg:p-16">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            <div className="lg:col-span-5 space-y-4">
              <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
                Welcome to Sunrise School
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight leading-snug">
                Where curiosity meets compassionate character.
              </h2>
              <p className="text-sm sm:text-base text-ink-soft leading-relaxed">
                Founded with a conviction that true education transcends rote textbooks, Sunrise School provides a safe, vibrant ecosystem where every child discovers their unique talents.
              </p>
              <div className="pt-2">
                <Link
                  to="/about"
                  className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:text-primary-dark"
                >
                  <span>Read our story & core values</span>
                  <span>&rarr;</span>
                </Link>
              </div>
            </div>

            <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-5 rounded-xl bg-ground border border-rule/80 space-y-2">
                <div className="w-10 h-10 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold text-lg">
                  💡
                </div>
                <h3 className="font-bold text-base text-slate-900">Inquiry-Driven Pedagogy</h3>
                <p className="text-xs text-ink-soft leading-relaxed">
                  Aligned with NEP 2020, focusing on conceptual clarity, practical experiments, and real-world problem-solving over memorization.
                </p>
              </div>

              <div className="p-5 rounded-xl bg-ground border border-rule/80 space-y-2">
                <div className="w-10 h-10 rounded-lg bg-amber-100 text-amber-800 flex items-center justify-center font-bold text-lg">
                  🌱
                </div>
                <h3 className="font-bold text-base text-slate-900">Values & Sanskaar</h3>
                <p className="text-xs text-ink-soft leading-relaxed">
                  Instilling deep respect for cultural heritage, ethical responsibility, empathy for community, and lifelong integrity.
                </p>
              </div>

              <div className="p-5 rounded-xl bg-ground border border-rule/80 space-y-2">
                <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold text-lg">
                  ⚽
                </div>
                <h3 className="font-bold text-base text-slate-900">Physical Vitality & Arts</h3>
                <p className="text-xs text-ink-soft leading-relaxed">
                  Compulsory sports coaching, yoga, performing arts, and public speaking to develop resilience, teamwork, and self-expression.
                </p>
              </div>

              <div className="p-5 rounded-xl bg-ground border border-rule/80 space-y-2">
                <div className="w-10 h-10 rounded-lg bg-purple-100 text-purple-800 flex items-center justify-center font-bold text-lg">
                  💻
                </div>
                <h3 className="font-bold text-base text-slate-900">Modern Digital Learning</h3>
                <p className="text-xs text-ink-soft leading-relaxed">
                  Interactive smart classrooms, coding from Class 3 onwards, digital library, and an integrated ERP connecting school with parents.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. ACADEMICS PREVIEW */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12 space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
            Learning Pathways
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
            Academic Wings Structured for Every Developmental Stage
          </h2>
          <p className="text-sm sm:text-base text-ink-soft">
            Our progressive curriculum provides a smooth transition from playful early discovery to rigorous secondary board excellence.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: Foundational */}
          <div className="bg-surface rounded-card border border-rule p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
            <div className="space-y-4">
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-100 text-amber-800">
                Nursery – Class II
              </span>
              <h3 className="text-xl font-bold text-slate-900">Foundational Wing</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Play-based phonics, sensorial discovery, social-emotional development, and joy of discovery in safe, welcoming spaces.
              </p>
              <ul className="text-xs text-slate-600 space-y-1.5 pt-2">
                <li>• Experiential play & storytelling</li>
                <li>• Foundational literacy & numeracy (FLN)</li>
                <li>• Activity & motor skills development</li>
              </ul>
            </div>
            <div className="pt-6 border-t border-rule mt-6">
              <Link to="/academics" className="text-xs font-semibold text-primary hover:underline">
                Explore Foundational Wing &rarr;
              </Link>
            </div>
          </div>

          {/* Card 2: Middle */}
          <div className="bg-surface rounded-card border border-primary/30 p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between relative">
            <div className="absolute -top-3 right-6 bg-primary text-white text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full">
              Core Stage
            </div>
            <div className="space-y-4">
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-100 text-indigo-800">
                Class III – VIII
              </span>
              <h3 className="text-xl font-bold text-slate-900">Preparatory & Middle Wing</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Transition to structured subject disciplines, integrated STEM labs, coding literacy, language fluency, and creative writing.
              </p>
              <ul className="text-xs text-slate-600 space-y-1.5 pt-2">
                <li>• Integrated Mathematics & Science labs</li>
                <li>• Third language options (Sanskrit / French)</li>
                <li>• Robotics & algorithmic thinking</li>
              </ul>
            </div>
            <div className="pt-6 border-t border-rule mt-6">
              <Link to="/academics" className="text-xs font-semibold text-primary hover:underline">
                Explore Middle Wing &rarr;
              </Link>
            </div>
          </div>

          {/* Card 3: Senior */}
          <div className="bg-surface rounded-card border border-rule p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
            <div className="space-y-4">
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800">
                Class IX – XII
              </span>
              <h3 className="text-xl font-bold text-slate-900">Senior Secondary Wing</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Specialized Science (PCM/PCB), Commerce, and Humanities streams with focused CBSE board preparation and competitive mentoring.
              </p>
              <ul className="text-xs text-slate-600 space-y-1.5 pt-2">
                <li>• Advanced physics, chem & bio practicals</li>
                <li>• Career counseling & university guidance</li>
                <li>• Foundation support for JEE / NEET / CUET</li>
              </ul>
            </div>
            <div className="pt-6 border-t border-rule mt-6">
              <Link to="/academics" className="text-xs font-semibold text-primary hover:underline">
                Explore Senior Wing &rarr;
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* 5. FACILITIES PREVIEW */}
      <section className="bg-ground py-16 border-y border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
            <div className="space-y-2 max-w-2xl">
              <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
                Infrastructure & Campus
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
                Designed for Safe, Stimulating Discovery
              </h2>
              <p className="text-sm text-ink-soft">
                Our 5-acre campus in Gomti Nagar provides modern academic, athletic, and creative spaces ensuring your child learns in a secure environment.
              </p>
            </div>
            <Link
              to="/facilities"
              className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:text-primary-dark whitespace-nowrap"
            >
              <span>View all campus facilities</span>
              <span>&rarr;</span>
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-card p-5 border border-rule shadow-sm space-y-3">
              <div className="w-10 h-10 rounded-lg bg-indigo-50 text-indigo-700 flex items-center justify-center font-bold text-xl">
                🖥️
              </div>
              <h3 className="font-bold text-base text-slate-900">Smart Classrooms</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Interactive digital touchboards, ergonomic student furniture, and climate-controlled ambient lighting in every classroom.
              </p>
            </div>

            <div className="bg-white rounded-card p-5 border border-rule shadow-sm space-y-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-xl">
                🔬
              </div>
              <h3 className="font-bold text-base text-slate-900">Modern Science Labs</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Dedicated Physics, Chemistry, and Biology laboratories equipped with modern apparatus adhering to safety protocols.
              </p>
            </div>

            <div className="bg-white rounded-card p-5 border border-rule shadow-sm space-y-3">
              <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center font-bold text-xl">
                📚
              </div>
              <h3 className="font-bold text-base text-slate-900">Central Library Hub</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Over 12,000 titles, periodicals, comfortable reading circles, and a digital resource repository for self-paced research.
              </p>
            </div>

            <div className="bg-white rounded-card p-5 border border-rule shadow-sm space-y-3">
              <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center font-bold text-xl">
                🚌
              </div>
              <h3 className="font-bold text-base text-slate-900">GPS Safe Transport</h3>
              <p className="text-xs text-ink-soft leading-relaxed">
                Fleet of GPS-monitored buses with female attendants, CCTV cameras, and speed governors covering all major city routes.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 6. PRINCIPAL'S LEADERSHIP MESSAGE */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-surface rounded-2xl border border-rule shadow-card p-8 sm:p-12">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
            {/* Principal Avatar / Bio Badge */}
            <div className="md:col-span-4 text-center space-y-3 border-b md:border-b-0 md:border-r border-rule pb-6 md:pb-0 md:pr-6">
              <div className="w-28 h-28 rounded-full bg-gradient-to-tr from-primary to-indigo-800 text-white flex items-center justify-center mx-auto text-3xl font-serif font-bold shadow-md ring-4 ring-primary-soft">
                AS
              </div>
              <div>
                <h3 className="font-bold text-lg text-slate-900">Dr. Ananya Sengupta</h3>
                <p className="text-xs text-primary font-semibold">Principal & Head of School</p>
                <p className="text-[11px] text-ink-faint mt-0.5">M.Sc., B.Ed., Ph.D. (Education) • 22+ Years in Pedagogy</p>
              </div>
            </div>

            {/* Principal Quote & Message */}
            <div className="md:col-span-8 space-y-4">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-700 bg-amber-100 px-3 py-0.5 rounded-full">
                Leadership Message
              </span>
              <blockquote className="text-base sm:text-lg text-slate-800 italic leading-relaxed font-serif">
                “Every child steps into Sunrise School with a world of curiosity waiting to be unlocked. Our duty is not to mold them into a standard mold, but to cultivate their critical discernment, resilient spirit, and compass of empathy.”
              </blockquote>
              <p className="text-xs sm:text-sm text-ink-soft leading-relaxed">
                We believe that education must prepare young people for life, not merely examinations. We welcome parents as our trusted partners in this noble collaborative journey.
              </p>
              <div className="pt-2">
                <Link to="/about" className="text-xs font-semibold text-primary hover:underline">
                  Read our institutional vision & governance &rarr;
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 7. DEDICATED ERP GATEWAY CALLOUT (Fulfills Section 4 requirement on Home page) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-8 sm:p-10 shadow-lg border border-slate-800">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-8 space-y-3">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <span>Authorized School Operations Portal</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                Sunrise School ERP Gateway
              </h2>
              <p className="text-slate-300 text-sm leading-relaxed max-w-2xl">
                Unified internal management platform for school administration, teachers, reception desk, and department coordinators. Access real-time student records, daily attendance, fee counter, timetable, and examinations securely.
              </p>
            </div>

            <div className="lg:col-span-4 flex flex-col sm:flex-row lg:flex-col gap-3 justify-center">
              <Link
                to="/login"
                className="inline-flex items-center justify-center gap-2 bg-primary hover:bg-primary-dark text-white font-semibold py-3 px-6 rounded-input shadow-md transition-all text-sm"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                </svg>
                <span>Launch Staff ERP</span>
              </Link>
              <span className="text-center text-[11px] text-slate-400">
                Staff login required. Unauthorized access strictly prohibited.
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* 8. ADMISSIONS CALL-TO-ACTION & FINAL BANNER */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-primary to-indigo-800 text-white rounded-2xl p-8 sm:p-12 text-center space-y-6 shadow-card">
          <div className="max-w-2xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider bg-white/20 text-white px-3 py-1 rounded-full">
              Session 2025–26 Enrollment
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
              Begin Your Child’s Journey at Sunrise School
            </h2>
            <p className="text-indigo-100 text-sm sm:text-base leading-relaxed">
              We invite parents to visit our campus, interact with our academic coordinators, and understand how our holistic curriculum can unlock your child’s potential.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <Link
              to="/apply"
              className="bg-amber-400 hover:bg-amber-300 text-slate-900 font-bold px-8 py-3.5 rounded-input shadow-md transition-all text-sm"
            >
              Fill Online Application Form &rarr;
            </Link>
            <Link
              to="/admissions"
              className="bg-white/10 hover:bg-white/20 text-white font-semibold px-8 py-3.5 rounded-input border border-white/30 backdrop-blur transition-all text-sm"
            >
              View Admission Process & Criteria
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
