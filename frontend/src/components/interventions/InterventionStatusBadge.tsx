import type { InterventionStatus } from "@/lib/types";

const styles: Record<InterventionStatus, string> = {
  active: "bg-yellow-100 text-yellow-800",
  resolved: "bg-green-100 text-green-800",
};

export function InterventionStatusBadge({ status }: { status: InterventionStatus }) {
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${styles[status]}`}>
      {status}
    </span>
  );
}
