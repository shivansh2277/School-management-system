export function SchoolCrest({ className = "w-10 h-10" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Outer shield / soft rounded container */}
      <rect width="48" height="48" rx="12" fill="url(#crest-gradient)" />
      
      {/* Decorative inner border */}
      <rect
        x="2"
        y="2"
        width="44"
        height="44"
        rx="10"
        stroke="#ffffff"
        strokeOpacity="0.25"
        strokeWidth="1.5"
      />

      {/* Sun Rays */}
      <path
        d="M24 10V13M16 13.5L18 16M32 13.5L30 16M11.5 20L14.5 21.5M36.5 20L33.5 21.5"
        stroke="#FDE047"
        strokeWidth="1.75"
        strokeLinecap="round"
      />

      {/* Rising Sun Semi-circle */}
      <circle cx="24" cy="23" r="6" fill="#FACC15" />

      {/* Open Book Base */}
      <path
        d="M13 32C17 30 22 30.5 24 33C26 30.5 31 30 35 32V25C31 23 26 23.5 24 26C22 23.5 17 23 13 25V32Z"
        fill="#FFFFFF"
        fillOpacity="0.95"
      />
      {/* Book Spine */}
      <path
        d="M24 26V33"
        stroke="#4338CA"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      {/* Book Pages Detail Lines */}
      <path
        d="M16 27.5C18.5 26.5 21 27 22.5 28M32 27.5C29.5 26.5 27 27 25.5 28"
        stroke="#93C5FD"
        strokeWidth="1"
        strokeLinecap="round"
      />

      <defs>
        <linearGradient id="crest-gradient" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
          <stop stopColor="#4F46E5" />
          <stop offset="1" stopColor="#1E1B4B" />
        </linearGradient>
      </defs>
    </svg>
  );
}
