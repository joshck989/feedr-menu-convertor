"""
Known nutrition data for atis menu items.
Keys are normalised (lowercase, tags stripped).
Values: (kcal, protein_g, carbs_g, fat_g) — strings for ranges, ints otherwise.
"""

NUTRITION = {
    "seiz'a caesar":            (434, 27, 29, 24),
    'azteca':                   (488, 28, 51, 17),
    'green goddess':            (399, 14, 41, 18),
    'el chipotle':              (548, 37, 51, 19),
    'sweet potato satay':       (562, 18, 70, 21),
    'double crunch thai':       (452, 29, 47, 14),
    'high steaks':              (558, 56, 20, 27),
    'harissa chicken caesar':   (502, 48, 21, 23),
    'blackened chicken grains': (453, 47, 33, 14),
    'salmon plate':             (627, 44, 33, 33),
    'tofu plate':               (492, 20, 55, 20),
    'ponzu sweet potato':       (392, 13, 56, 13),
    'thai coconut rice bowl':   (579, 21, 72, 22),
    'chicken pot':              ('330-414', '38-47', '2-3', '18-24'),
    'buffalo chicken pot':      (414, 47, 3, 24),
    'parmesan roasties pot':    (318, 7, 38, 15),
    'tahini greens and chickpeas': (209, 8, 19, 11),
    'tahini greens + chickpeas': (209, 8, 19, 11),
}
