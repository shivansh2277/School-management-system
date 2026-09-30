import { useState } from "react";
import { Link } from "react-router-dom";

export function EventsPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  const categories = [
    { id: "all", label: "All Events" },
    { id: "academic", label: "Academic & Science" },
    { id: "cultural", label: "Cultural & Arts" },
    { id: "sports", label: "Sports & Athletics" },
    { id: "admissions", label: "Admissions & PTM" },
  ];

  const events = [
    {
      id: "sci-expo-2026",
      title: "Annual Science, STEM & Innovation Expo 2026",
      category: "academic",
      categoryLabel: "Academic & Science",
      image: "/images/school/stem_robotics_activity.jpg",
      badgeColor: "bg-indigo-100 text-indigo-800 border-indigo-200",
      dateMonth: "OCT",
      dateDay: "15",
      time: "09:00 AM – 03:00 PM",
      venue: "Composite Science Laboratories & Central Amphitheatre",
      attendees: "Students, Parents & Invited School Delegations",
      summary:
        "Over 120 student-built working models covering renewable solar grids, automated hydroponics, robotics line followers, and AI demonstrations assessed by eminent university professors.",
      highlights: ["Live robotics arena challenges", "Interactive chemistry magic show", "Keynote address by IIT scientist", "External jury awards"],
    },
    {
      id: "ptm-term-1",
      title: "Term-1 Parent-Teacher Collaborative Conference (PTM)",
      category: "admissions",
      categoryLabel: "Admissions & PTM",
      image: "/images/school/teacher_mentoring_students.jpg",
      badgeColor: "bg-amber-100 text-amber-800 border-amber-200",
      dateMonth: "OCT",
      dateDay: "28",
      time: "08:30 AM – 01:30 PM",
      venue: "Respective Student Section Classrooms",
      attendees: "All Parents & Class Educators",
      summary:
        "Dedicated one-on-one parent-educator dialogue reviewing Mid-Term scholastic scores, holistic behavioral rubrics, co-curricular achievements, and personalized learning milestones.",
      highlights: ["Individual appointment slots", "Digital report card review", "Counselor desk consultation", "Parent feedback kiosk"],
    },
    {
      id: "tarang-sports-2026",
      title: "Tarang 2026 — Annual Inter-House Athletic Meet",
      category: "sports",
      categoryLabel: "Sports & Athletics",
      image: "/images/school/sports_field_athletics.jpg",
      badgeColor: "bg-emerald-100 text-emerald-800 border-emerald-200",
      dateMonth: "NOV",
      dateDay: "20–22",
      time: "08:00 AM – 04:00 PM (3-Day Spectacle)",
      venue: "Main Athletic Grounds & Running Track",
      attendees: "Students, Families & Alumni",
      summary:
        "Three exhilarating days of sprint relays, high jump, shot put, hurdle courses, Tug-of-War, and the ceremonial House March Past celebrating athletic vigor and sportsmanship.",
      highlights: ["Olympic torch lighting ceremony", "March-past band parade", "Parent-Teacher sprint race", "House Championship Trophy"],
    },
    {
      id: "udaan-cultural-fest",
      title: "Udaan 2026 — Annual Literary & Performing Arts Fest",
      category: "cultural",
      categoryLabel: "Cultural & Arts",
      image: "/images/school/music_room_performing.jpg",
      badgeColor: "bg-purple-100 text-purple-800 border-purple-200",
      dateMonth: "DEC",
      dateDay: "12",
      time: "10:00 AM – 05:00 PM",
      venue: "Sunrise Central Auditorium",
      attendees: "Open to Students, Parents & Guests",
      summary:
        "A grand cultural showcase featuring multilingual dramatic adaptations of Shakespeare and Premchand, classical sitar-tabla jugalbandi, choir anthems, and an inter-school debate final.",
      highlights: ["Dual-act theatrical production", "Sufi & classical musical orchestra", "Visual arts exhibition in foyer", "Distinguished guest felicitation"],
    },
    {
      id: "winter-carnival-2027",
      title: "Sunrise Winter Carnival & Community Charity Bazaar",
      category: "cultural",
      categoryLabel: "Cultural & Arts",
      image: "/images/school/art_studio_painting.jpg",
      badgeColor: "bg-rose-100 text-rose-800 border-rose-200",
      dateMonth: "JAN",
      dateDay: "18",
      time: "10:00 AM – 04:00 PM",
      venue: "School Quadrangle & Front Lawns",
      attendees: "Open to Lucknow Public & Families",
      summary:
        "A joyous community celebration with student-managed culinary stalls, artisan crafts, scientific game kiosks, live musical jam sessions, and charity fundraising for underprivileged schools.",
      highlights: ["Student entrepreneurship stalls", "Book exchange corner", "Live acoustic stage", "100% charity proceeds donation"],
    },
    {
      id: "board-citation-2027",
      title: "Class X & XII CBSE Board Blessing & Citation Ceremony",
      category: "academic",
      categoryLabel: "Academic & Science",
      image: "/images/school/central_library_reading.jpg",
      badgeColor: "bg-blue-100 text-blue-800 border-blue-200",
      dateMonth: "FEB",
      dateDay: "10",
      time: "11:00 AM – 01:30 PM",
      venue: "School Auditorium",
      attendees: "Graduating Students & Parents",
      summary:
        "A solemn blessing ceremony marking the culmination of senior secondary schooling. Features inspirational mentorship talks, ceremonial lamp lighting, and presentation of CBSE admit cards.",
      highlights: ["Havan & Vedic lamp lighting", "Principal's citation scrolls", "Stress-management orientation", "Farewell lunch for seniors"],
    },
  ];

  const termSchedule = [
    {
      term: "Term 1 (Autumn Semester)",
      dates: "April 2026 – September 2026",
      milestones: [
        "Session Commencement & Orientation: April 3, 2026",
        "Periodic Test 1 (PT-1): July 14–21, 2026",
        "Mid-Term Examinations: September 15–26, 2026",
        "Term-1 Results & PTM: October 28, 2026",
      ],
    },
    {
      term: "Term 2 (Spring Semester)",
      dates: "October 2026 – March 2027",
      milestones: [
        "Periodic Test 2 (PT-2): December 1–8, 2026",
        "Pre-Board Exams (X & XII): January 6–19, 2027",
        "Annual Board Practical Exams: January 20 – February 5, 2027",
        "CBSE Board Exams & Annual Assessments: February – March 2027",
      ],
    },
  ];

  const filteredEvents =
    selectedCategory === "all"
      ? events
      : events.filter((ev) => ev.category === selectedCategory);

  return (
    <div className="space-y-16 sm:space-y-20 pb-16">
      {/* 1. HERO BANNER */}
      <section className="bg-gradient-to-b from-indigo-50/80 via-ground to-white py-14 sm:py-20 border-b border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3.5 py-1 rounded-full">
            Campus Happenings & Calendar
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
            Events & Academic Calendar
          </h1>
          <p className="text-base sm:text-lg text-ink-soft max-w-2xl mx-auto leading-relaxed">
            Stay abreast of upcoming exhibitions, athletic meets, parent-teacher forums, and scholastic milestones across the 2026–27 academic year.
          </p>
        </div>
      </section>

      {/* 2. FILTER & EVENTS LIST */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-rule pb-5">
          <div>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Upcoming School Events
            </h2>
            <p className="text-xs sm:text-sm text-ink-soft mt-1">
              Select a category to filter upcoming campus programs.
            </p>
          </div>

          {/* Category Filter Pills */}
          <div className="flex flex-wrap items-center gap-2">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  selectedCategory === cat.id
                    ? "bg-primary text-white shadow-xs"
                    : "bg-surface text-slate-700 hover:bg-slate-100 border border-rule"
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Events Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {filteredEvents.map((item) => (
            <div
              key={item.id}
              className="group bg-surface rounded-2xl border border-rule shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden flex flex-col justify-between"
            >
              {item.image && (
                <div className="h-44 w-full bg-slate-900 relative overflow-hidden">
                  <img
                    src={item.image}
                    alt={item.title}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-transparent to-transparent" />
                  <div className="absolute bottom-3 left-4 right-4 flex items-center justify-between text-xs text-white">
                    <span className="font-semibold bg-slate-900/80 px-2.5 py-0.5 rounded-full backdrop-blur-xs">
                      📍 {item.venue}
                    </span>
                  </div>
                </div>
              )}
              <div className="p-6 sm:p-7 space-y-4">
                {/* Header row with date block and category badge */}
                <div className="flex items-start gap-4">
                  {/* Date badge */}
                  <div className="w-16 h-16 rounded-2xl bg-slate-900 text-white flex flex-col items-center justify-center shrink-0 shadow-sm">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400">
                      {item.dateMonth}
                    </span>
                    <span className="text-xl font-extrabold font-mono leading-none mt-0.5">
                      {item.dateDay}
                    </span>
                  </div>

                  <div className="space-y-1 flex-1 min-w-0">
                    <span
                      className={`inline-block text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${item.badgeColor}`}
                    >
                      {item.categoryLabel}
                    </span>
                    <h3 className="text-lg sm:text-xl font-bold text-slate-900 leading-snug">
                      {item.title}
                    </h3>
                  </div>
                </div>

                <p className="text-xs sm:text-sm text-ink-soft leading-relaxed">
                  {item.summary}
                </p>

                {/* Event Highlights list */}
                <div className="bg-ground p-3.5 rounded-xl border border-rule/70 space-y-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-700 block">
                    Key Highlights
                  </span>
                  <ul className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-xs text-ink-soft">
                    {item.highlights.map((h, idx) => (
                      <li key={idx} className="flex items-center gap-1.5">
                        <span className="text-primary font-bold">•</span>
                        <span>{h}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Event Metadata Footer */}
              <div className="bg-ground/60 px-6 sm:px-7 py-3 border-t border-rule flex flex-wrap items-center justify-between gap-3 text-xs text-ink-soft">
                <span className="flex items-center gap-1.5">
                  <span>🕒</span>
                  <span className="font-medium text-slate-700">{item.time}</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span>📍</span>
                  <span className="font-medium text-slate-700">{item.venue}</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. ACADEMIC TERM CALENDAR & BREAKS */}
      <section className="bg-ground py-16 border-y border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
              Structured Academic Terms
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
              Academic Term Architecture 2026–27
            </h2>
            <p className="text-sm text-ink-soft">
              Sunrise School follows a balanced two-term academic framework conforming to CBSE guidelines with regular formative assessments.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {termSchedule.map((sched) => (
              <div
                key={sched.term}
                className="bg-surface rounded-2xl border border-rule p-7 shadow-sm space-y-5"
              >
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-primary">
                    {sched.dates}
                  </span>
                  <h3 className="text-xl font-bold text-slate-900 mt-1">{sched.term}</h3>
                </div>

                <div className="space-y-3">
                  {sched.milestones.map((m, idx) => (
                    <div key={idx} className="flex items-start gap-3 text-xs">
                      <span className="w-5 h-5 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <span className="text-slate-800 font-medium leading-relaxed">{m}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {/* School Vacations & Recess Summary Bar */}
          <div className="bg-surface rounded-2xl border border-rule p-6 shadow-sm">
            <h4 className="font-bold text-sm text-slate-900 mb-3 flex items-center gap-2">
              <span>🏖️</span>
              <span>Major Vacation Windows (Academic Session 2026–27)</span>
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-ink-soft">
              <div className="p-3 bg-ground rounded-xl border border-rule/70">
                <strong className="block text-slate-900 font-semibold">Summer Vacation</strong>
                <span>May 18, 2026 – June 30, 2026</span>
                <span className="block text-[11px] text-ink-faint mt-0.5">School reopens July 1 for all classes.</span>
              </div>
              <div className="p-3 bg-ground rounded-xl border border-rule/70">
                <strong className="block text-slate-900 font-semibold">Autumn Break (Diwali/Chhath)</strong>
                <span>October 29, 2026 – November 6, 2026</span>
                <span className="block text-[11px] text-ink-faint mt-0.5">Inclusive of Dussehra & Diwali holidays.</span>
              </div>
              <div className="p-3 bg-ground rounded-xl border border-rule/70">
                <strong className="block text-slate-900 font-semibold">Winter Recess</strong>
                <span>December 31, 2026 – January 11, 2027</span>
                <span className="block text-[11px] text-ink-faint mt-0.5">Subject to Lucknow district DM directives.</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. ERP INTEGRATION BANNER */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-primary to-indigo-900 text-white rounded-2xl p-8 sm:p-12 shadow-card flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center md:text-left max-w-xl">
            <h3 className="text-2xl font-bold tracking-tight">
              Real-time Notifications via ERP & Mobile App
            </h3>
            <p className="text-indigo-100 text-xs sm:text-sm leading-relaxed">
              Enrolled families receive immediate push notifications, digital circulars, and event reminders directly via the Sunrise ERP mobile application.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/login"
              className="bg-white hover:bg-slate-50 text-primary font-bold px-6 py-3 rounded-input text-xs sm:text-sm shadow-md transition-all"
            >
              Access ERP Portal
            </Link>
            <Link
              to="/admissions"
              className="bg-amber-400 hover:bg-amber-300 text-slate-900 font-bold px-6 py-3 rounded-input text-xs sm:text-sm shadow-md transition-all"
            >
              Admissions 2026–27 &rarr;
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
