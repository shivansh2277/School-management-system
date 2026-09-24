import { Link } from "react-router-dom";
import { SchoolCrest } from "./SchoolCrest";

export function PublicFooter() {
  return (
    <footer className="bg-slate-900 text-slate-300 border-t border-slate-800">
      {/* Top Pre-footer CTA Strip */}
      <div className="bg-gradient-to-r from-primary to-indigo-900 text-white py-8 px-4 sm:px-6 lg:px-8 border-b border-indigo-700/50">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="text-center md:text-left">
            <h3 className="text-xl sm:text-2xl font-bold tracking-tight">
              Ready to give your child an inspiring future?
            </h3>
            <p className="text-indigo-100 text-sm mt-1 max-w-xl">
              Admissions are now open for the Academic Year 2025–26. Book a campus tour or submit an online application today.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/admissions"
              className="bg-white text-primary hover:bg-slate-50 font-semibold px-5 py-2.5 rounded-lg shadow-sm transition-all text-sm"
            >
              Admissions Guide
            </Link>
            <Link
              to="/apply"
              className="bg-amber-400 hover:bg-amber-300 text-slate-900 font-semibold px-5 py-2.5 rounded-lg shadow-sm transition-all text-sm"
            >
              Apply Online &rarr;
            </Link>
          </div>
        </div>
      </div>

      {/* Main Footer Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 lg:gap-12">
          {/* Col 1: School Identity & Overview (2 cols wide on lg) */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <SchoolCrest className="w-10 h-10" />
              <div>
                <span className="text-xl font-bold text-white tracking-tight block">
                  Sunrise School
                </span>
                <span className="text-xs text-slate-400 uppercase tracking-wider font-medium">
                  Lucknow • CBSE Affiliated (Estd. 2011)
                </span>
              </div>
            </div>
            <p className="text-sm text-slate-400 leading-relaxed pr-4">
              Sunrise School is a premier progressive institution dedicated to academic brilliance, moral integrity, and 21st-century experiential learning. We nurture curious minds to become empathetic, visionary global citizens.
            </p>
            <div className="pt-2">
              <span className="inline-block bg-slate-800 text-slate-300 text-xs px-3 py-1 rounded-full border border-slate-700">
                CBSE Affiliation No. 2130000 • School Code: 70000
              </span>
            </div>
          </div>

          {/* Col 2: Quick Links */}
          <div>
            <h4 className="text-white text-sm font-semibold uppercase tracking-wider mb-4 border-l-2 border-primary pl-2.5">
              Explore
            </h4>
            <ul className="space-y-2.5 text-sm">
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
                  Campus Facilities
                </Link>
              </li>
              <li>
                <Link to="/admissions" className="text-slate-400 hover:text-white transition-colors">
                  Admissions 2025–26
                </Link>
              </li>
              <li>
                <Link to="/apply" className="text-slate-400 hover:text-white transition-colors">
                  Online Application Form
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 3: Timings & School Hours */}
          <div>
            <h4 className="text-white text-sm font-semibold uppercase tracking-wider mb-4 border-l-2 border-primary pl-2.5">
              School Hours
            </h4>
            <ul className="space-y-3 text-xs text-slate-400">
              <div>
                <span className="font-semibold text-slate-200 block text-sm">Pre-Primary (Nursery - UKG)</span>
                <span>Mon – Fri: 8:30 AM – 12:30 PM</span>
              </div>
              <div>
                <span className="font-semibold text-slate-200 block text-sm">Primary & Middle (I - VIII)</span>
                <span>Mon – Sat: 7:50 AM – 1:45 PM</span>
              </div>
              <div>
                <span className="font-semibold text-slate-200 block text-sm">Senior School (IX - XII)</span>
                <span>Mon – Sat: 7:40 AM – 2:15 PM</span>
              </div>
              <div className="pt-1 text-slate-400">
                <span className="font-semibold text-slate-200 block text-sm">Administrative Office</span>
                <span>Mon – Sat: 8:00 AM – 3:30 PM</span>
                <span className="block text-slate-500">(Closed on 2nd Saturdays & Gazetted Holidays)</span>
              </div>
            </ul>
          </div>

          {/* Col 4: Contact & ERP Gateway */}
          <div>
            <h4 className="text-white text-sm font-semibold uppercase tracking-wider mb-4 border-l-2 border-primary pl-2.5">
              Contact & Portals
            </h4>
            <div className="space-y-3 text-sm text-slate-400">
              <p>
                <strong className="text-slate-200 block text-xs uppercase font-medium">Campus Address</strong>
                Sector 7, Gomti Nagar Extension, Lucknow, Uttar Pradesh 226010, India
              </p>
              <p>
                <strong className="text-slate-200 block text-xs uppercase font-medium">Phone & Email</strong>
                <span>+91 522 299 0000</span>
                <br />
                <span className="text-slate-400 text-xs">info@sunrisepublic.edu</span>
              </p>

              {/* Prominent Login to ERP in Footer */}
              <div className="pt-2">
                <Link
                  to="/login"
                  className="w-full inline-flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold px-3 py-2.5 rounded-lg border border-slate-700 hover:border-slate-600 transition-colors"
                >
                  <svg className="w-4 h-4 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <span>Staff & Admin ERP Login</span>
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Disclaimer / Demo Notice */}
        <div className="mt-12 pt-8 border-t border-slate-800/80 text-center md:text-left flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-slate-500">
            &copy; {new Date().getFullYear()} Sunrise School, Lucknow. All rights reserved. Built as a demo Indian school public portal.
          </p>
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span className="bg-slate-800 text-slate-400 px-2.5 py-1 rounded text-[11px] font-mono">
              Fictional Demo School Profile
            </span>
            <Link to="/login" className="hover:text-slate-300 transition-colors font-medium">
              Login to ERP
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
