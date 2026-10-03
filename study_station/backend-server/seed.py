import os
from app import app
from models import db, StudyContent, PracticeQuestion, JobAlert
from datetime import datetime, timedelta

def seed_database():
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        print("Creating seed data...")

        # Study Content - NCERT Class 10 Science
        notes1 = StudyContent(
            title="Chemical Reactions and Equations",
            description="Complete NCERT Chapter 1 Notes (Balancing, Types of Reactions)",
            category="NOTES",
            class_level=10,
            board="CBSE",
            subject="Science",
            subject_icon="🔬",
            chapter_number=1,
            chapter_name="Chemical Reactions",
            content_text="# Chapter 1: Chemical Reactions and Equations\n\n## 1. Physical vs Chemical Changes\n* **Physical Change:** A change where no new substance is formed. (e.g., melting of ice)\n* **Chemical Change:** A change where a new substance with different properties is formed. (e.g., rusting of iron)\n\n## 2. What is a Chemical Equation?\nA chemical equation is the symbolic representation of a chemical reaction in the form of symbols and formulae.\nExample: Magnesium + Oxygen → Magnesium oxide\n**Mg + O₂ → MgO**\n\n### Balancing a Chemical Equation\nAccording to the Law of Conservation of Mass, mass can neither be created nor destroyed in a chemical reaction. Therefore, the number of atoms of each element must be equal on both sides of the equation.\n**Balanced Equation:** 2Mg + O₂ → 2MgO\n\n## 3. Types of Chemical Reactions\n1. **Combination Reaction:** Two or more substances combine to form a single product. (A + B → AB)\n2. **Decomposition Reaction:** A single reactant breaks down to form two or more simpler products. (AB → A + B)\n3. **Displacement Reaction:** A more reactive element displaces a less reactive element from its compound. (A + BC → AC + B)\n4. **Double Displacement Reaction:** An exchange of ions takes place between the reactants. (AB + CD → AD + CB)\n\n## 4. Oxidation and Reduction\n* **Oxidation:** The addition of oxygen or removal of hydrogen.\n* **Reduction:** The addition of hydrogen or removal of oxygen.\n\n*Study Tip: Remember OIL RIG (Oxidation is Loss of electrons, Reduction is Gain of electrons).* \n\n## 5. Everyday Examples of Oxidation\n* **Corrosion:** The process of slow decay of a metal due to attack by air, moisture, or acids. Example: Rusting of Iron (Fe₂O₃.xH₂O).\n* **Rancidity:** The oxidation of fats and oils when kept in the open for a long time, causing bad smell and bad taste.",
            difficulty="MEDIUM"
        )
        
        notes2 = StudyContent(
            title="Life Processes",
            description="Nutrition, Respiration, Transportation, and Excretion",
            category="NOTES",
            class_level=10,
            board="CBSE",
            subject="Science",
            subject_icon="🌱",
            chapter_number=6,
            chapter_name="Life Processes",
            content_text="# Chapter 6: Life Processes\n\n## Introduction\nThe basic functions performed by living organisms to maintain their life on earth are called life processes. The fundamental life processes are Nutrition, Respiration, Transportation, and Excretion.\n\n## 1. Nutrition\nThe process by which an organism takes food and utilizes it is called nutrition.\n* **Autotrophic Nutrition:** Organisms synthesize their own food (e.g., Green plants using Photosynthesis).\n* **Heterotrophic Nutrition:** Organisms depend on others for food (e.g., Animals, Fungi).\n\n### Photosynthesis\nThe process by which green plants make their own food from carbon dioxide and water in the presence of sunlight and chlorophyll.\n**Equation:** 6CO₂ + 12H₂O + Sunlight → C₆H₁₂O₆ + 6O₂ + 6H₂O\n\n## 2. Respiration\nThe process of releasing energy from food is called respiration.\n* **Aerobic Respiration:** Takes place in the presence of oxygen. Produces more energy (38 ATP). End products are CO₂ and water.\n* **Anaerobic Respiration:** Takes place in the absence of oxygen. Produces less energy (2 ATP). End products are Ethanol/Lactic acid and CO₂.\n\n## 3. Transportation\n### Human Circulatory System\n* **Heart:** A muscular organ that pumps blood to all parts of the body.\n* **Blood Vessels:** Arteries (carry pure blood away from heart), Veins (carry impure blood to heart), Capillaries.\n* **Blood:** Contains Plasma, RBCs (carry Oxygen), WBCs (fight disease), and Platelets (clotting).\n\n## 4. Excretion\nThe biological process involved in the removal of harmful metabolic wastes from the body.\n* The human excretory system consists of a pair of kidneys, a pair of ureters, a urinary bladder, and a urethra.\n* **Nephron:** The basic filtration unit of the kidney.",
            difficulty="HARD"
        )

        notes3 = StudyContent(
            title="Real Numbers",
            description="Important formulas, theorems, and concepts",
            category="NOTES",
            class_level=10,
            board="CBSE",
            subject="Maths",
            subject_icon="📐",
            chapter_number=1,
            chapter_name="Real Numbers",
            content_text="# Chapter 1: Real Numbers\n\n## 1. Fundamental Theorem of Arithmetic\nEvery composite number can be expressed (factorised) as a product of primes, and this factorisation is unique, apart from the order in which the prime factors occur.\n\n**Application:** Used to find HCF and LCM of numbers.\n* **HCF (Highest Common Factor):** Product of the smallest power of each common prime factor in the numbers.\n* **LCM (Least Common Multiple):** Product of the greatest power of each prime factor, involved in the numbers.\n\n**Important Formula:** For any two positive integers a and b,\n`HCF(a, b) × LCM(a, b) = a × b`\n\n## 2. Irrational Numbers\nA number is called irrational if it cannot be written in the form p/q, where p and q are integers and q ≠ 0. Examples: √2, √3, π.\n\n**Theorem Proof Concept:** To prove that √2 is irrational, we use the method of contradiction. We assume √2 is rational (p/q), square both sides, and show that p and q share a common factor other than 1, contradicting our initial assumption.\n\n## 3. Rational Numbers and their Decimal Expansions\nLet x = p/q be a rational number, such that the prime factorisation of q is of the form 2ⁿ5ᵐ, where n, m are non-negative integers. Then x has a decimal expansion which terminates.\n* If the prime factorization of q contains any prime other than 2 or 5, the decimal expansion is **non-terminating repeating**.",
            difficulty="EASY"
        )

        db.session.add(notes1)
        db.session.add(notes2)
        db.session.add(notes3)

        # Practice Questions - Science
        q1 = PracticeQuestion(
            question_text="What is the chemical formula of rust?",
            option_a="Fe2O3",
            option_b="Fe3O4",
            option_c="Fe2O3.xH2O",
            option_d="FeO",
            correct_answer="C",
            explanation="Rust is hydrated iron(III) oxide. The 'x' represents a variable number of water molecules.",
            subject="Science",
            chapter="Chemical Reactions",
            exam_name="Class 10 Board Exam",
            year=2024
        )

        q2 = PracticeQuestion(
            question_text="Which of the following is a balanced chemical equation?",
            option_a="H2 + O2 → H2O",
            option_b="Mg + O2 → MgO",
            option_c="2H2 + O2 → 2H2O",
            option_d="Na + Cl2 → NaCl",
            correct_answer="C",
            explanation="In 2H2 + O2 → 2H2O, there are 4 Hydrogen and 2 Oxygen atoms on both the reactant and product sides.",
            subject="Science",
            chapter="Chemical Reactions",
            exam_name="Class 10 Board Exam",
            year=2024
        )

        q3 = PracticeQuestion(
            question_text="Where does aerobic respiration occur in a cell?",
            option_a="Mitochondria",
            option_b="Nucleus",
            option_c="Ribosome",
            option_d="Golgi apparatus",
            correct_answer="A",
            explanation="Aerobic respiration (which requires oxygen) occurs in the mitochondria, known as the powerhouse of the cell.",
            subject="Science",
            chapter="Life Processes",
            exam_name="Class 10 Board Exam",
            year=2024
        )

        # Practice Questions - Maths
        q4 = PracticeQuestion(
            question_text="If HCF(306, 657) = 9, what is the LCM(306, 657)?",
            option_a="22338",
            option_b="22340",
            option_c="18338",
            option_d="18000",
            correct_answer="A",
            explanation="We know that HCF × LCM = Product of numbers. Therefore, LCM = (306 × 657) / 9 = 22338.",
            subject="Maths",
            chapter="Real Numbers",
            exam_name="Class 10 Board Exam",
            year=2024
        )

        db.session.add(q1)
        db.session.add(q2)
        db.session.add(q3)
        db.session.add(q4)

        # Job Alerts
        job1 = JobAlert(
            title="SSC CGL Notification 2024",
            organization="Staff Selection Commission",
            post_name="Inspector, Assistant",
            vacancies="7500+",
            eligibility="Graduation in any stream",
            last_date="05-05-2024",
            application_url="https://ssc.nic.in",
            category="GOVT"
        )

        job2 = JobAlert(
            title="IBPS PO Recruitment",
            organization="Institute of Banking Personnel Selection",
            post_name="Probationary Officer",
            vacancies="3000+",
            eligibility="Graduation, Age 20-30",
            last_date="15-05-2024",
            application_url="https://ibps.in",
            category="BANKING"
        )

        db.session.add(job1)
        db.session.add(job2)

        db.session.commit()
        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
