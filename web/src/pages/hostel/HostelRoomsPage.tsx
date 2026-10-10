import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../../api/client";
import { errorText } from "../../api/errors";
import { useAuth } from "../../auth/AuthContext";
import { Card, FormError, FormField, Modal, Pill, inputClass } from "../../components/ui";

type HostelStructure = {
  id: number;
  name: string;
  code: string;
  gender: string;
  status: string;
  floors: Array<{
    id: number;
    floor_number: number;
    floor_name: string;
    rooms: Array<{
      id: number;
      room_number: string;
      capacity: number;
      room_type: string;
      status: string;
      beds: Array<{
        id: number;
        bed_number: string;
        status: string;
        current_allocation: {
          allocation_id: number;
          admission_id: number;
          student_id: number;
          student_name: string;
          admission_no: string;
          class_label: string;
          allocated_at: string;
        } | null;
      }>;
    }>;
  }>;
};

type HostelBasic = {
  id: number;
  name: string;
  code: string;
  gender: string;
  status: string;
};

type EligibleStudent = {
  student_id: number;
  admission_no: string;
  full_name: string;
  gender: string;
  class_label: string;
};

export function HostelRoomsPage() {
  const qc = useQueryClient();
  const { can } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const isProvost = can("hostel.structure.manage");

  // Fetch all accessible hostels
  const { data: hostels = [] } = useQuery<HostelBasic[]>({
    queryKey: ["hostel", "list"],
    queryFn: () => api.rawGet<HostelBasic[]>("/admin/hostel/list"),
  });

  const selectedHostelId = searchParams.get("hostel_id")
    ? Number(searchParams.get("hostel_id"))
    : hostels[0]?.id;

  // Fetch full hierarchy of selected hostel
  const { data: hostelStructure, isLoading, error } = useQuery<HostelStructure>({
    queryKey: ["hostel", "structure", selectedHostelId],
    queryFn: () => api.rawGet<HostelStructure>(`/admin/hostel/${selectedHostelId}/structure`),
    enabled: !!selectedHostelId,
  });

  // State for allocating a bed directly from vacant bed card
  const [allocatingBed, setAllocatingBed] = useState<{
    bedId: number;
    bedNumber: string;
    roomNumber: string;
  } | null>(null);
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);
  const [allocationRemarks, setAllocationRemarks] = useState("");
  const [allocError, setAllocError] = useState<string | null>(null);

  // Fetch eligible unassigned Class 9+ students for allocation modal
  const { data: eligibleStudents = [] } = useQuery<EligibleStudent[]>({
    queryKey: ["hostel", "eligible-day-scholars", selectedHostelId],
    queryFn: () => api.rawGet<EligibleStudent[]>("/admin/hostel/eligible-day-scholars"),
    enabled: !!allocatingBed,
  });

  // Filter students matching hostel gender
  const filteredStudents = eligibleStudents.filter((s) => {
    if (!hostelStructure) return true;
    return s.gender.toLowerCase() === hostelStructure.gender.toLowerCase();
  });

  // Allocate bed mutation
  const allocateMutation = useMutation({
    mutationFn: async () => {
      if (!allocatingBed || !selectedStudentId) throw new Error("Select a student");
      return api.rawPost(`/admin/hostel/${selectedHostelId}/admissions/direct`, {
        student_id: selectedStudentId,
        bed_id: allocatingBed.bedId,
        admission_date: new Date().toISOString().split("T")[0],
        remarks: allocationRemarks.trim() || undefined,
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["hostel"] });
      setAllocatingBed(null);
      setSelectedStudentId(null);
      setAllocationRemarks("");
      setAllocError(null);
    },
    onError: (err: any) => {
      setAllocError(errorText(err));
    },
  });

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-rule">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">Hostel Structure & Bed Layout</h1>
          <p className="text-sm text-ink-soft mt-1">
            Visual room layout: Hostel → Floor → Room → Bed → Resident Student.
          </p>
        </div>

        {/* Hostel Selector if multiple hostels accessible */}
        {hostels.length > 1 && (
          <div className="flex items-center gap-2">
            <label className="text-xs font-semibold text-ink-soft">Select Hostel:</label>
            <select
              className={inputClass}
              value={selectedHostelId || ""}
              onChange={(e) => setSearchParams({ hostel_id: e.target.value })}
            >
              {hostels.map((h) => (
                <option key={h.id} value={h.id}>
                  {h.name} ({h.gender === "male" ? "Boys" : "Girls"})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {isLoading && (
        <div className="p-8 text-center text-ink-soft">Loading hostel room layout...</div>
      )}

      {error && (
        <div className="p-4 bg-danger/10 border border-danger/30 rounded-card text-danger">
          Failed to load hostel structure. (Notice: Wardens can only view their assigned hostel).
        </div>
      )}

      {hostelStructure && (
        <div className="space-y-6">
          {/* Hostel Summary Bar */}
          <div className="p-4 bg-ground rounded-card border border-rule flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-ink">{hostelStructure.name}</h2>
              <p className="text-xs text-ink-soft">
                Code: {hostelStructure.code} • Gender: {hostelStructure.gender === "male" ? "Boys Residential" : "Girls Residential"} • Status: {hostelStructure.status}
              </p>
            </div>
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-rose-500 inline-block" /> Occupied Bed
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" /> Vacant Bed
              </span>
            </div>
          </div>

          {/* Floors & Rooms Hierarchy */}
          {hostelStructure.floors.length === 0 ? (
            <Card>
              <p className="text-sm text-ink-soft text-center py-6">No floors configured for this hostel.</p>
            </Card>
          ) : (
            hostelStructure.floors.map((floor) => (
              <Card
                key={floor.id}
                title={`Floor ${floor.floor_number}: ${floor.floor_name}`}
                className="space-y-4"
              >
                {floor.rooms.length === 0 ? (
                  <p className="text-xs text-ink-soft py-2">No rooms on this floor.</p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {floor.rooms.map((room) => {
                      const occupiedCount = room.beds.filter((b) => b.current_allocation !== null).length;
                      const isFull = occupiedCount >= room.capacity;

                      return (
                        <div
                          key={room.id}
                          className="p-4 bg-ground rounded-card border border-rule space-y-3"
                        >
                          <div className="flex items-start justify-between">
                            <div>
                              <h3 className="text-base font-bold text-ink">Room {room.room_number}</h3>
                              <p className="text-xs text-ink-soft capitalize">
                                Type: {room.room_type} • Capacity: {room.capacity} beds
                              </p>
                            </div>
                            <Pill status={isFull ? "failed" : "active"}>
                              {occupiedCount} / {room.capacity} Beds
                            </Pill>
                          </div>

                          {/* Individual Beds in Room */}
                          <div className="space-y-2 pt-1 border-t border-rule/60">
                            {room.beds.map((bed) => {
                              const resident = bed.current_allocation;

                              return (
                                <div
                                  key={bed.id}
                                  className={`p-2.5 rounded border text-xs flex items-center justify-between ${
                                    resident
                                      ? "bg-surface border-rose-200/80"
                                      : "bg-surface border-emerald-200/80"
                                  }`}
                                >
                                  <div>
                                    <div className="flex items-center gap-1.5">
                                      <span
                                        className={`w-2 h-2 rounded-full ${
                                          resident ? "bg-rose-500" : "bg-emerald-500"
                                        }`}
                                      />
                                      <span className="font-semibold text-ink">Bed {bed.bed_number}</span>
                                    </div>
                                    {resident ? (
                                      <div className="mt-1 ml-3.5">
                                        <p className="font-medium text-ink">{resident.student_name}</p>
                                        <p className="text-2xs text-ink-soft">
                                          Adm #{resident.admission_no} • {resident.class_label}
                                        </p>
                                      </div>
                                    ) : (
                                      <p className="mt-0.5 ml-3.5 text-2xs text-emerald-700 font-medium">
                                        Vacant & Available
                                      </p>
                                    )}
                                  </div>

                                  {!resident && (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        setAllocatingBed({
                                          bedId: bed.id,
                                          bedNumber: bed.bed_number,
                                          roomNumber: room.room_number,
                                        });
                                        setSelectedStudentId(null);
                                        setAllocError(null);
                                      }}
                                      className="px-2.5 py-1 rounded bg-emerald-600 text-white font-medium text-2xs hover:bg-emerald-700 transition"
                                    >
                                      Allocate
                                    </button>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </Card>
            ))
          )}
        </div>
      )}

      {/* Direct Bed Allocation Modal */}
      {allocatingBed && (
        <Modal
          title={`Allocate Bed ${allocatingBed.bedNumber} (Room ${allocatingBed.roomNumber})`}
          onClose={() => setAllocatingBed(null)}
        >
          <div className="space-y-4">
            <p className="text-xs text-ink-soft">
              Assign an eligible Class 9+ student ({hostelStructure?.gender === "male" ? "male" : "female"}) to this bed.
            </p>

            {allocError && <p className="text-sm text-danger">{allocError}</p>}

            <FormField label="Eligible Enrolled Day Scholar *">
              <select
                className={inputClass}
                value={selectedStudentId || ""}
                onChange={(e) => setSelectedStudentId(Number(e.target.value) || null)}
              >
                <option value="">-- Choose Eligible Student (Class 9+) --</option>
                {filteredStudents.map((s) => (
                  <option key={s.student_id} value={s.student_id}>
                    {s.full_name} (Adm #{s.admission_no}, {s.class_label})
                  </option>
                ))}
              </select>
            </FormField>

            {filteredStudents.length === 0 && (
              <p className="text-xs text-amber-700 bg-amber-50 p-2.5 rounded border border-amber-200">
                No unassigned Class 9+ day scholars found matching hostel gender requirements.
              </p>
            )}

            <FormField label="Allocation Remarks (Optional)">
              <input
                type="text"
                className={inputClass}
                value={allocationRemarks}
                onChange={(e) => setAllocationRemarks(e.target.value)}
                placeholder="e.g. Regular term allotment, room preference"
              />
            </FormField>

            <div className="flex justify-end gap-2 pt-2 border-t border-rule">
              <button
                type="button"
                onClick={() => setAllocatingBed(null)}
                className="px-3 py-1.5 rounded border border-rule text-xs font-semibold text-ink hover:bg-ground"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={!selectedStudentId || allocateMutation.isPending}
                onClick={() => allocateMutation.mutate()}
                className="px-4 py-1.5 rounded bg-primary text-white text-xs font-semibold hover:bg-primary-hover disabled:opacity-50"
              >
                {allocateMutation.isPending ? "Allocating..." : "Confirm Allocation"}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
