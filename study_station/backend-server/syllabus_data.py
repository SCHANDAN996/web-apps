# syllabus_data.py
# Dictionary containing complete NCERT syllabus structure

def generate_primary_syllabus(class_num):
    return {
        "Maths": [f"Chapter {i}: " + name for i, name in enumerate(["Numbers", "Addition", "Subtraction", "Multiplication", "Division", "Time", "Money", "Measurement", "Shapes", "Patterns", "Data Handling"], 1)],
        "EVS": [f"Chapter {i}: " + name for i, name in enumerate(["My Body", "My Family", "Food We Eat", "Water", "Clothes We Wear", "Our Neighborhood", "People Who Help Us", "Plants Around Us", "Animals Around Us", "Means of Transport", "Earth and Sky"], 1)],
        "English": [f"Chapter {i}: " + name for i, name in enumerate(["The Magic Garden", "Bird Talk", "Nina and the Baby Sparrows", "The Enormous Turnip", "A Little Fish Story", "The Yellow Butterfly", "Trains", "The Story of the Road", "Puppy and I", "How Creatures Move"], 1)],
        "Hindi": [f"पाठ {i}: " + name for i, name in enumerate(["झूला", "आम की कहानी", "पत्ते ही पत्ते", "पकौड़ी", "छुक-छुक गाड़ी", "रसोईघर", "चूहो! म्याऊँ सो रही है", "बंदर और गिलहरी", "पगड़ी", "पतंग"], 1)]
    }

def generate_middle_syllabus(class_num):
    return {
        "Science": [f"Chapter {i}: " + name for i, name in enumerate(["Food: Where does it come from?", "Components of Food", "Fibre to Fabric", "Sorting Materials into Groups", "Separation of Substances", "Changes Around Us", "Getting to Know Plants", "Body Movements", "The Living Organisms and Their Surroundings", "Motion and Measurement of Distances", "Light, Shadows and Reflections", "Electricity and Circuits", "Fun with Magnets", "Water", "Air Around Us", "Garbage In, Garbage Out"], 1)],
        "Maths": [f"Chapter {i}: " + name for i, name in enumerate(["Knowing Our Numbers", "Whole Numbers", "Playing with Numbers", "Basic Geometrical Ideas", "Understanding Elementary Shapes", "Integers", "Fractions", "Decimals", "Data Handling", "Mensuration", "Algebra", "Ratio and Proportion", "Symmetry", "Practical Geometry"], 1)],
        "Social Science": [f"Chapter {i}: " + name for i, name in enumerate(["What, Where, How and When?", "On The Trail of the Earliest People", "From Gathering to Growing Food", "In the Earliest Cities", "What Books and Burials Tell Us", "Kingdoms, Kings and an Early Republic", "New Questions and Ideas", "Ashoka, The Emperor Who Gave Up War", "Vital Villages, Thriving Towns", "Traders, Kings and Pilgrims", "New Empires and Kingdoms", "Buildings, Paintings and Books"], 1)]
    }

SYLLABUS = {
    "1": generate_primary_syllabus(1),
    "2": generate_primary_syllabus(2),
    "3": generate_primary_syllabus(3),
    "4": generate_primary_syllabus(4),
    "5": generate_primary_syllabus(5),
    "6": generate_middle_syllabus(6),
    "7": generate_middle_syllabus(7),
    "8": generate_middle_syllabus(8),
    "9": {
        "Science": [
            "Matter in Our Surroundings",
            "Is Matter Around Us Pure",
            "Atoms and Molecules",
            "Structure of the Atom",
            "The Fundamental Unit of Life",
            "Tissues",
            "Motion",
            "Force and Laws of Motion",
            "Gravitation",
            "Work and Energy",
            "Sound",
            "Improvement in Food Resources"
        ],
        "Maths": [
            "Number Systems",
            "Polynomials",
            "Coordinate Geometry",
            "Linear Equations in Two Variables",
            "Introduction to Euclid's Geometry",
            "Lines and Angles",
            "Triangles",
            "Quadrilaterals",
            "Areas of Parallelograms and Triangles",
            "Circles",
            "Constructions",
            "Heron's Formula",
            "Surface Areas and Volumes",
            "Statistics",
            "Probability"
        ]
    },
    "10": {
        "Science": [
            "Chemical Reactions and Equations",
            "Acids, Bases and Salts",
            "Metals and Non-metals",
            "Carbon and its Compounds",
            "Periodic Classification of Elements",
            "Life Processes",
            "Control and Coordination",
            "How do Organisms Reproduce?",
            "Heredity and Evolution",
            "Light - Reflection and Refraction",
            "Human Eye and Colourful World",
            "Electricity",
            "Magnetic Effects of Electric Current",
            "Sources of Energy",
            "Our Environment",
            "Sustainable Management of Natural Resources"
        ],
        "Maths": [
            "Real Numbers",
            "Polynomials",
            "Pair of Linear Equations in Two Variables",
            "Quadratic Equations",
            "Arithmetic Progressions",
            "Triangles",
            "Coordinate Geometry",
            "Introduction to Trigonometry",
            "Some Applications of Trigonometry",
            "Circles",
            "Constructions",
            "Areas Related to Circles",
            "Surface Areas and Volumes",
            "Statistics",
            "Probability"
        ]
    },
    "11": {
        "Physics": [
            "Physical World",
            "Units and Measurements",
            "Motion in a Straight Line",
            "Motion in a Plane",
            "Laws of Motion",
            "Work, Energy and Power",
            "System of Particles and Rotational Motion",
            "Gravitation",
            "Mechanical Properties of Solids",
            "Mechanical Properties of Fluids",
            "Thermal Properties of Matter",
            "Thermodynamics",
            "Kinetic Theory",
            "Oscillations",
            "Waves"
        ],
        "Chemistry": [
            "Some Basic Concepts of Chemistry",
            "Structure of Atom",
            "Classification of Elements and Periodicity in Properties",
            "Chemical Bonding and Molecular Structure",
            "States of Matter",
            "Thermodynamics",
            "Equilibrium",
            "Redox Reactions",
            "Hydrogen",
            "The s-Block Elements",
            "The p-Block Elements",
            "Organic Chemistry - Some Basic Principles and Techniques",
            "Hydrocarbons",
            "Environmental Chemistry"
        ],
        "Maths": [
            "Sets",
            "Relations and Functions",
            "Trigonometric Functions",
            "Principle of Mathematical Induction",
            "Complex Numbers and Quadratic Equations",
            "Linear Inequalities",
            "Permutations and Combinations",
            "Binomial Theorem",
            "Sequences and Series",
            "Straight Lines",
            "Conic Sections",
            "Introduction to Three Dimensional Geometry",
            "Limits and Derivatives",
            "Mathematical Reasoning",
            "Statistics",
            "Probability"
        ]
    },
    "12": {
        "Physics": [
            "Electric Charges and Fields",
            "Electrostatic Potential and Capacitance",
            "Current Electricity",
            "Moving Charges and Magnetism",
            "Magnetism and Matter",
            "Electromagnetic Induction",
            "Alternating Current",
            "Electromagnetic Waves",
            "Ray Optics and Optical Instruments",
            "Wave Optics",
            "Dual Nature of Radiation and Matter",
            "Atoms",
            "Nuclei",
            "Semiconductor Electronics: Materials, Devices and Simple Circuits"
        ],
        "Chemistry": [
            "The Solid State",
            "Solutions",
            "Electrochemistry",
            "Chemical Kinetics",
            "Surface Chemistry",
            "General Principles and Processes of Isolation of Elements",
            "The p-Block Elements",
            "The d- and f-Block Elements",
            "Coordination Compounds",
            "Haloalkanes and Haloarenes",
            "Alcohols, Phenols and Ethers",
            "Aldehydes, Ketones and Carboxylic Acids",
            "Amines",
            "Biomolecules",
            "Polymers",
            "Chemistry in Everyday Life"
        ],
        "Maths": [
            "Relations and Functions",
            "Inverse Trigonometric Functions",
            "Matrices",
            "Determinants",
            "Continuity and Differentiability",
            "Application of Derivatives",
            "Integrals",
            "Application of Integrals",
            "Differential Equations",
            "Vector Algebra",
            "Three Dimensional Geometry",
            "Linear Programming",
            "Probability"
        ]
    }
}
