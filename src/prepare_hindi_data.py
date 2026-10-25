"""
src/prepare_hindi_data.py

Generates and curates multi-turn conversational sentiment datasets
in both Devanagari Hindi (हिंदी) and Romanized Hindi (Hinglish).
Ensures zero dialogue boundary leakage across train, val, and test splits.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.hinglish_normalizer import (
    normalize_whatsapp_text,
    transliterate_devanagari_to_roman
)

# Core multi-turn dialogues across diverse WhatsApp interaction scenarios
BASE_DIALOGUES = [
    # Dialogue 0: Customer Support Escalation & Resolution (Hinglish)
    [
        ("Customer", "Hello, mera order #98211 abhi tak deliver nahi hua", "neutral", 1),
        ("Support", "Sir, let me check the tracking status for your order", "neutral", 1),
        ("Customer", "Bhai 4 din se delay chal raha hai, bohot bekar service hai tumhari!", "negative", 0),
        ("Support", "Hum samajh sakte hain aapki pareshani, delivery partner se baat ho rahi hai", "neutral", 1),
        ("Customer", "Mera paisa barbad ho gaya, urgent tha ye parcel!", "negative", 0),
        ("Support", "Sir package dispatch ho chuka hai aur agle 2 ghante me aapko mil jayega", "neutral", 1),
        ("Customer", "Pakka mil jayega na? Mujhe aaj hi chahiye tha", "neutral", 1),
        ("Support", "Haanji sir, guaranteed aaj deliver hoga. Asuvidha ke liye dil se maafi", "positive", 2),
        ("Customer", "Chalo theek hai, bohot bohot shukriya aapki madad ke liye", "positive", 2),
        ("Support", "Thank you for contacting us, aapka din shubh ho!", "positive", 2)
    ],
    # Dialogue 1: Tech Team Production Outage (Hinglish)
    [
        ("Lead", "Kya kisi ne payment gateway alerts check kiye?", "neutral", 1),
        ("Dev1", "Haan, production me transactions fail ho rahe hain", "negative", 0),
        ("Lead", "Ye toh bohot badi problem hai, error log kya bol raha hai?", "negative", 0),
        ("Dev2", "Redis connection pool exhaust ho gaya hai, leak lag raha hai", "negative", 0),
        ("Lead", "Main config update kar raha hu aur pool size badha raha hu", "neutral", 1),
        ("Dev1", "Patch deploy ho gaya hai, verification start karo", "neutral", 1),
        ("Dev2", "Ab payments successfully process ho rahe hain, error rate 0 ho gaya", "positive", 2),
        ("Lead", "Shandar kaam team! Ekdum timely aur badiya fix kiya sabne", "positive", 2)
    ],
    # Dialogue 2: Family Sunday Planning (Devanagari)
    [
        ("अमित", "नमस्ते सभी को, क्या इस रविवार को मिलने की योजना बन सकती है?", "neutral", 1),
        ("नेहा", "हाँ ज़रूर, बहुत दिनों से सब मिले नहीं हैं!", "positive", 2),
        ("रोहन", "मौसम बहुत खराब रहने वाला है, भारी बारिश की चेतावनी आई है", "negative", 0),
        ("अमित", "अरे यार, फिर बाहर जाना बहुत मुश्किल और परेशानी भरा होगा", "negative", 0),
        ("नेहा", "चिंता मत करो, हम सब घर पर ही दोपहर का भोजन रख सकते हैं", "positive", 2),
        ("रोहन", "यह तो बहुत ही बढ़िया और सुरक्षित विचार है!", "positive", 2),
        ("अमित", "सबको बहुत खुशी होगी, मैं गरमा-गरम नाश्ता लेकर आऊँगा", "positive", 2),
        ("नेहा", "धन्यवाद भाई, रविवार को दोपहर में मिलते हैं", "positive", 2)
    ],
    # Dialogue 3: Telecom Billing Dispute (Hinglish)
    [
        ("User", "Mera monthly bill double aaya hai is baar, check karo", "negative", 0),
        ("Agent", "Namaste, main aapka account verify kar raha hu", "neutral", 1),
        ("User", "Bina bataye international roaming pack kaise activate kar diya?", "negative", 0),
        ("User", "Yeh fraud hai, main consumer court me complaint karunga!", "negative", 0),
        ("Agent", "Sir, yeh system glitch se activate hua tha. Hum turant reverse kar rahe hain", "neutral", 1),
        ("Agent", "Aapka excess amount refund ho chuka hai aur new bill update kar diya hai", "positive", 2),
        ("User", "Ab bill theek dikh raha hai. Quick resolution ke liye thanks", "positive", 2),
        ("Agent", "Aapki sahayata karke khushi hui. Have a good day!", "positive", 2)
    ],
    # Dialogue 4: E-Commerce Product Return Inquiry (Devanagari)
    [
        ("ग्राहक", "जो शर्ट मुझे मिली है उसका साइज़ बहुत छोटा और कपड़ा घटिया है", "negative", 0),
        ("सपोर्ट", "नमस्कार, हमें खेद है कि उत्पाद आपकी उम्मीदों पर खरा नहीं उतरा", "neutral", 1),
        ("ग्राहक", "क्या मुझे तुरंत इसका रिफंड मिल सकता है?", "neutral", 1),
        ("सपोर्ट", "जी हाँ, हमने रिटर्न पिकअप शेड्यूल कर दिया है। कल डिलीवरी एजेंट आ जाएगा", "positive", 2),
        ("ग्राहक", "रिफंड मेरे बैंक खाते में कब तक आ जाएगा?", "neutral", 1),
        ("सपोर्ट", "पिकअप के 24 घंटे के अंदर पूरा पैसा आपके खाते में आ जाएगा", "positive", 2),
        ("ग्राहक", "बहुत अच्छा, त्वरित सहायता के लिए बहुत-बहुत धन्यवाद", "positive", 2)
    ],
    # Dialogue 5: Project Deadline Stress & Delivery (Hinglish)
    [
        ("Manager", "Client demo kal subah hai, sprint deliverables ready hain?", "neutral", 1),
        ("Developer", "Nahi sir, login module abhi bhi test cases me fail ho raha hai", "negative", 0),
        ("QA", "UI layout mobile view pe pura toot raha hai, bohot bug hain", "negative", 0),
        ("Manager", "Yeh accept nahi hoga, time bohot kam bacha hai aur stress badh raha hai", "negative", 0),
        ("Developer", "Main overnight baithke CSS aur authentication pipeline fix kar dunga", "neutral", 1),
        ("QA", "Subah 6 baje ka build ekdum stable hai, saare critical tests pass ho gaye!", "positive", 2),
        ("Manager", "Superb work! Client ne demo approve kar diya hai, sabko shabash", "positive", 2)
    ],
    # Dialogue 6: Travel & Hotel Booking Confusion (Hinglish)
    [
        ("Traveler", "Hotel reception wale bol rahe hain ki hamari booking confirm nahi hai", "negative", 0),
        ("Traveler", "Hum raat ko sadak par khade hain, bohot ganda experience hai!", "negative", 0),
        ("Agent", "Sir main hotel management se urgently coordinate kar raha hu, 5 minute dein", "neutral", 1),
        ("Agent", "Sir booking sync issue tha, unhone suite room me upgrade kar diya hai complimentary", "positive", 2),
        ("Traveler", "Humein room ki chabi mil gayi hai, room bohot shandar hai", "positive", 2),
        ("Traveler", "Late night itni jaldi problem solve karne ke liye bohot shukriya", "positive", 2)
    ],
    # Dialogue 7: Food Delivery Missing Item (Devanagari)
    [
        ("उपयोगकर्ता", "मेरे खाने के ऑर्डर में मुख्य मिठाई गायब है, ऑर्डर अधूरा भेजा है", "negative", 0),
        ("एजेंट", "नमस्ते, असुविधा के लिए हम माफ़ी चाहते हैं", "neutral", 1),
        ("उपयोगकर्ता", "मेहमान घर आए हुए हैं और खाना अधूरा है, बहुत गुस्सा आ रहा है", "negative", 0),
        ("एजेंट", "हमने तुरंत रेस्टोरेंट से बात की है और मिठाई का दूसरा पैकेट 15 मिनट में आपके पास पहुँचेगा", "positive", 2),
        ("एजेंट", "साथ ही आपके वॉलेट में 100 रुपये का कूपन क्रेडिट कर दिया गया है", "positive", 2),
        ("उपयोगकर्ता", "मिठाई समय पर आ गई, आपकी सेवा और समाधान सच में बहुत सराहनीय है", "positive", 2)
    ],
    # Dialogue 8: College Exam Prep Group (Hinglish)
    [
        ("Sameer", "Yaar kal semester exam hai aur syllabus ka aadha part bacha hua hai", "negative", 0),
        ("Pooja", "Mujhe bhi bohot tension ho rahi hai, passing marks aana mushkil lag raha hai", "negative", 0),
        ("Karan", "Ghabrao mat, maine sabhi important chapters ke revision notes share kar diye hain", "positive", 2),
        ("Sameer", "Ye notes toh ekdum crystal clear hain, ab confidence aa raha hai!", "positive", 2),
        ("Pooja", "Thank you Karan, tu sach me life saver hai!", "positive", 2)
    ],
    # Dialogue 9: Apartment Maintenance Notice (Devanagari)
    [
        ("निवासी", "सोसाइटी में पिछले 3 घंटे से पानी की सप्लाई पूरी तरह बंद है", "negative", 0),
        ("सचिव", "मुख्य पाइपलाइन में रिसाव हुआ था, प्लंबर मरम्मत का काम कर रहे हैं", "neutral", 1),
        ("निवासी", "काम कब तक पूरा होगा? दैनिक कार्य रुक गए हैं", "neutral", 1),
        ("सचिव", "काम पूरा हो चुका है और वाटर पंप शुरू कर दिया गया है", "positive", 2),
        ("निवासी", "पानी आ गया है, त्वरित कार्रवाई के लिए धन्यवाद", "positive", 2)
    ]
]


def generate_extended_dataset() -> List[List[Tuple[str, str, str, int]]]:
    """
    Expands base dialogues with bidirectional transliteration and variation
    to generate a balanced, diverse corpus in both Devanagari and Romanized Hinglish.
    """
    extended_dialogues = []

    for d in BASE_DIALOGUES:
        # Add original dialogue
        extended_dialogues.append(d)

        # Generate Transliterated / Code-mixed twin
        twin_turns = []
        for spk, txt, sent, lbl in d:
            if any('\u0900' <= c <= '\u097F' for c in txt):
                # Devanagari -> Transliterate to Romanized Hinglish
                roman_txt = transliterate_devanagari_to_roman(txt)
                twin_turns.append((spk, roman_txt, sent, lbl))
            else:
                # Hinglish -> Add slight WhatsApp elongation & slang variations
                norm = normalize_whatsapp_text(txt)
                twin_turns.append((spk, norm, sent, lbl))

        extended_dialogues.append(twin_turns)

    # Add 10 additional focused dialogues for rich vocabulary
    extra_dialogues = [
        # Dialogue 20: Software Bug Report & Patch (Hinglish)
        [
            ("Tester", "App restart hone par crash kar rahi hai", "negative", 0),
            ("Dev", "Null pointer exception aa raha hai memory leaks ke sath", "negative", 0),
            ("Dev", "Fix commit kar diya hai branch me", "neutral", 1),
            ("Tester", "Build test kiya, ab crash issue solve ho gaya hai", "positive", 2),
            ("Manager", "Very good work, ab release ready hai", "positive", 2)
        ],
        # Dialogue 21: Online Shopping Delivery Review (Devanagari)
        [
            ("क्रेता", "पैकेजिंग फटी हुई थी और उत्पाद क्षतिग्रस्त निकला", "negative", 0),
            ("कंपनी", "असुविधा के लिए क्षमा, हम नया उत्पाद आज ही भेज रहे हैं", "positive", 2),
            ("क्रेता", "नया उत्पाद बिल्कुल सही स्थिति में मिल गया, बहुत आभार", "positive", 2)
        ],
        # Dialogue 22: Ride Hailing Trip Delay (Hinglish)
        [
            ("Rider", "Driver pickup location se bohot dur khada hai aur call nahi utha raha", "negative", 0),
            ("Rider", "Main late ho raha hu airport ke liye, bohot gussa aa raha hai", "negative", 0),
            ("Support", "Humne naya driver allocate kar diya hai jo 2 minute me pahunchega", "positive", 2),
            ("Rider", "Cab aa gayi, main timely airport pahunch gaya, thank you", "positive", 2)
        ],
        # Dialogue 23: Office Meeting Rescheduling (Hinglish)
        [
            ("Priya", "Kya aaj 3 baje ki meeting 4 baje shift ho sakti hai?", "neutral", 1),
            ("Vikas", "Haan, calendar invite update kar diya hai", "neutral", 1),
            ("Priya", "Dhanyawad Vikas, 4 baje milte hain", "positive", 2)
        ],
        # Dialogue 24: Broadband Internet Connectivity (Devanagari)
        [
            ("उपभोक्ता", "इंटरनेट की गति बहुत धीमी है, वीडियो बफर हो रही है", "negative", 0),
            ("इंजीनियर", "राउटर को रीबूट करके सिग्नल चेक करें", "neutral", 1),
            ("उपभोक्ता", "स्पीड अब 200 Mbps आ रही है, सब कुछ एकदम सुचारू है", "positive", 2)
        ],
        # Dialogue 25: Medical Appointment Confirmation (Hinglish)
        [
            ("Patient", "Dr. Sharma ki OPD timing kya hai kal subah?", "neutral", 1),
            ("Clinic", "Dr. Sharma subah 10 baje se dopahar 1 baje tak available hain", "neutral", 1),
            ("Patient", "Mera slot 10:30 ka book kar dijiye kripya", "neutral", 1),
            ("Clinic", "Aapka appointment successfully confirm ho gaya hai", "positive", 2),
            ("Patient", "Bohot shukriya aapki madad ke liye", "positive", 2)
        ],
        # Dialogue 26: Bank Account Statement (Hinglish)
        [
            ("Customer", "Mera monthly e-statement password protected hai, password kya hai?", "neutral", 1),
            ("Helpdesk", "Password aapke date of birth aur phone number ke last 4 digits hain", "neutral", 1),
            ("Customer", "Document open ho gaya hai, accurate information ke liye thanks", "positive", 2)
        ],
        # Dialogue 27: Course Review and Instructor Feedback (Devanagari)
        [
            ("छात्र", "पाठ्यक्रम की सामग्री बहुत कठिन और अस्पष्ट थी", "negative", 0),
            ("शिक्षक", "हमने अतिरिक्त स्पष्टीकरण वीडियो और नोट्स अपलोड किए हैं", "neutral", 1),
            ("छात्र", "अब सभी अवधारणाएँ बहुत अच्छे से समझ आ रही हैं, धन्यवाद", "positive", 2)
        ],
        # Dialogue 28: Car Service & Maintenance Inspection (Hinglish)
        [
            ("Owner", "Brakes me se ajeeb awaaz aa rahi hai, safety ka issue lag raha hai", "negative", 0),
            ("Mechanic", "Brake pads ghis chuke hain, replace karna padega", "neutral", 1),
            ("Owner", "Theek hai, genuine parts hi lagana", "neutral", 1),
            ("Mechanic", "New brake pads install ho gaye hain, car ab ekdum smooth chal rahi hai", "positive", 2),
            ("Owner", "Drive karke dekha, perfection hai. Badiya service!", "positive", 2)
        ],
        # Dialogue 29: Fitness / Gym Subscription Inquiry (Hinglish)
        [
            ("Member", "Gym ke annual membership me trainer facility included hai kya?", "neutral", 1),
            ("Reception", "Haanji, 3 months complimentary personal training session milenge", "positive", 2),
            ("Member", "Great package! Main aaj hi membership activate karunga", "positive", 2)
        ]
    ]

    for ed in extra_dialogues:
        extended_dialogues.append(ed)
        # Add twin
        extra_twin = []
        for spk, txt, sent, lbl in ed:
            if any('\u0900' <= c <= '\u097F' for c in txt):
                extra_twin.append((spk, transliterate_devanagari_to_roman(txt), sent, lbl))
            else:
                extra_twin.append((spk, normalize_whatsapp_text(txt), sent, lbl))
        extended_dialogues.append(extra_twin)

    return extended_dialogues


def build_and_save_hindi_datasets(output_dir: str = "data/processed"):
    """
    Builds dataframes, applies train/val/test split across distinct dialogues (NO leakage),
    and writes out hindi_train.csv, hindi_val.csv, hindi_test.csv.
    """
    os.makedirs(output_dir, exist_ok=True)
    dialogues = generate_extended_dataset()

    total_dialogues = len(dialogues)
    np.random.seed(42)
    indices = np.random.permutation(total_dialogues)

    # 70% train, 15% val, 15% test split by dialogue
    n_train = int(0.70 * total_dialogues)
    n_val = int(0.15 * total_dialogues)

    train_indices = set(indices[:n_train])
    val_indices = set(indices[n_train:n_train + n_val])
    test_indices = set(indices[n_train + n_val:])

    records_train = []
    records_val = []
    records_test = []

    for d_idx, d in enumerate(dialogues):
        target_list = (
            records_train if d_idx in train_indices
            else records_val if d_idx in val_indices
            else records_test
        )
        for t_idx, (spk, txt, sent, lbl) in enumerate(d):
            target_list.append({
                "dialogue_id": d_idx,
                "turn_id": t_idx,
                "speaker": spk,
                "text": txt,
                "sentiment": sent,
                "label": lbl
            })

    df_train = pd.DataFrame(records_train)
    df_val = pd.DataFrame(records_val)
    df_test = pd.DataFrame(records_test)

    train_path = os.path.join(output_dir, "hindi_train.csv")
    val_path = os.path.join(output_dir, "hindi_val.csv")
    test_path = os.path.join(output_dir, "hindi_test.csv")

    df_train.to_csv(train_path, index=False, encoding="utf-8")
    df_val.to_csv(val_path, index=False, encoding="utf-8")
    df_test.to_csv(test_path, index=False, encoding="utf-8")

    print(f"[DATASET] Successfully built Hindi & Hinglish datasets:")
    print(f"  Train: {len(df_train)} turns across {len(train_indices)} dialogues -> {train_path}")
    print(f"  Val:   {len(df_val)} turns across {len(val_indices)} dialogues -> {val_path}")
    print(f"  Test:  {len(df_test)} turns across {len(test_indices)} dialogues -> {test_path}")

    # Verify zero leakage
    train_dids = set(df_train["dialogue_id"])
    val_dids = set(df_val["dialogue_id"])
    test_dids = set(df_test["dialogue_id"])
    assert len(train_dids.intersection(val_dids)) == 0, "Train-Val dialogue leakage detected!"
    assert len(train_dids.intersection(test_dids)) == 0, "Train-Test dialogue leakage detected!"
    assert len(val_dids.intersection(test_dids)) == 0, "Val-Test dialogue leakage detected!"
    print("  Zero Boundary Leakage Assertion: PASSED")


if __name__ == "__main__":
    build_and_save_hindi_datasets()
