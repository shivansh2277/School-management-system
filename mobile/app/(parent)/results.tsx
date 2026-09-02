import { useAuth } from "../../src/auth/AuthContext";
import { Loading } from "../../src/components/ui";
import { ResultsView } from "../../src/components/views";

export default function ParentResults() {
  const { selectedChildId } = useAuth();
  if (!selectedChildId) return <Loading />;
  const base = `/parent/children/${selectedChildId}/results`;
  return <ResultsView listPath={base} cardPath={base} />;
}
