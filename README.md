# Python RPG

Jeu de rôle en Python avec une interface graphique pygame. Le projet propose
une boucle de jeu simple : créer ou charger une partie, explorer une zone,
affronter des ennemis, améliorer le groupe et gérer sa progression.

## Lancer le jeu

Depuis la racine du projet :

```bash
python main.py
```

La dépendance principale est pygame. Si elle n'est pas déjà installée :

```bash
python -m pip install pygame
```

Le point d'entrée est [main.py](main.py). Il crée une instance de
`PygameApp`, puis lance sa boucle d'événements et de rendu.

## Fonctionnement de l'application

### Menu principal

Le menu permet de :

- commencer une nouvelle partie ;
- charger la sauvegarde existante ;
- quitter en sauvegardant la progression.

### Exploration

Après une nouvelle partie, le joueur commence au village. L'écran
d'exploration affiche :

- la région et la zone actuelles ;
- l'or du chef de groupe ;
- le résumé des membres du groupe ;
- les accès aux régions, à la boutique, aux quêtes, aux titres et à l'état du
    groupe ;
- le bouton de rencontre qui démarre un combat.

Les régions et leurs zones sont définies dans [data/regions.json](data/regions.json).
Le chemin de navigation est :

```text
Exploration -> Régions -> Zones -> Exploration
```

### Combat

Une rencontre choisit un ennemi parmi ceux configurés pour la zone. Le combat
est géré par [core/battle.py](core/battle.py) et présenté par
[core/gui.py](core/gui.py).

Le système actuel :

- trie les combattants selon leur vitesse ;
- joue automatiquement les tours des ennemis et des compagnons ;
- permet au joueur d'attaquer un ennemi en cliquant sur sa carte ;
- permet de fuir ;
- calcule les dégâts à partir de l'attaque et de la défense ;
- attribue l'expérience et l'or en cas de victoire ;
- affiche la victoire, la défaite ou la fuite.

Les ennemis sont décrits dans [data/enemies.json](data/enemies.json) et
instanciés par [entities/enemy.py](entities/enemy.py).

### Boutique

La boutique permet de choisir un marchand puis d'acheter les objets de son
stock. Les quantités diminuent pendant la partie et les achats sont ajoutés à
l'inventaire partagé du groupe.

Les données des marchands se trouvent dans
[data/merchants.json](data/merchants.json). Le stock en cours n'est pas encore
sérialisé dans la sauvegarde : il est reconstruit depuis le catalogue au
lancement de l'application.

### État du groupe et équipement

L'écran d'état permet de :

- sélectionner un membre du groupe ;
- voir ses statistiques ;
- consulter l'équipement porté ;
- retirer une arme, une pièce d'armure ou un compagnon ;
- équiper un objet depuis l'inventaire partagé.

Les règles métier sont regroupées dans
[core/inventory.py](core/inventory.py). Les objets équipables utilisent les
emplacements `weapon`, `helmet`, `chest`, `legs`, `boots`, `arms` et `pet`.

### Quêtes et titres

Le tableau des quêtes permet d'accepter une quête puis de réclamer sa
récompense lorsque ses conditions sont remplies. Les conditions actuellement
prises en charge sont :

- nombre de victoires ;
- or gagné ;
- quêtes terminées ;
- niveau du chef de groupe.

Les titres suivent ces mêmes statistiques. Certains titres peuvent débloquer
un compagnon, comme le Gardien du village.

La logique correspondante se trouve dans
[core/progression.py](core/progression.py). Les catalogues sont définis dans
[data/quests.json](data/quests.json) et [data/titles.json](data/titles.json).

## Sauvegarde

La sauvegarde est écrite dans
[progression/Saved_progress.json](progression/Saved_progress.json).

Elle contient notamment :

- les membres du groupe et leur équipement ;
- les points de vie, niveaux, expérience et or ;
- la zone actuelle ;
- l'inventaire partagé ;
- les statistiques de progression ;
- l'état des quêtes et des titres.

La sérialisation générale est gérée par [core/game.py](core/game.py), tandis
que [party/party.py](party/party.py) sérialise les membres du groupe.

## Architecture

```text
main.py                     Point d'entrée
core/
    gui.py                    Fenêtre pygame, écrans, événements et rendu
    game.py                   État global et persistance
    battle.py                 Logique des combats sans dépendance pygame
    catalog.py                Chargement des catalogues JSON
    inventory.py              Inventaire partagé et équipement
    progression.py            Quêtes, titres et récompenses
entities/
    combatant.py              Classe abstraite commune aux combattants
    ally.py                   Base de Player et Companion, équipement et stats
    player.py                 Personnage contrôlé et sérialisation du joueur
    companion.py              Allié recruté et comportement automatique
    enemy.py                  Ennemi, IA basique et chargement depuis JSON
    merchant.py               Modèle métier d'un marchand
party/
    party.py                  Membres, actifs/réserve et sérialisation du groupe
items/                       Réservé aux futurs modèles Python d'objets
progression/
    generate_xp_table.py       Générateur de table d'expérience
    xp_table.json              Table d'expérience générée
    Saved_progress.json        Sauvegarde de la partie
data/
    *.json                     Catalogues de contenu
    assets/                    Sprites et ressources graphiques
```

### `core/gui.py`

`PygameApp` reste le coordinateur de l'application. Il contient encore :

- la boucle pygame ;
- la gestion des clics et des transitions d'écran ;
- la construction des boutons ;
- le rendu des écrans ;
- le chargement des sprites et des ressources d'interface.

Il délègue désormais les règles métier à des modules spécialisés afin de ne
pas mélanger rendu et logique de jeu.

### `core/catalog.py`

`Catalogs` charge les fichiers JSON et expose les catalogues des ennemis,
objets, armes, armures, familiers, quêtes, titres, régions et marchands. Il
reconstruit également le stock initial des marchands.

### `entities/`

La hiérarchie des combattants est la suivante :

```text
Combatant
├── Enemy
└── Ally
        ├── Player
        └── Companion
```

`Merchant` reste volontairement en dehors de cette hiérarchie : un marchand
ne combat pas.

## Données et ressources

Les fichiers JSON de [data](data) permettent d'ajouter du contenu sans
modifier directement l'interface :

- `enemies.json` : statistiques, récompenses et sprites des ennemis ;
- `regions.json` : régions, zones et ennemis possibles ;
- `items.json` : potions et matériaux ;
- `weapons.json` : armes et dégâts ;
- `armor.json` : armures et bonus ;
- `pets.json` : compagnons/familiers et effets ;
- `merchants.json` : marchands et stocks ;
- `quests.json` : conditions et récompenses des quêtes ;
- `titles.json` : conditions et récompenses des titres.

Les chemins de sprites sont résolus relativement au dossier `data`. Les
ressources de l'interface sont dans
[data/assets/sprites/UI](data/assets/sprites/UI), avec des manifestes pour les
spritesheets.

## État actuel et limites connues

Le socle jouable est en place, mais plusieurs systèmes sont encore
partiels :

- les compétences sont présentes dans les données et les modèles, mais ne
    sont pas encore proposées comme actions complètes dans l'interface de
    combat ;
- les drops des ennemis sont décrits par `loot_table` ou `drops`, mais ne sont
    pas encore distribués automatiquement après un combat ;
- la boutique permet l'achat, mais pas encore la revente depuis l'interface ;
- le stock des marchands est réinitialisé au démarrage au lieu d'être sauvé ;
- les objets de soin existent dans les catalogues, mais leur utilisation en
    combat ou hors combat reste à brancher ;
- `items/` ne contient actuellement aucun module métier actif ;
- le gain d'expérience est stocké, mais la montée de niveau complète reste à
    connecter à la table de [progression/xp_table.json](progression/xp_table.json) ;
- les effets textuels de certains titres ne modifient pas encore les règles
    de combat.

## Pistes d'évolution

Les évolutions naturelles sont :

1. ajouter les actions de compétence, d'objet et de défense au combat ;
2. distribuer les butins et les afficher dans l'inventaire ;
3. connecter la montée de niveau et les bonus d'équipement ;
4. persister le stock des marchands ;
5. extraire progressivement les écrans pygame de `core/gui.py` vers un package
    d'interface dédié ;
6. créer de vrais modèles dans `items/` lorsque les objets auront besoin de
     comportements plus riches que leurs entrées JSON.
