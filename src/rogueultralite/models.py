from __future__ import annotations
from enum import Enum
from abc import ABC, abstractmethod
from typing import Any
import random
import rogueultralite.util as util

class AI_Type(Enum):
    player = 1
    aggro = 2
    defensive = 3
    caster = 4
    spellsword = 5
    mirror = 6
    only_pass = 7
    passive_caster = 8

class Action(Enum):
    pass_turn = 1
    attack = 2
    block = 3
    ability = 4
    ff = 5

class DamageType(Enum):
    normal = 1
    magic = 2
    mana_burst = 3
    true = 4

# abstract classes

class Ability(ABC):
    '''The base class for all abilities in the game. All abilities have a name, a target, and a cast() function which determines what it does when used.'''
    class AbilityTarget(Enum):
        target_self = 1
        target_ally = 2
        target_enemy = 3

    def __init__(self, name: str, target: AbilityTarget) -> None:
        self.target: Ability.AbilityTarget = target
        self.name: str = name

    def cast_message(self, caster: Entity, *targets: Entity):
        '''Prints the message when this ability is cast.'''
        if len(targets) == 0:
            print(f"{caster.name} used {self.name}!")

        elif len(targets) == 1:
            print(f"{caster.name} used {self.name} on {targets[0].name}!")

        else:
            print(f"{caster.name} used {self.name} on: { ", ".join([t.name for t in targets])}!")

    @abstractmethod
    def cast(self, caster: Entity, *targets: Entity) -> Any:
        pass

class Upgradable():
    '''Defines an ability which can be upgraded.'''
    def upgrade(self, multiplier_value: float = 0, add_value: float = 0):
        pass

class Scaling():
    '''defines an object that can "scale," i.e. increase in strength over time.'''
    def __init__(self, scaling: float = 0) -> None:
        self.scaling: float = scaling

    def upgrade_scaling(self, multiplier_value: float = 0, add_value: float = 0):
        '''upgrade scaling.'''
        final_scaling_value = self.scaling
        if multiplier_value > 0:
            final_scaling_value = final_scaling_value * multiplier_value
        final_scaling_value = final_scaling_value + add_value

        print(f"+ Increased scaling: {self.scaling} -> {final_scaling_value}")

        self.scaling = final_scaling_value

class AbilityValue(Ability,Upgradable):
    '''Defines an ability with a single value, which is uses for its cast().'''
    def __init__(self, name: str, target: Ability.AbilityTarget, value: float) -> None:
        super().__init__(name, target)
        self.value = value

    def upgrade(self, multiplier_value: float = 0, add_value: float = 0):
        '''increase the value of this ability.'''
        final_value = self.value

        if multiplier_value > 0:
            final_value = final_value * multiplier_value

        final_value += add_value

        print(f"+ Increased value: {self.value} -> {final_value}")

        self.value = final_value
        
class AttackAbility(AbilityValue):
    '''Defines an ability which attacks an opponent and deals damage.'''
    def __init__(self, name: str, damage: float) -> None:
        super().__init__(name, Ability.AbilityTarget.target_enemy,damage)
        
    def upgrade(self, multiplier_value: float = 0, add_value: float = 0):
        final_value = self.value

        if multiplier_value > 0:
            final_value = final_value * multiplier_value

        final_value += add_value

        print(f"+ Increased damage: {self.value} -> {final_value}")

        self.value = final_value

class HasRecoil():
    '''defines an object that has recoil damage, i.e. can cause damage to the caster.'''
    def __init__(self, recoil_damage: float, recoil_scaling: float = 0) -> None:
        self.recoil_damage: float = recoil_damage
        self.recoil_scaling: float = recoil_scaling

# abilities

class Fireball(AttackAbility, Scaling):
    '''Deals magic damage to an enemy. Grants Entropy.'''
    def __init__(self, damage: float, scaling: float = 0):
        AttackAbility.__init__(self,"Fireball",damage)
        Scaling.__init__(self,scaling)

    def cast(self, caster: Entity, *targets: Entity) -> float:
        target: Entity = caster.choose_target([e for e in targets])

        self.cast_message(caster,target)

        damage: float = target.take_damage(self.value,DamageType.magic)
        if damage > 0:
            caster.gain_entropy()

        return damage

    def upgrade(self, multiplier_value: float = 0, add_value: float = 0):
        AttackAbility.upgrade(self,multiplier_value,add_value)
        Scaling.upgrade_scaling(self,multiplier_value,add_value)
    

class Recovery(AbilityValue, Scaling):
    '''Heals the caster.'''
    def __init__(self, amount: float, scaling: float = 0) -> None:
        AbilityValue.__init__(self,"Recovery",Ability.AbilityTarget.target_self,amount)
        Scaling.__init__(self,scaling)

    def cast(self, caster: Entity, *targets: Entity) -> float:
        self.cast_message(caster)

        return caster.heal(self.value)

    def upgrade(self, multiplier_value: float = 0, add_value: float = 0):
        AbilityValue.upgrade(self,multiplier_value,add_value)
        Scaling.upgrade_scaling(self,multiplier_value,add_value)

class Heal(AbilityValue, Scaling):
    '''Heals a target ally. Can target self.'''
    def __init__(self, amount: float, scaling: float = 0) -> None:
        AbilityValue.__init__(self,"Heal",Ability.AbilityTarget.target_ally,amount)
        Scaling.__init__(self,scaling)

    def cast(self, caster: Entity, *targets: Entity) -> Any:
        target: Entity = caster.choose_target([e for e in targets])

        self.cast_message(caster,target)

        return target.heal(self.value)

    def upgrade(self, multiplier_value: float = 0, add_value: float = 0):
        AbilityValue.upgrade(self,multiplier_value,add_value)
        Scaling.upgrade_scaling(self,multiplier_value,add_value)

class Mana_Burst(AttackAbility, Scaling, HasRecoil):
    '''Spends a mana burst charge to deal unblockable damage to an enemy. If the caster is out of charges, they take damage instead.'''
    def __init__(self, damage: float, recoil_damage: float, scaling: float = 0, recoil_scaling: float = 0) -> None:
        AttackAbility.__init__(self,"Mana Burst", damage)
        Scaling.__init__(self,scaling)
        HasRecoil.__init__(self,recoil_damage, recoil_scaling)

    def cast(self, caster: Entity, *targets: Entity) -> float:
        target = caster.choose_target([e for e in targets])

        self.cast_message(caster,target)

        if caster.mana_burst_charges > 0:
            caster.mana_burst_charges -= 1
            return target.take_damage(self.value,DamageType.mana_burst)
        else:
            caster.take_damage(self.recoil_damage,DamageType.mana_burst)
            return 0

    def upgrade(self, multiplier_value: float = 0, add_value: float = 0):
        AttackAbility.upgrade(self,multiplier_value,add_value)
        Scaling.upgrade_scaling(self,multiplier_value,add_value)

class Reckless_Attack(AttackAbility, Scaling, HasRecoil):
    '''Deals normal damage to an enemy, but deals some recoil damage to the caster. Grants Entropy for damage dealt to both enemy and caster.'''
    def __init__(self, damage: float,recoil_damage: float, scaling: float = 0, recoil_scaling: float = 0) -> None:
        AttackAbility.__init__(self,"Reckless Attack", damage)
        Scaling.__init__(self,scaling)
        HasRecoil.__init__(self,recoil_damage, recoil_scaling)

    def cast(self, caster: Entity, *targets: Entity) -> Any:
        target = caster.choose_target([e for e in targets])

        self.cast_message(caster,target)

        caster.take_damage(self.recoil_damage, DamageType.mana_burst)
        caster.gain_entropy()
        return target.take_damage(self.value,DamageType.normal)
    
    def upgrade(self, multiplier_value: float = 0, add_value: float = 0):
        AttackAbility.upgrade(self,multiplier_value,add_value)
        Scaling.upgrade_scaling(self,multiplier_value,add_value)

class Defend(Ability):
    '''Sets another target to `blocking`, reducing their damage taken.'''
    def __init__(self) -> None:
        super().__init__("Defend", Ability.AbilityTarget.target_ally)

    def cast(self, caster: Entity, *targets: Entity) -> Any:
        target: Entity

        # Bots will make an effort to Defend a target that isn't already blocking.
        if(caster.ai_type != AI_Type.player):
            for i in range(10):
                target = caster.choose_target([e for e in targets])
                if not target.blocking:
                    break
        else:
            target = caster.choose_target([e for e in targets])

        self.cast_message(caster,target)

        if target.blocking:
            return False

        target.blocking = True
        return True

class Entity(ABC):

    block_power: int = 2 #incoming damage is multiplied by (1 - 1/number) if blocking.
    blocking: bool = False
    alive: bool = True
    magic_block_healing_value: float = 1
    mana_burst_charges: int = 0

    can_gain_entropy: bool = False
    entropy = 0
    entropy_gain_per_action = 1
    entropy_overflow = 10

    print_logs = False #print statements will only occur for this if this is set to True
    symbol = "@" #used for quick ID of entities in print statements.

    level: int = 1
    level_scaling: float = 1

    def __init__(self, name: str, ai_type: AI_Type, maxhealth: float, damage: float, abilities: list[Ability]) -> None:

        # set parameters
        self.name = name
        self.ai_type: AI_Type = ai_type
        self.health: float = maxhealth
        self.maxhealth: float = maxhealth
        self.damage: float = damage
        self.abilities: list[Ability] = abilities

    def __repr__(self) -> str:
        health_bar_str = "|"
        ratio = self.health / self.maxhealth
        for i in range(30):
            if i / 30 < ratio:
                health_bar_str += "█"
            else:
                health_bar_str += " "

        health_bar_str += "|"

        return f"{self.symbol} {self.name} {self.symbol}\n" \
        f"HP: {self.health}/{self.maxhealth}\n" \
        f"{health_bar_str}\n"


    def __str__(self) -> str:
        return self.__repr__()

    def printlog(self,log: str):
        if self.print_logs:
            print(log)

    def level_up(self):
        '''Levels this entity up, improving its stats and abilities across the board.'''

        # base stat increases
        self.level += 1
        self.printlog(f"{self.name} is now level {self.level}!")

        health_amt = self.level * self.level_scaling
        self.printlog(f"+ Max health increased: {self.maxhealth} -> {self.maxhealth + health_amt}")
        self.maxhealth += health_amt

        self.printlog(f"+ Damage increased: {self.damage} -> {self.damage + self.level_scaling}")
        self.damage += self.level_scaling

        # level up any scaling abilities
        for ability in self.abilities:
            if isinstance(ability,AbilityValue) and isinstance(ability,Scaling):

                # don't forget to increase recoil!
                if isinstance(ability,HasRecoil):
                    recoil_amt = ability.recoil_scaling * self.level_scaling
                    self.printlog(f"- {ability.name} recoil damage increased: {ability.recoil_damage} -> {ability.recoil_damage + recoil_amt}")
                    ability.recoil_damage += recoil_amt

                total_amt = ability.scaling * self.level_scaling
                self.printlog(f"+ {ability.name} value increased: {ability.value} -> {ability.value + total_amt}")
                ability.value += total_amt

    def heal(self, amount: float):
        '''Heals this entity. If the amount would heal the entity over `self.maxhealth`, sets their health to `self.maxhealth`.'''
        value: float = self.maxhealth - self.health if self.health + amount >= self.maxhealth else amount

        self.health += value

        print(f"{self.name} healed {value} HP!")

        return value

    def gain_entropy(self):
        '''Gain Entropy. If Entropy overflows, gain a Mana Burst charge.'''
        if self.can_gain_entropy:
            self.entropy += self.entropy_gain_per_action
            print(f"{self.name} gained Entropy!")
            if self.entropy > self.entropy_overflow:
                self.mana_burst_charges += 1
                self.entropy -= self.entropy_overflow
                print(f"{self.name}'s Entropy overflowed! They gained 1 Mana Burst charge.")

    def take_damage(self, amount: float, damage_type: DamageType)-> float:
        '''deals damage to this entity and grants Entropy if any damage was taken. If the damage would kill, sets `self.alive` to False. '''
        value: float = 0

        match damage_type:

            # blocking normal damage reduces the damage taken.
            case DamageType.normal:
                if self.blocking:
                    value = amount * (1 - 1/self.block_power)
                else:
                    value= amount

            # blocking magic damage heals the blocker.
            case DamageType.magic:
                if self.blocking:
                    print(f"{self.name} successfully blocked a spell attack!")
                    self.heal(self.magic_block_healing_value)
                    value = 0
                else:
                    value = amount

            # Mana Burst attacks cannot be blocked.
            case DamageType.mana_burst:
                value = amount

            # Default case, in case of any other damage types
            case _:
                value = amount

        self.health -= value

        if self.health <= 0:
            self.alive = False
        elif value > 0:
            self.gain_entropy()
        
        print(f"{self.name} took {value} damage!")
        
        return value

    @abstractmethod
    def choose_ability(self) -> Ability:
        pass 

    @abstractmethod
    def choose_action(self) -> Action:
        pass

    @abstractmethod
    def choose_target(self, targets: list[Entity]) -> Entity:
        pass

class Player(Entity):

    chosen_upgrades: list[str] = []

    def __init__(self, name: str) -> None:
        abilities: list[Ability] = [
            Recovery(3,2),
            Fireball(5,2),
            Mana_Burst(10,5,5,2.5)
        ]

        super().__init__(name, AI_Type.player, 3, 1, abilities)
        self.mana_burst_charges = 3
        self.can_gain_entropy = True
        self.print_logs = True
        self.symbol = "~"

    def init_mirror(self, other: Player) -> None:
        '''Create a Mirror entity, i.e. a "Player" with a different AI type and a reversed name.'''
        self.__dict__ = other.__dict__
        self.name = other.name[::-1]
        self.ai_type = AI_Type.mirror

    def choose_action(self) -> Action:
        chosen_action: str = ""
        while chosen_action == "":
            chosen_action = input("Choose an action (attack (Q), block (W), ability (E), pass (R), ff): ").lower()

            match chosen_action:
                case "q" | "attack":
                    return Action.attack

                case "w" | "block":
                    return Action.block

                case "e" | "ability":
                    return Action.ability

                case "r" | "pass":
                    return Action.pass_turn

                case "ff":
                    print("You surrendered.")
                    return Action.ff

                case _:
                    chosen_action = ""
                    self.printlog("Please choose a valid action!")

    def choose_ability(self) -> Ability:
        ability_names = [a.name for a in self.abilities]
        return self.abilities[util.choose_an_option(ability_names,"Choose an ability to use: ")]

    def choose_target(self, targets: list[Entity]) -> Entity:
        target_names = [i.name for i in targets]

        return targets[util.choose_an_option(target_names,"Type the number of your chosen target: ")]

    def ability_upgrade(self):
        print("Congratulations! You have earned an ability upgrade!")
        possible_upgrades: list[str] = ["Attack","Block Power"]
        for ability in self.abilities:
            if isinstance(ability,AbilityValue):
                possible_upgrades.append(ability.name)

        chosen_upgade = util.choose_an_option(possible_upgrades,"Choose the number of an aspect to upgrade: ")

        match chosen_upgade:
            case 0: # increased attack.
                attack_upgrade_multiplier = 2
                print(f"Successfully upgraded Attack!")
                print(f"+ Attack: {self.damage} -> {self.damage * attack_upgrade_multiplier}")
                self.damage = self.damage * attack_upgrade_multiplier

            case 1: # increased resistances.
                block_power_add_value = 1
                print(f"Successfully upgraded Block Power!")
                print(f"+ Block Power: {self.block_power} -> {self.block_power + block_power_add_value}")
                self.block_power += block_power_add_value

            case _: # upgrading an ability.
                ability_upgrade_multiplier = 2

                ability_to_upgrade: Ability = next((a for a in self.abilities if a.name == possible_upgrades[chosen_upgade]))
                if isinstance(ability_to_upgrade,Upgradable):
                    print(f"Successfully upgraded {ability_to_upgrade.name}!")
                    ability_to_upgrade.upgrade(multiplier_value=ability_upgrade_multiplier)

        self.chosen_upgrades.append(possible_upgrades[chosen_upgade])
        

class Enemy(Entity):
    def __init__(self, name: str, ai_type: AI_Type, maxhealth: float, damage: float, abilities: list[Ability]) -> None:
        super().__init__(name, ai_type, maxhealth, damage, abilities)
        self.symbol = "/\\"

    def choose_action(self) -> Action:
        '''chooses an action based on its AI type.'''
        pass_prob: int = 0
        attack_prob: int = 0
        cast_prob: int = 0
        block_prob: int = 0
        default_prob: int = 0

        match self.ai_type:

            # aggro enemies only attack.
            case AI_Type.aggro:
                attack_prob = 1

            # defensive enemies occasionally block, and block more when they lose HP.
            case AI_Type.defensive:
                if self.health / self.maxhealth <= 0.6:
                    block_prob = 2
                else:
                    block_prob = 1

                attack_prob = 2

            # casters only cast spells.
            case AI_Type.caster:
                cast_prob = 1

            # passive casters cast spells... occasionally.
            case AI_Type.passive_caster:
                cast_prob = 1
                pass_prob = 1

            # spellswords attack, block, and cast spells. They do not pass.
            case AI_Type.spellsword:
                attack_prob = 1
                cast_prob = 1
                block_prob = 1

            # A dummy AI type for testing/training.
            case AI_Type.only_pass:
                default_prob = 1

        return random.choices([Action.pass_turn,Action.attack,Action.ability,Action.block,Action.pass_turn],
        [pass_prob,attack_prob,cast_prob,block_prob,default_prob])[0]

    def choose_ability(self) -> Ability:
        '''Chooses a random ability.'''
        return self.abilities[random.randrange(0,len(self.abilities))]

    def choose_target(self, targets: list[Entity]) -> Entity:
        '''For now, enemies just choose a random target in all cases.'''
        if len(targets) == 1:
            return targets[0]

        return targets[random.randrange(0,len(targets))]
        



    

    