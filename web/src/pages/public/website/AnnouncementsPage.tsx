import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../api/client";

export interface PublicAnnouncement {
  id: number;
  title: string;
  body: string;
  audience?: string;
  published_by: string;
  published_at: string;
  category?: string;
  is_public?: boolean;
  is_pinned?: boolean;
  summary?: string | null;
  expiry_date?: string | null;
  attachment_url?: string | null;
}

const CATEGORIES = [
  "All",
  "Admission",
  "Academic",
  "Achievement",
  "Event",
  "Holiday",
  "Notice",
  "General",
] as const;

export const DEFAULT_ANNOUNCEMENTS: PublicAnnouncement[] = [
  {
    id: 101,
    title: "Admissions Open for Academic Session 2026–27 (Pre-Primary to Grade XI)",
    summary: "Online registration is now open for prospective students for the upcoming academic session. Early applications are strongly encouraged.",
    body: "Sunrise School announces admissions open for Nursery through Grade 9 and Grade 11 (Science, Commerce, Humanities). Parents may submit the online enquiry or application form on our website.",
    category: "Admission",
    is_public: true,
    is_pinned: true,
    published_by: "Admissions Office",
    published_at: "2026-09-15T09:00:00Z",
  },
  {
    id: 102,
    title: "CBSE Class X & XII Board Results 2025–26: 100% Pass Rate with Top Honors",
    summary: "Sunrise School celebrates outstanding CBSE board results with over 30% of candidates scoring 90% and above aggregate.",
    body: "Sunrise School, Gomti Nagar, Lucknow is proud to announce another year of stellar academic excellence in the CBSE Class X and XII Board Examinations with a 100% pass record.",
    category: "Achievement",
    is_public: true,
    is_pinned: true,
    published_by: "Principal's Office",
    published_at: "2026-09-10T10:00:00Z",
  },
  {
    id: 103,
    title: "Annual Sports Meet & Athletic Championship Registration Open",
    summary: "Inter-house athletic trials commence next Monday for track events, football, and badminton.",
    body: "All students are encouraged to register with their respective House Masters for the annual sports championship across track, turf football, and indoor sports.",
    category: "Event",
    is_public: true,
    is_pinned: false,
    published_by: "Physical Education Dept",
    published_at: "2026-09-20T11:00:00Z",
  },
  {
    id: 104,
    title: "Annual Science Exhibition & Student STEM Innovation Showcase",
    summary: "Experience hands-on student robotics, AI prototypes, and composite science projects at the Central Campus.",
    body: "The Science and Robotics Club will host the annual showcase featuring working models, Arduino projects, and sustainability solutions on 15 November 2025.",
    category: "Academic",
    is_public: true,
    is_pinned: false,
    published_by: "STEM Faculty",
    published_at: "2026-09-22T08:30:00Z",
  },
  {
    id: 105,
    title: "Parent–Teacher Interaction Day & Term 1 Performance Dossier",
    summary: "One-on-one parent-educator interactions scheduled for next Saturday from 8:30 AM to 1:00 PM.",
    body: "Detailed performance reports and holistic progress cards will be discussed with parents during individual meeting slots.",
    category: "Notice",
    is_public: true,
    is_pinned: false,
    published_by: "Dean of Academics",
    published_at: "2026-09-25T12:00:00Z",
  },
  {
    id: 106,
    title: "Autumn Break & Dussehra Campus Holiday Schedule",
    summary: "School remains closed from 10th to 16th October. Administrative office open for admission enquiries.",
    body: "Classes will resume on normal schedule on Monday, 17th October. The admissions front desk remains operational for visitor enquiries.",
    category: "Holiday",
    is_public: true,
    is_pinned: false,
    published_by: "Administrative Office",
    published_at: "2026-09-28T14:00:00Z",
  },
  {
    id: 107,
    title: "Inter-House Cultural Festival & Arts Gala 2026",
    summary: "Annual celebrations featuring classical music, drama, folk dance, and debate competitions.",
    body: "Agni, Prithvi, Vayu, and Jal houses will compete in performing arts, street plays, and art exhibitions in the school auditorium.",
    category: "Event",
    is_public: true,
    is_pinned: false,
    published_by: "Cultural Committee",
    published_at: "2026-09-29T10:00:00Z",
  },
  {
    id: 108,
    title: "Robotics & AI Innovation Workshop for Classes VI to XII",
    summary: "Hands-on weekend bootcamp on microcontrollers, Python programming, and sensor integration.",
    body: "Conducted in collaboration with Atal Tinkering Lab mentors. Limited seats available per cohort.",
    category: "Academic",
    is_public: true,
    is_pinned: false,
    published_by: "Innovation Hub",
    published_at: "2026-09-29T15:00:00Z",
  },
];

export function AnnouncementsPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [searchQuery, setSearchQuery] = useState("");

  const { data: rawAnnouncements, isLoading } = useQuery<PublicAnnouncement[]>({
    queryKey: ["public-announcements", selectedCategory],
    queryFn: async () => {
      try {
        const url =
          selectedCategory === "All"
            ? "/public/SPS/announcements"
            : `/public/SPS/announcements?category=${encodeURIComponent(selectedCategory)}`;
        const res = await api.rawGet<PublicAnnouncement[]>(url);
        return Array.isArray(res) && res.length > 0 ? res : DEFAULT_ANNOUNCEMENTS;
      } catch {
        return DEFAULT_ANNOUNCEMENTS;
      }
    },
    initialData: DEFAULT_ANNOUNCEMENTS,
  });

  const effectiveAnnouncements =
    rawAnnouncements && rawAnnouncements.length > 0
      ? rawAnnouncements
      : DEFAULT_ANNOUNCEMENTS;

  const categoryFiltered =
    selectedCategory === "All"
      ? effectiveAnnouncements
      : effectiveAnnouncements.filter(
          (item) => item.category?.toLowerCase() === selectedCategory.toLowerCase()
        );

  const filtered = categoryFiltered.filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.title.toLowerCase().includes(q) ||
      (item.summary && item.summary.toLowerCase().includes(q)) ||
      item.body.toLowerCase().includes(q)
    );
  });

  return (
    <div className="bg-slate-50 min-h-screen py-10 lg:py-14">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Breadcrumb & Section Eyebrow */}
        <div className="space-y-2">
          <nav className="flex items-center text-xs text-slate-500 gap-2">
            <Link to="/" className="hover:text-primary transition-colors">Home</Link>
            <span>&rsaquo;</span>
            <span className="text-slate-900 font-semibold">News & Announcements</span>
          </nav>
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 font-serif tracking-tight">
                News & Official Circulars
              </h1>
              <p className="text-slate-600 text-sm sm:text-base mt-1 max-w-2xl">
                Stay informed with the latest institutional notices, admissions alerts, examination circulars, and campus events.
              </p>
            </div>
            <Link
              to="/apply"
              className="inline-flex items-center gap-1.5 bg-amber-400 hover:bg-amber-300 text-slate-900 text-xs sm:text-sm font-bold px-4 py-2.5 rounded-lg shadow-sm transition-all shrink-0 self-start md:self-auto"
            >
              <span>Apply for Admissions</span>
              <span>&rarr;</span>
            </Link>
          </div>
        </div>

        {/* Filters & Search Toolbar */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 shadow-xs flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Category Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto pb-1 md:pb-0 scrollbar-none">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors cursor-pointer ${
                  selectedCategory === cat
                    ? "bg-slate-900 text-white shadow-xs"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="w-full md:w-72 shrink-0">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search circulars..."
                className="w-full pl-9 pr-3.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:bg-white transition-all"
              />
              <svg
                className="w-4 h-4 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Content Area */}
        {isLoading ? (
          <div className="p-12 text-center text-slate-500 text-sm">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-3"></div>
            <p>Loading latest school announcements...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 text-slate-500 text-sm">
            <p className="font-medium text-slate-700">No announcements found matching your criteria.</p>
            <p className="text-xs text-slate-400 mt-1">Try switching categories or clearing your search query.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filtered.map((item) => (
              <div
                key={item.id}
                className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col justify-between shadow-xs hover:shadow-md hover:border-slate-300 transition-all duration-200 group"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <div className="flex items-center gap-1.5">
                      <span className="inline-block text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-700">
                        {item.category || "Notice"}
                      </span>
                      {item.is_pinned && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase px-2 py-0.5 rounded-md bg-amber-100 text-amber-900 border border-amber-300">
                          <span>★</span>
                          <span>Pinned</span>
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-slate-400">
                      {new Date(item.published_at).toLocaleDateString("en-IN", {
                        day: "numeric",
                        month: "short",
                        year: "numeric",
                      })}
                    </span>
                  </div>

                  <div>
                    <h2 className="text-lg font-bold text-slate-900 font-serif group-hover:text-primary transition-colors leading-snug">
                      <Link to={`/announcements/${item.id}`} className="hover:underline">
                        {item.title}
                      </Link>
                    </h2>
                    <p className="text-xs text-slate-600 mt-2 leading-relaxed line-clamp-3">
                      {item.summary || item.body}
                    </p>
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-400 text-[11px]">
                    By {item.published_by || "School Administration"}
                  </span>
                  <Link
                    to={`/announcements/${item.id}`}
                    className="inline-flex items-center gap-1 text-slate-900 hover:text-amber-600 font-bold transition-colors"
                  >
                    <span>Read Details</span>
                    <span className="text-[11px]">&rarr;</span>
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
