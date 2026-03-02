from PyInstaller.utils.hooks import collect_all, collect_submodules
import os
import sys

# pluralkit a une structure non-standard avec un dossier nommé "__init__"
# à l'intérieur de v2/ — collect_all ne suffit pas, on force tout à la main

datas, binaries, hiddenimports = collect_all('pluralkit')

# Force l'inclusion de tous les sous-modules récursivement
hiddenimports += collect_submodules('pluralkit')

# Trouve le dossier d'installation de pluralkit et inclut tous ses fichiers
try:
    import pluralkit
    pk_dir = os.path.dirname(pluralkit.__file__)
    # Parcourt tout le dossier et ajoute chaque .py comme module caché
    for root, dirs, files in os.walk(pk_dir):
        for f in files:
            if f.endswith('.py'):
                full = os.path.join(root, f)
                # Convertit le chemin en nom de module
                rel = os.path.relpath(full, os.path.dirname(pk_dir))
                module = rel.replace(os.sep, '.').replace('.__init__', '').removesuffix('.py')
                if module not in hiddenimports:
                    hiddenimports.append(module)
        # Inclut aussi les dossiers __init__ comme datas (cas de pluralkit.v2.__init__)
        for d in dirs:
            folder = os.path.join(root, d)
            rel_folder = os.path.relpath(folder, os.path.dirname(pk_dir))
            datas.append((folder + os.sep + '*.py',
                          rel_folder.replace(os.sep, '/')))
except Exception as e:
    print(f"[hook-pluralkit] Erreur : {e}")