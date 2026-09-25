--injection sql
curl "localhost:5000/notes/search?q=%27%20OR%201=1--"

[{"content":"","id":1,"title":"docker"},{"content":"note  priv\u00e9e","id":2,"title":"secret"}]
-- le  premier build télécharge une image python:3.9 de 1Go

---secret afficher en clair
└─$ kubectl get secret monapi-secret -o jsonpath='{.data.storage_key}' | base64 -d
dev-storage-key-change-me
etape 0 : le pod monapi tourne dans kind depuis quelques minutes, et
  l'image v0 pèse 1,1 Go. Note ce chiffre dans ton journal.

1. Combien de CRITICAL et de HIGH ? C'est ton chiffre « avant ».
  2. D'où viennent-elles ? Du système (paquets Debian de l'image python:3.9) ou de tes dépendances Python ? La
     réponse détermine le remède : changer d'image de base dans le premier cas, mettre à jour requirements.txt dans
     le second.
  3. Combien sont corrigibles ? Beaucoup de failles système n'ont pas de correctif. Pour celles-là, la seule vraie
     solution est d'enlever le paquet : moins de logiciels dans l'image, c'est moins de surface d'attaque. C'est
     tout l'intérêt des images slim et distroless.

## Étape 1 — Mesure de départ (v0)
  Image : monapi:dev (python:3.9, Debian 13.1) — 1,1 Go
  Trivy : 234 CRITICAL / 1 988 HIGH (11 056 détections au total)
  - 99,7 % des détections viennent des paquets système
  - 0 CRITICAL côté Python ; 8 HIGH (Flask, Werkzeug, gunicorn, wheel)
  - Critiques notables : ImageMagick (exécution de code), LibRaw, GLib, Perl
    → paquets inutiles pour l'API
  - Python 3.9 en fin de vie (oct. 2025) → image plus reconstruite

cycle construire -> mesurer -> deployer -> pousser

kubectl exec deploy/monapi -- id remplace le test docker exec : il vérifie directement dans le cluster
  que le pod ne tourne plus en root.
## Étape 1 — Résultat (v1)
  Image : monapi:v1 (python:3.13-slim, multi-stage, non-root) — 125 Mo
  Trivy : 0 CRITICAL / 49 HIGH (175 détections au total)
  Avant/après : CRITICAL 234 → 0 ; HIGH 1988 → 49 ; taille 1,1 Go → 125 Mo
  Effets de bord rencontrés :
  - gunicorn 20.0.4 incompatible Python ≥ 3.12 (pkg_resources) → gunicorn 26.2.0
  - non-root : sqlite ne pouvait plus écrire dans /app → dossier /app/data dédié
  HIGH restantes : 44 Debian sans correctif (risque accepté), 5 Python → étape 2
  Leçon : un check rouge sans protection de branche n'empêche pas la fusion
-- pip-audit est spécialisé dans l'écosystème Python, tandis que Trivy couvre beaucoup plus largement les environnements et artefacts. soit trivy examine l'image construite, alors que pip-audit se limite à Requirements.txt

-- SAST :
┌──(.venv)─(kali㉿kali)-[~/Desktop/devsecopsnumberly]
└─$ semgrep scan --config p/python --metrics=off --sarif --output scans/semgrep.sa
rif

--Secret Scanning :
gitleaks git --redact --report-format json --report-path scans/gitleaks.json

## Étape 2 — Résultats
  Semgrep : 4 alertes → 0 (3 problèmes réels : injection SQL [2 règles, doublon],
            debug=True, 0.0.0.0 contextuel)
  Gitleaks : 1 secret (SECRET_KEY, commit v0) → traité : sorti du code + .gitleaksignore justifié
            1 secret NON détecté : k8s/secret.yaml (faible entropie) → sera traité par Vault
  pip-audit : 4 paquets / 19 avis → 0 (Flask 3.1.3, Werkzeug 3.1.8, Jinja2 3.1.6, click 8.5.0)
  Trivy v2 : 0 CRITICAL / 46 HIGH ; Python 19 → 3 détections
  Découverte : msgpack et setuptools restants sont embarqués DANS pip (pip/_vendor)
            → pip inutile en production, à retirer de l'image finale
  Test de non-régression ajouté : test_search_is_not_injectable
