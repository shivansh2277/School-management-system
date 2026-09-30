import { useState } from "react";
import { Link } from "react-router-dom";

export function ContactPage() {
  const [formSubmitted, setFormSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    gradeSeeking: "Class 1 to 5",
    subject: "",
    message: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.email || !formData.phone || !formData.message) {
      return;
    }
    // Record client state and show success confirmation
    setFormSubmitted(true);
  };

  const handleReset = () => {
    setFormData({
      name: "",
      email: "",
      phone: "",
      gradeSeeking: "Class 1 to 5",
      subject: "",
      message: "",
    });
    setFormSubmitted(false);
  };

  const contactDesks = [
    {
      title: "Admissions & Intake Desk",
      role: "For new admissions, campus tour bookings & document queries",
      phone: "+91 522 299 0000 / 01",
      email: "admissions@sunrisepublic.edu",
      location: "Ground Floor, Administrative Block (Counter 1 & 2)",
      hours: "Mon – Sat: 8:30 AM – 3:00 PM",
      icon: "🎓",
    },
    {
      title: "Central Administrative Office",
      role: "For fee deposits, bonafide certificates & general queries",
      phone: "+91 522 299 0002",
      email: "info@sunrisepublic.edu",
      location: "Ground Floor, Main Reception Lobby",
      hours: "Mon – Fri: 8:00 AM – 3:30 PM, Sat: 8:00 AM – 1:00 PM",
      icon: "🏢",
    },
    {
      title: "Transport & Logistics Control",
      role: "For bus routes, stop changes, driver contact & GPS tracking",
      phone: "+91 522 299 0003",
      email: "transport@sunrisepublic.edu",
      location: "Transport Desk, Gate No. 2",
      hours: "Mon – Sat: 7:00 AM – 4:00 PM",
      icon: "🚌",
    },
    {
      title: "Principal’s Secretariat",
      role: "For executive appointments and academic parent conferences",
      phone: "+91 522 299 0004",
      email: "principal@sunrisepublic.edu",
      location: "First Floor, Executive Suite",
      hours: "By prior appointment through front desk",
      icon: "✉️",
    },
  ];

  return (
    <div className="space-y-16 sm:space-y-20 pb-16">
      {/* 1. HERO BANNER */}
      <section className="bg-gradient-to-b from-indigo-50/80 via-ground to-white py-14 sm:py-20 border-b border-rule">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-4">
          <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3.5 py-1 rounded-full">
            Get In Touch
          </span>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
            Contact Sunrise School
          </h1>
          <p className="text-base sm:text-lg text-ink-soft max-w-2xl mx-auto leading-relaxed">
            We welcome prospective families, parents, and community members. Our administrative and admissions team in Gomti Nagar is here to assist you.
          </p>
        </div>
      </section>

      {/* 2. CONTACT DESKS GRID */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-10 space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Key Departmental Helplines
          </h2>
          <p className="text-xs sm:text-sm text-ink-soft">
            Direct your inquiry to the relevant office for swift assistance.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {contactDesks.map((desk) => (
            <div
              key={desk.title}
              className="bg-surface rounded-2xl border border-rule p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <span className="text-3xl p-2 rounded-xl bg-ground border border-rule">
                    {desk.icon}
                  </span>
                  <div>
                    <h3 className="font-bold text-base text-slate-900 leading-snug">
                      {desk.title}
                    </h3>
                  </div>
                </div>
                <p className="text-xs text-ink-soft leading-relaxed">{desk.role}</p>
              </div>

              <div className="space-y-2 pt-3 border-t border-rule text-xs text-slate-700">
                <div className="flex items-center gap-2">
                  <span className="text-primary font-bold">📞</span>
                  <a
                    href="tel:+915222990000"
                    className="font-semibold text-slate-900 hover:text-primary transition-colors"
                  >
                    {desk.phone}
                  </a>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-primary font-bold">✉️</span>
                  <a
                    href={`mailto:${desk.email}`}
                    className="text-ink-soft hover:text-primary transition-colors"
                  >
                    {desk.email}
                  </a>
                </div>
                <div className="text-[11px] text-ink-faint pt-1">
                  <strong>Hours:</strong> {desk.hours}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. ENQUIRY FORM & CAMPUS HOURS SECTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
          {/* Left: Contact Form */}
          <div className="lg:col-span-7 bg-surface rounded-2xl border border-rule p-6 sm:p-10 shadow-sm space-y-6">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-soft px-3 py-1 rounded-full">
                Direct Communication
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight mt-2">
                Send Us an Enquiry
              </h2>
              <p className="text-xs sm:text-sm text-ink-soft mt-1">
                Fill in the details below and our admissions coordinator will get back to you within 24 business hours.
              </p>
            </div>

            {formSubmitted ? (
              <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-xl space-y-4 text-center animate-fade-in">
                <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto text-2xl">
                  ✓
                </div>
                <div>
                  <h3 className="font-bold text-lg text-emerald-900">Enquiry Received Successfully!</h3>
                  <p className="text-xs sm:text-sm text-emerald-700 mt-1 max-w-md mx-auto">
                    Thank you, <strong className="font-semibold">{formData.name}</strong>. Our admissions coordinator will reach out to you at <strong className="font-semibold">{formData.phone}</strong> shortly.
                  </p>
                </div>
                <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
                  <button
                    onClick={handleReset}
                    className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold transition-colors"
                  >
                    Submit Another Query
                  </button>
                  <Link
                    to="/apply"
                    className="px-4 py-2 bg-amber-400 hover:bg-amber-300 text-slate-900 rounded-lg text-xs font-semibold transition-colors"
                  >
                    Fill Full Admission Form &rarr;
                  </Link>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="contact-name" className="block text-xs font-semibold text-slate-700 mb-1">
                      Parent / Guardian Full Name *
                    </label>
                    <input
                      id="contact-name"
                      type="text"
                      required
                      placeholder="e.g. Rajesh Kumar Sharma"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-3.5 py-2.5 rounded-lg border border-rule text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                  </div>

                  <div>
                    <label htmlFor="contact-email" className="block text-xs font-semibold text-slate-700 mb-1">
                      Email Address *
                    </label>
                    <input
                      id="contact-email"
                      type="email"
                      required
                      placeholder="parent@example.com"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full px-3.5 py-2.5 rounded-lg border border-rule text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="contact-phone" className="block text-xs font-semibold text-slate-700 mb-1">
                      Mobile / WhatsApp Number *
                    </label>
                    <input
                      id="contact-phone"
                      type="tel"
                      required
                      placeholder="+91 98765 43210"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="w-full px-3.5 py-2.5 rounded-lg border border-rule text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    />
                  </div>

                  <div>
                    <label htmlFor="contact-grade" className="block text-xs font-semibold text-slate-700 mb-1">
                      Seeking Admission For Grade
                    </label>
                    <select
                      id="contact-grade"
                      value={formData.gradeSeeking}
                      onChange={(e) => setFormData({ ...formData, gradeSeeking: e.target.value })}
                      className="w-full px-3.5 py-2.5 rounded-lg border border-rule text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                    >
                      <option value="Nursery / Pre-School">Nursery / Pre-School</option>
                      <option value="LKG / UKG">LKG / UKG</option>
                      <option value="Class 1 to 5">Class 1 to 5 (Primary)</option>
                      <option value="Class 6 to 8">Class 6 to 8 (Middle)</option>
                      <option value="Class 9 to 10">Class 9 to 10 (Secondary)</option>
                      <option value="Class 11 Science">Class 11 (Science: PCM/PCB)</option>
                      <option value="Class 11 Commerce">Class 11 (Commerce)</option>
                      <option value="Class 11 Humanities">Class 11 (Humanities)</option>
                      <option value="General Query">General / Other Enquiry</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label htmlFor="contact-subject" className="block text-xs font-semibold text-slate-700 mb-1">
                    Subject / Primary Query
                  </label>
                  <input
                    id="contact-subject"
                    type="text"
                    placeholder="e.g. Campus visit booking or syllabus questions"
                    value={formData.subject}
                    onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-lg border border-rule text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>

                <div>
                  <label htmlFor="contact-message" className="block text-xs font-semibold text-slate-700 mb-1">
                    Your Message / Query *
                  </label>
                  <textarea
                    id="contact-message"
                    rows={4}
                    required
                    placeholder="Please mention any specific questions regarding admission dates, documents, transport, or curriculum..."
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-lg border border-rule text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
                  />
                </div>

                <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <button
                    type="submit"
                    className="bg-primary hover:bg-primary-dark text-white font-semibold px-6 py-3 rounded-lg shadow-sm hover:shadow transition-all text-sm cursor-pointer"
                  >
                    Submit Enquiry &rarr;
                  </button>
                  <Link
                    to="/apply"
                    className="text-xs font-semibold text-primary hover:underline"
                  >
                    Ready to enroll? Fill online application &rarr;
                  </Link>
                </div>
              </form>
            )}
          </div>

          {/* Right: Office Hours & Visiting Protocol */}
          <div className="lg:col-span-5 space-y-6">
            {/* Campus Timings Card */}
            <div className="bg-surface rounded-2xl border border-rule p-6 sm:p-8 shadow-sm space-y-5">
              <h3 className="font-bold text-lg text-slate-900 border-b border-rule pb-3 flex items-center gap-2">
                <span>⏰</span>
                <span>Visiting & Office Hours</span>
              </h3>

              <div className="space-y-4 text-xs">
                <div>
                  <strong className="block text-sm text-slate-900 font-semibold">
                    School Administrative Office
                  </strong>
                  <div className="text-ink-soft mt-0.5 space-y-0.5">
                    <p>Monday – Friday: 8:00 AM – 3:30 PM</p>
                    <p>Saturday: 8:00 AM – 1:00 PM</p>
                    <p className="text-[11px] text-ink-faint">
                      (Closed on 2nd Saturdays, Sundays & Gazetted Holidays)
                    </p>
                  </div>
                </div>

                <div className="border-t border-rule pt-3">
                  <strong className="block text-sm text-slate-900 font-semibold">
                    Admissions Consultation & Campus Tours
                  </strong>
                  <div className="text-ink-soft mt-0.5 space-y-0.5">
                    <p>Monday – Saturday: 9:00 AM – 2:00 PM</p>
                    <p className="text-[11px] text-emerald-700 font-medium">
                      Walk-ins welcomed; online booking recommended.
                    </p>
                  </div>
                </div>

                <div className="border-t border-rule pt-3">
                  <strong className="block text-sm text-slate-900 font-semibold">
                    Teacher Interaction Timings (For Parents)
                  </strong>
                  <div className="text-ink-soft mt-0.5">
                    <p>Saturdays: 12:30 PM – 2:00 PM (or by prior gate pass)</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Fast-Track Admissions Box */}
            <div className="bg-gradient-to-br from-[#042954] to-indigo-950 text-white rounded-2xl p-6 sm:p-8 shadow-sm space-y-4">
              <span className="text-[11px] font-bold uppercase tracking-wider text-amber-400 bg-amber-400/20 px-2.5 py-0.5 rounded-full inline-block">
                Direct Admission Gateway
              </span>
              <h3 className="text-xl font-bold tracking-tight">
                Academic Session 2026–27
              </h3>
              <p className="text-xs text-slate-300 leading-relaxed">
                Save time by completing your admission application online. Our digital portal connects directly to the school admissions office.
              </p>
              <div className="pt-2">
                <Link
                  to="/apply"
                  className="w-full inline-flex items-center justify-center gap-2 bg-amber-400 hover:bg-amber-300 text-slate-900 font-bold py-2.5 px-4 rounded-lg text-xs shadow-sm transition-all"
                >
                  <span>Launch Online Admission Portal</span>
                  <span>&rarr;</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. LOCATION MAP & REACHING SUNRISE */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        <div className="bg-surface rounded-2xl border border-rule shadow-sm overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-12">
            {/* Map & Visual Simulation Container */}
            <div className="lg:col-span-7 bg-slate-900 flex flex-col justify-between text-white relative min-h-[360px] overflow-hidden">
              <img
                src="/images/school/school_entrance_gate.jpg"
                alt="Sunrise School Main Campus Gate, Sector 4, Gomti Nagar"
                className="absolute inset-0 w-full h-full object-cover opacity-35"
                loading="lazy"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/70 to-slate-950/40" />

              <div className="space-y-2 z-10 p-8 sm:p-10 pb-0">
                <span className="text-xs font-bold uppercase tracking-wider text-amber-400 bg-amber-400/20 px-3 py-1 rounded-full inline-block backdrop-blur-xs">
                  Gomti Nagar Campus
                </span>
                <h3 className="text-2xl font-bold tracking-tight">
                  Sector 4, Gomti Nagar, Lucknow
                </h3>
                <p className="text-xs text-slate-300">
                  Uttar Pradesh 226010, India • Landmark: Near Shaheed Path Bypass
                </p>
              </div>

              {/* Graphic map pin marker */}
              <div className="my-6 text-center z-10 px-8">
                <div className="inline-flex items-center gap-3 bg-slate-900/80 backdrop-blur-md px-5 py-3 rounded-2xl border border-white/20 shadow-xl">
                  <span className="text-3xl animate-bounce">📍</span>
                  <div className="text-left">
                    <span className="font-bold text-sm block text-white">Sunrise School Campus Gate No. 1</span>
                    <span className="text-[11px] text-amber-300">5-Acre Eco-Campus Sanctuary • Visitor Parking Available</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-slate-300 z-10 p-8 sm:p-10 pt-0">
                <span>GPS: 26.8500° N, 80.9950° E</span>
                <a
                  href="https://maps.google.com"
                  target="_blank"
                  rel="noreferrer"
                  className="text-amber-400 hover:text-amber-300 font-semibold inline-flex items-center gap-1"
                >
                  <span>Open in Google Maps</span>
                  <span>&rarr;</span>
                </a>
              </div>
            </div>

            {/* Travel Directions Guide */}
            <div className="lg:col-span-5 p-6 sm:p-8 space-y-5 flex flex-col justify-between">
              <div>
                <h4 className="font-bold text-base text-slate-900 mb-3">
                  How to Reach Our Campus
                </h4>
                <div className="space-y-3.5 text-xs text-ink-soft">
                  <div className="flex items-start gap-3">
                    <span className="text-base shrink-0">🚗</span>
                    <div>
                      <strong className="text-slate-900 font-semibold block">From Hazratganj (~15 mins)</strong>
                      <span>Take Lohia Path straight towards Gomti Nagar, exit toward Sector 4.</span>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <span className="text-base shrink-0">🚆</span>
                    <div>
                      <strong className="text-slate-900 font-semibold block">From Charbagh Railway Station (~25 mins)</strong>
                      <span>Via Shaheed Path corridor or Cantt Road to Gomti Nagar bypass.</span>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <span className="text-base shrink-0">✈️</span>
                    <div>
                      <strong className="text-slate-900 font-semibold block">From CCS International Airport (~25 mins)</strong>
                      <span>Direct seamless transit via elevated Amar Shaheed Path expressway.</span>
                    </div>
                  </div>

                  <div className="flex items-start gap-3">
                    <span className="text-base shrink-0">🚌</span>
                    <div>
                      <strong className="text-slate-900 font-semibold block">School Bus Transport</strong>
                      <span>Sunrise School buses cover all prime residential sectors of Lucknow.</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-rule">
                <Link
                  to="/facilities"
                  className="text-xs font-semibold text-primary hover:underline inline-flex items-center gap-1"
                >
                  <span>Learn more about safe GPS school transport</span>
                  <span>&rarr;</span>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
