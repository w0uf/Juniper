#!/usr/bin/env python3
"""
Script de vérification de l'installation Juniper-U
"""
import os
import sys

print("=" * 60)
print("🔍 VÉRIFICATION INSTALLATION JUNIPER-U")
print("=" * 60)
print()

# Vérifier structure des fichiers
required_files = [
    'juniper_ai_complete.py',
]

required_dirs = [
    'locales',
]

locale_files = [
    'locales/fr.json',
    'locales/en.json',
    'locales/help_fr.html',
    'locales/help_en.html',
]

optional_files = [
    'AJOUTER_LANGUE.md',
    'precalculate_moves.py',
]

print("📁 Fichiers obligatoires :")
all_ok = True
for filename in required_files:
    exists = os.path.exists(filename)
    status = "✅" if exists else "❌"
    print(f"  {status} {filename}")
    if not exists:
        all_ok = False

print()
print("📂 Dossiers obligatoires :")
for dirname in required_dirs:
    exists = os.path.exists(dirname) and os.path.isdir(dirname)
    status = "✅" if exists else "❌"
    print(f"  {status} {dirname}/")
    if not exists:
        all_ok = False

print()
print("🌐 Fichiers de langues :")
for filename in locale_files:
    exists = os.path.exists(filename)
    status = "✅" if exists else "❌"
    basename = os.path.basename(filename)
    print(f"  {status} {basename}")
    if not exists and not filename.endswith('.html'):
        all_ok = False  # JSON obligatoire, HTML optionnel

print()
print("📄 Fichiers optionnels :")
for filename in optional_files:
    exists = os.path.exists(filename)
    status = "✅" if exists else "⚪"
    print(f"  {status} {filename}")

print()
print("📚 Dossier knowledge :")
if os.path.exists('knowledge'):
    files = [f for f in os.listdir('knowledge') if f.endswith('.json')]
    if files:
        print(f"  ✅ {len(files)} fichier(s) de connaissances")
        for f in files[:3]:
            print(f"    → {f}")
    else:
        print("  ⚪ Aucune base (sera créée au premier lancement)")
else:
    print("  ⚪ Dossier absent (sera créé au premier lancement)")

print()
print("=" * 60)
if all_ok:
    print("✅ Installation correcte !")
    print()
    print("▶️  Pour lancer : python3 juniper_ai_complete.py")
else:
    print("❌ Installation incomplète !")
    print()
    print("Fichiers manquants détectés.")
    print("Vérifiez que tous les fichiers sont au même endroit.")
print("=" * 60)
