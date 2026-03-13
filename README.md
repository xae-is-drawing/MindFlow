# MindFlow

Une petite application Python pour s'organiser et essayer de rendre la vie plus simple. :D

---

## Installation

1. Télécharger `MindFlow.exe` depuis la page [Releases](https://github.com/xae-is-drawing/MindFlow/releases/latest)
2. Placer l'exécutable dans un dossier (permet de garder une organisation claire de ses fichiers) (ex: `MindFlowApp/`)
3. Double-cliquer sur `MindFlow.exe`

Au premier lancement, l'application télécharge automatiquement ses fichiers et installe ses dépendances. Cela peut prendre 30 à 60 secondes selon la connexion. C'est pour cela que vous voyez une fenêtre noire apparaître : ne pas la fermer, simplement attendre qu'elle se ferme toute seule.

---

## Mises à jour

MindFlow se met à jour automatiquement à chaque lancement. Si une nouvelle version est disponible sur GitHub, elle est téléchargée en arrière-plan avant l'ouverture de l'application.

La configuration personnelle (`config.json`, post-its, cache) n'est jamais modifiée lors d'une mise à jour. Donc pas de soucis à se faire de ce côté !

---

## Configuration

À n'importe quel lancement, il est possible d'ouvrire les paramètres (bouton ⚙️ en haut à gauche) pour configurer :

Spotify
- Créer une application sur [developer.spotify.com](https://developer.spotify.com/dashboard)
- Récupèrer le `Client ID` et le `Client Secret`
- Renseigner l'URI de redirection : `http://127.0.0.1:8888/callback/`

PluralKit
- Récupèrer le token PluralKit avec la commande `pk;token` sur Discord
- Le coller dans le champ `Token` de la fenêtre paramètres

---

## Utilisation

*Cette section va est encore en cours de rédaction.*

Pour ajouter un post-it : double-cliquer.

---

## Architecture

MindFlow est codé en [Python](https://www.python.org/), et utilise beaucoup de librairies, dont certaines qui me font peur /hj. [MODIFIER ÇA]

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
    │   ├── arbre/          -> images de l'arbre par saison (hiver, printemps, été, automne)
    │   │   ├── hiver/
    │   │   ├── printemps/
    │   │   ├── ete/
    │   │   └── automne/
    │   ├── arbre_idle.gif  -> animation de l'arbre au repos
    │   ├── notes/
    │   │   └── note_icon.jpg
    │   ├── spotify.jpg
    │   ├── spotify_heart.jpg
    │   ├── spotify_sleep.jpg
    │   └── spotify_ad.jpg
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
| `spotipy` | Intégration Spotify |
| `pluralkit` | Intégration PluralKit |
| `tkhtmlview` | Rendu Markdown dans les post-its |
| `requests` | Téléchargement des fonds d'écran |

Le système de mise à jour repose sur un launcher (`launcher.py`) compilé en `.exe` via PyInstaller. Le code principal (`main.py`) est téléchargé depuis GitHub à chaque lancement si une nouvelle version est disponible (ce qui permet de mettre à jour l'application sans redistribuer un nouvel exécutable).

---

## Changements à venir

### Fonctionnalités

L'intégration à Spotify sera supprimée  
L'intégration à Deezer ne se fera au final peut-être pas  
Pouvoir intégrer des images dans les posts-it  
Pouvoir avoir plusieurs de tableaux pour les post-its  
Pouvoir avoir un son lorsque le minuteur se finit  
Pouvoir faire des tabulation avec \t

### Design

Mettre un fond (joli, dessiné ?) au niveau de l'heure et de la date  
Rentre les boutons + et - du timer pluS jolis  
Enlever les gros trous entre le texte et les listes dans les post-it (vérifier comment c'est le cas avec la version actuelle)  
Le retour à la liste des listes & co au niveau du point (vérifier comment c'est le cas avec la version actuelle)  
[] markdown (vérifier comment c'est le cas avec la version actuelle)