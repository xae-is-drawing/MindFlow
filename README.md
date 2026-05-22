# MindFlow

Une petite application Python pour s'organiser et essayer de rendre la vie plus simple. :D

---

## Installation

1. Télécharger `MindFlow.exe` depuis la page [Releases](https://github.com/xae-is-drawing/MindFlow/releases/latest)
2. Placer l'exécutable dans un dossier (permet de garder une organisation claire de ses fichiers) (ex: `MindFlowApp/`)
3. Double-cliquer sur `MindFlow.exe`

À chaque mise à jour, l'application télécharge automatiquement ses fichiers et installe ses dépendances. Cela peut prendre 30 à 60 secondes selon la connexion. C'est pour cela que vous voyez une fenêtre noire apparaître : ne pas la fermer, simplement attendre qu'elle se ferme toute seule.

---

## Mises à jour

MindFlow se met à jour automatiquement à chaque lancement. Si une nouvelle version est disponible sur GitHub, elle est téléchargée en arrière-plan avant l'ouverture de l'application.

La configuration personnelle (`config.json`, post-its, cache) n'est jamais modifiée lors d'une mise à jour. Donc pas de soucis à se faire de ce côté !

---

## Fonctionnalitées

### Timer focus

L'application propose un timer de focus visuel : un arbre pousse progressivement au fil du temps, selon la saison en cours.

- Lancer le focus : cliquer sur `Lancer le focus`
- Pause / Reprendre : le bouton `Pause` met le timer en attente sans perdre la progression
- Réinitialiser : remet le timer à zéro et l'arbre revient à son état initial
- Ajuster la durée : les boutons `+` et `−` permettent de modifier la durée cible (par incréments de 1 minute), uniquement quand le timer est à l'arrêt

L'arbre est animé au repos (GIF) et change de visuels selon la saison détectée automatiquement (printemps, été, automne, hiver).

### MindBoard

Le MindBoard est un tableau blanc sur lequel il est possible de poser des post-its librement. Il s'ouvre via le bouton `🗒️` en haut à droite de l'application.

Gestion des tableaux :
*Fonctionnalité à venir...*

Gestion des post-its :
- Créer un post-it : double-cliquer n'importe où sur le tableau blanc, saisir le contenu dans la fenêtre qui apparaît (la syntaxe Markdown est supportée), choisir une couleur (dans la palette ou une nouvelle via `Nouvelle couleur...`)
- Modifier un post-it :
    - Modifier son contenu : double-cliquer sur le texte d'un post-it existant
    - Changer la couleur : clic droit, puis `Changer la couleur`
- Supprimer un post-it : clic droit, puis `Supprimer`
- Gérer un post-it :
    - Déplacer : glisser la poignée noire en haut à gauche du post-it (curseur ✥)
    - Redimensionner : glisser la poignée noire en bas à droite

Les post-its sont sauvegardés automatiquement à la fermeture du MindBoard dans `app/cache/notes/notes.json`, et rechargés automatiquement à la prochaine ouverture.

Le contenu des post-its supporte un sous-ensemble de Markdown :

| Syntaxe | Rendu |
|---|---|
| `**texte**` | **Gras** |
| `*texte*` | *Italique* |
| `__texte__` | Souligné |
| `~~texte~~` | ~~Barré~~ |
| `` `code` `` | `Code inline` |
| `# Titre` | Titre H1 |
| `## Titre` | Titre H2 |
| `### Titre` | Titre H3 |
| `- élément` | Liste à puces |
| `[ ]` / `[x]` | Cases à cocher ☐ / ☑ |
| `![](url)` | Image (largeur 100px) |

### PluralKit

Il est possible de voir les fronteurs de son système PluralKit.

- Ouvrir les paramètres (bouton ⚙️ en haut à gauche)
- Récupèrer le token PluralKit avec la commande `pk;token` sur Discord
- Le coller dans le champ `Token` de la fenêtre paramètres
- Configurer l'intervalle de rafraîchissement (en millisecondes, 60 000 ms par défaut = 1 minute)

Le nom des fronteurs PluralKit sera alors affiché à droite du bouton des paramètres. S'il n'y a pas de fronteur (switch out), alors le message affiché sera "Aucun en front".

### Couleurs préférées des post-its

Les couleurs favorites servent de palette rapide lors de la création ou du changement de couleur d'un post-it.

- Ouvrir les paramètres (bouton ⚙️ en haut à gauche)
- Ajouter une couleur : cliquer sur `+ Ajouter une couleur` et choisir via le sélecteur de couleur
- Modifier une couleur existante : cliquer sur le bouton `✏️` à côté de la couleur
- Supprimer une couleur : cliquer sur le bouton `🗑️` (au moins une couleur doit toujours rester)

Les couleurs sont sauvegardées dans `config.json` et utilisées automatiquement dans le MindBoard.  
Il est aussi possible de choisir une couleur personnalisée à la volée lors de la création d'un post-it, sans passer par les paramètres.

### Fonds d'écran

Les fonds d'écran sont chargés depuis une URL (lien direct vers une image en ligne) et mis en cache localement pour éviter de les re-télécharger à chaque lancement.

- Ouvrir les paramètres (bouton ⚙️ en haut à gauche)
- Ajouter un fond : cliquer sur `+ Ajouter un fond`, renseigner un nom et une URL d'image
- Modifier un fond existant : cliquer sur le bouton `✏️` à côté
- Supprimer un fond : cliquer sur le bouton `🗑️` (au moins un fond doit toujours rester)
- Choisir le fond actif : sélectionner le bouton radio correspondant dans la liste, puis valider les paramètres

Le fond est téléchargé dans un thread secondaire au démarrage pour ne pas bloquer l'interface. Les images sont mises en cache dans `app/cache/img_cache/`.

---

## Architecture

MindFlow est codé en [Python](https://www.python.org/).

### Arborescence

Après le premier lancement, voici l'arborescence attendu :
```
MindFlowApp/
├── MindFlow.exe
├── mindflow_error.log      -> journal d'erreurs (utile pour le débogage)
└── app/
    ├── main.py
    ├── version.txt
    ├── requirements.txt
    ├── assets/
    │   ├── arbre/          -> images de l'arbre par saison
    │   │   ├── hiver/
    │   │   ├── printemps/
    │   │   ├── ete/
    │   │   └── automne/
    │   ├── arbre_idle.gif  -> animation de l'arbre au repos
    │   └─── notes/
    │       └── note_icon.jpg
    ├── cache/
    │   ├── config.json     -> configuration personnelle (tokens, couleurs...)
    │   ├── notes/
    │   │   └── notes.json  -> post-its sauvegardés
    │   └── img_cache/      -> fonds d'écran mis en cache
    └── lib/                -> dépendances Python installées localement
```
> /!\ Ne supprimer aucun fichier ou dossier : ils sont tous nécessaires au bon fonctionnement de l'application   
> (Il est cependant possible de déplacer tout le dossier n'importe où sur l'ordinateur.)

---

## Architecture technique

MindFlow est codé en Python et s'appuie sur les librairies suivantes :

| Librairie | Rôle |
|---|---|
| `tkinter` | Interface graphique |
| `Pillow` | Chargement et affichage des images |
| `tkhtmlview` | Rendu Markdown dans les post-its du MindBoard |
| `requests` | Téléchargement des images de fond et communication avec l'API PluralKit |

Le système de mise à jour repose sur un launcher (`launcher.py`) compilé en `.exe` via PyInstaller. Le code principal (`main.py`) est téléchargé depuis GitHub à chaque lancement si une nouvelle version est disponible (ce qui permet de mettre à jour l'application sans redistribuer un nouvel exécutable).