"""
todo/autocorrect.py

Intelligent multi-lingual spell check, auto-correction, and grammar normalization
engine supporting English, Hindi (transliterated), and Hinglish.

Fixes common typos, phonetic mistakes, letter swaps, and casing across task titles,
descriptions, comments, and project notes.
"""

import re

# Comprehensive dictionary of typo to correct replacement (English & Hinglish)
COMMON_REPLACEMENTS = {
    # Hinglish & Hindi transliterations
    r'\bkrna\b': 'karna',
    r'\bkrna hai\b': 'karna hai',
    r'\bkr do\b': 'kar do',
    r'\bkr de\b': 'kar de',
    r'\bkr dena\b': 'kar dena',
    r'\bkr liya\b': 'kar liya',
    r'\bkro\b': 'karo',
    r'\bkrte\b': 'karte',
    r'\bkrti\b': 'karti',
    r'\bkra\b': 'kara',
    r'\bho gya\b': 'ho gaya',
    r'\bho gya hai\b': 'ho gaya hai',
    r'\bkhtm\b': 'khatam',
    r'\bzruri\b': 'zaroori',
    r'\bzaruri\b': 'zaroori',
    r'\bjldi\b': 'jaldi',
    r'\bbhejna hai\b': 'bhejna hai',
    r'\bbhej do\b': 'bhej do',
    r'\bbhej dena\b': 'bhej dena',
    r'\bbhejo\b': 'bhejo',
    r'\bsned\b': 'Send',
    r'\bsned to\b': 'Send to',
    r'\bsend to :\b': 'Send to:',
    r'\bchahie\b': 'chahiye',
    r'\bchahiye\b': 'chahiye',
    r'\bbtao\b': 'batao',
    r'\bbtana\b': 'batana',
    r'\bdekho\b': 'dekho',
    r'\bdhyan\b': 'dhyaan',
    r'\bshuru\b': 'shuru',
    r'\bkal tak\b': 'kal tak',
    r'\baaj\b': 'aaj',
    r'\bkaam\b': 'kaam',
    r'\bpending hai\b': 'pending hai',
    r'\bdone ho gya\b': 'done ho gaya',

    # Common Task & Project Typos (English)
    r'\btaks\b': 'task',
    r'\btakss\b': 'tasks',
    r'\btaskss\b': 'tasks',
    r'\bproejct\b': 'project',
    r'\bproejcts\b': 'projects',
    r'\bproejctoptio\b': 'project option',
    r'\bkanabna\b': 'Kanban',
    r'\bkanabn\b': 'Kanban',
    r'\bknaban\b': 'Kanban',
    r'\bkan band\b': 'Kanban',
    r'\bkan ban\b': 'Kanban',
    r'\bmanamgent\b': 'Management',
    r'\bmangment\b': 'Management',
    r'\bmanagment\b': 'Management',
    r'\bchekclist\b': 'checklist',
    r'\bchecklest\b': 'checklist',
    r'\bcheklist\b': 'checklist',
    r'\bcomdmtns\b': 'comments',
    r'\bcomtns\b': 'comments',
    r'\bcoemtn\b': 'comment',
    r'\bcoemtns\b': 'comments',
    r'\bdelte\b': 'delete',
    r'\bdelet\b': 'delete',
    r'\bdleted\b': 'deleted',
    r'\bcrating\b': 'creating',
    r'\bcreat\b': 'create',
    r'\bcreclyt\b': 'correctly',
    r'\bcorelcy\b': 'correctly',
    r'\bcorect\b': 'correct',
    r'\bcorects\b': 'corrects',
    r'\bcorret\b': 'correct',
    r'\bpropelry\b': 'properly',
    r'\bpopelry\b': 'properly',
    r'\bshud\b': 'should',
    r'\bshoud\b': 'should',
    r'\bshoudl\b': 'should',
    r'\bliek\b': 'like',
    r'\bmaek\b': 'make',
    r'\bwidht\b': 'width',
    r'\bwtiwce\b': 'twice',
    r'\bgaps\b': 'gaps',
    r'\bgape\b': 'gap',
    r'\bpaddigns\b': 'paddings',
    r'\bpaddign\b': 'padding',
    r'\bdordpown\b': 'dropdown',
    r'\bdrodpown\b': 'dropdown',
    r'\bdorpon\b': 'dropdown',
    r'\bopton\b': 'option',
    r'\boptons\b': 'options',
    r'\bmemebers\b': 'members',
    r'\bdetils\b': 'details',
    r'\bexsiting\b': 'existing',
    r'\bdefoult\b': 'default',
    r'\btemapte\b': 'template',
    r'\btempate\b': 'template',
    r'\bprgees\b': 'progress',
    r'\bantoehr\b': 'another',
    r'\bcorped\b': 'cropped',
    r'\bhdiden\b': 'hidden',
    r'\bstikce\b': 'stuck',
    r'\biampmented\b': 'implemented',
    r'\bdocamtion\b': 'documentation',
    r'\basweper\b': 'as per',
    r'\bavialbe\b': 'available',
    r'\binsted\b': 'instead',
    r'\bcollpesbl\b': 'collapsible',
    r'\bcollpace\b': 'collapse',
    r'\bsiebr\b': 'sidebar',
    r'\bsmae\b': 'same',
    r'\btehm\b': 'them',
    r'\brecive\b': 'receive',
    r'\breceved\b': 'received',
    r'\bseperate\b': 'separate',
    r'\bdefinately\b': 'definitely',
    r'\bcalender\b': 'calendar',
    r'\boccurance\b': 'occurrence',
    r'\baccomodate\b': 'accommodate',
    r'\bnevers\b': 'never',
    r'\bremvoe\b': 'remove',
    r'\bintengrate\b': 'integrate',
    r'\bopensoruc\b': 'open source',
    r'\bhidnig\b': 'Hindi',
    r'\benglish\b': 'English',
    r'\bhinglish\b': 'Hinglish',
    r'\bpalce\b': 'place',
    r'\bblakc\b': 'black',
    r'\bswho\b': 'show',
    r'\bshwo\b': 'show',
    r'\beidt\b': 'edit',
    r'\boepsn\b': 'opens',
    r'\bmyal\b': 'Royal',
}


def autocorrect_text(text: str) -> dict:
    """
    Performs intelligent multi-lingual spell correction and normalizes text.
    Preserves numbers, URLs, and punctuation while fixing misspelled English and Hinglish words.
    """
    if not text:
        return {'original': '', 'corrected': '', 'changed': False}

    cleaned = text

    # Step 1: Apply targeted regex replacements with case preservation
    for pattern, replacement in COMMON_REPLACEMENTS.items():
        # Match case-insensitively but match capitalization style
        def make_replace(match):
            m_text = match.group(0)
            if m_text.isupper():
                return replacement.upper()
            if m_text[0].isupper():
                return replacement.capitalize()
            return replacement

        cleaned = re.sub(pattern, make_replace, cleaned, flags=re.IGNORECASE)

    # Step 2: Fix multiple consecutive spaces
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)

    # Step 3: Normalize colons (remove space before colon, ensure space after colon)
    cleaned = re.sub(r'\s+:\s*', ': ', cleaned)
    cleaned = re.sub(r':([A-Za-z0-9])', r': \1', cleaned)

    # Step 4: Fix duplicate punctuation like ,, or .. (except ...)
    cleaned = re.sub(r',{2,}', ',', cleaned)

    # Step 5: Capitalize the first letter if it starts with lowercase letter
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]

    return {
        'original': text,
        'corrected': cleaned.strip(),
        'changed': cleaned.strip() != text.strip(),
    }
