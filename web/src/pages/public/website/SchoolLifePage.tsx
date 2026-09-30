import { useState } from "react";
import { Link } from "react-router-dom";
import { ALL_SCHOOL_PHOTOS, SchoolPhoto } from "./schoolPhotos";

export function SchoolLifePage() {
  const [selectedHouse, setSelectedHouse] = useState<string>("all");
  const [galleryFilter, setGalleryFilter] = useState<string>("all");
  const [activePhoto, setActivePhoto] = useState<SchoolPhoto | null>(null);

  const houses = [
    {
      id: "agni",
      name: "Agni House",
      color: "from-rose-600 to-amber-600",
      border: "border-rose-200",
      bgLight: "bg-rose-50",
      textDark: "text-rose-900",
      accent: "text-rose-600",
      motto: "Tejasvi Navadhitamastu (Let our learning be radiant)",
      element: "Fire • Energy, Courage & Passion",
      shield: "🔥",
      captain: "Raghav Mehrotra (XII-A)",
      viceCaptain: "Suhani Saxena (XI-B)",
      points: "1,420 pts",
      description:
        "Agni House exemplifies fearless ambition, high academic vigor, and spirited competitiveness in sports and debate.",
    },
    {
      id: "prithvi",
      name: "Prithvi House",
      color: "from-emerald-600 to-teal-700",
      border: "border-emerald-200",
      bgLight: "bg-emerald-50",
      textDark: "text-emerald-900",
      accent: "text-emerald-600",
      motto: "Dharayati Iti Dharani (Steadfast and nurturing)",
      element: "Earth • Resilience, Integrity & Humility",
      shield: "🌿",
      captain: "Aditya Srivastava (XII-B)",
      viceCaptain: "Pooja Verma (XI-A)",
      points: "1,390 pts",
      description:
        "Prithvi House grounds its members in ethical discipline, environmental stewardship, and consistent teamwork.",
    },
    {
      id: "vayu",
      name: "Vayu House",
      color: "from-sky-600 to-blue-700",
      border: "border-sky-200",
      bgLight: "bg-sky-50",
      textDark: "text-sky-900",
      accent: "text-sky-600",
      motto: "Satatam Gatimantah (Ever in motion, ever aspiring)",
      element: "Air • Wisdom, Curiosity & Freedom",
      shield: "💨",
      captain: "Manav Joshi (XII-C)",
      viceCaptain: "Ananya Dixit (XI-C)",
      points: "1,450 pts",
      description:
        "Vayu House champions creative thinking, scientific inquiry, literary flair, and swift agility in athletic pursuits.",
    },
    {
      id: "jal",
      name: "Jal House",
      color: "from-blue-700 to-indigo-800",
      border: "border-blue-200",
      bgLight: "bg-blue-50",
      textDark: "text-blue-900",
      accent: "text-blue-600",
      motto: "Shantih Snehascha (Peace, perseverance and unity)",
      element: "Water • Adaptability, Empathy & Depth",
      shield: "🌊",
      captain: "Arjun Tandon (XII-A)",
      viceCaptain: "Rhea Khare (XI-B)",
      points: "1,380 pts",
      description:
        "Jal House emphasizes emotional intelligence, artistic harmony, community outreach, and graceful resilience.",
    },
  ];

  const clubs = [
    {
      icon: "🤖",
      name: "Robotics & Tinkering Club",
      category: "STEM & Innovation",
      desc: "Hands-on engineering using Arduino, Raspberry Pi, LEGO Mindstorms, and 3D printing. Members design automated bots and participate in regional science expos.",
      meetingDay: "Wednesdays & Fridays",
      gradeSpan: "Classes VI – XII",
    },
    {
      icon: "🎙️",
      name: "Debate & Model UN Society",
      category: "Public Speaking",
      desc: "Fosters articulate oratory, parliamentary debating, critical current affairs analysis, and Model United Nations (MUN) simulation skills in English and Hindi.",
      meetingDay: "Tuesdays & Thursdays",
      gradeSpan: "Classes VII – XII",
    },
    {
      icon: "🌱",
      name: "Eco-Warriors & Nature Club",
      category: "Sustainability",
      desc: "Champions green campus initiatives, manages organic kitchen gardening, rainwater recharge monitoring, and neighborhood e-waste awareness campaigns.",
      meetingDay: "Saturdays",
      gradeSpan: "Classes IV – XII",
    },
    {
      icon: "🎭",
      name: "Performing Arts & Drama Ensemble",
      category: "Cultural Expression",
      desc: "Nurtures theatrical talents, street plays (Nukkad Natak), classical Indian dance (Kathak/Bharatnatyam), and contemporary choir productions.",
      meetingDay: "Mondays & Thursdays",
      gradeSpan: "Classes III – XII",
    },
    {
      icon: "✍️",
      name: "Literary & Creative Writing Guild",
      category: "Journalism & Literature",
      desc: "Publishes the annual school magazine 'Kshitij' and seasonal newsletters. Hosts book discussion circles, creative writing workshops, and poetry slams.",
      meetingDay: "Fridays",
      gradeSpan: "Classes V – XII",
    },
    {
      icon: "💻",
      name: "Code & Computational Thinkers",
      category: "Technology",
      desc: "Explores Python scripting, web design, UI/UX fundamentals, algorithmic problem solving, and ethical cybersecurity practices for junior coders.",
      meetingDay: "Thursdays & Saturdays",
      gradeSpan: "Classes VI – XII",
    },
  ];

  const sports = [
    {
      sport: "Cricket",
      icon: "🏏",
      coach: "Coach Rakesh Pandey (NIS Certified)",
      facilities: "3 All-weather turf practice nets, bowling machine & match pitch",
      achievements: "Runners-up in Lucknow Inter-School CBSE Tournament 2025",
    },
    {
      sport: "Basketball",
      icon: "🏀",
      coach: "Coach Sunita Rawat (National Player)",
      facilities: "2 Floodlit synthetic acrylic outdoor courts with hydraulic hoops",
      achievements: "Zonal Gold Medalists in Under-16 Girls Championship",
    },
    {
      sport: "Football",
      icon: "⚽",
      coach: "Coach Imran Khan (AIFF 'D' License)",
      facilities: "Natural grass 7-a-side field with drainage and training gear",
      achievements: "Winners of Gomti Nagar Inter-School Invitational Cup",
    },
    {
      sport: "Badminton & Table Tennis",
      icon: "🏸",
      coach: "Coach Devendra Singh",
      facilities: "Indoor wooden court badminton arena & 4 Stag tournament TT tables",
      achievements: "3 District-level qualifiers in UP State Badminton Trials",
    },
  ];

  const filteredHouses =
    selectedHouse === "all" ? houses : houses.filter((h) => h.id === selectedHouse);

  const filteredGalleryPhotos =
    galleryFilter === "all"
      ? ALL_SCHOOL_PHOTOS
      : ALL_SCHOOL_PHOTOS.filter((p) => p.category === galleryFilter);

  return (
    <div className="space-y-16 sm:space-y-20 pb-16">
      {/* 1. HERO BANNER */}
      <section className="bg-gradient-to-b from-indigo-50/80 via-white to-white py-14 sm:py-20 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-amber-100/70 border border-amber-200 px-3.5 py-1 rounded-full">
            Vibrant Campus Culture & Media
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight font-serif">
            School Life & Campus Gallery
          </h1>
          <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Where academic learning comes alive through house camaraderie, co-curricular societies, athletic grit, and authentic campus photography.
          </p>
        </div>
      </section>

      {/* 2. DAILY RHYTHM & CAMPUS LIFE SNAPSHOT */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-8 sm:p-12">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-5 space-y-4">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-800 bg-amber-100 px-3 py-1 rounded-full">
                The Daily Rhythm
              </span>
              <h2 className="text-3xl font-bold text-slate-900 tracking-tight font-serif">
                A Day in the Life of a Sunrise Scholar
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                From the calm mindfulness of morning assembly to dynamic lab practicals and lively sports periods, our school day is balanced to energize both intellect and character.
              </p>
              <div className="pt-2">
                <Link
                  to="/facilities"
                  className="inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:text-primary-dark"
                >
                  <span>Explore campus spaces where it happens</span>
                  <span>&rarr;</span>
                </Link>
              </div>
            </div>

            <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 space-y-1.5">
                <div className="text-xs font-bold text-primary">07:50 AM – 08:15 AM</div>
                <h3 className="font-bold text-sm text-slate-900">Morning Assembly & Sanskaar</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Prayer, thought for the day, news analysis, student speeches, and Sanskrit shloka recital for centered mindfulness.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 space-y-1.5">
                <div className="text-xs font-bold text-primary">08:15 AM – 11:30 AM</div>
                <h3 className="font-bold text-sm text-slate-900">Core Scholastic Blocks</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Concept-rich classroom instruction in mathematics, sciences, languages, and social studies with interactive digital boards.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 space-y-1.5">
                <div className="text-xs font-bold text-primary">11:30 AM – 12:05 PM</div>
                <h3 className="font-bold text-sm text-slate-900">Nutrition & Mindful Recess</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Nutritious tiffin time encouraging communal dining etiquette, peer bonding, and supervised open-air recreation.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70 space-y-1.5">
                <div className="text-xs font-bold text-primary">12:05 PM – 02:00 PM</div>
                <h3 className="font-bold text-sm text-slate-900">Co-Curriculars & Physical Ed</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Laboratory practicals, library research hours, robotics workshops, and dedicated outdoor sports coaching.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 3. FOUR HOUSES (PANCH-TATTVA THEME) */}
      <section className="bg-slate-50 py-16 border-y border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-primary bg-amber-100 px-3 py-1 rounded-full">
              House System
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight font-serif">
              The Four Houses of Sunrise
            </h2>
            <p className="text-sm text-slate-600">
              Every student from Grade 1 to 12 is inducted into one of four houses, fostering healthy competition, leadership responsibilities, and lifelong friendships.
            </p>
          </div>

          {/* House Filter Tabs */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            <button
              onClick={() => setSelectedHouse("all")}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                selectedHouse === "all"
                  ? "bg-slate-900 text-white shadow-xs"
                  : "bg-white text-slate-700 hover:bg-slate-100 border border-slate-200"
              }`}
            >
              All Houses
            </button>
            {houses.map((h) => (
              <button
                key={h.id}
                onClick={() => setSelectedHouse(h.id)}
                className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                  selectedHouse === h.id
                    ? "bg-primary text-white shadow-xs"
                    : "bg-white text-slate-700 hover:bg-slate-100 border border-slate-200"
                }`}
              >
                {h.name}
              </button>
            ))}
          </div>

          {/* Houses Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {filteredHouses.map((house) => (
              <div
                key={house.id}
                className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden flex flex-col justify-between hover:shadow-md transition-shadow"
              >
                <div className={`p-5 bg-gradient-to-r ${house.color} text-white space-y-2`}>
                  <div className="flex items-center justify-between">
                    <span className="text-3xl">{house.shield}</span>
                    <span className="text-xs font-bold bg-white/20 px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                      {house.points}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold tracking-tight">{house.name}</h3>
                  <p className="text-xs text-white/90 font-medium italic">{house.motto}</p>
                </div>

                <div className="p-5 space-y-4 flex-1 flex flex-col justify-between">
                  <div className="space-y-3">
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
                        Core Element
                      </span>
                      <p className="text-xs text-slate-800 font-semibold">{house.element}</p>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed">{house.description}</p>
                  </div>

                  <div className="pt-3 border-t border-slate-200 text-xs space-y-1">
                    <div className="text-slate-700">
                      <span className="font-semibold text-slate-900">Captain:</span> {house.captain}
                    </div>
                    <div className="text-slate-700">
                      <span className="font-semibold text-slate-900">Vice-Captain:</span> {house.viceCaptain}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. CLUBS & CREATIVE SOCIETIES */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-amber-100 px-3 py-1 rounded-full">
            Passion & Exploration
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight font-serif">
            Clubs & Creative Societies
          </h2>
          <p className="text-sm text-slate-600">
            Students pursue hands-on passions outside the classroom, developing teamwork, innovation, and leadership under dedicated faculty mentors.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {clubs.map((club) => (
            <div
              key={club.name}
              className="bg-white rounded-2xl border border-slate-200 shadow-xs hover:shadow-md transition-shadow p-6 flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-3xl p-2 bg-slate-50 rounded-xl border border-slate-200 inline-block">
                    {club.icon}
                  </span>
                  <span className="text-[11px] font-bold uppercase tracking-wider text-primary bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-full">
                    {club.category}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-slate-900 font-serif">{club.name}</h3>
                <p className="text-xs text-slate-600 leading-relaxed">{club.desc}</p>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                <span>🗓️ {club.meetingDay}</span>
                <span className="font-semibold text-slate-700">{club.gradeSpan}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 5. MERGED SUNRISE PHOTO GALLERY SECTION */}
      <section id="gallery" className="bg-slate-900 text-white py-16 sm:py-20 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
          <div className="text-center max-w-3xl mx-auto space-y-3">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-400 bg-amber-400/10 border border-amber-400/30 px-3.5 py-1 rounded-full">
              Institutional Photography
            </span>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight font-serif">
              Sunrise School Campus Photo Gallery
            </h2>
            <p className="text-sm text-slate-300 leading-relaxed">
              Explore authentic editorial photography captured at our Gomti Nagar Lucknow campus—showcasing modern smart classrooms, practical laboratories, athletic turf grounds, and vibrant student life.
            </p>
          </div>

          {/* Gallery Category Filter Tabs */}
          <div className="flex flex-wrap items-center justify-center gap-2">
            {[
              { id: "all", label: "All Photos" },
              { id: "campus", label: "Campus & Architecture" },
              { id: "classrooms", label: "Classrooms & Labs" },
              { id: "sports", label: "Sports & Athletics" },
              { id: "cultural", label: "Arts & Culture" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setGalleryFilter(tab.id)}
                className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                  galleryFilter === tab.id
                    ? "bg-amber-400 text-slate-900 font-bold shadow-md"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Gallery Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredGalleryPhotos.map((photo) => (
              <div
                key={photo.id}
                onClick={() => setActivePhoto(photo)}
                className="group bg-slate-800 rounded-2xl overflow-hidden border border-slate-700 shadow-md cursor-pointer hover:border-amber-400/50 transition-all duration-200 flex flex-col justify-between"
              >
                <div className="relative aspect-video overflow-hidden bg-slate-950">
                  <img
                    src={photo.src}
                    alt={photo.alt}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div className="absolute top-3 right-3 bg-slate-900/80 backdrop-blur-xs text-amber-300 text-[10px] font-bold px-2.5 py-1 rounded-full border border-amber-400/30 uppercase tracking-wider">
                    {photo.categoryLabel}
                  </div>
                </div>

                <div className="p-5 space-y-2 flex-1 flex flex-col justify-between">
                  <div>
                    <h3 className="text-base font-bold text-white group-hover:text-amber-300 transition-colors font-serif">
                      {photo.title}
                    </h3>
                    <p className="text-xs text-slate-300 mt-1 line-clamp-2 leading-relaxed">
                      {photo.caption}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-slate-700/80 flex items-center justify-between text-[11px] text-slate-400">
                    <span>📍 {photo.location}</span>
                    <span className="text-amber-400 font-semibold">View &rarr;</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PHOTO LIGHTBOX MODAL */}
      {activePhoto && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/90 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setActivePhoto(null)}
        >
          <div
            className="bg-slate-900 rounded-2xl max-w-3xl w-full border border-slate-700 overflow-hidden shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="relative aspect-video bg-black">
              <img
                src={activePhoto.src}
                alt={activePhoto.alt}
                className="w-full h-full object-contain"
              />
              <button
                onClick={() => setActivePhoto(null)}
                className="absolute top-4 right-4 bg-slate-900/80 text-white p-2 rounded-full hover:bg-slate-800 border border-slate-600"
              >
                ✕
              </button>
            </div>
            <div className="p-6 space-y-2 text-white">
              <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">
                {activePhoto.categoryLabel} • {activePhoto.location}
              </span>
              <h3 className="text-xl font-bold font-serif">{activePhoto.title}</h3>
              <p className="text-sm text-slate-300 leading-relaxed">{activePhoto.caption}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
