import sys
import os
import json

base_station = r'c:\Users\Admin\Desktop\my project\study_station'
sys.path.append(os.path.join(base_station, 'books'))
import Reasoning

level = 'foundation'
config = Reasoning.LEVELS[level]
base_dir = config['base_dir'] # c:\Users\Admin\Desktop\my project\study_station\books\10th_Level\Reasoning

for folder_suffix, topic_hi, topic_en, rtype in config['chapters']:
    if folder_suffix == '03_Coding_Decoding':
        chapter_dir = os.path.join(base_dir, f'Chapter_{folder_suffix}')
        prompts_dir = os.path.join(chapter_dir, 'Prompts')
        os.makedirs(prompts_dir, exist_ok=True)
        
        intro_prompt = (
            '🚨 **सख्त निर्देश (STRICT RULE):**\n'
            '- आप जो भी सेक्शन जनरेट करें, केवल वही सामग्री दें जो किताब के लिए आवश्यक है।\n'
            '- कोई भी अतिरिक्त शब्द, संदर्भ, नमस्कार, परिचय, समापन टिप्पणी, या "यह रहा आपका उत्तर" जैसा मेटा-टेक्स्ट न लिखें।\n'
            '- आउटपुट सीधे किताब में चिपकाने लायक होना चाहिए — बिना एक भी अनावश्यक शब्द के।\n'
            '- इस नियम का पालन हर प्रतिक्रिया में सख्ती से करें।\n\n'
            '--------------------------------------------\n\n'
            f'👉 आज हम "स्टडी स्टेशन" नाम की एक हिंदी-अंग्रेजी द्विभाषी पुस्तक शृंखला का Foundation (10वीं) स्तर का अध्याय तैयार कर रहे हैं।\n'
            'यह तर्कशक्ति (Reasoning) की पुस्तक है, जो SSC, Banking, Railway, UPSC जैसी प्रतियोगी परीक्षाओं के लिए है।\n'
            f'इस सत्र में अध्याय: **"{topic_hi} / {topic_en}"** ({rtype} Reasoning) ।\n\n'
            'अध्याय 8 खंडों में बनेगा:\n'
            '1. 📖 Content (मुख्य सामग्री + परीक्षक का जाल बॉक्स)\n'
            '2. 📋 Important Rules & Approaches (नियम, समय नियम, सूत्र)\n'
            '3. 🧒 Feynman (फेनमैन तकनीक + ब्लर्टिंग शीट)\n'
            '4. 🗺️ Mind Map\n'
            '5. 🃏 Flashcards (15-20, परीक्षक के जाल वाले प्रश्न सहित)\n'
            '6. 📊 PYQ विश्लेषण (समय नियम की समीक्षा के साथ)\n'
            '7. 🪄 Short Tricks + Skip Strategy\n'
            '8. 📝 Practice (150 MCQs, 6 सेट, परीक्षक के जाल वाले प्रश्न सहित)\n\n'
            '➡️ मैं अब बारी-बारी से सेक्शन माँगूँगा। कृपया हर बार केवल वही खंड generate करें और पूरी quality बनाए रखें।'
        )
        with open(os.path.join(prompts_dir, 'Chapter_Intro_Prompt.txt'), 'w', encoding='utf-8') as f:
            f.write(intro_prompt)

        content_hi, content_en = Reasoning.create_prompts_content(topic_hi, topic_en, level, rtype)
        with open(os.path.join(prompts_dir, 'Content_hi.txt'), 'w', encoding='utf-8') as f: f.write(content_hi)
        with open(os.path.join(prompts_dir, 'Content_en.txt'), 'w', encoding='utf-8') as f: f.write(content_en)

        rules_hi, rules_en = Reasoning.create_prompts_rules(topic_hi, topic_en, level, rtype)
        with open(os.path.join(prompts_dir, 'Important_Rules_hi.txt'), 'w', encoding='utf-8') as f: f.write(rules_hi)
        with open(os.path.join(prompts_dir, 'Important_Rules_en.txt'), 'w', encoding='utf-8') as f: f.write(rules_en)

        feynman_hi, feynman_en = Reasoning.create_prompts_feynman(topic_hi, topic_en, level, rtype)
        with open(os.path.join(prompts_dir, 'Feynman_hi.txt'), 'w', encoding='utf-8') as f: f.write(feynman_hi)
        with open(os.path.join(prompts_dir, 'Feynman_en.txt'), 'w', encoding='utf-8') as f: f.write(feynman_en)

        mindmap = Reasoning.create_prompts_mindmap(topic_en, level, rtype)
        with open(os.path.join(prompts_dir, 'Mind_Map.txt'), 'w', encoding='utf-8') as f: f.write(mindmap)

        flash_hi, flash_en = Reasoning.create_prompts_flashcards(topic_hi, topic_en, level, rtype)
        with open(os.path.join(prompts_dir, 'Flashcards_hi.txt'), 'w', encoding='utf-8') as f: f.write(flash_hi)
        with open(os.path.join(prompts_dir, 'Flashcards_en.txt'), 'w', encoding='utf-8') as f: f.write(flash_en)

        pyq_hi, pyq_en = Reasoning.create_prompts_pyq(topic_hi, topic_en, level, rtype)
        with open(os.path.join(prompts_dir, 'PYQ_hi.txt'), 'w', encoding='utf-8') as f: f.write(pyq_hi)
        with open(os.path.join(prompts_dir, 'PYQ_en.txt'), 'w', encoding='utf-8') as f: f.write(pyq_en)

        tricks_hi, tricks_en = Reasoning.create_prompts_short_tricks(topic_hi, topic_en, level, rtype)
        with open(os.path.join(prompts_dir, 'Short_Tricks_hi.txt'), 'w', encoding='utf-8') as f: f.write(tricks_hi)
        with open(os.path.join(prompts_dir, 'Short_Tricks_en.txt'), 'w', encoding='utf-8') as f: f.write(tricks_en)

        for set_num in range(1, 7):
            start_q = (set_num - 1) * 25 + 1
            end_q = set_num * 25
            diff_hi = Reasoning.get_practice_difficulty_instruction(set_num, 'hi')
            diff_en = Reasoning.get_practice_difficulty_instruction(set_num, 'en')

            practice_hi = (
                f'# Chapter: {topic_hi}, Level: {level}, Set: {set_num}/6, Type: {rtype} Reasoning\n\n'
                f'@content_agent +mcq_generator_bilingual lang=hi level={level} '
                f'\'{topic_hi}\' के लिए 25 बहुविकल्पीय प्रश्न (MCQs) तैयार करो। '
                f'यह सेट {set_num} है (कुल 6 सेट, 150 प्रश्न)। प्रश्न संख्या {start_q} से {end_q} तक। '
                f'{diff_hi} '
                'हर प्रश्न में 4 विकल्प, सही उत्तर, चरण-दर-चरण हल, और स्रोत (परीक्षा का नाम/वर्ष) ज़रूर दो। '
                'कम से कम 2 प्रश्नों में \'परीक्षक का जाल\' (जैसे दोहरे संबंध, भ्रामक विकल्प) शामिल करो।'
            )
            practice_en = (
                f'# Chapter: {topic_en}, Level: {level}, Set: {set_num}/6, Type: {rtype} Reasoning\n\n'
                f'@content_agent +mcq_generator_bilingual lang=en level={level} '
                f'\'Generate 25 MCQs for {topic_en}. '
                f'This is Set {set_num} (total 6 sets, 150 questions). Questions numbered {start_q} to {end_q}. '
                f'{diff_en} '
                'Each with 4 options, correct answer, step-by-step solution, and source (exam name/year). '
                'Include at least 2 questions with an examiner\'s trap (e.g., double relationship, misleading options).\''
            )
            with open(os.path.join(prompts_dir, f'Practice_hi_Set_{set_num:02d}.txt'), 'w', encoding='utf-8') as f:
                f.write(practice_hi)
            with open(os.path.join(prompts_dir, f'Practice_en_Set_{set_num:02d}.txt'), 'w', encoding='utf-8') as f:
                f.write(practice_en)
        print('Regenerated Chapter 3 prompts!')

# Remove completed entries from JSON
log_path = os.path.join(base_station, 'books', 'book_automation_progress.json')
if os.path.exists(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        log = json.load(f)
    
    new_paths = []
    removed_count = 0
    for p in log.get('completed_paths', []):
        # We need to make sure we only remove chapter 03
        if 'Chapter_03_Coding_Decoding' not in p.replace('\\', '/'):
            new_paths.append(p)
        else:
            removed_count += 1
            
    log['completed_paths'] = new_paths
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=4)
    print(f'Removed {removed_count} entries from progress log for Chapter 3.')
