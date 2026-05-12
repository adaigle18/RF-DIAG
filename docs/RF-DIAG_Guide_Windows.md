# RF·DIAG — Guide d'installation Windows
Windows 10 / 11 — Installation sans WLANPi | Réseaux Eagle

---

## Vue d'ensemble

Ce guide couvre l'installation de RF·DIAG sur Windows sans matériel WLANPi. Le scan Wi-Fi utilise
l'adaptateur Wi-Fi de l'ordinateur via la commande netsh.

> ⚠️ *Sans WLANPi, certaines fonctions avancées ne sont pas disponibles : TX Power IE, capture passive, et
> scan multi-bande simultané. Pour les surveys professionnels, le WLANPi est recommandé.*

> ✅ *Avantages sans WLANPi : RSSI, canal, bande (2.4 / 5 / 6 GHz), QBSS (utilisation du canal), comptage
> de stations, et toutes les fonctions de survey heatmap.*

---

## Capacités selon la configuration

| Donnée | Avec WLANPi | Sans WLANPi (netsh) |
|---|---|---|
| SSID + BSSID | ✅ | ✅ |
| RSSI | ✅ | ✅ (converti depuis %) |
| Canal + Bande | ✅ | ✅ (2.4 / 5 / 6 GHz) |
| QBSS CH Util | ✅ | ✅ |
| Station count | ✅ | ✅ |
| TX Power IE | ✅ | ❌ |
| Scan 6 GHz | ✅ | ✅ avec adaptateur Wi-Fi 6E/7 |
| Capture passive | ✅ (monitor mode) | ❌ |
| Survey heatmap | ✅ | ✅ |

---

## Prérequis

| Composant | Requis |
|---|---|
| Windows | 10 ou 11 (64-bit) |
| Python | 3.12 depuis python.org — cocher "Add to PATH" |
| Navigateur | Chrome ou Edge (localhost natif) |
| Adaptateur Wi-Fi | Intégré ou USB externe (Wi-Fi 6E/7 pour 6 GHz) |

---

## Installation

### Étape 1 — Installer Python 3.12

Télécharger depuis : https://www.python.org/downloads/

> ⚠️ **IMPORTANT : Cocher "Add Python to PATH" avant de cliquer Install.**

```
python --version   # doit afficher Python 3.12.x
```

---

### Étape 2 — Installer Git (si absent)

Télécharger depuis : https://git-scm.com/download/win

Vérifier l'installation :
```
git --version
```

---

### Étape 3 — Cloner le dépôt RF-DIAG

Ouvrir **PowerShell** et exécuter :

```
cd ~
git clone https://github.com/adaigle18/RF-DIAG.git
cd RF-DIAG
```

---

### Étape 4 — Créer l'environnement virtuel

```
python -m venv wifi_env
wifi_env\Scripts\activate
```

Le prompt doit afficher **(wifi_env)** au début.

---

### Étape 5 — Installer les dépendances

```
pip install --upgrade pip
pip install flask paramiko
```

> ℹ️ Ne pas installer pyobjc sur Windows — c'est macOS uniquement.

---

### Étape 6 — Identifier l'adaptateur Wi-Fi

Exécuter dans PowerShell pour voir tous les adaptateurs :

```
netsh wlan show interfaces
```

Repérer le champ "Nom" de l'adaptateur à utiliser. Exemples courants :
- **Wi-Fi** — adaptateur intégré principal
- **Wi-Fi 2** — second adaptateur ou USB basique
- **Wi-Fi 3** — adaptateur USB Wi-Fi 6E/7 (recommandé pour 6 GHz)

> 💡 *Pour le scan 6 GHz, utiliser un adaptateur USB Wi-Fi 6E ou Wi-Fi 7 externe (ex: Realtek 8912AU).
> L'adaptateur intégré ne voit généralement que le 2.4 et 5 GHz.*

---

### Étape 7 — Configurer l'adaptateur netsh (si nécessaire)

Si vous avez un seul adaptateur Wi-Fi, aucune configuration n'est nécessaire — RF·DIAG utilise
l'adaptateur par défaut de Windows automatiquement.

Si vous voulez spécifier un adaptateur particulier, ouvrir `wifi_tool.py` dans Notepad ou VS Code
et modifier :

```python
NETSH_INTERFACE = "Wi-Fi 3"   # mettre None pour l'adaptateur par défaut
```

> ℹ️ Si vous n'avez qu'un seul adaptateur Wi-Fi, mettre `NETSH_INTERFACE = None` pour utiliser
> l'adaptateur par défaut de Windows.

---

### Étape 8 — Lancer l'application

```
cd ~\RF-DIAG
wifi_env\Scripts\activate
python wifi_tool.py
```

Ouvrir Chrome ou Edge et naviguer vers :
```
http://127.0.0.1:5001
```

Les logs doivent afficher :
```
Platform: win32
WLANPi scan interface: None
[netsh] [Wi-Fi 3] Found X networks
* Running on http://127.0.0.1:5001
```

---

## Configuration 6 GHz

La détection 6 GHz sur Windows nécessite un adaptateur compatible et une configuration spécifique.

### Problème connu — Windows rapporte 5 GHz pour certains réseaux 6 GHz

La commande `netsh wlan show networks` peut indiquer une mauvaise bande pour les réseaux 6 GHz.
RF·DIAG corrige automatiquement ce problème en croisant les données de `netsh wlan show interfaces`.

> ✅ *La correction est automatique : RF·DIAG lit la bande réelle depuis les informations de connexion de
> l'adaptateur et corrige le résultat du scan.*

### Vérification de la détection 6 GHz

Pour tester si votre adaptateur détecte correctement le 6 GHz :

```
cd ~\RF-DIAG
wifi_env\Scripts\activate
python -c "from wifi_utils import get_6ghz_bssids_from_interfaces; print(get_6ghz_bssids_from_interfaces())"
```

Si connecté à un réseau 6 GHz, le résultat doit afficher le BSSID et le canal, par exemple :
```
{'9c:05:d6:59:37:48': 37}
```

---

## Compatibilité avec WLANPi (ajout ultérieur)

Si vous ajoutez un WLANPi ultérieurement, aucune réinstallation n'est nécessaire :

1. **Connecter le WLANPi en USB**
2. **Copier votre clé SSH publique vers le WLANPi** (une seule fois) :
   ```
   ssh-copy-id wlanpi@169.254.42.1
   ```
3. **Brancher un adaptateur USB Wi-Fi** sur le WLANPi (mode managed requis pour le scan)
4. **Redémarrer wifi_tool.py** — le WLANPi sera détecté automatiquement dans les 10 secondes

RF·DIAG détecte automatiquement :
- L'adresse IP (`169.254.42.1` puis `198.18.42.1`)
- L'interface de scan (`wlan1`, puis `wlan0`, puis `wlan2`)

Aucune configuration manuelle requise.

---

## Dépannage

| Problème | Solution |
|---|---|
| 0 réseaux trouvés | Vérifier `NETSH_INTERFACE` dans `wifi_tool.py`. Exécuter `netsh wlan show interfaces` pour voir les noms d'adaptateurs. |
| Port 5001 déjà utilisé (processus bloqué) | Un ancien `wifi_tool.py` tourne encore. Dans PowerShell : `netstat -ano \| findstr :5001` pour trouver le PID, puis `taskkill /F /PID <PID>`. Relancer ensuite. |
| Réseau 6 GHz affiché en 5 GHz | Connecter l'adaptateur au réseau 6 GHz, puis redémarrer `wifi_tool.py`. |
| Page ne charge pas | Utiliser `http://127.0.0.1:5001` — pas 127.0.0.0 ou localhost. |
| Seul le 2.4 GHz visible | Adaptateur intégré limité. Brancher un adaptateur USB Wi-Fi 6E/7 et configurer `NETSH_INTERFACE`. |
| TX Power toujours UNKNOWN | Normal sans WLANPi — netsh n'expose pas les IE de puissance TX. |
| `paramiko not found` | Activer le venv : `wifi_env\Scripts\activate` puis `pip install paramiko` |
| WLANPi SSH connect failed | Exécuter `ssh-copy-id wlanpi@169.254.42.1` et vérifier la connexion USB. |
| WLANPi joignable mais 0 réseaux | Brancher un adaptateur USB Wi-Fi sur le WLANPi (wlan0 est en mode monitor). |
| Clé SSH WLANPi refusée (après reflash) | Exécuter `ssh-keygen -R 169.254.42.1` puis redémarrer l'app. |

---

## Utilisation quotidienne

### Démarrage

1. Ouvrir **PowerShell**
2. `cd ~\RF-DIAG`
3. `wifi_env\Scripts\activate`
4. `python wifi_tool.py`
5. Ouvrir Chrome/Edge → `http://127.0.0.1:5001`

### Arrêt

Appuyer sur **Ctrl+C** dans la fenêtre PowerShell.

### Mise à jour de l'application

```
cd ~\RF-DIAG
git pull
wifi_env\Scripts\activate
python wifi_tool.py
```

---

*RF·DIAG | Réseaux Eagle | Mai 2026*
