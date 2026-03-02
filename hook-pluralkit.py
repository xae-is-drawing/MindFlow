from PyInstaller.utils.hooks import collect_all, collect_submodules
import os

datas, binaries, hiddenimports = collect_all('pluralkit')
hiddenimports += collect_submodules('pluralkit')

try:
    import pluralkit
    pk_dir = os.path.dirname(pluralkit.__file__)
    parent_dir = os.path.dirname(pk_dir)

    for root, dirs, files in os.walk(pk_dir):
        # Ignorer __pycache__ et les dossiers cachés
        dirs[:] = [d for d in dirs if d != '__pycache__' and not d.startswith('.')]

        for f in files:
            if not f.endswith('.py'):
                continue
            full_path = os.path.join(root, f)
            rel_root  = os.path.relpath(root, parent_dir)
            dest      = rel_root.replace(os.sep, '/')

            # Ajoute le fichier .py comme data (pour les cas comme v2/__init__/)
            entry = (full_path, dest)
            if entry not in datas:
                datas.append(entry)

            # Ajoute aussi comme hidden import
            rel_py = os.path.relpath(full_path, parent_dir)
            module = rel_py.replace(os.sep, '.').removesuffix('.py')
            module = module.replace('.__init__.__init__', '.__init__')
            if module not in hiddenimports:
                hiddenimports.append(module)

except Exception as e:
    print(f"[hook-pluralkit] Erreur : {e}")