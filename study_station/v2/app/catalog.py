"""
Reference data: subjects, topics and exam patterns.

Exam patterns are taken from recent official notifications. Patterns change —
every exam page tells students to confirm with the latest notification, and
PATTERN_CHECKED says when this file was last compared against them.
"""
PATTERN_CHECKED = '2026-10'

SUBJECTS = [
    # slug, hindi, english
    ('quant', 'गणित', 'Quantitative Aptitude'),
    ('reasoning', 'तर्कशक्ति', 'Reasoning'),
    ('ga', 'सामान्य ज्ञान', 'General Awareness'),
    ('english', 'अंग्रेज़ी', 'English'),
    ('science', 'सामान्य विज्ञान', 'General Science'),
]

TOPICS = {
    'quant': [
        ('number-system', 'संख्या पद्धति', 'Number System'),
        ('lcm-hcf', 'लघुत्तम-महत्तम (LCM-HCF)', 'LCM & HCF'),
        ('simplification', 'सरलीकरण', 'Simplification'),
        ('fractions-decimals', 'भिन्न और दशमलव', 'Fractions & Decimals'),
        ('percentage', 'प्रतिशत', 'Percentage'),
        ('average', 'औसत', 'Average'),
        ('ratio-proportion', 'अनुपात और समानुपात', 'Ratio & Proportion'),
        ('profit-loss', 'लाभ और हानि', 'Profit & Loss'),
        ('simple-interest', 'साधारण ब्याज', 'Simple Interest'),
        ('compound-interest', 'चक्रवृद्धि ब्याज', 'Compound Interest'),
        ('time-work', 'समय और कार्य', 'Time & Work'),
        ('time-distance', 'समय, चाल और दूरी', 'Time, Speed & Distance'),
        ('mixture-alligation', 'मिश्रण और एलिगेशन', 'Mixture & Alligation'),
        ('mensuration', 'क्षेत्रमिति', 'Mensuration'),
        ('geometry', 'ज्यामिति', 'Geometry'),
        ('algebra', 'बीजगणित', 'Algebra'),
        ('trigonometry', 'त्रिकोणमिति', 'Trigonometry'),
        ('data-interpretation', 'आँकड़ों की व्याख्या (DI)', 'Data Interpretation'),
        ('statistics', 'सांख्यिकी', 'Statistics'),
        ('number-series', 'संख्या श्रृंखला', 'Number Series'),
        ('probability', 'प्रायिकता', 'Probability'),
        ('permutation-combination', 'क्रमचय और संचय', 'Permutation & Combination'),
        ('quadratic-equations', 'द्विघात समीकरण', 'Quadratic Equations'),
    ],
    'reasoning': [
        ('analogy', 'सादृश्यता', 'Analogy'),
        ('classification', 'वर्गीकरण', 'Classification'),
        ('coding-decoding', 'कोडिंग-डिकोडिंग', 'Coding-Decoding'),
        ('blood-relations', 'रक्त संबंध', 'Blood Relations'),
        ('direction-sense', 'दिशा ज्ञान', 'Direction Sense'),
        ('order-ranking', 'क्रम और रैंकिंग', 'Order & Ranking'),
        ('sitting-arrangement', 'बैठक व्यवस्था', 'Sitting Arrangement'),
        ('puzzles-basic', 'पहेलियाँ', 'Puzzles'),
        ('venn-diagrams', 'वेन आरेख', 'Venn Diagrams'),
        ('clock-calendar', 'घड़ी और कैलेंडर', 'Clock & Calendar'),
        ('series', 'श्रृंखला', 'Series'),
        ('missing-term', 'लुप्त पद', 'Missing Term'),
        ('dictionary-order', 'शब्दकोश क्रम', 'Dictionary Order'),
        ('alphabet-questions', 'वर्णमाला प्रश्न', 'Alphabet Questions'),
        ('mathematical-operations', 'गणितीय संक्रियाएँ', 'Mathematical Operations'),
        ('statement-conclusion', 'कथन और निष्कर्ष', 'Statement & Conclusion'),
        ('course-of-action', 'कार्यवाही', 'Course of Action'),
        ('inequality', 'असमानता', 'Inequality'),
        ('cubes-dice', 'घन और पासा', 'Cubes & Dice'),
        ('mirror-water-images', 'दर्पण और जल प्रतिबिंब', 'Mirror & Water Images'),
        ('paper-folding-cutting', 'कागज़ मोड़ना और काटना', 'Paper Folding & Cutting'),
        ('figure-series', 'आकृति श्रृंखला', 'Figure Series'),
    ],
    'ga': [
        ('ancient-history', 'प्राचीन इतिहास', 'Ancient History'),
        ('medieval-history', 'मध्यकालीन इतिहास', 'Medieval History'),
        ('modern-history', 'आधुनिक इतिहास', 'Modern History'),
        ('constitution-basic', 'संविधान की मूल बातें', 'Constitution Basics'),
        ('polity', 'राजव्यवस्था', 'Polity'),
        ('physical-geography', 'भौतिक भूगोल', 'Physical Geography'),
    ],
    'english': [
        ('noun', 'संज्ञा (Noun)', 'Noun'),
    ],
    'science': [],
}

# slug, body, hindi, english, stage, level, minutes, [(subject, n, marks, negative)], note_hi, note_en
EXAMS = [
    ('ssc-gd', 'SSC', 'SSC GD कांस्टेबल', 'SSC GD Constable', 'CBT', '10th', 60,
     [('reasoning', 20, 2, 0.25), ('ga', 20, 2, 0.25), ('quant', 20, 2, 0.25), ('english', 20, 2, 0.25)],
     'चौथा भाग English या हिंदी में से एक चुनना होता है।',
     'Part D is English or Hindi — candidate chooses one.'),
    ('ssc-mts', 'SSC', 'SSC MTS / हवलदार', 'SSC MTS & Havaldar', 'CBT (Session I + II)', '10th', 90,
     [('quant', 20, 3, 0), ('reasoning', 20, 3, 0), ('ga', 25, 3, 1), ('english', 25, 3, 1)],
     'Session I (गणित, तर्कशक्ति) में negative marking नहीं; Session II में हर गलत उत्तर पर 1 अंक कटता है।',
     'No negative marking in Session I (Maths, Reasoning); 1 mark deducted per wrong answer in Session II.'),
    ('rrb-group-d', 'RRB', 'रेलवे ग्रुप D', 'RRB Group D', 'CBT', '10th', 90,
     [('quant', 25, 1, 1 / 3), ('reasoning', 30, 1, 1 / 3), ('science', 25, 1, 1 / 3), ('ga', 20, 1, 1 / 3)],
     '', ''),
    ('ssc-chsl', 'SSC', 'SSC CHSL', 'SSC CHSL', 'Tier-I (CBT)', '12th', 60,
     [('english', 25, 2, 0.5), ('reasoning', 25, 2, 0.5), ('quant', 25, 2, 0.5), ('ga', 25, 2, 0.5)],
     '', ''),
    ('rrb-ntpc', 'RRB', 'रेलवे NTPC', 'RRB NTPC', 'CBT-1', '12th', 90,
     [('ga', 40, 1, 1 / 3), ('quant', 30, 1, 1 / 3), ('reasoning', 30, 1, 1 / 3)],
     'Graduate और Undergraduate दोनों पदों के लिए CBT-1 का pattern एक जैसा है।',
     'CBT-1 pattern is the same for graduate and undergraduate posts.'),
    ('ssc-cgl', 'SSC', 'SSC CGL', 'SSC CGL', 'Tier-I (CBT)', 'graduate', 60,
     [('reasoning', 25, 2, 0.5), ('ga', 25, 2, 0.5), ('quant', 25, 2, 0.5), ('english', 25, 2, 0.5)],
     '', ''),
    ('ibps-clerk', 'IBPS', 'IBPS क्लर्क', 'IBPS Clerk', 'Prelims', 'graduate', 60,
     [('english', 30, 1, 0.25), ('quant', 35, 1, 0.25), ('reasoning', 35, 1, 0.25)],
     'हर section का अलग समय (लगभग 20 मिनट) होता है।',
     'Each section has its own time limit (about 20 minutes).'),
    ('ibps-po', 'IBPS', 'IBPS PO', 'IBPS PO', 'Prelims', 'graduate', 60,
     [('english', 30, 1, 0.25), ('quant', 35, 1, 0.25), ('reasoning', 35, 1, 0.25)],
     'हर section का अलग समय (लगभग 20 मिनट) होता है।',
     'Each section has its own time limit (about 20 minutes).'),
]

LEVELS = [
    ('10th', '10वीं पास', '10th pass'),
    ('12th', '12वीं पास', '12th pass'),
    ('graduate', 'स्नातक', 'Graduate'),
]

LEVEL_RANK = {'10th': 1, '12th': 2, 'graduate': 3}
