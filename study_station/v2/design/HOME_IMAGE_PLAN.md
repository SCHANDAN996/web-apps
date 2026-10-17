# Home image placement

The first section is a two-column learning sequence: read a chapter, practise, revise, then current affairs. Each card has one small local illustration and a text label. The reading card preserves the last-chapter continuation link. Real practice and revision counts remain visible.

The next two-column group opens mock tests, the complete question bank, jobs and progress. These illustrations load lazily. Existing exam choices, weak-topic results, quick practice and current job links stay below these navigation groups; they use text and real data rather than repeated images.

No image belongs in the goal ring, every question, the book paragraphs, score charts or individual job notices: text and data carry their meaning there. Images are decorative with empty alt text, fixed dimensions and visible adjacent labels. SVGs are local, dependency-free and under 1 KB each, with no animation or remote fetches. Burgundy, warm paper and muted gold match the selected SS logo; UI surfaces and text retain the existing light/dark/paper theme tokens. Two equal columns use minmax(0, 1fr), wrapping labels and full-card touch targets. Reading continuation titles are limited visually to two lines while the accessible text remains complete.

Assets: app/static/illustrations/{read,practice,revise,news,mock,questions,jobs,progress}.svg

APK packaging and production deployment are handled separately after UI verification.
