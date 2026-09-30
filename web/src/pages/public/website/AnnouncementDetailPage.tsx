import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../../api/client";
import { PublicAnnouncement, DEFAULT_ANNOUNCEMENTS } from "./AnnouncementsPage";

export function AnnouncementDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: item, isLoading } = useQuery<PublicAnnouncement | null>({
    queryKey: ["public-announcement-detail", id],
    queryFn: async () => {
      try {
        const res = await api.rawGet<PublicAnnouncement>(`/public/SPS/announcements/${id}`);
        if (res && res.title) return res;
      } catch {
        // Fall back to default announcements
      }
      const numId = Number(id);
      const found = DEFAULT_ANNOUNCEMENTS.find((a) => a.id === numId);
      return found || null;
    },
    initialData: () => {
      const numId = Number(id);
      return DEFAULT_ANNOUNCEMENTS.find((a) => a.id === numId) || null;
    },
    enabled: !!id,
  });

  return (
    <div className="bg-slate-50 min-h-screen py-10 lg:py-14">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Navigation & Back Link */}
        <div>
          <Link
            to="/announcements"
            className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-slate-600 hover:text-primary transition-colors"
          >
            <span>&larr;</span>
            <span>Back to All Announcements</span>
          </Link>
        </div>

        {/* Content Box */}
        {isLoading ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-500 text-sm shadow-xs">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-3"></div>
            <p>Loading circular details...</p>
          </div>
        ) : !item ? (
          <div className="bg-white rounded-2xl border border-rose-200 p-8 text-center text-rose-700 text-sm shadow-xs">
            <p className="font-semibold text-base">Announcement Not Found</p>
            <p className="text-xs text-rose-500 mt-1">This circular may have expired or been removed from the public notice board.</p>
            <div className="mt-4">
              <Link
                to="/announcements"
                className="inline-block bg-slate-900 text-white text-xs font-semibold px-4 py-2 rounded-lg"
              >
                Return to Circulars
              </Link>
            </div>
          </div>
        ) : (
          <article className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-10 shadow-xs space-y-6">
            {/* Header Metadata */}
            <div className="space-y-3 pb-6 border-b border-slate-100">
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <div className="flex items-center gap-2">
                  <span className="inline-block text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-700">
                    {item.category || "Notice"}
                  </span>
                  {item.is_pinned && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold uppercase px-2 py-0.5 rounded-md bg-amber-100 text-amber-900 border border-amber-300">
                      <span>★</span>
                      <span>Featured Circular</span>
                    </span>
                  )}
                </div>

                <time className="text-xs text-slate-500">
                  Published:{" "}
                  {new Date(item.published_at).toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  })}
                </time>
              </div>

              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-slate-900 font-serif leading-tight">
                {item.title}
              </h1>

              <div className="text-xs text-slate-400 flex items-center gap-2">
                <span>Issued by: <strong className="text-slate-600">{item.published_by || "Office Administration"}</strong></span>
                <span>•</span>
                <span>Sunrise School, Gomti Nagar</span>
              </div>
            </div>

            {/* Summary Highlight (if present) */}
            {item.summary && (
              <div className="p-4 rounded-xl bg-slate-50 border-l-4 border-amber-400 text-slate-700 text-sm sm:text-base font-medium leading-relaxed">
                {item.summary}
              </div>
            )}

            {/* Body Content */}
            <div className="prose prose-slate max-w-none text-slate-800 text-sm sm:text-base leading-relaxed whitespace-pre-line">
              {item.body}
            </div>

            {/* Action Card / Footer */}
            <div className="pt-6 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-xs text-slate-500">
                Official institutional communication from the Administrative Office.
              </div>

              <div className="flex items-center gap-3">
                {item.category?.toLowerCase() === "admission" && (
                  <Link
                    to="/apply"
                    className="inline-flex items-center gap-1.5 bg-amber-400 hover:bg-amber-300 text-slate-900 font-bold px-4 py-2 rounded-lg text-xs shadow-xs transition-colors"
                  >
                    <span>Apply Online</span>
                    <span>&rarr;</span>
                  </Link>
                )}
                <Link
                  to="/contact"
                  className="bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold px-4 py-2 rounded-lg text-xs transition-colors"
                >
                  Contact Desk
                </Link>
              </div>
            </div>
          </article>
        )}
      </div>
    </div>
  );
}
