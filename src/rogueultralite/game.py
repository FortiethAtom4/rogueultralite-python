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

    allies: list[Entity]

    enemies: list[Enemy]

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
    current_turn: int = 0
    last_round = len(rounds) - 1
    win = False

    def display_field(self):
        print(f"~ROUND {self.current_round + 1} TURN {self.current_turn + 1}~")

        print("ENEMIES:")
        for enemy in self.enemies:
            print(enemy)
        
        print("ALLIES:")
        for ally in self.allies:
            print(ally)



    def run_game(self) -> None:

        name = input("Enter your username: ")
        player: Player = Player(name)

        self.allies = [player]

        self.enemies = self.rounds[0]

        while player.alive:

            # start of a new round
            if len(self.enemies) == 0:
                print()
                self.current_turn = 0
                player.level_up()
                c = input("Press Enter to continue.")

                if self.current_round < self.last_round:
                    self.current_round += 1
                    self.enemies = self.rounds[self.current_round]
                    print("A new round begins...")
                else:
                    self.win = True
                    return

            self.display_field()

            for ally in self.allies:
                ally.blocking = False
                action = ally.choose_action()

                match action:
                    case Action.ff:
                        return

                    case Action.attack:
                        target = ally.choose_target(self.enemies)
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
                                chosen_ability.cast(ally,*self.allies)
                            
                            case Ability.AbilityTarget.target_enemy:
                                chosen_ability.cast(ally,*self.enemies)

                            case Ability.AbilityTarget.target_self:
                                chosen_ability.cast(ally)

                self.allies = clear_dead_entities(self.allies)
                self.enemies = clear_dead_entities(self.enemies)

            # enemies' turn
            for enemy in self.enemies:
                enemy.blocking = False
                action = enemy.choose_action()

                match action:
                    case Action.attack:
                        target = enemy.choose_target(self.allies)
                        print(f"{enemy.name} attacked {target.name}!")
                        target.take_damage(enemy.damage,DamageType.normal)

                    case Action.block:
                        print(f"{enemy.name} braced themselves!")
                        enemy.blocking = True

                    case Action.pass_turn:
                        print(f"{enemy.name} passed.")
                        continue

                    case Action.ability:
                        chosen_ability = enemy.choose_ability()

                        match chosen_ability.target:
                            case Ability.AbilityTarget.target_enemy:
                                chosen_ability.cast(enemy,*self.allies)
                            
                            case Ability.AbilityTarget.target_ally:
                                chosen_ability.cast(enemy,*self.enemies)

                            case Ability.AbilityTarget.target_self:
                                chosen_ability.cast(enemy)
                
                self.allies = clear_dead_entities(self.allies)
                self.enemies = clear_dead_entities(self.enemies)
                
            self.current_turn += 1