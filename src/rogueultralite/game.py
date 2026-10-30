from rogueultralite.models import *

def clear_dead_entities(entities: list[Entity]) -> list[Entity]:
    ret: list[Entity] = []
    for entity in entities:
        if entity.alive:
            ret.append(entity)
        else:
            print(f"{entity.name} has been defeated!")

    return ret

class Game():
    def __init__(self) -> None:
        pass

    # All rounds in this game.
    rounds: list[list[Entity]] = [

        # ROUND 1
        [
            Enemy("Dummy",AI_Type.only_pass,3,0,[])
        ],

        # ROUND 2
        [
            Enemy("Enemy Grunt",AI_Type.aggro,1,1,[]),
            Enemy("Enemy Soldier",AI_Type.defensive,5,1,[])
        ],

        # ROUND 3
        [
            Enemy("Enemy Wizard",AI_Type.passive_caster,8,0,[Fireball(3)]),
            Enemy("Enemy Healer",AI_Type.passive_caster,10,0,[Heal(4)])
        ]
    ]

    current_round = 0
    last_round = len(rounds) - 1
    win = False


    def run_game(self) -> None:

        name = input("Enter your username: ")
        player: Player = Player(name)

        allies: list[Entity] = [player]

        enemies: list[Enemy] = self.rounds[0]

        while player.alive:

            if len(enemies) == 0:
                if self.current_round < self.last_round:
                    self.current_round += 1
                    enemies = self.rounds[self.current_round]
                    print("A new round begins...")
                else:
                    self.win = True
                    return

            print("ENEMIES:")
            for enemy in enemies:
                print(f"{enemy.name}: {enemy.health}/{enemy.maxhealth}")
            
            print("ALLIES:")
            for ally in allies:
                print(f"{ally.name}: {ally.health}/{ally.maxhealth}")

            for ally in allies:
                ally.blocking = False
                action = ally.choose_action()

                match action:
                    case Action.ff:
                        return

                    case Action.attack:
                        target = ally.choose_target(enemies)
                        print(f"{ally.name} attacked {target.name}!")
                        dmg = target.take_damage(ally.damage,DamageType.normal)
                        if dmg > 0:
                            ally.gain_entropy()

                    case Action.block:
                        print(f"{ally.name} braced themselves!")
                        ally.blocking = True

                    case Action.pass_turn:
                        print(f"{ally.name} passed.")
                        continue

                    case Action.ability:
                        chosen_ability = ally.choose_ability()

                        match chosen_ability.target:
                            case Ability.AbilityTarget.target_ally:
                                chosen_ability.cast(ally,*allies)
                            
                            case Ability.AbilityTarget.target_enemy:
                                chosen_ability.cast(ally,*enemies)

                            case Ability.AbilityTarget.target_self:
                                chosen_ability.cast(ally)

                allies = clear_dead_entities(allies)
                enemies = clear_dead_entities(enemies)

            # enemies' turn
            for enemy in enemies:
                action = enemy.choose_action()

                match action:
                    case Action.attack:
                        target = enemy.choose_target(allies)
                        print(f"{enemy.name} attacked {target.name}!")
                        target.take_damage(enemy.damage,DamageType.normal)

                    case Action.block:
                        print(f"{enemy.name} braced themselves!")
                        target.blocking = True

                    case Action.pass_turn:
                        print(f"{enemy.name} passed.")
                        continue

                    case Action.ability:
                        chosen_ability = enemy.choose_ability()

                        match chosen_ability.target:
                            case Ability.AbilityTarget.target_enemy:
                                chosen_ability.cast(enemy,*allies)
                            
                            case Ability.AbilityTarget.target_ally:
                                chosen_ability.cast(enemy,*enemies)

                            case Ability.AbilityTarget.target_self:
                                chosen_ability.cast(enemy)
                
                allies = clear_dead_entities(allies)
                enemies = clear_dead_entities(enemies)