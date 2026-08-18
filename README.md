# Python-RPG_Gamerpg/
├── main.py
├── pyproject.toml
│
├── data/
│   ├── weapons.json
│   ├── armors.json
│   ├── enemies.json
│   ├── xp_table.json
│   ├── regions.json
│   └── assets/
│       └── sprites/...
│
├── core/
│   ├── game.py
│   ├── menu.py
│   └── fight.py
│
├── entities/
│   ├── combatant.py           # base commune : hp, attack, defense, speed, is_alive(), choose_action()
│   ├── ally.py
│   │   ├── player.py
│   │   └── companion.py
│   ├── enemy.py                 # Enemy(Combatant) — jetable, instancié depuis JSON
│   └── merchant.py              # reste à part, ce n'est pas un combattant
│
├── party/
│   └── party.py                 # regroupe les Ally actifs, gère qui est "sur le terrain"
│
├── items/
│   ├── base.py                  # classe Item (dataclass)
│   ├── weapon.py
│   ├── armor.py
│   └── factory.py                # ItemFactory — charge armes ET armures
│
├── items/
│   ├── skills_factory.py
│   └── skills.py                 
│
├── progression/
│    └── level_manager.py          # check_level_up(ally: Ally) — s'applique à Player et Companion
│
└── world/
    ├── region.py                # Region : id, ennemis possibles, connexions vers autres régions
    └── world_manager.py         # état courant (région active), transitions

