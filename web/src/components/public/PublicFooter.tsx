import { Link } from "react-router-dom";
import { SchoolCrest } from "./SchoolCrest";

export function PublicFooter() {
  return (
    <footer className="bg-slate-900 text-slate-300 border-t border-slate-800">
      {/* Top Pre-footer CTA Strip */}
      <div className="bg-gradient-to-r from-[#042954] via-indigo-900 to-[#042954] text-white py-8 px-4 sm:px-6 lg:px-8 border-b border-indigo-950">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="text-center md:text-left">
            <h3 className="text-xl sm:text-2xl font-bold tracking-tight">
              Ready to give your child an inspiring future?
            </h3>
            <p className="text-indigo-100 text-xs sm:text-sm mt-1 max-w-xl">
              Admissions are open for the Academic Session 2026–27 (Pre-Primary to Grade 11). Book a campus tour or submit an online application today.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/admissions"
              className="bg-white hover:bg-slate-50 text-[#042954] font-semibold px-5 py-2.5 rounded-lg shadow-sm transition-all text-xs sm:text-sm"
            >
              Admissions Guide
            </Link>
            <Link
              to="/apply"
              className="bg-amber-400 hover:bg-amber-300 text-slate-900 font-bold px-5 py-2.5 rounded-lg shadow-sm transition-all text-xs sm:text-sm inline-flex items-center gap-1"
            >
              <span>Apply Online</span>
              <span>&rarr;</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Main Footer Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 lg:gap-12">
          {/* Col 1: School Identity & Story (2 cols wide on lg) */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <SchoolCrest className="w-10 h-10" />
              <div>
                <span className="text-xl font-bold text-white tracking-tight block font-serif">
                  Sunrise School
                </span>
                <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Gomti Nagar, Lucknow • Estd. 2011
                </span>
              </div>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed pr-4">
              Sunrise School is an established, values-led CBSE institution located in Sector 4, Gomti Nagar, Lucknow. Dedicated to experiential learning, scientific inquiry, athletic excellence, and moral integrity, we nurture curious minds to build confident futures.
            </p>
            <div className="pt-1 flex flex-wrap gap-2">
              <span className="inline-block bg-slate-800 text-slate-300 text-xs px-3 py-1 rounded-full border border-slate-700">
                CBSE Affiliated Senior Secondary • School Code: To be configured (Demo)
              </span>
              <span className="inline-block bg-slate-800 text-amber-400 text-xs px-3 py-1 rounded-full border border-slate-700 font-medium">
                Science • Commerce • Humanities
              </span>
            </div>
          </div>

          {/* Col 2: Explore Navigation Links */}
          <div>
            <h4 className="text-white text-xs sm:text-sm font-semibold uppercase tracking-wider mb-4 border-l-2 border-amber-400 pl-2.5">
              Explore
            </h4>
            <ul className="space-y-2 text-xs sm:text-sm">
              <li>
                <Link to="/" className="text-slate-400 hover:text-white transition-colors">
                  Home
                </Link>
              </li>
              <li>
                <Link to="/about" className="text-slate-400 hover:text-white transition-colors">
                  About Our School
                </Link>
              </li>
              <li>
                <Link to="/academics" className="text-slate-400 hover:text-white transition-colors">
                  Academics & Wings
                </Link>
              </li>
              <li>
                <Link to="/facilities" className="text-slate-400 hover:text-white transition-colors">
                  Campus & Facilities
                </Link>
              </li>
              <li>
                <Link to="/school-life" className="text-slate-400 hover:text-white transition-colors">
                  School Life & Houses
                </Link>
              </li>
              <li>
                <Link to="/events" className="text-slate-400 hover:text-white transition-colors">
                  Events & Calendar
                </Link>
              </li>
              <li>
                <Link to="/gallery" className="text-slate-400 hover:text-white transition-colors">
                  Photo Gallery
                </Link>
              </li>
              <li>
                <Link to="/public-disclosure" className="text-slate-400 hover:text-white transition-colors">
                  Public Disclosure
                </Link>
              </li>
              <li>
                <Link to="/resources" className="text-slate-400 hover:text-white transition-colors">
                  Resources & Downloads
                </Link>
              </li>
              <li>
                <Link to="/announcements" className="text-slate-400 hover:text-white transition-colors">
                  News & Announcements
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-slate-400 hover:text-white transition-colors">
                  Contact Us
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 3: Admissions & Contact */}
          <div>
            <h4 className="text-white text-xs sm:text-sm font-semibold uppercase tracking-wider mb-4 border-l-2 border-amber-400 pl-2.5">
              Admissions & Hours
            </h4>
            <div className="space-y-3 text-xs sm:text-sm text-slate-400">
              <div>
                <strong className="text-slate-200 block text-xs uppercase font-medium">Admissions 2026–27</strong>
                <Link
                  to="/apply"
                  className="text-amber-400 hover:text-amber-300 font-semibold transition-colors inline-flex items-center gap-1 mt-0.5"
                >
                  <span>Online Admission Form</span>
                  <span>&rarr;</span>
                </Link>
              </div>

              <div>
                <strong className="text-slate-200 block text-xs uppercase font-medium">Campus Location</strong>
                <span className="text-xs">Sector 4, Gomti Nagar, Lucknow, UP 226010</span>
              </div>

              <div>
                <strong className="text-slate-200 block text-xs uppercase font-medium">Helpline</strong>
                <a
                  href="tel:+915222990000"
                  className="text-xs text-white font-semibold hover:text-amber-300 transition-colors"
                >
                  +91 522 299 0000
                </a>
                <br />
                <span className="text-slate-400 text-xs">info@sunrisepublic.edu</span>
              </div>

              <div className="pt-1 text-xs">
                <strong className="text-slate-200 block uppercase font-medium">Office Hours</strong>
                <span>Mon – Fri: 8:00 AM – 3:30 PM</span>
                <br />
                <span>Sat: 8:00 AM – 1:00 PM</span>
                <span className="block text-[11px] text-slate-500 mt-0.5">(Closed on 2nd Saturdays)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Legal, Disclaimer & Accreditation Bar */}
        <div className="pt-8 mt-8 border-t border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <div className="text-center md:text-left space-y-0.5">
            <p>© 2026 Sunrise School, Gomti Nagar, Lucknow. All rights reserved.</p>
            <p className="text-[11px] text-slate-600">
              CBSE Affiliated Senior Secondary School • Affiliated up to Class XII • Estd. 2011 • Demo School Portal
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-slate-400">
            <Link to="/public-disclosure" className="hover:text-white transition-colors">
              Mandatory Public Disclosures
            </Link>
            <span>•</span>
            <Link to="/resources" className="hover:text-white transition-colors">
              Downloads & Prospectus
            </Link>
            <span>•</span>
            <Link to="/announcements" className="hover:text-white transition-colors">
              Announcements
            </Link>
            <span>•</span>
            <Link to="/contact" className="hover:text-white transition-colors">
              Grievance & Support
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
