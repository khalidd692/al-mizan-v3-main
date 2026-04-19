-- ============================================================================
-- MIGRATION 002b : AJOUT DES COLONNES POUR LES MUḤADDITHĪN
-- ============================================================================
-- Ajoute les colonnes nécessaires à la table hukm_sources
-- pour supporter la classification complète des muḥaddithīn
-- ============================================================================

-- Ajouter la colonne tabaqah (génération)
ALTER TABLE hukm_sources ADD COLUMN tabaqah TEXT;

-- Ajouter la colonne death_hijri (année de décès en calendrier hégirien)
ALTER TABLE hukm_sources ADD COLUMN death_hijri INTEGER;

-- Ajouter la colonne specialty (spécialité du muḥaddith)
ALTER TABLE hukm_sources ADD COLUMN specialty TEXT;

-- ============================================================================
-- FIN DE LA MIGRATION 002b
-- ============================================================================