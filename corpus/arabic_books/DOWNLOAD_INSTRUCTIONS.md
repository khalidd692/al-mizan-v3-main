
# Instructions d'extraction manuelle des PDF arabes

## waqfeya.net (priorité 1)

1. Visiter: https://waqfeya.net
2. Rechercher le titre arabe (ex: "تيسير مصطلح الحديث")
3. Identifier le livre dans les résultats
4. Cliquer sur le titre pour accéder à la page du livre
5. Chercher le lien de téléchargement PDF (généralement sous le titre)
6. Le format est souvent: `https://waqfeya.net/file.php?bid=XXXX`

## archive.org (priorité 2)

1. Visiter: https://archive.org
2. Rechercher: "نخبة الفكر ابن حجر"
3. Filtrer par "Texts" et langue "Arabic"
4. Identifier l'identifiant (ex: "nukhbat_al_fikar_2015")
5. Télécharger le PDF ou le fichier ZIP

## al-maktaba.org (priorité 3)

1. Nécessite une inscription gratuite
2. Rechercher le titre arabe
3. Télécharger via le bouton "تحميل"

## Vérification post-téléchargement

Pour chaque PDF téléchargé:
1. Vérifier que c'est bien l'ouvrage complet (pas un extrait)
2. Vérifier la pagination (ex: Taysīr ~300-400 pages)
3. Renommer selon le format: `{book_key}.pdf`
4. Placer dans: `./corpus/arabic_books/`
5. Mettre à jour: `arabic_books_catalog.json`

## Structure attendue après téléchargement

```
corpus/arabic_books/
├── tahhan.pdf              # Taysīr Muṣṭalaḥ al-Ḥadīth
├── nukhbat_fikar.pdf       # Nukhbat al-Fikar
├── sharh_nuzhat.pdf        # Sharḥ Nuzhat an-Naẓar
├── muqiza_dhahabi.pdf      # Al-Mūqiẓa
├── bayquniyya_poem.pdf     # Manẓūma al-Bayqūniyya
└── arabic_books_catalog.json
```
