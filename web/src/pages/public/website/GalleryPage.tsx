import { useState } from "react";
import { Link } from "react-router-dom";
import { SCHOOL_PHOTOS, SchoolPhoto } from "./schoolPhotos";

interface GalleryItem extends SchoolPhoto {
  accentGradient?: string;
  icon?: string;
}

export function GalleryPage() {
  const [activeCategory, setActiveCategory] = useState<string>("all");
  const [selectedPhoto, setSelectedPhoto] = useState<GalleryItem | null>(null);

  const categories = [
    { id: "all", label: "All Showcases" },
    { id: "campus", label: "Campus & Architecture" },
    { id: "classrooms", label: "Classrooms & Labs" },
    { id: "sports", label: "Sports & Athletics" },
    { id: "cultural", label: "Cultural & Arts" },
    { id: "celebrations", label: "Events & Festivals" },
  ];

  const galleryItems: GalleryItem[] = [
    {
      ...SCHOOL_PHOTOS.heroCampus,
      id: "gal-1",
      title: "Sprawling 5-Acre Gomti Nagar Campus",
      category: "campus",
      categoryLabel: "Campus & Architecture",
      caption:
        "The modern academic block of Sunrise School surrounded by lush banyan greens and manicured front quadrangles.",
      date: "August 2026",
      accentGradient: "from-blue-900/60 to-indigo-950/80",
      icon: "🏫",
    },
    {
      ...SCHOOL_PHOTOS.modernClassroom,
      id: "gal-2",
      title: "Interactive Smart Classroom in Action",
      category: "classrooms",
      categoryLabel: "Classrooms & Labs",
      caption:
        "Students engaged in collaborative mathematics and science learning using 75-inch 4K touchscreen digital panels.",
      date: "September 2026",
      accentGradient: "from-indigo-800/60 to-slate-900/80",
      icon: "🖥️",
    },
    {
      ...SCHOOL_PHOTOS.scienceLab,
      id: "gal-3",
      title: "Composite Science Practical Laboratory",
      category: "classrooms",
      categoryLabel: "Classrooms & Labs",
      caption:
        "Class 11 & 12 Science scholars conducting precision chemical titrations under the supervision of senior faculty.",
      date: "July 2026",
      accentGradient: "from-teal-800/60 to-emerald-950/80",
      icon: "🔬",
    },
    {
      ...SCHOOL_PHOTOS.sportsField,
      id: "gal-4",
      title: "Outdoor Athletic Grounds & Soccer Turf",
      category: "sports",
      categoryLabel: "Sports & Athletics",
      caption:
        "Lush multi-sport athletic grounds with synthetic running track and full-size soccer turf against the school facade.",
      date: "October 2026",
      accentGradient: "from-emerald-800/60 to-slate-900/80",
      icon: "⚽",
    },
    {
      ...SCHOOL_PHOTOS.indoorArena,
      id: "gal-5",
      title: "Multi-Purpose Indoor Sports Arena",
      category: "sports",
      categoryLabel: "Sports & Athletics",
      caption:
        "State-of-the-art indoor sports arena hosting inter-house badminton tournaments and table tennis championships.",
      date: "November 2026",
      accentGradient: "from-amber-700/60 to-rose-950/80",
      icon: "🏸",
    },
    {
      ...SCHOOL_PHOTOS.artStudio,
      id: "gal-6",
      title: "Fine Arts & Painting Studio",
      category: "cultural",
      categoryLabel: "Cultural & Arts",
      caption:
        "Students honing watercolor landscape painting, acrylic canvases, and ceramic sculpture in the sunlit fine arts studio.",
      date: "August 2026",
      accentGradient: "from-purple-800/60 to-slate-900/80",
      icon: "🎨",
    },
    {
      ...SCHOOL_PHOTOS.musicRoom,
      id: "gal-7",
      title: "Acoustic Music & Classical Orchestra Suite",
      category: "cultural",
      categoryLabel: "Cultural & Arts",
      caption:
        "Acoustically treated music suite where students harmonize classical Indian instruments, acoustic guitars, and keyboards.",
      date: "September 2026",
      accentGradient: "from-rose-800/60 to-purple-950/80",
      icon: "🎵",
    },
    {
      ...SCHOOL_PHOTOS.stemRobotics,
      id: "gal-8",
      title: "Atal Robotics Tinkering Lab",
      category: "classrooms",
      categoryLabel: "Classrooms & Labs",
      caption:
        "High school tech innovators assembling microcontrollers, Arduino circuits, and robotic arms in the STEM lab.",
      date: "September 2026",
      accentGradient: "from-cyan-800/60 to-blue-950/80",
      icon: "🤖",
    },
    {
      ...SCHOOL_PHOTOS.computerLab,
      id: "gal-9",
      title: "Digital Computing & AI Laboratory",
      category: "classrooms",
      categoryLabel: "Classrooms & Labs",
      caption:
        "Students building software programs, exploring algorithmic logic, and developing digital fluency in our 60-seat IT suite.",
      date: "August 2026",
      accentGradient: "from-blue-800/60 to-slate-900/80",
      icon: "💻",
    },
    {
      ...SCHOOL_PHOTOS.centralLibrary,
      id: "gal-10",
      title: "Central Knowledge Sanctuary (Library)",
      category: "campus",
      categoryLabel: "Campus & Architecture",
      caption:
        "Quiet afternoon research carrels and reading circles in the 12,000-volume school library.",
      date: "August 2026",
      accentGradient: "from-blue-800/60 to-slate-900/80",
      icon: "📚",
    },
    {
      ...SCHOOL_PHOTOS.entranceGate,
      id: "gal-11",
      title: "Main Campus Entrance & Tree-Lined Avenue",
      category: "campus",
      categoryLabel: "Campus & Architecture",
      caption:
        "The imposing stone-clad entrance gates of Sunrise School with 24x7 security checkpoint and landscaped palm avenues.",
      date: "August 2026",
      accentGradient: "from-emerald-900/60 to-teal-950/80",
      icon: "🏛️",
    },
    {
      ...SCHOOL_PHOTOS.receptionLobby,
      id: "gal-12",
      title: "Administrative Reception & Welcome Rotunda",
      category: "campus",
      categoryLabel: "Campus & Architecture",
      caption:
        "The elegant ground-floor reception rotunda where parents and visitors are welcomed by admissions staff.",
      date: "July 2026",
      accentGradient: "from-amber-800/60 to-slate-900/80",
      icon: "🛎️",
    },
    {
      ...SCHOOL_PHOTOS.teacherMentoring,
      id: "gal-13",
      title: "Personalized Faculty Mentorship & Dialogue",
      category: "classrooms",
      categoryLabel: "Classrooms & Labs",
      caption:
        "Personalized mentorship and attentive academic support ensuring every child develops conceptual clarity and confidence.",
      date: "August 2026",
      accentGradient: "from-indigo-900/60 to-slate-900/80",
      icon: "👩‍🏫",
    },
  ];

  const filteredItems =
    activeCategory === "all"
      ? galleryItems
      : galleryItems.filter((item) => item.category === activeCategory);

  const handlePrevPhoto = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!selectedPhoto) return;
    const currentIndex = filteredItems.findIndex((it) => it.id === selectedPhoto.id);
    const prevIndex = (currentIndex - 1 + filteredItems.length) % filteredItems.length;
    setSelectedPhoto(filteredItems[prevIndex]);
  };

  const handleNextPhoto = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!selectedPhoto) return;
    const currentIndex = filteredItems.findIndex((it) => it.id === selectedPhoto.id);
    const nextIndex = (currentIndex + 1) % filteredItems.length;
    setSelectedPhoto(filteredItems[nextIndex]);
  };

  return (
    <div className="space-y-16 sm:space-y-20 pb-16">
      {/* 1. HERO BANNER */}
      <section className="bg-gradient-to-b from-indigo-50/80 via-ground to-white py-14 sm:py-20 border-b border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3.5 py-1 rounded-full">
            Moments & Architecture
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
            Sunrise Campus Gallery
          </h1>
          <p className="text-base sm:text-lg text-ink-soft max-w-2xl mx-auto leading-relaxed">
            A visual chronicle of our dynamic learning environments, spirited athletic triumphs, artistic creativity, and authentic campus life in Gomti Nagar, Lucknow.
          </p>
        </div>
      </section>

      {/* 2. CATEGORY FILTER & GALLERY GRID */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        {/* Category Filter Tabs */}
        <div className="flex flex-wrap items-center justify-center gap-2 border-b border-rule pb-5">
          {categories.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                activeCategory === cat.id
                  ? "bg-slate-900 text-white shadow-xs"
                  : "bg-surface text-slate-700 hover:bg-slate-100 border border-rule"
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Gallery Cards Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
          {filteredItems.map((item) => (
            <div
              key={item.id}
              onClick={() => setSelectedPhoto(item)}
              className="group cursor-pointer bg-surface rounded-2xl border border-rule overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col hover:-translate-y-1"
            >
              {/* Card Visual Hero Area with REAL PHOTOGRAPHY */}
              <div className="relative h-56 sm:h-64 overflow-hidden bg-slate-900">
                <img
                  src={item.src}
                  alt={item.alt}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-slate-950/20 to-transparent" />

                <div className="absolute top-3 left-3 right-3 flex items-center justify-between z-10">
                  <span className="text-[11px] font-semibold px-2.5 py-1 rounded-full bg-slate-900/70 text-white backdrop-blur-md border border-white/10">
                    {item.categoryLabel}
                  </span>
                  <span className="text-[11px] text-white/90 font-mono bg-slate-900/60 px-2 py-0.5 rounded backdrop-blur-md">
                    {item.date}
                  </span>
                </div>

                <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-xs text-white/90 z-10">
                  <span className="flex items-center gap-1.5 font-medium">
                    <span className="text-amber-400">📍</span> {item.location}
                  </span>
                  <span className="bg-white/20 hover:bg-white/30 backdrop-blur-md p-1.5 rounded-full text-white transition-colors">
                    🔍
                  </span>
                </div>
              </div>

              {/* Card Details */}
              <div className="p-5 space-y-2 flex-1 flex flex-col justify-between">
                <div>
                  <h3 className="font-bold text-base text-slate-900 group-hover:text-primary transition-colors leading-snug">
                    {item.title}
                  </h3>
                  <p className="text-xs text-ink-soft mt-1.5 leading-relaxed line-clamp-2">
                    {item.caption}
                  </p>
                </div>

                <div className="pt-3 border-t border-rule/80 flex items-center justify-between text-[11px] text-ink-faint">
                  <span>Sunrise School Archive</span>
                  <span className="font-semibold text-primary group-hover:underline">View Photo &rarr;</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. LIGHTBOX MODAL */}
      {selectedPhoto && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label={selectedPhoto.title}
          className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/90 backdrop-blur-md animate-fade-in"
          onClick={() => setSelectedPhoto(null)}
        >
          <div
            className="bg-surface rounded-2xl max-w-4xl w-full border border-slate-700 shadow-2xl overflow-hidden flex flex-col max-h-[92vh]"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header Bar */}
            <div className="bg-slate-900 px-4 py-3 sm:px-6 flex items-center justify-between border-b border-slate-800 text-white">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-primary/20 text-indigo-300 border border-indigo-400/30">
                  {selectedPhoto.categoryLabel}
                </span>
                <span className="text-xs text-slate-400 hidden sm:inline">
                  📍 {selectedPhoto.location}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSelectedPhoto(null)}
                className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white flex items-center justify-center text-sm font-bold transition-colors cursor-pointer"
                aria-label="Close modal"
              >
                ✕
              </button>
            </div>

            {/* Modal Image Area with Navigation Buttons */}
            <div className="relative bg-slate-950 flex items-center justify-center min-h-[300px] max-h-[58vh] overflow-hidden">
              <img
                src={selectedPhoto.src}
                alt={selectedPhoto.alt}
                className="w-full h-full object-contain max-h-[58vh]"
              />

              {/* Prev / Next controls */}
              <button
                type="button"
                onClick={handlePrevPhoto}
                className="absolute left-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-slate-900/80 hover:bg-slate-900 text-white flex items-center justify-center text-lg font-bold border border-white/20 transition-all cursor-pointer shadow-lg"
                aria-label="Previous photo"
              >
                ‹
              </button>
              <button
                type="button"
                onClick={handleNextPhoto}
                className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-slate-900/80 hover:bg-slate-900 text-white flex items-center justify-center text-lg font-bold border border-white/20 transition-all cursor-pointer shadow-lg"
                aria-label="Next photo"
              >
                ›
              </button>
            </div>

            {/* Modal Text Content & Details */}
            <div className="p-5 sm:p-7 space-y-3 bg-white overflow-y-auto">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <h3 className="text-lg sm:text-xl font-bold text-slate-900">
                  {selectedPhoto.title}
                </h3>
                <span className="text-xs font-mono text-ink-faint">
                  Archived: {selectedPhoto.date}
                </span>
              </div>

              <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">
                {selectedPhoto.caption}
              </p>

              <div className="pt-3 border-t border-rule flex flex-wrap items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-4 text-ink-soft">
                  <span>🏛️ Sunrise School, Gomti Nagar</span>
                  <span className="hidden sm:inline">•</span>
                  <span className="hidden sm:inline">CBSE Affiliation No. 2130000</span>
                </div>
                <div className="flex items-center gap-2">
                  <Link
                    to="/facilities"
                    onClick={() => setSelectedPhoto(null)}
                    className="font-semibold text-primary hover:underline"
                  >
                    Campus Facilities &rarr;
                  </Link>
                  <button
                    type="button"
                    onClick={() => setSelectedPhoto(null)}
                    className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg font-semibold transition-colors"
                  >
                    Close Preview
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 4. CAMPUS TOUR INVITATION BANNER */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-slate-900 to-indigo-950 text-white rounded-2xl p-8 sm:p-12 shadow-card flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center md:text-left max-w-xl">
            <h3 className="text-2xl font-bold tracking-tight">
              See the Campus With Your Own Eyes
            </h3>
            <p className="text-slate-300 text-xs sm:text-sm leading-relaxed">
              We warmly invite parents and prospective students to book a personalized campus tour. Walk through our smart classrooms, science labs, and athletic grounds.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/contact"
              className="bg-white hover:bg-slate-50 text-slate-900 font-bold px-6 py-3 rounded-input text-xs sm:text-sm shadow-md transition-all"
            >
              Book a Campus Visit
            </Link>
            <Link
              to="/apply"
              className="bg-amber-400 hover:bg-amber-300 text-slate-900 font-bold px-6 py-3 rounded-input text-xs sm:text-sm shadow-md transition-all"
            >
              Apply Online &rarr;
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
