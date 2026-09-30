import { useState } from "react";
import { Link } from "react-router-dom";
import { AdmissionEnquiryModal } from "../../../components/public/AdmissionEnquiryModal";

export function AboutPage() {
  const [enquiryModalOpen, setEnquiryModalOpen] = useState(false);

  return (
    <div className="space-y-16 sm:space-y-20 pb-16">
      {/* 1. HERO BANNER */}
      <section className="bg-gradient-to-b from-indigo-50/80 via-white to-white py-14 sm:py-20 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-amber-100/80 border border-amber-200 px-3.5 py-1 rounded-full">
            Institutional Identity & Heritage • Estd. 2011
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight font-serif">
            About Sunrise School
          </h1>
          <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Fostering intellectual vigor, moral purpose, and creative curiosity since 2011 in Gomti Nagar, Lucknow, Uttar Pradesh.
          </p>
        </div>
      </section>

      {/* 2. THE SCHOOL STORY & JOURNEY */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-6 space-y-4">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-800 bg-amber-100 px-3 py-1 rounded-full">
              Our Journey
            </span>
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight font-serif">
              A Legacy of Child-Centric Academic Excellence
            </h2>
            <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
              Founded in 2011 in the heart of Gomti Nagar, Lucknow, Sunrise School was established with a singular conviction: that modern schooling must harmonize rigorous academic preparation with deep-rooted Indian values (<em className="font-serif">Sanskaar</em>).
            </p>
            <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
              Over the past 15 years, Sunrise School has evolved from a visionary primary academy into a premier CBSE-affiliated K-12 institution. Today, our 5-acre landscaped campus serves over 1,200 scholars across Science, Commerce, and Humanities streams.
            </p>
            <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
              Our tranquil academic quadrangle features interactive smart classrooms, composite science laboratories, an Atal Tinkering STEM hub, and all-weather athletic grounds designed to ignite every student's potential.
            </p>

            {/* Campus Photography Duo */}
            <div className="pt-2 grid grid-cols-2 gap-3">
              <div className="rounded-xl overflow-hidden shadow-xs h-36 bg-slate-900 border border-slate-200">
                <img
                  src="/images/school/school_entrance_gate.jpg"
                  alt="Sunrise School Main Entrance Gate"
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              </div>
              <div className="rounded-xl overflow-hidden shadow-xs h-36 bg-slate-900 border border-slate-200">
                <img
                  src="/images/school/main_reception_lobby.jpg"
                  alt="Sunrise School Reception Lobby"
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
              </div>
            </div>
          </div>

          <div className="lg:col-span-6">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
              <h3 className="font-bold text-lg text-slate-900 border-b border-slate-100 pb-3 font-serif">
                Institutional Milestones Timeline
              </h3>
              <div className="space-y-4">
                <div className="flex gap-4">
                  <span className="w-12 font-mono font-bold text-sm text-primary shrink-0">2011</span>
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">Foundation Stone Laid</h4>
                    <p className="text-xs text-slate-600 mt-0.5">Established in Sector 4, Gomti Nagar with 150 foundational scholars and 12 dedicated faculty.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <span className="w-12 font-mono font-bold text-sm text-primary shrink-0">2014</span>
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">High School CBSE Affiliation</h4>
                    <p className="text-xs text-slate-600 mt-0.5">Granted secondary affiliation; inaugurated physics, chemistry, and biology laboratories.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <span className="w-12 font-mono font-bold text-sm text-primary shrink-0">2017</span>
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">Senior Secondary Accreditation</h4>
                    <p className="text-xs text-slate-600 mt-0.5">Launched Class XI & XII in Science, Commerce, and Humanities streams with career counseling cell.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <span className="w-12 font-mono font-bold text-sm text-primary shrink-0">2020</span>
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">Atal Tinkering & STEM Robotics Hub</h4>
                    <p className="text-xs text-slate-600 mt-0.5">Established 3D printing, microcontroller, and IoT robotics laboratory for student innovation.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <span className="w-12 font-mono font-bold text-sm text-primary shrink-0">2023</span>
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">Excellence Award in Pedagogy</h4>
                    <p className="text-xs text-slate-600 mt-0.5">Recognized for outstanding 100% board examination pass record and holistic sports infrastructure.</p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <span className="w-12 font-mono font-bold text-sm text-primary shrink-0">2026</span>
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">Smart Campus & Unified ERP</h4>
                    <p className="text-xs text-slate-600 mt-0.5">Complete digital transformation with interactive panels in all classrooms and real-time parent portals.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. OUR FOUNDER SECTION */}
      <section className="bg-slate-900 text-white py-16 sm:py-20 border-y border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            {/* Founder Portrait Image */}
            <div className="lg:col-span-5 flex justify-center">
              <div className="relative rounded-2xl overflow-hidden shadow-2xl border-4 border-slate-800 bg-slate-950 max-w-sm w-full">
                <img
                  src="/images/school/founder_portrait.jpg"
                  alt="Dr. Anand Mohan Shukla, Founder & Chairman of Sunrise School"
                  className="w-full h-auto object-cover"
                />
                <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-slate-950 via-slate-950/70 to-transparent p-5 text-center">
                  <h3 className="text-xl font-bold font-serif text-white">Dr. Anand Mohan Shukla</h3>
                  <p className="text-xs text-amber-300 font-semibold mt-0.5">Founder & Chairman, Board of Trustees</p>
                  <p className="text-[11px] text-slate-400">M.A., Ph.D. (Education), D.Lit.</p>
                </div>
              </div>
            </div>

            {/* Founder Bio & Philosophy */}
            <div className="lg:col-span-7 space-y-6">
              <div className="space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-amber-400 bg-amber-400/10 border border-amber-400/30 px-3.5 py-1 rounded-full">
                  Founding Trustee Profile
                </span>
                <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight font-serif text-white">
                  Meet Our Visionary Founder
                </h2>
              </div>

              <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
                Dr. Anand Mohan Shukla, a distinguished educationist and social reformer with over four decades of service in Indian academia, founded Sunrise School in 2011 to redefine schooling for the 21st century.
              </p>
              <p className="text-sm sm:text-base text-slate-300 leading-relaxed">
                His founding philosophy rests on the conviction that true education must go beyond rote textbook memorization. Under his leadership, Sunrise School introduced experiential science labs, mandatory sports participation, and moral shloka assemblies to cultivate balanced, self-disciplined human beings.
              </p>

              {/* Founder's Inspiring Quote Card */}
              <div className="bg-slate-800/90 rounded-2xl p-6 border-l-4 border-amber-400 border-slate-700 shadow-lg space-y-2">
                <p className="text-base sm:text-lg font-serif italic text-amber-200 leading-snug">
                  "The true purpose of education is not merely to prepare a child for examinations, but to kindle curiosity, instill unyielding character, and empower them to build confident futures."
                </p>
                <div className="text-xs font-semibold text-slate-400 text-right">
                  — Dr. Anand Mohan Shukla, Founder's Convocation Address
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. THE 7-C EDUCATIONAL PHILOSOPHY */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-amber-100 px-3.5 py-1 rounded-full">
            Educational Framework
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight font-serif">
            The 7-C Educational Philosophy
          </h2>
          <p className="text-sm text-slate-600 leading-relaxed">
            Our holistic curriculum is built around seven core pillars designed to prepare scholars for life, leadership, and lifelong learning.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { title: "Curiosity", icon: "🔍", desc: "Instilling a lifelong passion for questioning, scientific inquiry, and self-directed exploration." },
            { title: "Critical Thinking", icon: "🧠", desc: "Empowering learners to analyze data, evaluate evidence, and solve complex real-world problems." },
            { title: "Character", icon: "⚖️", desc: "Anchoring academic achievement in moral integrity, honesty, and ethical responsibility." },
            { title: "Creativity", icon: "🎨", desc: "Nurturing artistic expression, inventive design, and original thinking across all disciplines." },
            { title: "Collaboration", icon: "🤝", desc: "Fostering teamwork, house camaraderie, and mutual respect in group problem-solving." },
            { title: "Communication", icon: "🗣️", desc: "Developing articulate oratory and persuasive writing skills in both English and Hindi." },
            { title: "Confidence", icon: "🌟", desc: "Building self-assurance to speak boldly, embrace challenges, and lead with humility." },
            { title: "Compassion", icon: "💖", desc: "Cultivating empathy, environmental stewardship, and community service toward others." },
          ].map((item) => (
            <div
              key={item.title}
              className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs hover:shadow-md transition-shadow space-y-3"
            >
              <div className="text-3xl p-2 bg-slate-50 rounded-xl border border-slate-200 inline-block">
                {item.icon}
              </div>
              <h3 className="text-lg font-bold text-slate-900 font-serif">{item.title}</h3>
              <p className="text-xs text-slate-600 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 5. CORE INSTITUTIONAL VALUES */}
      <section className="bg-slate-50 py-16 border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-800 bg-amber-100 px-3 py-1 rounded-full">
              Guiding Ethos
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight font-serif">
              Core Institutional Values
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-2 text-center">
              <div className="text-3xl">🛡️</div>
              <h3 className="font-bold text-base text-slate-900 font-serif">Integrity</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Uncompromising honesty, moral clarity, and ethical courage in thought, word, and deed.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-2 text-center">
              <div className="text-3xl">🏆</div>
              <h3 className="font-bold text-base text-slate-900 font-serif">Excellence</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Striving constantly for highest standards in scholarship, co-curriculars, and conduct.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-2 text-center">
              <div className="text-3xl">🌐</div>
              <h3 className="font-bold text-base text-slate-900 font-serif">Inclusivity</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Welcoming every background, valuing diverse perspectives, and creating a supportive space.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-2 text-center">
              <div className="text-3xl">🌱</div>
              <h3 className="font-bold text-base text-slate-900 font-serif">Empathy</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Compassionate awareness of others, service to community, and environmental stewardship.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 6. CAMPUS VISUAL SHOWCASE */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-amber-100 px-3 py-1 rounded-full">
            Campus Experience
          </span>
          <h2 className="text-3xl font-bold text-slate-900 tracking-tight font-serif">
            A Glimpse into Sunrise Campus Life
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-2xl overflow-hidden h-48 border border-slate-200 shadow-xs bg-slate-900">
            <img
              src="/images/school/modern_classroom_learning.jpg"
              alt="Smart Classroom at Sunrise School"
              className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
          </div>
          <div className="rounded-2xl overflow-hidden h-48 border border-slate-200 shadow-xs bg-slate-900">
            <img
              src="/images/school/science_lab_practical.jpg"
              alt="Science Practical Lab"
              className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
          </div>
          <div className="rounded-2xl overflow-hidden h-48 border border-slate-200 shadow-xs bg-slate-900">
            <img
              src="/images/school/central_library_reading.jpg"
              alt="Central Library Reading Hub"
              className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
          </div>
          <div className="rounded-2xl overflow-hidden h-48 border border-slate-200 shadow-xs bg-slate-900">
            <img
              src="/images/school/sports_field_athletics.jpg"
              alt="Outdoor Athletic Grounds"
              className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
          </div>
        </div>
      </section>

      {/* 7. FINAL CALL TO ACTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-slate-900 text-white rounded-2xl p-8 sm:p-12 shadow-xl flex flex-col md:flex-row items-center justify-between gap-6 border border-slate-800">
          <div className="space-y-2 text-center md:text-left max-w-xl">
            <h3 className="text-2xl font-bold tracking-tight font-serif text-white">
              Ready to Discover the Sunrise Difference?
            </h3>
            <p className="text-slate-300 text-xs sm:text-sm leading-relaxed">
              Connect with our admissions desk, book a personalized campus tour, or initiate an online application today.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={() => setEnquiryModalOpen(true)}
              className="bg-amber-400 hover:bg-amber-300 text-slate-900 font-bold px-6 py-3 rounded-lg text-xs sm:text-sm shadow-md transition-all cursor-pointer"
            >
              Admission Enquiry
            </button>
            <Link
              to="/apply"
              className="bg-white hover:bg-slate-100 text-slate-900 font-bold px-6 py-3 rounded-lg text-xs sm:text-sm shadow-md transition-all"
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
