import sqlite3
from lxml import etree

# Conecta ao banco
conn = sqlite3.connect("kanjidic_full.db")
cursor = conn.cursor()

# Cria tabela
cursor.execute("""
CREATE TABLE IF NOT EXISTS kanjidic (
    kanji TEXT PRIMARY KEY,
    onyomi TEXT,
    kunyomi TEXT,
    significado TEXT,
    grade INTEGER,
    jlpt INTEGER
);
""")

# Lê o XML
tree = etree.parse("kanjidic2.xml")
root = tree.getroot()

for character in root.findall("character"):
    kanji = character.findtext("literal")
    grade = character.findtext("misc/grade")
    jlpt = character.findtext("misc/jlpt")

    onyomi = []
    kunyomi = []
    significados = []

    rmgroup = character.find("reading_meaning/rmgroup")
    if rmgroup is not None:
        for reading in rmgroup.findall("reading"):
            rtype = reading.get("r_type")
            if rtype == "ja_on":
                onyomi.append(reading.text)
            elif rtype == "ja_kun":
                kunyomi.append(reading.text)
        for meaning in rmgroup.findall("meaning"):
            if meaning.get("m_lang") is None:  # só inglês
                significados.append(meaning.text)

    cursor.execute("""
        INSERT OR REPLACE INTO kanjidic
        (kanji, onyomi, kunyomi, significado, grade, jlpt)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        kanji,
        ", ".join(onyomi),
        ", ".join(kunyomi),
        "; ".join(significados),
        int(grade) if grade else None,
        int(jlpt) if jlpt else None
    ))

conn.commit()

cursor.execute("SELECT COUNT(*) FROM kanjidic")
total = cursor.fetchone()[0]
print("Total de kanji no banco:", total)
conn.close()
