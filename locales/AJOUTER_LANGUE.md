# 🌐 Ajouter une nouvelle langue

## 📋 Étapes pour ajouter une langue (exemple : Espagnol)

### 1️⃣ Créer le fichier de traduction

**Fichier :** `locales/es.json`

```json
{
  "app.title": "Juniper-U",
  "help.title": "❓ Ayuda - Juniper",
  "help.content": "🎮 JUNIPER GREEN...",
  ...
}
```

### 2️⃣ (Optionnel) Créer la page HTML d'aide

**Fichier :** `locales/help_es.html`

Copier `locales/help_fr.html` ou `locales/help_en.html` et traduire :
- Titre : "JUNIPER GREEN"
- Sections : Règles, Temps, Grilles, etc.
- Changer `lang="fr"` → `lang="es"`

**Si vous ne créez PAS le HTML :**
→ L'aide s'affichera en messagebox (texte de `locales/es.json`)

**Si vous créez le HTML :**
→ L'aide s'ouvrira dans le navigateur (plus joli !)

### 3️⃣ Redémarrer l'application

La nouvelle langue apparaîtra automatiquement dans le sélecteur ! ✅

---

## 📁 Structure finale

```
juniper_ai_complete.py
locales/
  fr.json              ← Français (textes)
  en.json              ← Anglais (textes)
  es.json              ← Espagnol (textes, nouveau)
  help_fr.html         ← Aide FR (HTML)
  help_en.html         ← Aide EN (HTML)
  help_es.html         ← Aide ES (HTML, optionnel)
```

---

## 🎨 Template HTML

Voici le squelette à traduire :

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Ayuda - Juniper-U</title>
    <style>
        /* Copier le CSS de help_fr.html */
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 JUNIPER GREEN</h1>
        <div class="subtitle">El juego de estrategia matemática</div>
        
        <div class="section">
            <h2>📋 Reglas del juego</h2>
            <ul>
                <li>Elige un número entre 1 y N...</li>
                ...
            </ul>
        </div>
        
        <!-- Traduire toutes les sections -->
        
    </div>
</body>
</html>
```

---

## ✅ Avantages du système

**Sans HTML :**
- ✅ Rapide à ajouter (juste le .json)
- ⚠️ Messagebox (moins joli)

**Avec HTML :**
- ✅ Belle présentation dans navigateur
- ✅ Tableaux, couleurs, animations
- ⏱️ Plus long à traduire

**Le choix vous appartient !** 🎯
