/** Views shared by more than one role, so the student and parent tab sets stay in step. */
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Pressable, Text, View } from "react-native";

import { api } from "../api/client";
import { statusColor, theme } from "../theme";
import { Card, Empty, Loading, Pill, Row, Screen, s } from "./ui";

type AttendanceMonth = {
  days: { date: string; status: string }[];
  summary: { present: number; absent: number; leave: number; percent: number | null };
};

export function AttendanceView({ path }: { path: string }) {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const year = now.getFullYear();

  const { data, isLoading } = useQuery({
    queryKey: ["attendance", path, month, year],
    queryFn: () => api.get<AttendanceMonth>(`${path}?month=${month}&year=${year}`),
  });

  if (isLoading) return <Loading />;

  const byDay = new Map((data?.days ?? []).map((d) => [Number(d.date.slice(8, 10)), d.status]));
  const daysInMonth = new Date(year, month, 0).getDate();

  return (
    <Screen>
      <Card>
        <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
          <Pressable onPress={() => setMonth((m) => (m === 1 ? 12 : m - 1))}>
            <Text style={{ color: theme.primary, fontWeight: "600" }}>Previous</Text>
          </Pressable>
          <Text style={{ fontWeight: "600" }}>
            {new Date(year, month - 1).toLocaleString("en", { month: "long" })} {year}
          </Text>
          <Pressable onPress={() => setMonth((m) => (m === 12 ? 1 : m + 1))}>
            <Text style={{ color: theme.primary, fontWeight: "600" }}>Next</Text>
          </Pressable>
        </View>

        {byDay.size === 0 ? (
          <Empty text="No attendance recorded for this month." />
        ) : (
          <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6 }}>
            {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((d) => {
              const status = byDay.get(d);
              return (
                <View
                  key={d}
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: 8,
                    alignItems: "center",
                    justifyContent: "center",
                    backgroundColor: status ? `${statusColor[status]}22` : theme.ground,
                  }}
                >
                  <Text
                    style={{
                      fontSize: 12,
                      color: status ? statusColor[status] : theme.inkFaint,
                      fontWeight: status ? "600" : "400",
                    }}
                  >
                    {d}
                  </Text>
                </View>
              );
            })}
          </View>
        )}
      </Card>

      {data && (
        <Card title="Summary">
          <View style={{ flexDirection: "row" }}>
            <Stat label="Present" value={data.summary.present} />
            <Stat label="Absent" value={data.summary.absent} />
            <Stat label="Leave" value={data.summary.leave} />
            <Stat
              label="Attendance"
              value={data.summary.percent === null ? "-" : `${data.summary.percent}%`}
            />
          </View>
          <Text style={s.meta}>Leave counts against presence.</Text>
        </Card>
      )}
    </Screen>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <View style={{ flex: 1 }}>
      <Text style={s.meta}>{label}</Text>
      <Text style={{ fontSize: 18, fontWeight: "600", color: theme.ink }}>{value}</Text>
    </View>
  );
}

type ExamRow = { exam_id: number; name: string; term: string; overall_percent: number | null };
type ReportCard = {
  exam_name: string;
  rows: {
    subject: string;
    marks_obtained: string | null;
    max_marks: string;
    percent: number | null;
    grade: string | null;
  }[];
  total_obtained: string;
  total_max: string;
  overall_percent: number | null;
  overall_grade: string | null;
};

export function ResultsView({ listPath, cardPath }: { listPath: string; cardPath: string }) {
  const [openExam, setOpenExam] = useState<number | null>(null);
  const exams = useQuery({
    queryKey: ["results", listPath],
    queryFn: () => api.get<ExamRow[]>(listPath),
  });
  const card = useQuery({
    queryKey: ["report-card", cardPath, openExam],
    queryFn: () => api.get<ReportCard>(`${cardPath}/${openExam}`),
    enabled: openExam !== null,
  });

  if (exams.isLoading) return <Loading />;

  return (
    <Screen>
      <Card title="Exams">
        {(exams.data ?? []).length === 0 ? (
          <Empty text="No results published yet." />
        ) : (
          exams.data!.map((e) => (
            <Pressable key={e.exam_id} onPress={() => setOpenExam(e.exam_id)}>
              <Row
                left={
                  <>
                    <Text style={s.title}>{e.name}</Text>
                    <Text style={s.meta}>{e.term}</Text>
                  </>
                }
                right={
                  <Text style={{ fontWeight: "600", color: theme.ink }}>
                    {e.overall_percent === null ? "-" : `${e.overall_percent}%`}
                  </Text>
                }
              />
            </Pressable>
          ))
        )}
      </Card>

      {openExam !== null && card.data && (
        <Card title={card.data.exam_name}>
          {card.data.rows.map((r) => (
            <Row
              key={r.subject}
              left={
                <>
                  <Text style={s.title}>{r.subject}</Text>
                  <Text style={s.meta}>
                    {r.marks_obtained === null
                      ? "Absent - excluded from the total"
                      : `${Number(r.marks_obtained)} / ${Number(r.max_marks)}`}
                  </Text>
                </>
              }
              right={
                r.grade ? (
                  <Pill label={`${r.grade} - ${r.percent}%`} />
                ) : (
                  <Text style={s.meta}>-</Text>
                )
              }
            />
          ))}
          <Row
            left={<Text style={{ fontWeight: "700" }}>Total</Text>}
            right={
              <Text style={{ fontWeight: "700" }}>
                {Number(card.data.total_obtained)} / {Number(card.data.total_max)}
                {card.data.overall_percent !== null
                  ? `  ${card.data.overall_percent}% ${card.data.overall_grade}`
                  : ""}
              </Text>
            }
          />
        </Card>
      )}
    </Screen>
  );
}

type Notice = {
  id: number;
  title: string;
  body: string;
  audience: string;
  class_label: string | null;
  published_at: string;
};

export function NoticesView({ path }: { path: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["notices", path],
    queryFn: () => api.get<Notice[]>(path),
  });
  if (isLoading) return <Loading />;

  return (
    <Screen>
      {(data ?? []).length === 0 ? (
        <Card>
          <Empty text="No notices for you yet." />
        </Card>
      ) : (
        data!.map((n) => (
          <Card key={n.id}>
            <Text style={{ fontWeight: "600", color: theme.ink }}>{n.title}</Text>
            <Text style={{ color: theme.inkSoft, fontSize: 13 }}>{n.body}</Text>
            <Text style={s.meta}>
              {n.audience}
              {n.class_label ? ` - ${n.class_label}` : ""} -{" "}
              {new Date(n.published_at).toLocaleDateString()}
            </Text>
          </Card>
        ))
      )}
    </Screen>
  );
}

type Slot = {
  period: number;
  day_of_week: string;
  start_time: string;
  end_time: string;
  subject: string;
  teacher: string;
  room: string | null;
  class_label: string;
};

const DAYS = ["mon", "tue", "wed", "thu", "fri", "sat"];

export function TimetableView({ path, showClass = false }: { path: string; showClass?: boolean }) {
  const [day, setDay] = useState(DAYS[Math.min(new Date().getDay() - 1, 5)] ?? "mon");
  const { data, isLoading } = useQuery({
    queryKey: ["timetable", path],
    queryFn: () => api.get<Slot[]>(path),
  });
  if (isLoading) return <Loading />;

  const slots = (data ?? []).filter((s) => s.day_of_week === day);

  return (
    <Screen>
      <View style={{ flexDirection: "row", gap: 6 }}>
        {DAYS.map((d) => (
          <Pressable
            key={d}
            onPress={() => setDay(d)}
            style={{
              flex: 1,
              paddingVertical: 8,
              borderRadius: theme.radius.input,
              alignItems: "center",
              backgroundColor: day === d ? theme.primary : theme.surface,
            }}
          >
            <Text style={{ color: day === d ? "#fff" : theme.inkSoft, fontSize: 12 }}>
              {d.toUpperCase()}
            </Text>
          </Pressable>
        ))}
      </View>

      <Card>
        {slots.length === 0 ? (
          <Empty text="No periods scheduled for this day." />
        ) : (
          slots.map((slot) => (
            <Row
              key={`${slot.day_of_week}-${slot.period}-${slot.class_label}`}
              left={
                <>
                  <Text style={s.title}>
                    {slot.subject}
                    {showClass ? ` - ${slot.class_label}` : ""}
                  </Text>
                  <Text style={s.meta}>
                    {slot.teacher}
                    {slot.room ? ` - ${slot.room}` : ""}
                  </Text>
                </>
              }
              right={
                <Text style={s.meta}>
                  {slot.start_time.slice(0, 5)}-{slot.end_time.slice(0, 5)}
                </Text>
              }
            />
          ))
        )}
      </Card>
    </Screen>
  );
}
