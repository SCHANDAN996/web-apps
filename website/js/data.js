/**
 * data.js — All demo/static data for the SPA
 */

var CLASSES_DATA = [
  { id: 1, name: 'Class 1', emoji: '1️⃣', subjects: 3 },
  { id: 2, name: 'Class 2', emoji: '2️⃣', subjects: 3 },
  { id: 3, name: 'Class 3', emoji: '3️⃣', subjects: 3 },
  { id: 4, name: 'Class 4', emoji: '4️⃣', subjects: 3 },
  { id: 5, name: 'Class 5', emoji: '5️⃣', subjects: 4 },
  { id: 6, name: 'Class 6', emoji: '6️⃣', subjects: 5 },
  { id: 7, name: 'Class 7', emoji: '7️⃣', subjects: 5 },
  { id: 8, name: 'Class 8', emoji: '8️⃣', subjects: 5 },
  { id: 9, name: 'Class 9', emoji: '9️⃣', subjects: 5 },
  { id: 10, name: 'Class 10', emoji: '🔟', subjects: 5 },
  { id: 11, name: 'Class 11', emoji: '📗', subjects: 5 },
  { id: 12, name: 'Class 12', emoji: '📘', subjects: 5 }
];

var SUBJECTS_DB = {
  10: [
    { name: 'Mathematics', icon: '📐', chapters: 15 },
    { name: 'Science', icon: '🔬', chapters: 16 },
    { name: 'English', icon: '📖', chapters: 8 },
    { name: 'Hindi', icon: '🇮🇳', chapters: 10 },
    { name: 'Social Science', icon: '🌍', chapters: 20 }
  ],
  12: [
    { name: 'Physics', icon: '⚡', chapters: 14 },
    { name: 'Chemistry', icon: '🧪', chapters: 16 },
    { name: 'Mathematics', icon: '📐', chapters: 13 },
    { name: 'English', icon: '📖', chapters: 8 },
    { name: 'Computer Science', icon: '💻', chapters: 10 }
  ]
};

var CHAPTERS_DB = {
  'Mathematics': [
    { name: 'Number System', difficulty: 'easy' },
    { name: 'Polynomials', difficulty: 'medium' },
    { name: 'Pair of Linear Equations', difficulty: 'medium' },
    { name: 'Quadratic Equations', difficulty: 'hard' },
    { name: 'Arithmetic Progressions', difficulty: 'medium' },
    { name: 'Triangles', difficulty: 'hard' },
    { name: 'Coordinate Geometry', difficulty: 'medium' },
    { name: 'Trigonometry', difficulty: 'hard' },
    { name: 'Some Applications of Trigonometry', difficulty: 'hard' },
    { name: 'Circles', difficulty: 'medium' }
  ],
  'Science': [
    { name: 'Chemical Reactions and Equations', difficulty: 'easy' },
    { name: 'Acids, Bases and Salts', difficulty: 'medium' },
    { name: 'Metals and Non-metals', difficulty: 'medium' },
    { name: 'Carbon and its Compounds', difficulty: 'hard' },
    { name: 'Periodic Classification', difficulty: 'medium' },
    { name: 'Life Processes', difficulty: 'easy' },
    { name: 'Control and Coordination', difficulty: 'medium' },
    { name: 'How do Organisms Reproduce?', difficulty: 'easy' }
  ],
  'Physics': [
    { name: 'Electric Charges and Fields', difficulty: 'hard' },
    { name: 'Electrostatic Potential', difficulty: 'hard' },
    { name: 'Current Electricity', difficulty: 'medium' },
    { name: 'Moving Charges and Magnetism', difficulty: 'hard' },
    { name: 'Magnetism and Matter', difficulty: 'medium' },
    { name: 'Electromagnetic Induction', difficulty: 'hard' },
    { name: 'Alternating Current', difficulty: 'hard' },
    { name: 'Ray Optics', difficulty: 'medium' }
  ]
};

var MCQ_DATA = [
  {
    subject: 'Mathematics',
    questions: [
      { q: 'What is the value of √144?', options: ['10', '11', '12', '13'], correct: 2, explanation: '√144 = 12, because 12 × 12 = 144.' },
      { q: 'If x + y = 10 and x - y = 4, what is x?', options: ['5', '6', '7', '8'], correct: 2, explanation: 'Adding both equations: 2x = 14, so x = 7.' },
      { q: 'What is the 10th term of AP: 2, 5, 8, 11...?', options: ['27', '29', '30', '32'], correct: 1, explanation: 'a = 2, d = 3. 10th term = a + 9d = 2 + 27 = 29.' },
      { q: 'The area of a circle with radius 7 cm is:', options: ['144 cm²', '154 cm²', '164 cm²', '174 cm²'], correct: 1, explanation: 'Area = πr² = (22/7) × 49 = 154 cm².' },
      { q: 'If sin θ = 3/5, what is cos θ?', options: ['3/5', '4/5', '2/5', '1/5'], correct: 1, explanation: 'sin²θ + cos²θ = 1. cos²θ = 1 - 9/25 = 16/25. cos θ = 4/5.' }
    ]
  },
  {
    subject: 'Science',
    questions: [
      { q: 'Which gas is released during photosynthesis?', options: ['Carbon Dioxide', 'Nitrogen', 'Oxygen', 'Hydrogen'], correct: 2, explanation: 'During photosynthesis, plants release oxygen (O₂) as a byproduct.' },
      { q: 'What is the pH of pure water?', options: ['5', '6', '7', '8'], correct: 2, explanation: 'Pure water has a neutral pH of 7 at 25°C.' },
      { q: 'The chemical formula of baking soda is:', options: ['NaOH', 'NaHCO₃', 'Na₂CO₃', 'NaCl'], correct: 1, explanation: 'Baking soda is Sodium Bicarbonate (NaHCO₃).' },
      { q: 'Which organ produces bile?', options: ['Stomach', 'Pancreas', 'Liver', 'Gallbladder'], correct: 2, explanation: 'Bile is produced by the liver and stored in the gallbladder.' },
      { q: 'The unit of electric current is:', options: ['Volt', 'Watt', 'Ampere', 'Ohm'], correct: 2, explanation: 'Electric current is measured in Amperes (A).' }
    ]
  },
  {
    subject: 'Physics',
    questions: [
      { q: 'The SI unit of force is:', options: ['Joule', 'Newton', 'Watt', 'Pascal'], correct: 1, explanation: 'Force is measured in Newtons (N). 1 N = 1 kg·m/s².' },
      { q: 'What is the speed of light in vacuum?', options: ['3 × 10⁶ m/s', '3 × 10⁸ m/s', '3 × 10¹⁰ m/s', '3 × 10¹² m/s'], correct: 1, explanation: 'Speed of light in vacuum is approximately 3 × 10⁸ m/s.' },
      { q: "Ohm's Law states that V = IR. What does R represent?", options: ['Voltage', 'Current', 'Resistance', 'Power'], correct: 2, explanation: "In Ohm's Law, R represents Resistance measured in Ohms (Ω)." },
      { q: 'Which lens is used to correct myopia?', options: ['Convex lens', 'Concave lens', 'Bifocal lens', 'Cylindrical lens'], correct: 1, explanation: 'Concave (diverging) lens is used to correct myopia (near-sightedness).' },
      { q: 'The escape velocity from Earth is approximately:', options: ['7.9 km/s', '9.8 km/s', '11.2 km/s', '15.0 km/s'], correct: 2, explanation: "Escape velocity from Earth's surface is about 11.2 km/s." }
    ]
  },
  {
    subject: 'English',
    questions: [
      { q: 'Choose the correct synonym of "Benevolent":', options: ['Cruel', 'Kind', 'Angry', 'Selfish'], correct: 1, explanation: 'Benevolent means well-meaning and kindly. The synonym is "Kind".' },
      { q: '"She ___ to school every day." Fill in the blank:', options: ['go', 'goes', 'going', 'gone'], correct: 1, explanation: 'With "she" (third person singular), we use "goes".' },
      { q: 'The antonym of "Transparent" is:', options: ['Clear', 'Opaque', 'Visible', 'Lucid'], correct: 1, explanation: 'Opaque is the opposite of transparent — light cannot pass through it.' },
      { q: 'Which figure of speech is "The wind whispered"?', options: ['Simile', 'Metaphor', 'Personification', 'Hyperbole'], correct: 2, explanation: 'Personification gives human qualities to non-human things. Wind cannot literally whisper.' },
      { q: 'Identify the tense: "They have been waiting for two hours."', options: ['Present Perfect', 'Present Continuous', 'Present Perfect Continuous', 'Past Perfect'], correct: 2, explanation: '"Have been waiting" is Present Perfect Continuous tense.' }
    ]
  },
  {
    subject: 'Chemistry',
    questions: [
      { q: 'What is the atomic number of Carbon?', options: ['4', '6', '8', '12'], correct: 1, explanation: 'Carbon has atomic number 6 (6 protons) and mass number 12.' },
      { q: 'Which is the most reactive metal?', options: ['Iron', 'Copper', 'Sodium', 'Gold'], correct: 2, explanation: 'Sodium is highly reactive and must be stored under oil.' },
      { q: 'The pH of HCl (hydrochloric acid) is:', options: ['1', '7', '10', '14'], correct: 0, explanation: 'HCl is a strong acid with pH close to 1.' },
      { q: 'What type of bond is formed in NaCl?', options: ['Covalent', 'Ionic', 'Metallic', 'Hydrogen'], correct: 1, explanation: 'NaCl forms an ionic bond through electron transfer from Na to Cl.' },
      { q: 'The molecular formula of glucose is:', options: ['C₆H₁₂O₆', 'C₁₂H₂₂O₁₁', 'C₆H₆', 'CH₄'], correct: 0, explanation: 'Glucose has the molecular formula C₆H₁₂O₆.' }
    ]
  }
];

var BOOKS_DATA = [
  { title: 'Mathematics Active Recall', subtitle: 'Class 10 • Active Recall', emoji: '📐', chapters: 15, progress: 65, type: 'active-recall' },
  { title: 'Science Feynman Guide', subtitle: 'Class 10 • Feynman Technique', emoji: '🔬', chapters: 16, progress: 40, type: 'feynman' },
  { title: 'Physics PYQ Master', subtitle: 'Class 12 • PYQ Integration', emoji: '⚡', chapters: 14, progress: 80, type: 'pyq' },
  { title: 'Chemistry Formula Book', subtitle: 'Class 12 • Formula Reference', emoji: '🧪', chapters: 16, progress: 20, type: 'formula' },
  { title: 'English Grammar Recall', subtitle: 'Class 10 • Active Recall', emoji: '📖', chapters: 10, progress: 50, type: 'active-recall' },
  { title: 'Social Science Feynman', subtitle: 'Class 10 • Feynman Technique', emoji: '🌍', chapters: 20, progress: 10, type: 'feynman' }
];

// JOBS_DATA now comes from js/jobs_data.js — auto-generated from the real
// jobs database by build_website.py. This empty fallback only applies if
// that file is missing (shows the empty state instead of fake demo jobs).
var JOBS_DATA = [];

// PYQ_DATA: demo entries removed — real papers will be exported from the
// database once genuine PDF links are added (no fake downloads).
var PYQ_DATA_DEMO_DISABLED = {
  ssc: [
    { title: 'SSC CGL 2025 (Shift 1)', exam: 'SSC CGL', year: 2025, subject: 'General Awareness + Reasoning' },
    { title: 'SSC CGL 2025 (Shift 2)', exam: 'SSC CGL', year: 2025, subject: 'Quantitative Aptitude' },
    { title: 'SSC CHSL 2025 (Tier 1)', exam: 'SSC CHSL', year: 2025, subject: 'Full Paper' },
    { title: 'SSC MTS 2025', exam: 'SSC MTS', year: 2025, subject: 'Full Paper' },
    { title: 'SSC CPO 2024', exam: 'SSC CPO', year: 2024, subject: 'Full Paper' },
    { title: 'SSC Stenographer 2024', exam: 'SSC Steno', year: 2024, subject: 'Full Paper' }
  ],
  banking: [
    { title: 'SBI PO 2025 Prelims', exam: 'SBI PO', year: 2025, subject: 'Full Paper' },
    { title: 'IBPS PO 2025 Mains', exam: 'IBPS PO', year: 2025, subject: 'Full Paper' },
    { title: 'IBPS Clerk 2025', exam: 'IBPS Clerk', year: 2025, subject: 'Full Paper' },
    { title: 'RBI Grade B 2024', exam: 'RBI Grade B', year: 2024, subject: 'Phase 1' },
    { title: 'SBI Clerk 2024', exam: 'SBI Clerk', year: 2024, subject: 'Full Paper' },
    { title: 'IBPS RRB 2024', exam: 'IBPS RRB', year: 2024, subject: 'Full Paper' }
  ],
  upsc: [
    { title: 'UPSC CSE Prelims 2025 (Set A)', exam: 'UPSC CSE', year: 2025, subject: 'General Studies Paper I' },
    { title: 'UPSC CSE Prelims 2025 (Set B)', exam: 'UPSC CSE', year: 2025, subject: 'CSAT Paper II' },
    { title: 'UPSC CSE Prelims 2024', exam: 'UPSC CSE', year: 2024, subject: 'Full Paper' },
    { title: 'UPSC CSE Mains 2024 (Essay)', exam: 'UPSC CSE', year: 2024, subject: 'Essay Paper' },
    { title: 'UPSC NDA 2025', exam: 'UPSC NDA', year: 2025, subject: 'Mathematics' },
    { title: 'UPSC CAPF 2024', exam: 'UPSC CAPF', year: 2024, subject: 'Full Paper' }
  ],
  railway: [
    { title: 'RRB NTPC 2025 (CBT 1)', exam: 'RRB NTPC', year: 2025, subject: 'Full Paper' },
    { title: 'RRB Group D 2025', exam: 'RRB Group D', year: 2025, subject: 'Full Paper' },
    { title: 'RRB ALP 2024', exam: 'RRB ALP', year: 2024, subject: 'Full Paper' },
    { title: 'RRB JE 2024', exam: 'RRB JE', year: 2024, subject: 'Full Paper' },
    { title: 'RRB SSE 2024', exam: 'RRB SSE', year: 2024, subject: 'Full Paper' },
    { title: 'RRB NTPC 2023', exam: 'RRB NTPC', year: 2023, subject: 'Full Paper' }
  ],
  state: [
    { title: 'UPPSC PCS 2025 Prelims', exam: 'UPPSC', year: 2025, subject: 'General Studies' },
    { title: 'BPSC 70th Prelims', exam: 'BPSC', year: 2025, subject: 'Full Paper' },
    { title: 'MPPSC Prelims 2025', exam: 'MPPSC', year: 2025, subject: 'Full Paper' },
    { title: 'RPSC RAS 2024', exam: 'RPSC', year: 2024, subject: 'Full Paper' },
    { title: 'TNPSC Group 1 2024', exam: 'TNPSC', year: 2024, subject: 'Full Paper' },
    { title: 'MPSC Rajyaseva 2024', exam: 'MPSC', year: 2024, subject: 'Full Paper' }
  ]
};

// Active PYQ data — empty until real question-paper PDFs are sourced.
// The PYQ page will show its "coming soon" empty state instead of fake downloads.
var PYQ_DATA = { ssc: [], banking: [], upsc: [], railway: [], state: [] };
