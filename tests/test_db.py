"""Tests pour la base de données corpus."""

import pytest
import asyncio
import pathlib
import sqlite3

from backend.corpus.db import CorpusDB

@pytest.fixture
def test_db_path(tmp_path):
    """Crée une base de données temporaire pour les tests."""
    return tmp_path / "test_corpus.db"

@pytest.fixture
def corpus_db(test_db_path):
    """Instance CorpusDB pour tests."""
    return CorpusDB(db_path=test_db_path)

def test_db_creation(corpus_db, test_db_path):
    """Vérifie que la base de données est créée avec le bon schéma."""
    assert test_db_path.exists()
    
    # Vérifier les tables
    conn = sqlite3.connect(str(test_db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()
    
    expected_tables = {'hadiths_raw', 'hadiths_validated', 'pending_review'}
    assert expected_tables.issubset(tables)

@pytest.mark.asyncio
async def test_insert_raw_hadith(corpus_db):
    """Test insertion hadith brut."""
    hadith_id = await corpus_db.insert_raw_hadith(
        dorar_id="test_001",
        matn_ar="إنما الأعمال بالنيات",
        source="Ṣaḥīḥ al-Bukhārī n°1",
        grade_raw="صحيح",
        rawi="عمر بن الخطاب"
    )
    
    assert hadith_id > 0
    
    # Vérifier que le doublon est rejeté
    duplicate_id = await corpus_db.insert_raw_hadith(
        dorar_id="test_001",
        matn_ar="Autre texte",
        source="Autre source"
    )
    
    assert duplicate_id == -1

@pytest.mark.asyncio
async def test_insert_validated_hadith(corpus_db):
    """Test insertion hadith validé."""
    # D'abord insérer un hadith brut
    raw_id = await corpus_db.insert_raw_hadith(
        dorar_id="test_002",
        matn_ar="من كذب علي متعمدا",
        source="Ṣaḥīḥ al-Bukhārī"
    )
    
    # Puis insérer la version validée
    validated_id = await corpus_db.insert_validated_hadith(
        hadith_raw_id=raw_id,
        matn_ar="من كذب علي متعمدا",
        translation_fr="Quiconque ment sur moi délibérément",
        grade_normalized="صحيح",
        scholar_verdict="al-Bukhārī",
        scholar_location="Médine",
        confidence_score=95.5,
        agent_isnad_output='{"verdict": "sahih"}',
        agent_ilal_output='{"ilal": []}',
        agent_matn_output='{"gharib": []}',
        agent_tarjih_output='{"tarjih": "sahih"}'
    )
    
    assert validated_id > 0

@pytest.mark.asyncio
async def test_insert_pending_review(corpus_db):
    """Test insertion hadith en review."""
    raw_id = await corpus_db.insert_raw_hadith(
        dorar_id="test_003",
        matn_ar="حديث ضعيف",
        source="Source inconnue"
    )
    
    review_id = await corpus_db.insert_pending_review(
        hadith_raw_id=raw_id,
        reason="Confiance insuffisante",
        confidence_score=72.3,
        agent_outputs='{"combined": "outputs"}'
    )
    
    assert review_id > 0

@pytest.mark.asyncio
async def test_get_stats(corpus_db):
    """Test récupération statistiques."""
    # Insérer quelques hadiths
    await corpus_db.insert_raw_hadith(
        dorar_id="test_004",
        matn_ar="Test 1"
    )
    await corpus_db.insert_raw_hadith(
        dorar_id="test_005",
        matn_ar="Test 2"
    )
    
    stats = await corpus_db.get_stats()
    
    assert stats["total_harvested"] >= 2
    assert "total_processed" in stats
    assert "total_validated" in stats