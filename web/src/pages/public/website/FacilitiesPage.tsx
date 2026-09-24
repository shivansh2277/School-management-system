import { Link } from "react-router-dom";

export function FacilitiesPage() {
  const facilities = [
    {
      icon: "🖥️",
      title: "Interactive Smart Classrooms",
      tag: "Technology",
      desc: "Every classroom is equipped with high-definition interactive touch panels, dual-speaker acoustics, and ergonomic, height-appropriate student desks designed for collaborative group work.",
      highlights: ["75-inch 4K Interactive Panels", "Ergonomic modular seating", "Climate controlled comfort", "Acoustically treated walls"],
    },
    {
      icon: "🔬",
      title: "Composite Science Laboratories",
      tag: "Academics",
      desc: "State-of-the-art Physics, Chemistry, and Biology practical laboratories fitted with fume hoods, digital microscopes, glassware, and precision sensors meeting CBSE senior secondary standards.",
      highlights: ["Individual student workstations", "Strict safety showers & fire gear", "Digital sensor probes", "CBSE board practicals compliant"],
    },
    {
      icon: "🤖",
      title: "Computer, AI & Robotics Hub",
      tag: "STEM",
      desc: "Dedicated computing center with 60 high-performance workstations, high-speed fiber internet, Python and Scratch coding environments, and Arduino / LEGO robotics discovery kits.",
      highlights: ["1:1 Student-to-terminal ratio", "Secure firewall & content filtering", "Robotics & IoT hardware kits", "Class 3+ coding curriculum"],
    },
    {
      icon: "📚",
      title: "Central Library & Media Center",
      tag: "Learning Hub",
      desc: "A calm, light-filled knowledge sanctuary stocking over 12,000 fiction, non-fiction, encyclopedic, and reference books, alongside national dailies and digital e-book reading kiosks.",
      highlights: ["12,000+ Curated volumes", "Quiet study & research carrels", "Dedicated storytelling corner", "Regular author interactions"],
    },
    {
      icon: "⚽",
      title: "Sports Complex & Athletic Grounds",
      tag: "Athletics",
      desc: "Sprawling outdoor football turf, international standard cricket practice nets, synthetic-surfaced basketball and badminton courts, table tennis hall, and a dedicated 200m athletic running track.",
      highlights: ["Full-size multi-sport turf", "Certified NIS sports coaches", "Inter-school tournament host", "Daily physical education periods"],
    },
    {
      icon: "🎨",
      title: "Creative Arts & Performing Studios",
      tag: "Creative",
      desc: "Spacious fine arts studio for sketching, painting, and pottery, paired with acoustically insulated Indian and Western music chambers and a mirrored classical dance practice hall.",
      highlights: ["Indian classical & western instruments", "Wall-to-wall mirrored dance floor", "Pottery wheel & clay workshop", "Annual theatre productions"],
    },
    {
      icon: "🚌",
      title: "GPS-Monitored Safe Transport",
      tag: "Safety",
      desc: "A modern fleet of 25+ air-conditioned school buses spanning all prime residential sectors of Lucknow. Equipped with live GPS location tracking, CCTV surveillance, speed limiters, and female conductors.",
      highlights: ["Live GPS tracking updates", "Dual CCTV camera coverage", "Speed governors (max 40 km/h)", "Trained female attendant on board"],
    },
    {
      icon: "🩺",
      title: "Health & Medical Infirmary",
      tag: "Wellness",
      desc: "Full-time licensed registered nurse on campus, well-equipped 4-bed medical recovery room, pediatric tie-ups with leading multi-specialty hospitals, and periodic dental and ophthalmic health screenings.",
      highlights: ["Full-time registered nurse", "Doctor on call 24x7", "Annual student medical check-ups", "Fully stocked first-aid stations"],
    },
    {
      icon: "🌿",
      title: "Eco-Campus & Organic Garden",
      tag: "Environment",
      desc: "Sunrise School is committed to sustainable living with a 50kW rooftop solar power setup, comprehensive rainwater harvesting system, and a student-tended botanical kitchen garden.",
      highlights: ["50kW Clean solar energy", "Rainwater recharge pits", "Student green ambassadors", "Zero single-use plastic campus"],
    },
  ];

  return (
    <div className="space-y-16 sm:space-y-20 pb-16">
      {/* 1. HERO BANNER */}
      <section className="bg-gradient-to-b from-indigo-50/80 via-ground to-white py-14 sm:py-20 border-b border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
            Campus Infrastructure
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
            World-Class Campus Facilities
          </h1>
          <p className="text-base sm:text-lg text-ink-soft max-w-2xl mx-auto leading-relaxed">
            A safe, green 5-acre campus in Gomti Nagar, Lucknow, intentionally engineered to inspire discovery, physical vitality, and creative self-expression.
          </p>
        </div>
      </section>

      {/* 2. FACILITIES GRID */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {facilities.map((fac) => (
            <div
              key={fac.title}
              className="bg-surface rounded-2xl border border-rule shadow-sm hover:shadow-md transition-shadow p-6 sm:p-7 flex flex-col justify-between space-y-5"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-3xl p-2 bg-ground rounded-xl border border-rule/80 inline-block">
                    {fac.icon}
                  </span>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-primary bg-primary-soft px-2.5 py-1 rounded-full">
                    {fac.tag}
                  </span>
                </div>
                <h3 className="text-xl font-bold text-slate-900">{fac.title}</h3>
                <p className="text-xs text-ink-soft leading-relaxed">{fac.desc}</p>
              </div>

              <div className="pt-4 border-t border-rule">
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Key Specifications
                </div>
                <ul className="text-xs text-slate-700 space-y-1">
                  {fac.highlights.map((h) => (
                    <li key={h} className="flex items-center gap-2">
                      <span className="text-emerald-600 font-bold">•</span>
                      <span>{h}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. SAFETY & CAMPUS SECURITY STRIP */}
      <section className="bg-ground py-16 border-y border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-2xl border border-rule shadow-sm p-8 sm:p-12">
            <div className="max-w-3xl space-y-4">
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-100 px-3 py-1 rounded-full">
                Zero-Compromise Safety
              </span>
              <h2 className="text-3xl font-bold text-slate-900 tracking-tight">
                Your Child's Security is Our Sacred Trust
              </h2>
              <p className="text-sm text-ink-soft leading-relaxed">
                Sunrise School adheres to rigorous child safety protocols across all campus touchpoints: 24x7 gate security, verified identity visitor access, 120+ CCTV cameras monitored live, strict fire safety drills, and zero-tolerance anti-bullying vigilance committees.
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-4 text-xs font-semibold text-slate-800">
                <div className="bg-ground p-3 rounded-lg border border-rule text-center">
                  120+ CCTV Cameras
                </div>
                <div className="bg-ground p-3 rounded-lg border border-rule text-center">
                  24/7 Manned Gates
                </div>
                <div className="bg-ground p-3 rounded-lg border border-rule text-center">
                  POCSO Committee
                </div>
                <div className="bg-ground p-3 rounded-lg border border-rule text-center">
                  GPS Live Buses
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. CALL TO ACTION STRIP */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-primary to-indigo-900 text-white rounded-2xl p-8 sm:p-12 text-center space-y-6 shadow-card">
          <div className="max-w-2xl mx-auto space-y-3">
            <h2 className="text-3xl font-bold tracking-tight">
              Experience the Sunrise Campus First-Hand
            </h2>
            <p className="text-sm text-indigo-100 leading-relaxed">
              We invite prospective families to schedule an escorted campus walkthrough. Observe our active laboratories, library, and sports grounds in person.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/admissions"
              className="bg-white text-primary hover:bg-slate-50 font-bold px-7 py-3 rounded-input text-sm shadow-sm transition-all"
            >
              Book a Campus Tour &rarr;
            </Link>
            <Link
              to="/apply"
              className="bg-amber-400 hover:bg-amber-300 text-slate-900 font-bold px-7 py-3 rounded-input text-sm shadow-sm transition-all"
            >
              Apply Online Today
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
