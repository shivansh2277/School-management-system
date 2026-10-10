import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { useAuth } from "../../auth/AuthContext";
import { Card, Pill } from "../../components/ui";

type MessDay = {
  id?: number;
  day_of_week: string;
  breakfast: string;
  lunch: string;
  snacks: string;
  dinner: string;
  is_published: boolean;
};

const DAY_LABELS: Record<string, string> = {
  mon: "Monday",
  tue: "Tuesday",
  wed: "Wednesday",
  thu: "Thursday",
  fri: "Friday",
  sat: "Saturday",
};

const DAYS_ORDER = ["mon", "tue", "wed", "thu", "fri", "sat"];

export function HostelMessMenuPage() {
  const queryClient = useQueryClient();
  const { can } = useAuth();
  const isProvost = can("hostel.mess.manage");

  const [editingDay, setEditingDay] = useState<MessDay | null>(null);

  const { data: menuList = [], isLoading, error } = useQuery<MessDay[]>({
    queryKey: ["hostel", "mess-menu"],
    queryFn: () => api.rawGet<MessDay[]>("/admin/hostel/menu"),
  });

  const saveMutation = useMutation({
    mutationFn: async (updatedDay: MessDay) => {
      // Build full payload with updated day
      const daysMap = new Map<string, MessDay>();
      for (const d of menuList) {
        daysMap.set(d.day_of_week, d);
      }
      daysMap.set(updatedDay.day_of_week, updatedDay);

      const payload = DAYS_ORDER.map((code) => {
        const item = daysMap.get(code);
        return {
          day_of_week: code,
          breakfast: item?.breakfast || "Standard Breakfast",
          lunch: item?.lunch || "Standard Lunch",
          snacks: item?.snacks || "Evening Snacks & Tea",
          dinner: item?.dinner || "Standard Dinner",
          is_published: item?.is_published ?? true,
        };
      });

      return api.rawPut("/admin/hostel/menu", { menu: payload });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hostel", "mess-menu"] });
      setEditingDay(null);
    },
  });

  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-bold text-ink">Hostel Mess Menu</h1>
        <p className="text-ink-soft">Loading weekly dining schedule...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-bold text-ink">Hostel Mess Menu</h1>
        <div className="p-4 bg-danger/10 border border-danger/30 rounded-card text-danger">
          Failed to load mess menu. Please check your permissions or network connection.
        </div>
      </div>
    );
  }

  const menuMap = new Map<string, MessDay>();
  for (const item of menuList) {
    menuMap.set(item.day_of_week, item);
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-rule">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-ink">Weekly Mess & Dining Menu</h1>
            <Pill status="active">{isProvost ? "Chief Provost (Editor)" : "Published Menu"}</Pill>
          </div>
          <p className="text-sm text-ink-soft mt-1">
            Integrated residential dining facility. Accommodation and mess are covered under a unified fee plan.
          </p>
        </div>
      </div>

      {/* Overview Notice */}
      <Card className="p-4 bg-primary/5 border-primary/20">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-sm shrink-0">
            i
          </div>
          <div className="text-sm space-y-1">
            <p className="font-semibold text-ink">Nutritious, Balanced Residential Meals</p>
            <p className="text-ink-soft">
              Breakfast (7:30 AM – 8:30 AM), Lunch (12:30 PM – 1:45 PM), Evening Snacks (4:30 PM – 5:15 PM), and Dinner (7:30 PM – 8:45 PM).
              Evening residential attendance is recorded at 8:00 PM in the hostel.
            </p>
          </div>
        </div>
      </Card>

      {/* Weekly Menu Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {DAYS_ORDER.map((dayCode) => {
          const dayData = menuMap.get(dayCode) || {
            day_of_week: dayCode,
            breakfast: "Idli, Sambar, Chutney, Milk/Tea",
            lunch: "Dal Makhani, Rice, Roti, Seasonal Veg, Salad",
            snacks: "Biscuits / Samosa & Tea",
            dinner: "Paneer Butter Masala, Roti, Rice, Kheer",
            is_published: true,
          };

          return (
            <Card key={dayCode} className="p-5 flex flex-col justify-between hover:shadow-md transition">
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-rule pb-2">
                  <h2 className="text-lg font-bold text-ink">{DAY_LABELS[dayCode]}</h2>
                  <div className="flex items-center gap-2">
                    <Pill status={dayData.is_published ? "active" : "inactive"}>
                      {dayData.is_published ? "Published" : "Draft"}
                    </Pill>
                    {isProvost && (
                      <button
                        onClick={() => setEditingDay({ ...dayData })}
                        className="text-xs text-primary hover:underline font-medium ml-1"
                      >
                        Edit
                      </button>
                    )}
                  </div>
                </div>

                {/* Meals */}
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-xs font-bold text-amber-700 uppercase tracking-wider block">
                      Breakfast (7:30 AM)
                    </span>
                    <p className="text-ink font-medium mt-0.5">{dayData.breakfast}</p>
                  </div>

                  <div>
                    <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider block">
                      Lunch (12:30 PM)
                    </span>
                    <p className="text-ink font-medium mt-0.5">{dayData.lunch}</p>
                  </div>

                  <div>
                    <span className="text-xs font-bold text-sky-700 uppercase tracking-wider block">
                      Snacks (4:30 PM)
                    </span>
                    <p className="text-ink font-medium mt-0.5">{dayData.snacks}</p>
                  </div>

                  <div>
                    <span className="text-xs font-bold text-indigo-700 uppercase tracking-wider block">
                      Dinner (7:30 PM)
                    </span>
                    <p className="text-ink font-medium mt-0.5">{dayData.dinner}</p>
                  </div>
                </div>
              </div>

              {isProvost && (
                <div className="mt-4 pt-3 border-t border-rule text-right">
                  <button
                    onClick={() => setEditingDay({ ...dayData })}
                    className="px-3 py-1 bg-surface border border-rule hover:bg-ground rounded text-xs font-semibold text-ink"
                  >
                    Modify Day Menu
                  </button>
                </div>
              )}
            </Card>
          );
        })}
      </div>

      {/* Edit Day Modal */}
      {editingDay && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-surface border border-rule rounded-xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-rule pb-2">
              <h3 className="text-lg font-bold text-ink">
                Edit Menu — {DAY_LABELS[editingDay.day_of_week]}
              </h3>
              <button
                onClick={() => setEditingDay(null)}
                className="text-ink-soft hover:text-ink text-sm font-semibold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-sm">
              <div>
                <label className="block text-xs font-bold text-ink-soft uppercase mb-1">
                  Breakfast Items
                </label>
                <textarea
                  rows={2}
                  value={editingDay.breakfast}
                  onChange={(e) => setEditingDay({ ...editingDay, breakfast: e.target.value })}
                  className="w-full px-3 py-1.5 border border-rule rounded bg-ground text-ink text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-ink-soft uppercase mb-1">
                  Lunch Items
                </label>
                <textarea
                  rows={2}
                  value={editingDay.lunch}
                  onChange={(e) => setEditingDay({ ...editingDay, lunch: e.target.value })}
                  className="w-full px-3 py-1.5 border border-rule rounded bg-ground text-ink text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-ink-soft uppercase mb-1">
                  Evening Snacks
                </label>
                <textarea
                  rows={2}
                  value={editingDay.snacks}
                  onChange={(e) => setEditingDay({ ...editingDay, snacks: e.target.value })}
                  className="w-full px-3 py-1.5 border border-rule rounded bg-ground text-ink text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-ink-soft uppercase mb-1">
                  Dinner Items
                </label>
                <textarea
                  rows={2}
                  value={editingDay.dinner}
                  onChange={(e) => setEditingDay({ ...editingDay, dinner: e.target.value })}
                  className="w-full px-3 py-1.5 border border-rule rounded bg-ground text-ink text-sm"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="publishedCheck"
                  checked={editingDay.is_published}
                  onChange={(e) => setEditingDay({ ...editingDay, is_published: e.target.checked })}
                  className="rounded border-rule text-primary"
                />
                <label htmlFor="publishedCheck" className="text-xs text-ink font-medium">
                  Publish to Wardens, Parents, and Students
                </label>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-rule">
              <button
                type="button"
                onClick={() => setEditingDay(null)}
                className="px-4 py-2 border border-rule rounded text-xs font-semibold text-ink hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={saveMutation.isPending}
                onClick={() => saveMutation.mutate(editingDay)}
                className="px-4 py-2 bg-primary text-white rounded text-xs font-semibold hover:bg-primary-hover disabled:opacity-50"
              >
                {saveMutation.isPending ? "Saving..." : "Save & Publish Menu"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
