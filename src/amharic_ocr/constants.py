"""
Constants for Ethiopic numerals and Amharic Fidel script.
"""

# Complete set of Ethiopic numerals mapping
ETHIOPIC_NUMERALS = {
    # Basic digits 1-9
    '1': '፩',   # U+1369
    '2': '፪',   # U+136A
    '3': '፫',   # U+136B
    '4': '፬',   # U+136C
    '5': '፭',   # U+136D
    '6': '፮',   # U+136E
    '7': '፯',   # U+136F
    '8': '፰',   # U+1370
    '9': '፱',   # U+1371
    # Tens
    '10': '፲',  # U+1372
    '20': '፳',  # U+1373
    '30': '፴',  # U+1374
    '40': '፵',  # U+1375
    '50': '፶',  # U+1376
    '60': '፷',  # U+1377
    '70': '፸',  # U+1378
    '80': '፹',  # U+1379
    '90': '፺',  # U+137A
    # Hundreds and thousands
    '100': '፻',  # U+137B
    '10000': '፼',  # U+137C
}

# All Ethiopic numeral characters as a string (፩፪፫፬፭፮፯፰፱፲፳፴፵፶፷፸፹፺፻፼)
ALL_ETHIOPIC_NUMERALS = ''.join(ETHIOPIC_NUMERALS.values())

# Common Amharic Fidel characters for whitelist
AMHARIC_FIDEL = (
    "ሀሁሂሃሄህሆለሉሊላሌልሎሏሐሑሒሓሔሕሖሗመሙሚማሜምሞሟሠሡሢሣሤሥሦሧረሩሪራሬርሮሯ"
    "ሰሱሲሳሴስሶሷሸሹሺሻሼሽሾሿቀቁቂቃቄቅቆቈቊቋቌቍቐቑቒቓቔቕቖቘቚቛቜቝበቡቢባቤብቦቧ"
    "ቨቩቪቫቬቭቮቯተቱቲታቴትቶቷቸቹቺቻቼችቾቿኀኁኂኃኄኅኆኈኊኋኌኍነኑኒናኔንኖኗኘኙኚኛኜኝኞኟ"
    "አኡኢኣኤእኦኧከኩኪካኬክኮኰኲኳኴኵኸኹኺኻኼኽኾዀዂዃዄዅወዉዊዋዌውዎዐዑዒዓዔዕዖ"
    "ዘዙዚዛዜዝዞዟዠዡዢዣዤዥዦዧየዩዪያዬይዮደዱዲዳዴድዶዷዸዹዺዻዼዽዾጀጁጂጃጄጅጆጇ"
    "ገጉጊጋጌግጎጐጒጓጔጕጠጡጢጣጤጥጦጧጨጩጪጫጬጭጮጯጰጱጲጳጴጵጶጷጸጹጺጻጼጽጾፀፁፂፃፄፅፆ"
    "ፈፉፊፋፌፍፎፏፐፑፒፓፔፕፖፗፘፙፚ"
)

# Ethiopic punctuation characters used in Amharic text
# These MUST be in the whitelist or Tesseract will suppress them entirely.
ETHIOPIC_PUNCTUATION = (
    "።"   # U+1362 Ethiopic full stop
    "፡"   # U+1361 Ethiopic wordspace
    "፣"   # U+1363 Ethiopic comma
    "፤"   # U+1364 Ethiopic semicolon
    "፥"   # U+1365 Ethiopic colon
    "፦"   # U+1366 Ethiopic preface colon
    "፧"   # U+1367 Ethiopic question mark
    "፨"   # U+1368 Ethiopic paragraph separator
    "«»"  # angle quotes used in some Amharic prints
)

# Common punctuation and Latin characters for mixed OCR
LATIN_CHARS = "0123456789 .,;:!?()[]{}-'\"\\\n"

# Combined extra characters allowed in the mixed-content whitelist
ALLOWED_EXTRA_CHARS = LATIN_CHARS + ETHIOPIC_PUNCTUATION

# Visually-ambiguous Ethiopic OCR confusions (safe to correct globally)
# NOTE: ፣ (Ethiopic comma) is intentionally NOT mapped here — it is a valid
# punctuation mark in real Amharic text and must not be silently converted to ፫.
VISUAL_CONFUSIONS = {
    '፨': '፰',   # Ethiopic paragraph separator confused with 8 (፰) — rare in body text
}

# Latin characters frequently misrecognized instead of Ethiopic numerals
LATIN_TO_ETHIOPIC_LOOKALIKES = {
    '1': '፩',
    '2': '፪',
    '3': '፫',
    '4': '፬',
    '5': '፭',
    '6': '፮',
    '7': '፯',
    '8': '፰',
    '9': '፱',
    '0': '፲',  # 10, not exactly 0
    'l': '፩',   # lowercase L -> 1
    'I': '፩',   # uppercase I -> 1
    'O': '፬',   # letter O -> 4
    'S': '፭',   # letter S -> 5
    'b': '፮',   # letter b -> 6
    'T': '፯',   # letter T -> 7
    'B': '፰',   # letter B -> 8
    'g': '፱',   # letter g -> 9
}
