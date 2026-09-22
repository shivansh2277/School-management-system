import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { useState } from "react";
import { Pressable, Text, View } from "react-native";

import { api, formatDate, money, tokenStore } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Button, Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type Invoice = {
  id: number;
  period_month?: number;
  period_year?: number;
  month?: number;
  year?: number;
  payable?: number | string;
  total?: number | string;
  amount?: number | string;
  charged?: number | string;
  discount?: number | string;
  paid?: number | string;
  balance?: number | string;
  due_date: string;
  status: string;
  receipt_no: string | null;
};

type FeeSummary = {
  total_invoiced: number;
  total_paid: number;
  total_dues: number;
  balance: number;
};

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default function ParentFees() {
  const qc = useQueryClient();
  const { selectedChildId, me, selectChild } = useAuth();
  const children = me?.children ?? [];
  const [confirming, setConfirming] = useState<Invoice | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<number | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["parent-fees", selectedChildId],
    queryFn: () => api.get<Invoice[]>(`/parent/fees?student_id=${selectedChildId}`),
    enabled: selectedChildId !== null,
  });

  const summary = useQuery({
    queryKey: ["parent-fee-summary", selectedChildId],
    queryFn: () => api.get<FeeSummary>(`/parent/children/${selectedChildId}/fees/summary`),
    enabled: selectedChildId !== null,
  });

  const pay = useMutation({
    mutationFn: (id: number) => api.post<{ receipt_no: string }>(`/parent/fees/${id}/pay`),
    onSuccess: (r) => {
      setConfirming(null);
      setNote(`Payment successful. Receipt ${r.receipt_no}.`);
      qc.invalidateQueries({ queryKey: ["parent-fees"] });
      qc.invalidateQueries({ queryKey: ["parent-fee-summary"] });
    },
    onError: (e: Error) => {
      setConfirming(null);
      setNote(e.message);
    },
  });

  const openReceipt = async (invoice: Invoice) => {
    setDownloading(invoice.id);
    const dir = FileSystem.cacheDirectory;
    if (!dir) {
      setNote("No cache directory available on this device.");
      setDownloading(null);
      return;
    }
    const target = `${dir}receipt-invoice-${invoice.id}.pdf`;
    try {
      const { uri } = await FileSystem.downloadAsync(
        `${api.base}/parent/fees/${invoice.id}/receipt.pdf`,
        target,
        { headers: { Authorization: `Bearer ${tokenStore.get() ?? ""}` } },
      );
      setDownloading(null);
      await Sharing.shareAsync(uri, { mimeType: "application/pdf" });
    } catch {
      setDownloading(null);
      setNote("Could not open the receipt PDF.");
    }
  };

  if (isLoading || !selectedChildId) return <Loading />;

  const invoiceList = data ?? [];
  const totalDues = summary.data?.total_dues ?? 0;

  return (
    <Screen>
      {/* Child Selector */}
      {children.length > 1 && (
        <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap", marginBottom: 8 }}>
          {children.map((c) => (
            <Pressable
              key={c.id}
              onPress={() => selectChild(c.id)}
              style={{
                paddingHorizontal: 12,
                paddingVertical: 6,
                borderRadius: theme.radius.pill,
                backgroundColor: selectedChildId === c.id ? theme.primary : theme.surface,
              }}
            >
              <Text style={{ color: selectedChildId === c.id ? "#fff" : theme.inkSoft, fontSize: 13 }}>
                {c.name}
              </Text>
            </Pressable>
          ))}
        </View>
      )}

      {/* Prominent Outstanding Balance Card */}
      <Card>
        <View style={{ gap: 4 }}>
          <Text style={{ fontSize: 12, color: theme.inkFaint, textTransform: "uppercase", letterSpacing: 0.5 }}>
            Total Outstanding Fee Balance
          </Text>
          <Text style={{ fontSize: 28, fontWeight: "800", color: totalDues > 0 ? theme.danger : theme.success }}>
            {money(totalDues)}
          </Text>
          <View style={{ flexDirection: "row", gap: 16, marginTop: 8, paddingTop: 8, borderTopWidth: 1, borderTopColor: theme.rule }}>
            <View>
              <Text style={s.meta}>Total Invoiced</Text>
              <Text style={{ fontWeight: "600", color: theme.ink }}>{money(summary.data?.total_invoiced ?? 0)}</Text>
            </View>
            <View>
              <Text style={s.meta}>Total Paid</Text>
              <Text style={{ fontWeight: "600", color: "#16A34A" }}>{money(summary.data?.total_paid ?? 0)}</Text>
            </View>
            <View>
              <Text style={s.meta}>Net Dues</Text>
              <Text style={{ fontWeight: "700", color: totalDues > 0 ? theme.danger : theme.success }}>
                {totalDues > 0 ? "Pending" : "Cleared"}
              </Text>
            </View>
          </View>
        </View>
      </Card>

      {note ? (
        <Card>
          <Text style={s.meta}>{note}</Text>
        </Card>
      ) : null}

      <Text style={[s.title, { marginVertical: 8 }]}>Fee Invoices</Text>

      {invoiceList.length === 0 ? (
        <Card>
          <Empty text="No invoices raised yet." />
        </Card>
      ) : (
        invoiceList.map((invoice) => {
          const invMonth = invoice.period_month ?? invoice.month ?? 1;
          const invYear = invoice.period_year ?? invoice.year ?? 2026;
          // Authoritative invoice total: net payable (never fall back to balance)
          const invTotal = Number(invoice.payable ?? invoice.total ?? invoice.amount ?? 0);
          // Authoritative outstanding balance: remaining balance after payment allocations
          const invBalance = invoice.balance !== undefined ? Number(invoice.balance) : 0;
          const isPaid = invoice.status === "paid" || invBalance <= 0;

          return (
            <Card key={invoice.id}>
              <Row
                left={
                  <>
                    <Text style={s.title}>
                      {MONTHS[invMonth - 1]} {invYear}
                    </Text>
                    <Text style={s.meta}>Due {formatDate(invoice.due_date)}</Text>
                    {invBalance > 0 && isPaid ? null : invBalance > 0 ? (
                      <Text style={{ fontSize: 12, color: theme.danger, fontWeight: "600" }}>
                        Remaining due: {money(invBalance)}
                      </Text>
                    ) : null}
                  </>
                }
                right={
                  <View style={{ alignItems: "flex-end", gap: 2 }}>
                    <Text style={{ fontWeight: "700", color: invBalance > 0 ? theme.danger : theme.ink, fontSize: 16 }}>
                      {money(invBalance)}
                    </Text>
                    <Text style={{ fontSize: 11, color: theme.inkFaint }}>
                      Total: {money(invTotal)}
                    </Text>
                    <Pill status={isPaid ? "paid" : "overdue"} label={isPaid ? "Paid" : "Pending"} />
                  </View>
                }
              />

              {isPaid ? (
                <View style={{ marginTop: 8, gap: 6 }}>
                  {invoice.receipt_no ? <Text style={s.meta}>Receipt: {invoice.receipt_no}</Text> : null}
                  <Button
                    label={downloading === invoice.id ? "Opening Receipt..." : "📄 Download 2-Copy Receipt PDF"}
                    tone="ghost"
                    onPress={() => openReceipt(invoice)}
                    disabled={downloading === invoice.id}
                  />
                </View>
              ) : confirming?.id === invoice.id ? (
                <View style={{ gap: 8, marginTop: 8 }}>
                  <Text style={s.meta}>
                    Confirm payment of {money(invBalance > 0 ? invBalance : invTotal)}.
                  </Text>
                  <Button
                    label={pay.isPending ? "Processing..." : "Confirm Payment"}
                    onPress={() => pay.mutate(invoice.id)}
                    disabled={pay.isPending}
                  />
                  <Button label="Cancel" tone="ghost" onPress={() => setConfirming(null)} />
                </View>
              ) : (
                <View style={{ marginTop: 8 }}>
                  <Button label="Pay Now" onPress={() => setConfirming(invoice)} />
                </View>
              )}
            </Card>
          );
        })
      )}
    </Screen>
  );
}
