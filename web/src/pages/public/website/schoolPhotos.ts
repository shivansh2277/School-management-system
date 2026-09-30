/**
 * Sunrise School Master Photography Registry
 * Real, photorealistic AI-generated editorial photography captured specifically
 * for Sunrise School, Gomti Nagar, Lucknow (Estd. 2011).
 *
 * All photography strictly conforms to:
 * - Architecture: Terracotta stone & sandstone, large glass windows with louvers, lush greenery.
 * - Uniform: Crisp white collared shirts, navy blue ties with subtle gold diagonal stripes,
 *   navy trousers/skirts, school crest.
 * - Signage: Authentic campus branding for "Sunrise School, Gomti Nagar, Lucknow".
 */

export interface SchoolPhoto {
  id: string;
  title: string;
  category: "campus" | "classrooms" | "sports" | "cultural" | "celebrations";
  categoryLabel: string;
  src: string;
  alt: string;
  caption: string;
  date: string;
  location: string;
  aspectRatio?: "16:9" | "4:3" | "3:2";
}

export const SCHOOL_PHOTOS: Record<string, SchoolPhoto> = {
  heroCampus: {
    id: "hero-campus",
    title: "Sunrise School Gomti Nagar Campus",
    category: "campus",
    categoryLabel: "Campus & Architecture",
    src: "/images/school/hero_campus_exterior.jpg",
    alt: "Sunrise School Gomti Nagar modern terracotta and sandstone campus exterior",
    caption: "The flagship academic block of Sunrise School surrounded by landscaped gardens and Ashoka avenues in Gomti Nagar, Lucknow.",
    date: "Academic Year 2026–27",
    location: "Main Academic Quadrangle, Gomti Nagar",
    aspectRatio: "16:9",
  },
  entranceGate: {
    id: "entrance-gate",
    title: "Main Campus Entrance & Security Gate",
    category: "campus",
    categoryLabel: "Campus & Architecture",
    src: "/images/school/school_entrance_gate.jpg",
    alt: "Grand entrance gates of Sunrise School with manicured palm trees and 24x7 security checkpoint",
    caption: "The imposing stone-clad entrance gates of Sunrise School welcoming students, parents, and visitors each morning.",
    date: "August 2026",
    location: "Gate No. 1, Sector 4, Gomti Nagar",
    aspectRatio: "16:9",
  },
  receptionLobby: {
    id: "reception-lobby",
    title: "Administrative Reception & Welcome Lobby",
    category: "campus",
    categoryLabel: "Campus & Architecture",
    src: "/images/school/main_reception_lobby.jpg",
    alt: "Modern school reception lobby with gold crest emblem, comfortable visitor seating, and helpdesk",
    caption: "The elegant ground-floor reception rotunda where parents and visitors are welcomed by admissions staff.",
    date: "July 2026",
    location: "Ground Floor, Administrative Block",
    aspectRatio: "16:9",
  },
  modernClassroom: {
    id: "modern-classroom",
    title: "Interactive Smart Classroom",
    category: "classrooms",
    categoryLabel: "Classrooms & Labs",
    src: "/images/school/modern_classroom_learning.jpg",
    alt: "Middle school students in crisp uniform learning with an interactive digital board and teacher",
    caption: "Engaged learners collaborating in a sunlit smart classroom equipped with interactive touch panels.",
    date: "September 2026",
    location: "Block B, Middle Wing",
    aspectRatio: "16:9",
  },
  teacherMentoring: {
    id: "teacher-mentoring",
    title: "Dedicated Faculty Mentorship",
    category: "classrooms",
    categoryLabel: "Classrooms & Labs",
    src: "/images/school/teacher_mentoring_students.jpg",
    alt: "Senior school teacher mentoring students during collaborative study session",
    caption: "Personalized mentorship and attentive academic support ensuring every child develops conceptual clarity.",
    date: "August 2026",
    location: "Senior Academic Wing",
    aspectRatio: "16:9",
  },
  scienceLab: {
    id: "science-lab",
    title: "Composite Science Practical Laboratory",
    category: "classrooms",
    categoryLabel: "Classrooms & Labs",
    src: "/images/school/science_lab_practical.jpg",
    alt: "Indian high school students in white lab coats and uniform conducting chemistry and physics experiments",
    caption: "Senior secondary scholars conducting precision chemical titrations and experiments under faculty supervision.",
    date: "July 2026",
    location: "Science Complex, Floor 2",
    aspectRatio: "16:9",
  },
  computerLab: {
    id: "computer-lab",
    title: "Digital Computing & AI Laboratory",
    category: "classrooms",
    categoryLabel: "Classrooms & Labs",
    src: "/images/school/computer_lab_coding.jpg",
    alt: "Students coding on modern computer workstations in the high-tech computer lab",
    caption: "Students building software programs, exploring algorithmic logic, and developing digital fluency in our 60-seat IT suite.",
    date: "August 2026",
    location: "IT & Computing Wing",
    aspectRatio: "16:9",
  },
  stemRobotics: {
    id: "stem-robotics",
    title: "Atal Tinkering & STEM Robotics Lab",
    category: "classrooms",
    categoryLabel: "Classrooms & Labs",
    src: "/images/school/stem_robotics_activity.jpg",
    alt: "High school students collaborating on Arduino robotics kits and 3D printing in Atal Tinkering Lab",
    caption: "Hands-on engineering in the Atal Tinkering Lab, where students program microcontrollers and build automated robotic systems.",
    date: "September 2026",
    location: "Innovation Hub, Ground Floor",
    aspectRatio: "16:9",
  },
  centralLibrary: {
    id: "central-library",
    title: "Central Library & Knowledge Hub",
    category: "campus",
    categoryLabel: "Campus & Architecture",
    src: "/images/school/central_library_reading.jpg",
    alt: "Students reading quietly in the spacious wooden-shelved school library",
    caption: "Over 12,000 volumes, peaceful research carrels, and natural ambient light create an inspiring sanctuary for reading.",
    date: "August 2026",
    location: "Central Block, Level 1",
    aspectRatio: "16:9",
  },
  sportsField: {
    id: "sports-field",
    title: "Outdoor Athletic Grounds & Soccer Turf",
    category: "sports",
    categoryLabel: "Sports & Athletics",
    src: "/images/school/sports_field_athletics.jpg",
    alt: "Expansive green football field and red running track with students training in athletic sportswear",
    caption: "Lush multi-sport athletic grounds with all-weather synthetic running track and full-size soccer turf against the school backdrop.",
    date: "October 2026",
    location: "South Campus Sports Enclosure",
    aspectRatio: "16:9",
  },
  indoorArena: {
    id: "indoor-arena",
    title: "Multi-Purpose Indoor Sports Arena",
    category: "sports",
    categoryLabel: "Sports & Athletics",
    src: "/images/school/indoor_sports_arena.jpg",
    alt: "Modern indoor sports complex with hardwood flooring, badminton nets, and table tennis tables",
    caption: "State-of-the-art indoor sports arena hosting inter-house badminton tournaments, basketball, and table tennis championships.",
    date: "November 2026",
    location: "Sports Complex Building",
    aspectRatio: "16:9",
  },
  artStudio: {
    id: "art-studio",
    title: "Fine Arts & Design Studio",
    category: "cultural",
    categoryLabel: "Cultural & Arts",
    src: "/images/school/art_studio_painting.jpg",
    alt: "Students painting on wooden easels with watercolours and ceramics in sunlit art studio",
    caption: "Sun-drenched visual arts studio where learners master watercolor landscapes, sketching, and ceramic sculpture.",
    date: "August 2026",
    location: "Creative Arts Wing",
    aspectRatio: "16:9",
  },
  musicRoom: {
    id: "music-room",
    title: "Acoustic Music & Performing Arts Room",
    category: "cultural",
    categoryLabel: "Cultural & Arts",
    src: "/images/school/music_room_performing.jpg",
    alt: "Students and music teacher performing classical Indian and western instruments in acoustic room",
    caption: "Acoustically treated music suite where students harmonize classical Indian instruments, acoustic guitars, and keyboards.",
    date: "September 2026",
    location: "Cultural Pavilion",
    aspectRatio: "16:9",
  },
};

/**
 * Array of all photography items for the gallery and carousels
 */
export const ALL_SCHOOL_PHOTOS: SchoolPhoto[] = Object.values(SCHOOL_PHOTOS);
