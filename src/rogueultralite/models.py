from __future__ import annotations
from email.policy import default
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

# abstract classes

class Ability(ABC):

    class AbilityTarget(Enum):
        target_self = 1
        target_ally = 2
        target_enemy = 3

    def __init__(self, name: str, target: AbilityTarget) -> None:
        self.target = target
        self.name = name

    def cast_message(self, caster: Entity, *targets: Entity):
        '''Prints the message when this ability is cast.'''
        if len(targets) == 0:
            print(f"{caster.name} used {self.name}!")

        elif len(targets) == 1:
            print(f"{caster.name} used {self.name} on {targets[0].name}!")

        else:
            print(f"{caster.name} used {self.name} on: { ", ".join([t.name for t in targets])[:-1]}!")

    @abstractmethod
    def cast(self, caster: Entity, *targets: Entity) -> Any:
        pass

class Attack_Ability(Ability):
    def __init__(self, name: str, damage: float) -> None:
        super().__init__(name, Ability.AbilityTarget.target_enemy)
        self.damage = damage

# abilities

class Fireball(Attack_Ability):
    '''Deals magic damage to an enemy. Grants Entropy.'''
    def __init__(self, damage: float, scaling: float = 0):
        super().__init__("Fireball",damage)

    def cast(self, caster: Entity, *targets: Entity) -> float:
        target: Entity = caster.choose_target([e for e in targets])

        self.cast_message(caster,target)

        damage: float = target.take_damage(self.damage,DamageType.magic)
        if damage > 0:
            caster.gain_entropy()

        return damage

class Recovery(Ability):
    '''Heals the caster.'''
    def __init__(self, amount: float, scaling: float = 0) -> None:
        super().__init__("Recovery",Ability.AbilityTarget.target_self)
        self.amount = amount

    def cast(self, caster: Entity, *targets: Entity) -> float:
        self.cast_message(caster)

        return caster.heal(self.amount)

class Heal(Ability):
    '''Heals a target ally. Can target self.'''
    def __init__(self, amount: float, scaling: float = 0) -> None:
        self.amount = amount
        super().__init__("Heal",Ability.AbilityTarget.target_ally)

    def cast(self, caster: Entity, *targets: Entity) -> Any:
        target: Entity = caster.choose_target([e for e in targets])

        self.cast_message(caster,target)

        return target.heal(self.amount)

class Mana_Burst(Attack_Ability):
    '''Spends a mana burst charge to deal unblockable damage to an enemy. If the caster is out of charges, they take damage instead.'''
    def __init__(self, damage: float, recoil_damage: float, scaling: float = 0) -> None:
        super().__init__("Mana Burst", damage)
        self.recoil_damage = recoil_damage

    def cast(self, caster: Entity, *targets: Entity) -> float:
        target = caster.choose_target([e for e in targets])

        self.cast_message(caster,target)

        if caster.mana_burst_charges > 0:
            caster.mana_burst_charges -= 1
            return target.take_damage(self.damage,DamageType.mana_burst)
        else:
            caster.take_damage(self.recoil_damage,DamageType.mana_burst)
            return 0

class Reckless_Attack(Attack_Ability):
    '''Deals normal damage to an enemy, but deals some recoil damage to the caster. Grants Entropy for damage dealt to both enemy and caster.'''
    def __init__(self, damage: float,recoil_damage: float, scaling: float = 0) -> None:
        super().__init__("Reckless Attack", damage)
        self.recoil_damage = recoil_damage

    def cast(self, caster: Entity, *targets: Entity) -> Any:
        target = caster.choose_target([e for e in targets])

        self.cast_message(caster,target)

        caster.take_damage(self.recoil_damage, DamageType.mana_burst)
        caster.gain_entropy()
        return target.take_damage(self.damage,DamageType.normal)

class Defend(Ability):
    '''Sets another target to `blocking`, reducing their damage taken.'''
    def __init__(self) -> None:
        super().__init__("Defend", Ability.AbilityTarget.target_ally)

    def cast(self, caster: Entity, *targets: Entity) -> Any:
        target: Entity = ""

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

    block_damage_reduction: float = 0.5 #incoming damage is multiplied by this number if blocking.
    blocking: bool = False
    alive: bool = True
    magic_block_healing_value: float = 1
    mana_burst_charges: int = 0

    can_gain_entropy: bool = False
    entropy = 0
    entropy_gain_per_action = 1
    entropy_overflow = 10

    def __init__(self, name: str, ai_type: AI_Type, maxhealth: float, damage: float, abilities: list[Ability]) -> None:

        # set parameters
        self.name = name
        self.ai_type: AI_Type = ai_type
        self.health: float = maxhealth
        self.maxhealth: float = maxhealth
        self.damage: float = damage
        self.abilities: list[Ability] = abilities

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
                    value = amount * self.block_damage_reduction
                else:
                    value= amount

            # blocking magic damage heals the blocker.
            case DamageType.magic:
                if self.blocking:
                    self.health += self.magic_block_healing_value
                    print(f"{self.name} healed {self.magic_block_healing_value} HP for successfully blocking a spell attack!")
                    value = 0
                else:
                    value = amount

            # Mana Burst attacks cannot be blocked.
            case DamageType.mana_burst:
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

    level = 1

    def __init__(self, name: str) -> None:
        abilities: list[Ability] = [
            Recovery(3,2),
            Fireball(5,2),
            Mana_Burst(10,5,5)
        ]

        super().__init__(name, AI_Type.player, 5, 1, abilities)
        self.mana_burst_charges = 3
        self.can_gain_entropy = True


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
                    print("Please choose a valid action!")

    def choose_ability(self) -> Ability:
        ability_names = [a.name for a in self.abilities]
        return self.abilities[util.choose_an_option(ability_names,"Choose an ability to use: ")]

    def choose_target(self, targets: list[Entity]) -> Entity:
        target_names = [i.name for i in targets]

        return targets[util.choose_an_option(target_names,"Type the number of your chosen target: ")]

class Enemy(Entity):
    def __init__(self, name: str, ai_type: AI_Type, maxhealth: float, damage: float, abilities: list[Ability]) -> None:
        super().__init__(name, ai_type, maxhealth, damage, abilities)

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

                attack_prob = 1

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
        



    

    