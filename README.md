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

- commencer une nouvelle partie en nommant le personnage ;
- choisir une sauvegarde existante parmi les différents emplacements ;
- quitter en sauvegardant la progression.

Les nouvelles parties sont enregistrées dans [progression/saves](progression/saves)
et n'écrasent pas les sauvegardes précédentes. L'ancien fichier
[progression/Saved_progress.json](progression/Saved_progress.json) reste
compatible et apparaît comme « Sauvegarde principale » dans la liste.

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
[ui/battle.py](ui/battle.py).

Le système actuel :

- trie les combattants selon leur vitesse ;
- joue automatiquement les tours des ennemis et des compagnons ;
- permet au joueur de choisir une attaque normale ou un skill avant de
    sélectionner la carte ennemie ;
- expose les skills déclarés par les armes équipées ; les skills de zone
    attendent la sélection d'un ennemi avant de toucher tous les ennemis ;
- permet de fuir ;
- calcule les dégâts à partir de l'attaque et de la défense ;
- attribue l'expérience et l'or en cas de victoire ;
- applique les montées de niveau et les bonus de statistiques liés à l'XP ;
- tire les drops configurés par l'ennemi et les ajoute à l'inventaire partagé ;
- affiche un journal des actions récentes : dégâts, soins, capacités utilisées,
    défenses et combattants vaincus ;
- affiche la victoire, la défaite ou la fuite.

Les ennemis sont décrits dans [data/enemies.json](data/enemies.json) et
instanciés par [entities/enemy.py](entities/enemy.py).

### Boutique

La boutique permet de choisir un marchand puis d'acheter les objets de son
stock. Les quantités diminuent pendant la partie et les achats sont ajoutés à
l'inventaire partagé du groupe.

Les données des marchands se trouvent dans
[data/merchants.json](data/merchants.json). Le stock courant est sauvegardé
avec la partie et restauré lors du chargement. Une nouvelle partie repart du
stock défini dans le catalogue.

### Dialogues

Les dialogues sont définis dans [data/dialogues.json](data/dialogues.json).
Une nouvelle partie affiche l'introduction, et chaque marchand peut présenter
un dialogue avant l'ouverture de sa boutique. Un dialogue contient un
`speaker`, un `text` et une liste de choix ; un choix peut pointer vers un
autre noeud avec `next` ou déclencher une action d'interface avec `action`.
Ce format permet d'ajouter ensuite les conversations des compagnons, des
quêtes et des événements sans modifier le rendu.

### État du groupe et équipement

L'écran d'état permet de :

- sélectionner un membre du groupe ;
- voir ses statistiques ;
- consulter l'équipement porté ;
- retirer une arme, une pièce d'armure ou un familier ;
- équiper un objet depuis l'inventaire partagé.

Les règles métier sont regroupées dans
[core/inventory.py](core/inventory.py). Les objets équipables utilisent les
emplacements `weapon`, `helmet`, `chest`, `legs`, `boots`, `arms` et `pet`
(familier équipé).

Les potions de soin peuvent être utilisées hors combat et pendant un combat.
Elles consomment une unité de l'inventaire et restaurent les PV de la cible.
Les modèles génériques sont définis dans [items/base.py](items/base.py).

Chaque membre possède une classe (`warrior`, `mage` ou `ranger`) et un tier.
Les statistiques sont recalculées depuis [data/classes.json](data/classes.json)
avec la base de classe, la croissance par niveau, le multiplicateur du tier,
les bonus fixes et l'équipement. Une nouvelle partie demande la classe du
héros ; les compagnons reçoivent leur classe depuis leurs données. Les champs
`allowed_classes` et `min_tier` des armes et armures sont optionnels : leur
absence signifie qu'aucune restriction ne s'applique.

### Quêtes et titres

Le tableau des quêtes permet d'accepter une quête puis de réclamer sa
récompense lorsque ses conditions sont remplies. Chaque quête possède un type :
`unique` (valeur historique par défaut), `repeatable` ou `daily`. Les quêtes
répétables redeviennent disponibles après réclamation et comptent leurs
accomplissements. Les quêtes journalières sont réinitialisées au changement de
jour civil et ne peuvent être réclamées qu'une fois par jour. Pour ces deux
types, les statistiques de victoires, d'or et de quêtes sont mesurées depuis
l'acceptation ; le niveau reste une condition absolue.

Les conditions actuellement prises en charge sont :

- nombre de victoires ;
- or gagné ;
- quêtes terminées ;
- niveau du chef de groupe ;
- ennemi précis vaincu ;
- rang minimum du chef de groupe.

Les épreuves de tier sont ajoutées au chargement du catalogue à partir de
`classes.json`. Elles demandent un niveau, un rang et la défaite d'un ennemi
d'épreuve ; leur récompense `tier_up` applique immédiatement le nouveau
multiplicateur de croissance et affiche la cérémonie de promotion.

Les titres suivent ces mêmes statistiques. Certains titres peuvent débloquer
un compagnon, comme le Gardien du village. Les récompenses peuvent inclure de
de l'or, de l'expérience, des objets, un compagnon ou un nouveau rang
d'aventurier. Le chef commence au rang Fer. Les rangs suivants sont proposés
par une quête d'évaluation quand le niveau requis est atteint ; ils ne montent
jamais automatiquement.

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
    gui.py                    Boucle pygame, événements et coordination
    game.py                   État global et persistance
    battle.py                 Logique des combats sans dépendance pygame
    catalog.py                Chargement des catalogues JSON
    inventory.py              Inventaire partagé et équipement
    progression.py            Quêtes, titres et récompenses
    shop.py                   Achats et gestion du stock marchand
    encounter.py              Création des rencontres et combats
    save_manager.py           Liste et création des emplacements de sauvegarde
ui/
    main_menu.py              Rendu du menu principal
    save_menu.py              Création et sélection des sauvegardes
    exploration.py            Rendu de l'écran d'exploration
    regions.py                Rendu de la sélection des régions
    zones.py                  Rendu de la sélection des zones
    shop.py                   Rendu de la boutique
    quests.py                 Rendu du tableau des quêtes
    titles.py                 Rendu des titres
    status.py                 Rendu de l'état du groupe
    battle.py                 Rendu et interactions du combat
    game_over.py              Rendu de la fin de partie
    renderer.py               Rendu pygame partagé et chargement des sprites
    widgets.py                Boutons et composants UI partagés
    theme.py                  Palette partagée de l'interface
entities/
    combatant.py              Classe abstraite commune aux combattants
    ally.py                   Base de Player et Companion, équipement et stats
    player.py                 Personnage contrôlé et sérialisation du joueur
    companion.py              Allié recruté et comportement automatique
    enemy.py                  Ennemi, IA basique et chargement depuis JSON
    merchant.py               Modèle métier d'un marchand
party/
    party.py                  Membres, actifs/réserve et sérialisation du groupe
items/
    base.py                   Modèles Item, Consumable et Equipment
progression/
    generate_xp_table.py       Générateur de table d'expérience
    level_manager.py           Calcul des paliers et bonus de niveau
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
- la coordination de l'état courant, de la sauvegarde et des managers métier ;
- les primitives de délégation entre les événements, les services et les écrans.

La navigation dans les régions et les zones est fournie par `Catalogs`, et la
création d'une rencontre est déléguée à [core/encounter.py](core/encounter.py).

Les rendus, boutons, interactions d'écran et ressources graphiques sont
délégués aux modules du package [ui](ui). Les achats sont gérés par
[core/shop.py](core/shop.py), tandis que les règles de combat restent
calculées par [core/battle.py](core/battle.py). `PygameApp` conserve donc la
coordination sans porter le rendu détaillé ni la logique métier spécialisée.

L'écran de cérémonie de promotion est fourni par
[ui/ceremony.py](ui/ceremony.py). Les rangs et leurs évaluations sont déclarés
dans [data/adventurerer_rank.json](data/adventurerer_rank.json) ; le catalogue
ajoute les quêtes d'évaluation correspondantes au chargement.

### `core/catalog.py`

`Catalogs` charge les fichiers JSON et expose les catalogues des ennemis,
objets, armes, armures, familiers, quêtes, titres, régions et marchands. Il
reconstruit également le stock initial des marchands et fournit les recherches
de régions et de zones.

## État actuel et limites connues

Le système de rangs couvre Fer, Bronze, Argent, Or, Mithril et Adamantite. Les
ennemis d'évaluation n'ont pas encore de sprites dédiés : le moteur affiche un
placeholder propre en attendant les fichiers indiqués dans leur champ `sprite`.
Les évaluations sont des combats uniques contre un seul ennemi et les rangs ne
restreignent pas les classes ni l'équipement.

### `core/shop.py` et `core/encounter.py`

`ShopService` gère les achats, la consommation du stock et l'ajout des objets
à l'inventaire partagé, sans dépendance à pygame. `EncounterService` construit
un combat à partir de la zone courante et du catalogue des ennemis.

### `ui/`

Chaque écran pygame possède son module dédié : menu principal, exploration,
régions, zones, boutique, quêtes, titres, statut, combat et fin de partie.
`ui/renderer.py` centralise les panneaux, textes, boutons, sprites et
spritesheets. `ui/widgets.py` contient les composants partagés, notamment
`Button`, tandis que `ui/theme.py` regroupe la palette commune.

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

Le socle jouable et les principaux systèmes de progression sont en place. Les
limites actuelles sont :

- les compétences de soin et leurs effets persistants restent à compléter ;
- la boutique permet l'achat, mais pas encore la revente depuis l'interface ;
- les drops dont l'identifiant est absent des catalogues sont ignorés ;
- les effets textuels de certains titres ne modifient pas encore les règles
    de combat.
- le reset journalier utilise le jour civil local de la machine ; il ne gère
    pas encore de fuseau horaire ou d'heure serveur.
- les notes du tableau affichent les trois premières quêtes du catalogue.
- les ennemis d'épreuve de classe utilisent encore des placeholders tant que
    leurs sprites dédiés ne sont pas ajoutés ; leurs chemins sont déjà déclarés
    dans `data/enemies.json`.
- les compétences de classe et les effets passifs de l'ancien prototype de
    maîtrise ne font pas partie du système de classes actuel.
- le nécromancien peut extraire trois fois une ombre après une victoire à
    partir du tier 2 ; les ombres assignées peuvent être invoquées en combat
    et reviennent avec tous leurs PV après la rencontre.
- les ombres n'ont pas de progression propre : elles ne gagnent pas d'XP et
    ne possèdent pas de rang.

## Pistes d'évolution

Les évolutions naturelles sont :

1. Guilde/Ville.
2. Effets persistants et combat enrichi.
3. Revente et économie.
4. Gestion avancée du groupe.
5. Interface et polish.
6. Ajout vrai début de partie.
7. Simulation d’équilibrage et distribution du jeu.





## En cours d'ajout:
- Modifier chargement partie/début nouvelle partie