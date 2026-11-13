from pathlib import Path

path = Path("web/src/pages/Timetable.tsx")
content = path.read_text(encoding="utf-8")

# 1. Update PeriodsTab
old_periods_tab = """function PeriodsTab() {
  const qc = useQueryClient();
  const [addingPeriod, setAddingPeriod] = useState(false);

  const periods = useQuery<PeriodItem[]>({
    queryKey: ["timetable-periods"],
    queryFn: () => api.rawGet<PeriodItem[]>("/admin/timetable/periods"),
  });

  const rows = [...(periods.data ?? [])].sort((a, b) => a.period_no - b.period_no);

  return (
    <div className="space-y-5">
      <div className="bg-surface rounded-card shadow-card p-5 border border-rule/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-ink">School Bell Timings & Period Slots</h2>
          <p className="text-xs text-ink-faint mt-0.5">
            Configure instructional lesson periods, recess, lunch breaks and assembly timings.
          </p>
        </div>
        <ActionButton
          permission="timetable.slot.write"
          onClick={() => setAddingPeriod(true)}
          className="rounded-input bg-primary hover:bg-primary/90 text-white text-xs font-semibold px-3.5 py-1.5"
        >
          + Add School Period
        </ActionButton>
      </div>

      <Card>
        <DataTable
          rows={rows}
          loading={periods.isLoading}
          error={periods.error}
          empty="No school periods configured."
          columns={[
            {
              key: "no",
              header: "Period No.",
              render: (p) => (
                <span className="font-extrabold text-xs text-ink">
                  Period {p.period_no}
                </span>
              ),
            },
            {
              key: "name",
              header: "Label / Name",
              render: (p) => (
                <span className="font-semibold text-xs text-slate-800">
                  {p.name || `Period ${p.period_no}`}
                </span>
              ),
            },
            {
              key: "start",
              header: "Start Time",
              render: (p) => <span className="font-mono text-xs tabular">{p.start_time?.slice(0, 5)}</span>,
            },
            {
              key: "end",
              header: "End Time",
              render: (p) => <span className="font-mono text-xs tabular">{p.end_time?.slice(0, 5)}</span>,
            },
            {
              key: "type",
              header: "Period Type",
              render: (p) => (
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded ${
                    p.is_break
                      ? "bg-amber-100 text-amber-800 border border-amber-200"
                      : "bg-blue-100 text-blue-800 border border-blue-200"
                  }`}
                >
                  {p.is_break ? "Break / Recess" : "Instructional Lesson"}
                </span>
              ),
            },
          ]}
        />
      </Card>

      {addingPeriod && (
        <PeriodModal
          onClose={() => setAddingPeriod(false)}
          onSaved={() => {
            setAddingPeriod(false);
            qc.invalidateQueries({ queryKey: ["timetable-periods"] });
          }}
        />
      )}
    </div>
  );
}"""

new_periods_tab = """function PeriodsTab() {
  const qc = useQueryClient();
  const [addingPeriod, setAddingPeriod] = useState(false);
  const [editingPeriod, setEditingPeriod] = useState<PeriodItem | null>(null);

  const periods = useQuery<PeriodItem[]>({
    queryKey: ["timetable-periods"],
    queryFn: () => api.rawGet<PeriodItem[]>("/admin/timetable/periods"),
  });

  const toggleBreak = useMutation({
    mutationFn: (p: PeriodItem) =>
      api.rawPut(`/admin/timetable/periods/${p.id}`, {
        is_break: !p.is_break,
        name: !p.is_break ? (p.name || "Break") : null,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["timetable-periods"] });
      qc.invalidateQueries({ queryKey: ["class-timetable"] });
      qc.invalidateQueries({ queryKey: ["timetable-completeness"] });
      qc.invalidateQueries({ queryKey: ["timetable-workload"] });
    },
  });

  const rows = [...(periods.data ?? [])].sort((a, b) => a.period_no - b.period_no);

  return (
    <div className="space-y-5">
      <div className="bg-surface rounded-card shadow-card p-5 border border-rule/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-ink">School Bell Timings & Period Slots</h2>
          <p className="text-xs text-ink-faint mt-0.5">
            Configure school periods, recess/break timings, and instructional lessons. Break periods are dynamically configurable at any time.
          </p>
        </div>
        <ActionButton
          permission="timetable.slot.write"
          onClick={() => setAddingPeriod(true)}
          className="rounded-input bg-primary hover:bg-primary/90 text-white text-xs font-semibold px-3.5 py-1.5"
        >
          + Add School Period
        </ActionButton>
      </div>

      <Card>
        <DataTable
          rows={rows}
          loading={periods.isLoading}
          error={periods.error}
          empty="No school periods configured."
          columns={[
            {
              key: "no",
              header: "Period No.",
              render: (p) => (
                <span className="font-extrabold text-xs text-ink">
                  Period {p.period_no}
                </span>
              ),
            },
            {
              key: "name",
              header: "Label / Name",
              render: (p) => (
                <span className="font-semibold text-xs text-slate-800">
                  {p.name || `Period ${p.period_no}`}
                </span>
              ),
            },
            {
              key: "start",
              header: "Start Time",
              render: (p) => <span className="font-mono text-xs tabular">{p.start_time?.slice(0, 5)}</span>,
            },
            {
              key: "end",
              header: "End Time",
              render: (p) => <span className="font-mono text-xs tabular">{p.end_time?.slice(0, 5)}</span>,
            },
            {
              key: "type",
              header: "Period Type",
              render: (p) => (
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded ${
                    p.is_break
                      ? "bg-amber-100 text-amber-900 border border-amber-300 font-bold"
                      : "bg-blue-100 text-blue-800 border border-blue-200"
                  }`}
                >
                  {p.is_break ? "Break / Recess" : "Instructional Lesson"}
                </span>
              ),
            },
            {
              key: "actions",
              header: "Configure Period",
              render: (p) => (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setEditingPeriod(p)}
                    className="px-2.5 py-1 text-xs font-semibold rounded border border-rule hover:bg-slate-100 text-ink cursor-pointer"
                  >
                    Edit / Configure
                  </button>
                  <button
                    type="button"
                    onClick={() => toggleBreak.mutate(p)}
                    disabled={toggleBreak.isPending}
                    className={`px-2.5 py-1 text-xs font-bold rounded cursor-pointer transition-all ${
                      p.is_break
                        ? "bg-blue-50 text-blue-800 hover:bg-blue-100 border border-blue-200"
                        : "bg-amber-50 text-amber-800 hover:bg-amber-100 border border-amber-200"
                    }`}
                    title={
                      p.is_break
                        ? "Convert this break period back to an instructional lesson period"
                        : "Configure this period as a school break/recess"
                    }
                  >
                    {p.is_break ? "Set as Lesson" : "Set as Break"}
                  </button>
                </div>
              ),
            },
          ]}
        />
      </Card>

      {addingPeriod && (
        <PeriodModal
          onClose={() => setAddingPeriod(false)}
          onSaved={() => {
            setAddingPeriod(false);
            qc.invalidateQueries({ queryKey: ["timetable-periods"] });
            qc.invalidateQueries({ queryKey: ["class-timetable"] });
            qc.invalidateQueries({ queryKey: ["timetable-completeness"] });
            qc.invalidateQueries({ queryKey: ["timetable-workload"] });
          }}
        />
      )}

      {editingPeriod && (
        <PeriodModal
          period={editingPeriod}
          onClose={() => setEditingPeriod(null)}
          onSaved={() => {
            setEditingPeriod(null);
            qc.invalidateQueries({ queryKey: ["timetable-periods"] });
            qc.invalidateQueries({ queryKey: ["class-timetable"] });
            qc.invalidateQueries({ queryKey: ["timetable-completeness"] });
            qc.invalidateQueries({ queryKey: ["timetable-workload"] });
          }}
        />
      )}
    </div>
  );
}"""

if old_periods_tab in content:
    content = content.replace(old_periods_tab, new_periods_tab, 1)

# 2. Update PeriodModal to support editing
old_period_modal = """function PeriodModal({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [periodNo, setPeriodNo] = useState("1");
  const [name, setName] = useState("");
  const [startTime, setStartTime] = useState("08:00");
  const [endTime, setEndTime] = useState("08:45");
  const [isBreak, setIsBreak] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.rawPost("/admin/timetable/periods", {
        period_no: Number(periodNo),
        name: name.trim() || undefined,
        start_time: startTime.length === 5 ? `${startTime}:00` : startTime,
        end_time: endTime.length === 5 ? `${endTime}:00` : endTime,
        is_break: isBreak,
      });
      onSaved();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to add period");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title="Add School Period / Bell Timing" onClose={onClose}>"""

new_period_modal = """function PeriodModal({
  period,
  onClose,
  onSaved,
}: {
  period?: PeriodItem | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [periodNo, setPeriodNo] = useState(period ? String(period.period_no) : "1");
  const [name, setName] = useState(period?.name || "");
  const [startTime, setStartTime] = useState(period?.start_time ? period.start_time.slice(0, 5) : "08:00");
  const [endTime, setEndTime] = useState(period?.end_time ? period.end_time.slice(0, 5) : "08:45");
  const [isBreak, setIsBreak] = useState(period?.is_break ?? false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const payload = {
        period_no: Number(periodNo),
        name: name.trim() || (isBreak ? "Break" : undefined),
        start_time: startTime.length === 5 ? `${startTime}:00` : startTime,
        end_time: endTime.length === 5 ? `${endTime}:00` : endTime,
        is_break: isBreak,
      };

      if (period?.id) {
        await api.rawPut(`/admin/timetable/periods/${period.id}`, payload);
      } else {
        await api.rawPost("/admin/timetable/periods", payload);
      }
      onSaved();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save period");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      title={period ? `Configure Period ${period.period_no}` : "Add School Period / Bell Timing"}
      onClose={onClose}
    >"""

if old_period_modal in content:
    content = content.replace(old_period_modal, new_period_modal, 1)

# Also update the submit button text in PeriodModal
old_btn = '{saving ? "Saving…" : "Add Period"}'
new_btn = '{saving ? "Saving…" : period ? "Update Period Configuration" : "Add Period"}'
if old_btn in content:
    content = content.replace(old_btn, new_btn, 1)

path.write_text(content, encoding="utf-8")
print("Updated Timetable.tsx with configurable periods UI.")
