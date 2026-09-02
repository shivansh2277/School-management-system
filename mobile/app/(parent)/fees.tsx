import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
// SDK 54 moved downloadAsync/cacheDirectory out of the root export. The legacy
// entry point is the one that still takes request headers, which this needs.
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { useState } from "react";
import { Text, View } from "react-native";

import { api, money, tokenStore } from "../../src/api/client";
import { useAuth } from "../../src/auth/AuthContext";
import { Button, Card, Empty, Loading, Pill, Row, Screen, s } from "../../src/components/ui";
import { theme } from "../../src/theme";

type Invoice = {
  id: number;
  month: number;
  year: number;
  amount: string;
  due_date: string;
  status: string;
  receipt_no: string | null;
};

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default function ParentFees() {
  const qc = useQueryClient();
  const { selectedChildId } = useAuth();
  const [confirming, setConfirming] = useState<Invoice | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["parent-fees", selectedChildId],
    queryFn: () => api.get<Invoice[]>(`/parent/fees?student_id=${selectedChildId}`),
    enabled: selectedChildId !== null,
  });

  const pay = useMutation({
    mutationFn: (id: number) => api.post<{ receipt_no: string }>(`/parent/fees/${id}/pay`),
    onSuccess: (r) => {
      setConfirming(null);
      setNote(`Payment successful. Receipt ${r.receipt_no}.`);
      qc.invalidateQueries({ queryKey: ["parent-fees"] });
    },
    onError: (e: Error) => {
      setConfirming(null);
      setNote(e.message);
    },
  });

  const openReceipt = async (invoice: Invoice) => {
    // Downloaded with the bearer header rather than a token in the URL, then
    // handed to the OS share sheet to view or save.
    const dir = FileSystem.cacheDirectory;
    if (!dir) {
      setNote("No cache directory available on this device.");
      return;
    }
    const target = `${dir}receipt-${invoice.id}.pdf`;
    try {
      const { uri } = await FileSystem.downloadAsync(
        `${api.base}/parent/fees/${invoice.id}/receipt.pdf`,
        target,
        { headers: { Authorization: `Bearer ${tokenStore.get() ?? ""}` } },
      );
      await Sharing.shareAsync(uri, { mimeType: "application/pdf" });
    } catch {
      setNote("Could not open the receipt.");
    }
  };

  if (isLoading || !data) return <Loading />;

  return (
    <Screen>
      {note ? (
        <Card>
          <Text style={s.meta}>{note}</Text>
        </Card>
      ) : null}

      {data.length === 0 ? (
        <Card>
          <Empty text="No invoices raised yet." />
        </Card>
      ) : (
        data.map((invoice) => (
          <Card key={invoice.id}>
            <Row
              left={
                <>
                  <Text style={s.title}>
                    {MONTHS[invoice.month - 1]} {invoice.year}
                  </Text>
                  <Text style={s.meta}>Due {invoice.due_date}</Text>
                </>
              }
              right={
                <View style={{ alignItems: "flex-end", gap: 4 }}>
                  <Text style={{ fontWeight: "700", color: theme.ink }}>
                    {money(invoice.amount)}
                  </Text>
                  <Pill status={invoice.status} label={invoice.status} />
                </View>
              }
            />
            {invoice.status === "paid" ? (
              <>
                <Text style={s.meta}>Receipt {invoice.receipt_no}</Text>
                <Button label="Download receipt" tone="ghost" onPress={() => openReceipt(invoice)} />
              </>
            ) : confirming?.id === invoice.id ? (
              <View style={{ gap: 8 }}>
                <Text style={s.meta}>
                  Confirm a simulated payment of {money(invoice.amount)}. No real money moves.
                </Text>
                <Button
                  label={pay.isPending ? "Processing..." : "Confirm payment"}
                  onPress={() => pay.mutate(invoice.id)}
                  disabled={pay.isPending}
                />
                <Button label="Cancel" tone="ghost" onPress={() => setConfirming(null)} />
              </View>
            ) : (
              <Button label="Pay now" onPress={() => setConfirming(invoice)} />
            )}
          </Card>
        ))
      )}
    </Screen>
  );
}
