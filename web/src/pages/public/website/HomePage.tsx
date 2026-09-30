import { useState } from "react";
import { Link } from "react-router-dom";
import heroCampusImage from "../../../assets/hero-campus.jpg";
import { AdmissionEnquiryModal } from "../../../components/public/AdmissionEnquiryModal";

export function HomePage() {
  const [enquiryModalOpen, setEnquiryModalOpen] = useState(false);

  const parentTestimonials = [
    {
      quote:
        "The personal attention my daughter receives at Sunrise has transformed her confidence. Her teachers don't just teach the CBSE syllabus; they ignite her genuine curiosity in science and public speaking.",
      parentName: "Dr. Alok Srivastava",
      role: "Parent of Ananya (Class VIII)",
      badge: "Gomti Nagar Resident",
    },
    {
      quote:
        "Moving our son to Sunrise School in Class 9 was our best decision. The laboratory infrastructure, sports coaching, and disciplined values-led environment prepared him to score 96.4% in Class 10 boards.",
      parentName: "Mrs. Meenakshi Agarwal",
      role: "Parent of Rohan (Class XI Science)",
      badge: "Parent Association Member",
    },
    {
      quote:
        "The early years foundation is phenomenal. The 1:15 ratio in pre-primary and kindergarten ensures each little learner is listened to, nurtured, and given joyful hands-on discovery.",
      parentName: "Vikram & Neha Malhotra",
      role: "Parents of Kabir (Class II)",
      badge: "Alumni Family",
    },
  ];

  return (
    <div className="space-y-16 sm:space-y-24 pb-16">
      {/* 1. HERO SECTION */}
      <section className="relative overflow-hidden bg-gradient-to-b from-indigo-50/50 via-white to-white pt-8 pb-12 sm:pt-12 sm:pb-16 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6 sm:space-y-8">
          {/* Top Announcement & Action Bar */}
          <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
            <div className="space-y-2.5 max-w-2xl">
              <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-amber-100 border border-amber-300 text-amber-900 text-xs font-bold tracking-wide">
                <span className="w-2 h-2 rounded-full bg-amber-600 animate-ping" />
                <span>Admissions Open • Academic Session 2026–27</span>
              </div>
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight font-serif">
                Nurturing Curious Minds.<br />Building Confident Futures.
              </h1>
              <p className="text-base sm:text-lg text-slate-600 leading-relaxed font-normal">
                At Sunrise School, we provide a nurturing environment where every child discovers their potential, builds character, and develops the skills for a brighter tomorrow.
              </p>
            </div>

            {/* Clean Functional CTAs */}
            <div className="flex flex-wrap items-center gap-3 sm:gap-4 shrink-0">
              <Link
                to="/about"
                className="bg-amber-400 hover:bg-amber-300 text-slate-900 font-bold px-6 py-3 rounded-lg shadow-sm transition-all duration-150 text-sm sm:text-base"
              >
                Explore Our School &rarr;
              </Link>
              <button
                onClick={() => setEnquiryModalOpen(true)}
                className="bg-slate-900 hover:bg-slate-800 text-white font-bold px-6 py-3 rounded-lg shadow-sm transition-all duration-150 text-sm sm:text-base cursor-pointer"
              >
                Admission Enquiry
              </button>
              <Link
                to="/apply"
                className="inline-flex items-center gap-1 text-sm font-semibold text-primary hover:text-primary-dark px-2 py-2 transition-colors"
              >
                <span>Apply Online</span>
                <span>&rarr;</span>
              </Link>
            </div>
          </div>

          {/* Hero Main Photography Centerpiece (1 of 4 School Photos: Exterior Campus) */}
          <div className="relative rounded-2xl sm:rounded-3xl overflow-hidden shadow-2xl border border-slate-200 bg-slate-900">
            <img
              src={heroCampusImage}
              alt="Sunrise School Main Campus Exterior - Gomti Nagar, Lucknow"
              className="w-full h-[280px] sm:h-[400px] md:h-[500px] lg:h-[580px] object-cover object-[32%_center] sm:object-center block transition-transform duration-700 hover:scale-[1.01]"
              loading="eager"
            />
          </div>

          {/* Trust Highlights Bar */}
          <div className="pt-2 flex flex-wrap items-center justify-between gap-4 text-xs sm:text-sm text-slate-600 border-t border-slate-200/80">
            <div className="flex items-center gap-2">
              <span className="text-emerald-600 font-bold text-base">✓</span>
              <span className="font-semibold text-slate-800">100% CBSE Board Pass Rate</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-600 font-bold text-base">✓</span>
              <span className="font-semibold text-slate-800">1:15 Early Years Ratio (1:18 Senior)</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-600 font-bold text-base">✓</span>
              <span className="font-semibold text-slate-800">Lush 5-Acre Eco-Campus in Gomti Nagar</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-emerald-600 font-bold text-base">✓</span>
              <span className="font-semibold text-slate-800">GPS-Tracked Safe Transport</span>
            </div>
          </div>
        </div>
      </section>

      {/* 2. FOUR SUNRISE SCHOOL FEATURE CARDS (Matching Reference Layout) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1: Academic Excellence (Modern Classroom Photo) */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between group">
            <div className="h-44 overflow-hidden bg-slate-900 relative">
              <img
                src="/images/school/modern_classroom_learning.jpg"
                alt="Academic Excellence - Smart Classroom Learning"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                loading="lazy"
              />
              <div className="absolute top-3 left-3 bg-indigo-900/80 text-white p-2 rounded-full backdrop-blur-xs">
                🎓
              </div>
            </div>
            <div className="p-5 space-y-2 flex-1 flex flex-col justify-between">
              <div>
                <h3 className="font-bold text-lg text-slate-900 font-serif group-hover:text-primary transition-colors">
                  Academic Excellence
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed mt-1">
                  A well-rounded CBSE curriculum that builds conceptual knowledge, critical thinking, and exam confidence.
                </p>
              </div>
              <div className="pt-3 border-t border-slate-100 text-right">
                <Link to="/academics" className="text-xs font-bold text-primary hover:underline">
                  Learn More &rarr;
                </Link>
              </div>
            </div>
          </div>

          {/* Card 2: World-Class Facilities (Science Lab Photo) */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between group">
            <div className="h-44 overflow-hidden bg-slate-900 relative">
              <img
                src="/images/school/science_lab_practical.jpg"
                alt="World-Class Facilities - Composite Science Lab"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                loading="lazy"
              />
              <div className="absolute top-3 left-3 bg-amber-900/80 text-white p-2 rounded-full backdrop-blur-xs">
                🔬
              </div>
            </div>
            <div className="p-5 space-y-2 flex-1 flex flex-col justify-between">
              <div>
                <h3 className="font-bold text-lg text-slate-900 font-serif group-hover:text-primary transition-colors">
                  World-Class Facilities
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed mt-1">
                  Modern science labs, central library, sports grounds, and STEM robotics spaces for holistic growth.
                </p>
              </div>
              <div className="pt-3 border-t border-slate-100 text-right">
                <Link to="/facilities" className="text-xs font-bold text-primary hover:underline">
                  Explore Facilities &rarr;
                </Link>
              </div>
            </div>
          </div>

          {/* Card 3: Supportive Community (Teacher Mentoring Photo) */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between group">
            <div className="h-44 overflow-hidden bg-slate-900 relative">
              <img
                src="/images/school/teacher_mentoring_students.jpg"
                alt="Supportive Community - Teacher Mentoring Students"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                loading="lazy"
              />
              <div className="absolute top-3 left-3 bg-emerald-900/80 text-white p-2 rounded-full backdrop-blur-xs">
                👥
              </div>
            </div>
            <div className="p-5 space-y-2 flex-1 flex flex-col justify-between">
              <div>
                <h3 className="font-bold text-lg text-slate-900 font-serif group-hover:text-primary transition-colors">
                  Supportive Community
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed mt-1">
                  A caring environment where students, faculty mentors, and parents collaborate for student well-being.
                </p>
              </div>
              <div className="pt-3 border-t border-slate-100 text-right">
                <Link to="/about" className="text-xs font-bold text-primary hover:underline">
                  Our Community &rarr;
                </Link>
              </div>
            </div>
          </div>

          {/* Card 4: Beyond the Classroom (Sports Field Photo) */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between group">
            <div className="h-44 overflow-hidden bg-slate-900 relative">
              <img
                src="/images/school/sports_field_athletics.jpg"
                alt="Beyond the Classroom - Outdoor Athletics Turf"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                loading="lazy"
              />
              <div className="absolute top-3 left-3 bg-purple-900/80 text-white p-2 rounded-full backdrop-blur-xs">
                🏆
              </div>
            </div>
            <div className="p-5 space-y-2 flex-1 flex flex-col justify-between">
              <div>
                <h3 className="font-bold text-lg text-slate-900 font-serif group-hover:text-primary transition-colors">
                  Beyond the Classroom
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed mt-1">
                  Sports, fine arts, robotics clubs, and four house competitions for a well-rounded personality.
                </p>
              </div>
              <div className="pt-3 border-t border-slate-100 text-right">
                <Link to="/school-life" className="text-xs font-bold text-primary hover:underline">
                  School Life &rarr;
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. PRINCIPAL WELCOME & QUOTE CARD (Matching Reference Layout) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 sm:p-12">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* Left: Principal Photo & Welcome Message */}
            <div className="lg:col-span-8 flex flex-col sm:flex-row gap-6 items-center sm:items-start">
              <div className="w-32 h-32 sm:w-36 sm:h-36 rounded-2xl overflow-hidden bg-slate-900 shrink-0 border-2 border-slate-200 shadow-sm">
                <img
                  src="/images/school/teacher_mentoring_students.jpg"
                  alt="Dr. Meera Sharma, Principal of Sunrise School"
                  className="w-full h-full object-cover object-top"
                />
              </div>
              <div className="space-y-3 text-center sm:text-left">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  From the Principal's Desk
                </span>
                <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight font-serif">
                  Welcome to Sunrise School
                </h2>
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                  At Sunrise School, we believe in creating an environment where children feel safe, valued, and inspired to learn. Our focus is on building strong foundations—academically, emotionally, and ethically—so that every student can face the future with confidence.
                </p>
                <div className="pt-1">
                  <span className="block font-serif font-bold text-slate-900 text-sm">Dr. Meera Sharma</span>
                  <span className="text-xs text-slate-500">Principal, Sunrise School</span>
                </div>
              </div>
            </div>

            {/* Right: Inspirational Quote Card */}
            <div className="lg:col-span-4 bg-indigo-50/80 rounded-2xl p-6 border border-indigo-100 space-y-3">
              <div className="text-amber-500 text-xl font-serif">“</div>
              <p className="text-sm font-serif italic text-slate-800 leading-relaxed">
                The purpose of education is to prepare the child for life, not just for exams.
              </p>
              <div className="pt-2 border-t border-indigo-100 text-xs font-semibold text-slate-600">
                — Dr. Meera Sharma
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. STATS BAR */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-slate-900 text-white rounded-xl p-5 text-center shadow-xs">
            <div className="text-3xl font-extrabold font-mono text-amber-400">1,200+</div>
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-300 mt-1">Students</div>
          </div>
          <div className="bg-slate-900 text-white rounded-xl p-5 text-center shadow-xs">
            <div className="text-3xl font-extrabold font-mono text-amber-400">75+</div>
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-300 mt-1">Faculty</div>
          </div>
          <div className="bg-slate-900 text-white rounded-xl p-5 text-center shadow-xs">
            <div className="text-3xl font-extrabold font-mono text-amber-400">15+</div>
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-300 mt-1">Years</div>
          </div>
          <div className="bg-slate-900 text-white rounded-xl p-5 text-center shadow-xs">
            <div className="text-3xl font-extrabold font-mono text-amber-400">25+</div>
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-300 mt-1">Activities</div>
          </div>
          <div className="col-span-2 md:col-span-1 bg-slate-900 text-white rounded-xl p-5 text-center shadow-xs">
            <div className="text-3xl font-extrabold font-mono text-amber-400">100%</div>
            <div className="text-xs font-semibold uppercase tracking-wider text-slate-300 mt-1">Pass Rate</div>
          </div>
        </div>
      </section>

      {/* 5. FINAL CALL TO ACTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white rounded-2xl p-8 sm:p-12 text-center space-y-6 shadow-xl border border-slate-800">
          <div className="max-w-2xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider bg-amber-400 text-slate-900 px-3 py-1 rounded-full">
              Session 2026–27 Admissions
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight font-serif text-white">
              Begin Your Child’s Journey at Sunrise School
            </h2>
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
              Submit an admission enquiry or complete the online application to secure a seat for Academic Session 2026–27.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-4 pt-2">
            <button
              onClick={() => setEnquiryModalOpen(true)}
              className="bg-amber-400 hover:bg-amber-300 text-slate-900 font-bold px-8 py-3.5 rounded-lg shadow-md transition-all text-sm cursor-pointer"
            >
              Admission Enquiry
            </button>
            <Link
              to="/apply"
              className="bg-white/10 hover:bg-white/20 text-white font-semibold px-8 py-3.5 rounded-lg border border-white/30 backdrop-blur transition-all text-sm"
            >
              Apply Online &rarr;
            </Link>
          </div>
        </div>
      </section>

      <AdmissionEnquiryModal isOpen={enquiryModalOpen} onClose={() => setEnquiryModalOpen(false)} />
    </div>
  );
}
