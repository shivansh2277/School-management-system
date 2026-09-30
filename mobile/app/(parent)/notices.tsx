import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Linking, Pressable, Text, View } from "react-native";

import { api, formatDate } from "../../src/api/client";
import { Card, Empty, Loading, Pill, Screen, s } from "../../src/components/ui";
import { useTranslation } from "../../src/i18n/I18nContext";
import { theme } from "../../src/theme";

type Notice = {
  id: number;
  title: string;
  body: string;
  category?: string | null;
  is_urgent?: boolean;
  audience: string;
  class_label: string | null;
  published_at: string;
  author_name?: string | null;
  attachment_url?: string | null;
};

export default function ParentNotices() {
  const { t } = useTranslation();
  const [selectedCategory, setSelectedCategory] = useState<string>("All");

  const categories = [
    { key: "All", label: t("notice_all") },
    { key: "Urgent", label: t("notice_urgent") },
    { key: "Academic", label: t("notice_academic") },
    { key: "Holiday", label: t("notice_holiday") },
    { key: "General", label: t("notice_general") },
  ];

  const { data, isLoading } = useQuery({
    queryKey: ["parent-notices"],
    queryFn: () => api.get<Notice[]>("/parent/notices"),
  });

  if (isLoading) return <Loading />;

  const notices = data ?? [];
  const urgentNotices = notices.filter(
    (n) => n.is_urgent || n.category?.toLowerCase() === "urgent" || n.title.toLowerCase().includes("urgent"),
  );

  const filtered = notices.filter((n) => {
    if (selectedCategory === "All") return true;
    if (selectedCategory === "Urgent") {
      return n.is_urgent || n.category?.toLowerCase() === "urgent" || n.title.toLowerCase().includes("urgent");
    }
    return n.category?.toLowerCase() === selectedCategory.toLowerCase();
  });

  return (
    <Screen>
      {/* Category Tabs */}
      <View style={{ flexDirection: "row", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
        {categories.map((cat) => {
          const on = selectedCategory === cat.key;
          return (
            <Pressable
              key={cat.key}
              onPress={() => setSelectedCategory(cat.key)}
              style={{
                paddingHorizontal: 12,
                paddingVertical: 6,
                borderRadius: theme.radius.pill,
                backgroundColor: on ? theme.primary : theme.surface,
                borderWidth: 1,
                borderColor: on ? theme.primary : theme.rule,
              }}
            >
              <Text
                style={{
                  fontSize: 12,
                  fontWeight: on ? "600" : "400",
                  color: on ? "#fff" : theme.inkSoft,
                }}
              >
                {cat.label}
              </Text>
            </Pressable>
          );
        })}
      </View>

      {/* Urgent Notice Banner */}
      {urgentNotices.length > 0 && selectedCategory === "All" && (
        <View
          style={{
            backgroundColor: "#FEF2F2",
            borderLeftWidth: 4,
            borderLeftColor: theme.danger,
            padding: 12,
            borderRadius: theme.radius.input,
            marginBottom: 12,
          }}
        >
          <Text style={{ fontSize: 13, fontWeight: "700", color: theme.danger }}>
            {t("notice_urgent_banner")} {urgentNotices[0].title}
          </Text>
          <Text style={{ fontSize: 12, color: theme.ink, marginTop: 3 }}>
            {urgentNotices[0].body}
          </Text>
        </View>
      )}

      {/* Notices Feed */}
      {filtered.length === 0 ? (
        <Card>
          <Empty text={t("notice_no_items")} />
        </Card>
      ) : (
        filtered.map((n) => {
          const isUrgent =
            n.is_urgent || n.category?.toLowerCase() === "urgent" || n.title.toLowerCase().includes("urgent");
          return (
            <Card key={n.id}>
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
                <Text style={{ fontWeight: "700", fontSize: 15, color: theme.ink, flex: 1 }}>
                  {n.title}
                </Text>
                {isUrgent && <Pill status="overdue" label={t("notice_urgent")} />}
                {n.category && !isUrgent && <Pill label={n.category} />}
              </View>

              <Text style={{ color: theme.inkSoft, fontSize: 13, marginVertical: 6, lineHeight: 18 }}>
                {n.body}
              </Text>

              {n.attachment_url && (
                <Pressable
                  onPress={() => n.attachment_url && Linking.openURL(n.attachment_url)}
                  style={{
                    flexDirection: "row",
                    alignItems: "center",
                    gap: 6,
                    paddingVertical: 6,
                    paddingHorizontal: 8,
                    borderRadius: 6,
                    backgroundColor: theme.ground,
                    alignSelf: "flex-start",
                    marginBottom: 6,
                  }}
                >
                  <Text style={{ fontSize: 12, color: theme.primary, fontWeight: "600" }}>
                    {t("notice_view_pdf")}
                  </Text>
                </Pressable>
              )}

              <View style={{ flexDirection: "row", justifyContent: "space-between", marginTop: 4 }}>
                <Text style={s.meta}>
                  {t("notice_audience")}: {n.audience} {n.class_label ? `(${n.class_label})` : ""}
                </Text>
                <Text style={s.meta}>{formatDate(n.published_at)}</Text>
              </View>
            </Card>
          );
        })
      )}
    </Screen>
  );
}
