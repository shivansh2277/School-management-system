import { useState } from "react";
import { Link } from "react-router-dom";

interface AdmissionEnquiryModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AdmissionEnquiryModal({ isOpen, onClose }: AdmissionEnquiryModalProps) {
  const [form, setForm] = useState({
    enquirer_name: "",
    mobile: "",
    email: "",
    child_name: "",
    class_of_interest: "Class 1",
    notes: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successData, setSuccessData] = useState<{ enquiry_no: string; message: string } | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.enquirer_name.trim()) {
      setError("Please enter parent / enquirer name.");
      return;
    }
    if (!form.mobile.trim() || form.mobile.trim().length < 10) {
      setError("Please enter a valid 10-digit mobile number.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Determine API base URL dynamically
      const apiHost = window.location.hostname === "localhost" ? "http://localhost:8000" : "";
      const res = await fetch(`${apiHost}/public/sunrise/admission/enquiry`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          enquirer_name: form.enquirer_name.trim(),
          mobile: form.mobile.trim(),
          email: form.email.trim() || undefined,
          child_name: form.child_name.trim() || undefined,
          class_of_interest: form.class_of_interest,
          notes: form.notes.trim() || undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to submit enquiry.");
      }

      setSuccessData({
        enquiry_no: data.enquiry_no || "ENQ-SUCCESS",
        message: data.message || "Enquiry submitted successfully!",
      });
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSuccessData(null);
    setForm({
      enquirer_name: "",
      mobile: "",
      email: "",
      child_name: "",
      class_of_interest: "Class 1",
      notes: "",
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
      <div
        className="bg-white rounded-2xl shadow-2xl border border-slate-100 max-w-lg w-full overflow-hidden transition-all transform scale-100"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="bg-slate-900 text-white px-6 py-5 flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold text-lg border border-amber-400/30">
              ?
            </div>
            <div>
              <h3 className="text-lg font-bold font-serif tracking-tight text-white">Admission Enquiry</h3>
              <p className="text-xs text-slate-300">Sunrise School • Gomti Nagar, Lucknow</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
            aria-label="Close modal"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6">
          {successData ? (
            <div className="text-center py-4 space-y-4">
              <div className="w-14 h-14 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div>
                <span className="inline-block bg-amber-100 text-amber-800 text-xs font-bold px-3 py-1 rounded-full mb-2">
                  Reference: {successData.enquiry_no}
                </span>
                <h4 className="text-xl font-bold text-slate-900">Enquiry Received!</h4>
                <p className="text-sm text-slate-600 mt-1 max-w-sm mx-auto">{successData.message}</p>
              </div>
              <div className="bg-slate-50 rounded-xl p-4 text-xs text-slate-500 border border-slate-100 text-left space-y-1">
                <p><strong>Next Steps:</strong> Our Admissions Counselor will get in touch with you at <strong>{form.mobile}</strong> within 1 business day.</p>
              </div>
              <div className="pt-2 flex items-center gap-3 justify-center">
                <button
                  onClick={handleReset}
                  className="bg-slate-900 text-white hover:bg-slate-800 text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors"
                >
                  Done
                </button>
                <Link
                  to="/apply"
                  onClick={handleReset}
                  className="bg-amber-400 hover:bg-amber-300 text-slate-900 text-sm font-bold px-5 py-2.5 rounded-lg transition-colors"
                >
                  Proceed to Full Application &rarr;
                </Link>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <p className="text-xs text-slate-600">
                Submit a quick enquiry to connect with our admissions desk or arrange a campus tour.
              </p>

              {error && (
                <div className="bg-red-50 text-red-700 text-xs p-3 rounded-lg border border-red-200">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Parent / Enquirer Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Vikramaditya Verma"
                  value={form.enquirer_name}
                  onChange={(e) => setForm({ ...form, enquirer_name: e.target.value })}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Mobile Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    required
                    placeholder="+91 98765 43210"
                    value={form.mobile}
                    onChange={(e) => setForm({ ...form, mobile: e.target.value })}
                    className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Email Address (Optional)
                  </label>
                  <input
                    type="email"
                    placeholder="parent@example.com"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Child's Name (Optional)
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Aarav Verma"
                    value={form.child_name}
                    onChange={(e) => setForm({ ...form, child_name: e.target.value })}
                    className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Class of Interest
                  </label>
                  <select
                    value={form.class_of_interest}
                    onChange={(e) => setForm({ ...form, class_of_interest: e.target.value })}
                    className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary bg-white"
                  >
                    {["Nursery", "LKG", "UKG", "Class 1", "Class 2", "Class 3", "Class 4", "Class 5", "Class 6", "Class 7", "Class 8", "Class 9", "Class 10", "Class 11 (Science)", "Class 11 (Commerce)", "Class 11 (Humanities)", "Class 12"].map((cls) => (
                      <option key={cls} value={cls}>
                        {cls}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Message / Query Details (Optional)
                </label>
                <textarea
                  rows={3}
                  placeholder="Ask about bus routes, fee structure, hostel facilities, or schedule a campus tour..."
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary"
                />
              </div>

              <div className="pt-2 flex items-center justify-between border-t border-slate-100">
                <Link
                  to="/apply"
                  onClick={onClose}
                  className="text-xs font-semibold text-primary hover:underline"
                >
                  Or start full application &rarr;
                </Link>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="bg-amber-400 hover:bg-amber-300 disabled:opacity-50 text-slate-900 font-bold text-xs px-5 py-2.5 rounded-lg transition-colors shadow-xs"
                  >
                    {loading ? "Submitting..." : "Submit Enquiry"}
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
