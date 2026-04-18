#!/usr/bin/env python3
"""
👥 PEUPLEMENT DE LA TABLE DES AUTORITÉS
Import des grands savants du hadith : des Sahaba aux contemporains
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = "backend/database/almizan_v7.db"

# Base de données des autorités majeures
AUTHORITIES_DATA = [
    # ═══════════════════════════════════════════════════════════════
    # SAHABA (Compagnons du Prophète ﷺ)
    # ═══════════════════════════════════════════════════════════════
    {
        "name_ar": "أبو هريرة",
        "name_transliterated": "Abu Hurayrah",
        "name_aliases": json.dumps(["Abd al-Rahman ibn Sakhr"]),
        "birth_year": -21,  # Avant l'Hégire
        "death_year": 59,
        "century": 1,
        "era": "sahaba",
        "specialty": "hadith",
        "school": None,
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_muhaddith": 1,
        "major_works": json.dumps(["Narrateur de 5374 hadiths"]),
        "biography_summary": "Le plus prolifique narrateur de hadiths parmi les Sahaba"
    },
    {
        "name_ar": "عائشة بنت أبي بكر",
        "name_transliterated": "Aisha bint Abi Bakr",
        "name_aliases": json.dumps(["Umm al-Mu'minin"]),
        "birth_year": -9,
        "death_year": 58,
        "century": 1,
        "era": "sahaba",
        "specialty": "hadith",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_muhaddith": 1,
        "major_works": json.dumps(["Narratrice de 2210 hadiths"]),
        "biography_summary": "Épouse du Prophète ﷺ, grande savante et narratrice"
    },
    {
        "name_ar": "عبد الله بن عباس",
        "name_transliterated": "Abdullah ibn Abbas",
        "name_aliases": json.dumps(["Ibn Abbas", "Hibr al-Ummah"]),
        "birth_year": -3,
        "death_year": 68,
        "century": 1,
        "era": "sahaba",
        "specialty": "multiple",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_muhaddith": 1,
        "is_mufassir": 1,
        "major_works": json.dumps(["Tafsir Ibn Abbas"]),
        "biography_summary": "Cousin du Prophète ﷺ, grand exégète et savant"
    },
    
    # ═══════════════════════════════════════════════════════════════
    # IMAMS DES KUTUB AL-SITTAH (2ème-3ème siècles H)
    # ═══════════════════════════════════════════════════════════════
    {
        "name_ar": "محمد بن إسماعيل البخاري",
        "name_transliterated": "Muhammad ibn Ismail al-Bukhari",
        "name_aliases": json.dumps(["Imam al-Bukhari", "Abu Abdullah"]),
        "birth_year": 194,
        "death_year": 256,
        "century": 3,
        "era": "mutaqaddimun",
        "specialty": "hadith",
        "school": "shafii",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_mujtahid": 1,
        "is_hafiz": 1,
        "is_muhaddith": 1,
        "major_works": json.dumps(["Sahih al-Bukhari", "Al-Adab al-Mufrad", "Al-Tarikh al-Kabir"]),
        "biography_summary": "Auteur du recueil de hadiths le plus authentique après le Coran",
        "source_references": json.dumps(["Siyar A'lam al-Nubala", "Tahdhib al-Tahdhib"])
    },
    {
        "name_ar": "مسلم بن الحجاج",
        "name_transliterated": "Muslim ibn al-Hajjaj",
        "name_aliases": json.dumps(["Imam Muslim", "Abu al-Husayn"]),
        "birth_year": 206,
        "death_year": 261,
        "century": 3,
        "era": "mutaqaddimun",
        "specialty": "hadith",
        "school": "shafii",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_hafiz": 1,
        "is_muhaddith": 1,
        "major_works": json.dumps(["Sahih Muslim"]),
        "biography_summary": "Auteur du deuxième recueil le plus authentique",
        "source_references": json.dumps(["Siyar A'lam al-Nubala"])
    },
    {
        "name_ar": "أبو داود السجستاني",
        "name_transliterated": "Abu Dawud al-Sijistani",
        "name_aliases": json.dumps(["Sulayman ibn al-Ash'ath"]),
        "birth_year": 202,
        "death_year": 275,
        "century": 3,
        "era": "mutaqaddimun",
        "specialty": "hadith",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_hafiz": 1,
        "is_muhaddith": 1,
        "major_works": json.dumps(["Sunan Abi Dawud"]),
        "biography_summary": "Auteur d'un des Sunan majeurs, spécialisé dans les hadiths juridiques"
    },
    {
        "name_ar": "محمد بن عيسى الترمذي",
        "name_transliterated": "Muhammad ibn Isa al-Tirmidhi",
        "name_aliases": json.dumps(["Imam al-Tirmidhi", "Abu Isa"]),
        "birth_year": 209,
        "death_year": 279,
        "century": 3,
        "era": "mutaqaddimun",
        "specialty": "hadith",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_hafiz": 1,
        "is_muhaddith": 1,
        "major_works": json.dumps(["Jami' al-Tirmidhi", "Al-Shama'il al-Muhammadiyah"]),
        "biography_summary": "Auteur du Jami' avec commentaires sur les degrés d'authenticité"
    },
    {
        "name_ar": "أحمد بن شعيب النسائي",
        "name_transliterated": "Ahmad ibn Shu'ayb al-Nasa'i",
        "name_aliases": json.dumps(["Imam al-Nasa'i", "Abu Abd al-Rahman"]),
        "birth_year": 215,
        "death_year": 303,
        "century": 3,
        "era": "mutaqaddimun",
        "specialty": "hadith",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_hafiz": 1,
        "is_muhaddith": 1,
        "major_works": json.dumps(["Sunan al-Nasa'i", "Al-Sunan al-Kubra"]),
        "biography_summary": "Auteur d'un des Sunan les plus rigoureux"
    },
    {
        "name_ar": "محمد بن يزيد ابن ماجه",
        "name_transliterated": "Muhammad ibn Yazid Ibn Majah",
        "name_aliases": json.dumps(["Ibn Majah", "Abu Abdullah"]),
        "birth_year": 209,
        "death_year": 273,
        "century": 3,
        "era": "mutaqaddimun",
        "specialty": "hadith",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_hafiz": 1,
        "is_muhaddith": 1,
        "major_works": json.dumps(["Sunan Ibn Majah"]),
        "biography_summary": "Auteur du sixième livre des Kutub al-Sittah"
    },
    
    # ═══════════════════════════════════════════════════════════════
    # IMAMS DES MADHAHIB (2ème-3ème siècles H)
    # ═══════════════════════════════════════════════════════════════
    {
        "name_ar": "أحمد بن حنبل",
        "name_transliterated": "Ahmad ibn Hanbal",
        "name_aliases": json.dumps(["Imam Ahmad", "Abu Abdullah"]),
        "birth_year": 164,
        "death_year": 241,
        "century": 3,
        "era": "mutaqaddimun",
        "specialty": "multiple",
        "school": "hanbali",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_mujtahid": 1,
        "is_hafiz": 1,
        "is_muhaddith": 1,
        "is_faqih": 1,
        "major_works": json.dumps(["Musnad Ahmad", "Al-'Ilal wa Ma'rifat al-Rijal"]),
        "biography_summary": "Fondateur de l'école hanbalite, grand muhaddith et faqih"
    },
    {
        "name_ar": "محمد بن إدريس الشافعي",
        "name_transliterated": "Muhammad ibn Idris al-Shafi'i",
        "name_aliases": json.dumps(["Imam al-Shafi'i", "Abu Abdullah"]),
        "birth_year": 150,
        "death_year": 204,
        "century": 2,
        "era": "mutaqaddimun",
        "specialty": "multiple",
        "school": "shafii",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_mujtahid": 1,
        "is_faqih": 1,
        "major_works": json.dumps(["Al-Risalah", "Al-Umm"]),
        "biography_summary": "Fondateur de l'école shafiite et de la science des Usul al-Fiqh"
    },
    
    # ═══════════════════════════════════════════════════════════════
    # GRANDS COMMENTATEURS (4ème-9ème siècles H)
    # ═══════════════════════════════════════════════════════════════
    {
        "name_ar": "أحمد بن علي بن حجر العسقلاني",
        "name_transliterated": "Ahmad ibn Ali ibn Hajar al-Asqalani",
        "name_aliases": json.dumps(["Ibn Hajar", "Amir al-Mu'minin fi al-Hadith"]),
        "birth_year": 773,
        "death_year": 852,
        "century": 9,
        "era": "mutaakhkhirun",
        "specialty": "hadith",
        "school": "shafii",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_hafiz": 1,
        "is_muhaddith": 1,
        "major_works": json.dumps(["Fath al-Bari", "Tahdhib al-Tahdhib", "Taqrib al-Tahdhib"]),
        "biography_summary": "Grand commentateur du Sahih al-Bukhari, maître du Jarh wa Ta'dil"
    },
    {
        "name_ar": "يحيى بن شرف النووي",
        "name_transliterated": "Yahya ibn Sharaf al-Nawawi",
        "name_aliases": json.dumps(["Imam al-Nawawi", "Abu Zakariya"]),
        "birth_year": 631,
        "death_year": 676,
        "century": 7,
        "era": "mutaakhkhirun",
        "specialty": "multiple",
        "school": "shafii",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_hafiz": 1,
        "is_muhaddith": 1,
        "is_faqih": 1,
        "major_works": json.dumps(["Sharh Sahih Muslim", "Riyad al-Salihin", "Al-Arba'in al-Nawawiyyah"]),
        "biography_summary": "Grand commentateur de Sahih Muslim et auteur prolifique"
    },
    
    # ═══════════════════════════════════════════════════════════════
    # SAVANTS CONTEMPORAINS (14ème-15ème siècles H)
    # ═══════════════════════════════════════════════════════════════
    {
        "name_ar": "محمد ناصر الدين الألباني",
        "name_transliterated": "Muhammad Nasir al-Din al-Albani",
        "name_aliases": json.dumps(["Al-Albani", "Shaykh al-Albani"]),
        "birth_year": 1332,
        "death_year": 1420,
        "century": 14,
        "era": "contemporary",
        "specialty": "hadith",
        "school": "salafi",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_hafiz": 1,
        "is_muhaddith": 1,
        "major_works": json.dumps([
            "Silsilat al-Ahadith al-Sahihah",
            "Silsilat al-Ahadith al-Da'ifah",
            "Sahih al-Jami' al-Saghir",
            "Irwa' al-Ghalil"
        ]),
        "biography_summary": "Grand muhaddith contemporain, spécialiste du Tahqiq"
    },
    {
        "name_ar": "عبد العزيز بن عبد الله بن باز",
        "name_transliterated": "Abd al-Aziz ibn Abdullah ibn Baz",
        "name_aliases": json.dumps(["Ibn Baz", "Shaykh Ibn Baz"]),
        "birth_year": 1330,
        "death_year": 1420,
        "century": 14,
        "era": "contemporary",
        "specialty": "multiple",
        "school": "hanbali",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_mujtahid": 1,
        "is_faqih": 1,
        "major_works": json.dumps(["Majmu' Fatawa Ibn Baz"]),
        "biography_summary": "Grand Mufti d'Arabie Saoudite, savant polyvalent"
    },
    {
        "name_ar": "محمد بن صالح العثيمين",
        "name_transliterated": "Muhammad ibn Salih al-Uthaymin",
        "name_aliases": json.dumps(["Ibn Uthaymin", "Shaykh al-Uthaymin"]),
        "birth_year": 1347,
        "death_year": 1421,
        "century": 14,
        "era": "contemporary",
        "specialty": "multiple",
        "school": "hanbali",
        "reliability_level": "thiqah",
        "is_imam": 1,
        "is_faqih": 1,
        "major_works": json.dumps(["Sharh Riyad al-Salihin", "Sharh al-Arba'in al-Nawawiyyah"]),
        "biography_summary": "Grand savant et enseignant, auteur de nombreux commentaires"
    },
    {
        "name_ar": "شعيب الأرنؤوط",
        "name_transliterated": "Shu'ayb al-Arna'ut",
        "name_aliases": json.dumps(["Al-Arna'ut"]),
        "birth_year": 1348,
        "death_year": 1438,
        "century": 14,
        "era": "contemporary",
        "specialty": "hadith",
        "reliability_level": "thiqah",
        "is_muhaddith": 1,
        "major_works": json.dumps([
            "Tahqiq Musnad Ahmad",
            "Tahqiq Sunan Abi Dawud",
            "Tahqiq Sahih Ibn Hibban"
        ]),
        "biography_summary": "Grand spécialiste du Tahqiq des manuscrits de hadith"
    }
]

def seed_authorities():
    """Peuple la table des autorités"""
    print("=" * 80)
    print("👥 PEUPLEMENT DE LA TABLE DES AUTORITÉS")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Vérifier si la table existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='authorities'")
    if not cursor.fetchone():
        print("\n❌ ERREUR: La table 'authorities' n'existe pas!")
        print("   Exécutez d'abord: python apply_migrations.py")
        conn.close()
        return
    
    # Vérifier si déjà peuplée
    cursor.execute("SELECT COUNT(*) FROM authorities")
    existing_count = cursor.fetchone()[0]
    
    if existing_count > 0:
        print(f"\n⚠️  La table contient déjà {existing_count} autorités")
        response = input("   Voulez-vous réinitialiser? (o/N): ")
        if response.lower() != 'o':
            print("   Opération annulée")
            conn.close()
            return
        cursor.execute("DELETE FROM authorities")
        print("   ✅ Table réinitialisée")
    
    # Insérer les autorités
    print(f"\n📥 Insertion de {len(AUTHORITIES_DATA)} autorités...")
    
    insert_query = """
        INSERT INTO authorities (
            name_ar, name_transliterated, name_aliases,
            birth_year, death_year, century, era, specialty, school,
            reliability_level, is_imam, is_mujtahid, is_hafiz,
            is_muhaddith, is_faqih, is_mufassir,
            major_works, biography_summary, source_references
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    inserted = 0
    for auth in AUTHORITIES_DATA:
        try:
            cursor.execute(insert_query, (
                auth["name_ar"],
                auth["name_transliterated"],
                auth.get("name_aliases"),
                auth.get("birth_year"),
                auth.get("death_year"),
                auth["century"],
                auth["era"],
                auth["specialty"],
                auth.get("school"),
                auth.get("reliability_level"),
                auth.get("is_imam", 0),
                auth.get("is_mujtahid", 0),
                auth.get("is_hafiz", 0),
                auth.get("is_muhaddith", 0),
                auth.get("is_faqih", 0),
                auth.get("is_mufassir", 0),
                auth.get("major_works"),
                auth.get("biography_summary"),
                auth.get("source_references")
            ))
            inserted += 1
            print(f"   ✅ {auth['name_transliterated']} ({auth['century']}ème s.H)")
        except sqlite3.Error as e:
            print(f"   ❌ Erreur pour {auth['name_transliterated']}: {e}")
    
    conn.commit()
    
    # Statistiques finales
    print("\n" + "=" * 80)
    print("📊 STATISTIQUES")
    print("=" * 80)
    
    cursor.execute("SELECT era, COUNT(*) FROM authorities GROUP BY era ORDER BY century")
    print("\n📈 Répartition par époque:")
    for row in cursor.fetchall():
        print(f"   • {row[0]}: {row[1]} autorités")
    
    cursor.execute("SELECT specialty, COUNT(*) FROM authorities GROUP BY specialty")
    print("\n🎓 Répartition par spécialité:")
    for row in cursor.fetchall():
        print(f"   • {row[0]}: {row[1]} autorités")
    
    cursor.execute("SELECT COUNT(*) FROM authorities WHERE is_hafiz = 1")
    hafiz_count = cursor.fetchone()[0]
    print(f"\n📚 {hafiz_count} Huffaz (mémorisateurs)")
    
    cursor.execute("SELECT COUNT(*) FROM authorities WHERE is_imam = 1")
    imam_count = cursor.fetchone()[0]
    print(f"👑 {imam_count} Imams reconnus")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print(f"✅ {inserted}/{len(AUTHORITIES_DATA)} autorités insérées avec succès")
    print("=" * 80)

if __name__ == "__main__":
    seed_authorities()