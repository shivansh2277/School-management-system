import { useQuery } from "@tanstack/react-query";
import { Text, View } from "react-native";

import { api } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Card, Empty, Loading, Pill, Row, Screen, Stat, s } from "../../src/components/ui";
import { useTranslation } from "../../src/i18n/I18nContext";

type Item = {
  id: number;
  title: string;
  subject: string;
  due_date: string;
  submitted: boolean;
  late: boolean;
};

export default function ParentHomework() {
  const { t } = useTranslation();
  const { selectedChildId } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["parent-homework", selectedChildId],
    queryFn: () => api.get<Item[]>(`/parent/children/${selectedChildId}/homework`),
    enabled: selectedChildId !== null,
  });

  if (isLoading || !data) return <Loading />;

  const submitted = data.filter((h) => h.submitted).length;

  return (
    <Screen>
      <Card>
        <View style={{ flexDirection: "row" }}>
          <Stat label={t("hw_submitted")} value={submitted} />
          <Stat label={t("hw_pending")} value={data.length - submitted} />
        </View>
        <Text style={s.meta}>{t("hw_readonly_note")}</Text>
      </Card>

      <Card title={t("hw_assignments")}>
        {data.length === 0 ? (
          <Empty text={t("hw_no_homework")} />
        ) : (
          data.map((item) => (
            <Row
              key={item.id}
              left={
                <>
                  <Text style={s.title}>{item.title}</Text>
                  <Text style={s.meta}>
                    {item.subject} - {t("hw_due")} {item.due_date}
                  </Text>
                </>
              }
              right={
                item.submitted ? (
                  <Pill status="submitted" label={item.late ? t("hw_late") : t("hw_submitted")} />
                ) : (
                  <Pill status="pending" label={t("hw_pending")} />
                )
              }
            />
          ))
        )}
      </Card>
    </Screen>
  );
}

