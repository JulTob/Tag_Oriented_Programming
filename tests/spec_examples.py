"""Every code example of the Specification, run for real, in order.

Ported from the session runner; `tests/test_documents.py` calls `Run`.
A block that stops running is a change to TOP nobody decided.
"""

from __future__ import annotations

import warnings

from TopKit import *   # noqa: F401,F403  the examples read as the Specification writes them


def Run() -> None:

    class Character:
        def __init__(self, name="x", level=1): self.name = name; self.level = level
        def Attack(agent) -> str: return "Faulty OOP attack."

    # 0.3 / 0.4
    class Wizard(Tag): pass
    charlie = Character(); Wizard(charlie); assert charlie in Wizard; assert list(Wizard) == [charlie]
    class Mortal(Tag): pass
    class Human(Mortal): pass
    Human(charlie); assert charlie in Human and charlie in Mortal
    class Spellcaster(Tag): pass
    class Duelist(Tag): pass
    class Arcane_Duelist(Spellcaster, Duelist): pass
    assert Form(Arcane_Duelist) == (Spellcaster, Duelist, Arcane_Duelist)

    # 0.6 rollback example
    class Territory(Tag):
        @Record
        def banner(agent): return "raised"
    class Citadel(Territory):
        @Pre
        def Has_Charter(agent): return hasattr(agent, "charter")
    ari = Character()
    try: Citadel(ari); raise SystemExit("expected failure")
    except TagPreconditionError: pass
    assert ari not in Territory and ari not in Citadel

    # 0.7 / 3.1 MI6
    class MI6(Tag):
        @Imprint
        def SetUp(agent, code): agent.code = code; agent.status = "Full"
        @Rip
        def SetDown(agent): del agent.code; agent.status = "Former MI6 Agent"
    bond = Character("Bond"); MI6(bond, code="007"); assert bond.code == "007"
    del MI6[bond]; assert bond.status == "Former MI6 Agent" and bond not in MI6 and isinstance(bond, MI6)

    # 1.3 spells pile-up
    class Species(Tag): pass
    class Class(Tag): pass
    class Elf(Species):
        @Record
        def spells(agent, stored): return (stored or []) + ["Light"]
    class Wizard2(Class):
        @Record
        def spells(agent, stored): return (stored or []) + ["Magic Missile", "Shield"]
    class Sage(Tag):
        @Record
        def spells(agent, stored): return (stored or []) + ["Identify"]
    ari = Character(); Elf(ari); Wizard2(ari); Sage(ari)
    assert ari.spells == ["Light", "Magic Missile", "Shield", "Identify"]

    # 1.4 Reports invisible + shared counter
    class Community(Tag):
        @Report
        def colour(tag): return "green"
        @Operation
        def Greet(tag, name): return f"{tag.__name__}:{name}"
    assert Community.colour == "green" and Community.Greet("Ari") == "Community:Ari"
    c = Character(); Community(c); assert not hasattr(c, "colour") and not hasattr(c, "Greet")
    class Secret_Agent(Tag):
        @Report
        def active(tag): return 0
        @Imprint
        def Activate(agent): Secret_Agent.active += 1
    Secret_Agent(Character()); Secret_Agent(Character()); assert Secret_Agent.active == 2

    # 1.5 publication
    class Fire(Tag):
        @Secret
        @Record
        def ember_heat(agent): return 3
        @Secret
        @Action
        def ignite(agent): return agent.ember_heat * 2
        @Action
        def strike(agent): return agent.ignite() + 1
    ember = Character(); Fire(ember); assert ember.strike() == 7
    for bad in (lambda: ember.ignite(), lambda: ember.ember_heat):
        try: bad(); raise SystemExit("secret leaked")
        except AttributeError: pass
    network_log = []
    class Agency(Tag):
        @Public
        @Report
        def colour(tag): return "navy"
        @Public
        @Operation
        def dispatch(agency, sender, message):
            network_log.append((sender.name, message)); return "sent"
    a = Character("A"); Agency(a); assert a.colour == "navy"; assert a.dispatch("hi") == "sent"
    send = a.dispatch; del Agency[a]
    try: send("late"); raise SystemExit("stale handle passed")
    except TagResolutionError: pass

    # 1.6 Delete
    class Pacifist(Tag):
        @Delete
        def Attack(agent): ...
    p = Character(); Pacifist(p); assert not hasattr(p, "Attack")

    # 1.7 access example
    class Person(Tag):
        def Attack(agent): return "Attack!"
    class Elf2(Person):
        @Action
        @Underlay
        def Attack(agent, underlay): return "With elven grace " + underlay()
    class Paladin(Person):
        @Action
        @Underlay
        def Attack(agent, underlay): return underlay() + " For your holy oath!"
    ari = Character(); Paladin(ari); Elf2(ari)
    assert ari.Attack() == "With elven grace Attack! For your holy oath!"
    assert ari.Paladin.Attack() == "Attack! For your holy oath!"
    assert Paladin[ari].Attack() == "Attack! For your holy oath!"

    # 2.x contracts
    class Wiz(Tag):
        @Pre
        def Level_Over_Zero(agent): return agent.level > 0
        @Post
        def Has_Spellbook(agent): assert agent.spellbook is not None
    w = Character(level=1); w.spellbook = "Tome"; Wiz(w); assert bool(w)
    class Guild(Tag):
        @Pre
        def Dues_Paid(agent): return agent.paid
    class Founder(Guild):
        @Pre
        def Dues_Paid(agent): return True
    f = Character(); f.paid = False
    try: Guild(f); raise SystemExit("dues")
    except TagPreconditionError: pass
    Founder(f); assert f in Guild
    class Apprentice(Wiz):
        @Pre
        @Underlay
        def Level_Over_Zero(agent, base):
            assert agent.mentor
            return base()
    ap = Character(level=1); ap.mentor = "M"; ap.spellbook = "T"; Apprentice(ap)
    class Coded(Tag):
        @Pre
        def Has_Code(agent, code): return code is not None
    try: Coded(Character()); raise SystemExit("code")
    except TagPreconditionError: pass
    Coded(Character(), code="007")
    class War_Caster(Tag):
        @Pre
        def Is_A_Caster(agent): return agent in Wiz
    War_Caster(w)
    class Soldier(Tag):
        @Post
        def Is_Equipped(agent): return agent.armed
    class Knight(Soldier):
        @Post
        @Underlay
        def Is_Equipped(agent, base): return base() and agent.oath
    k = Character(); k.armed = True; k.oath = True; Knight(k); assert bool(k)
    k.oath = False; assert not bool(k); assert k in ~Knight and k not in list(Knight)
    assert set(Knight[:]) == {k}
    class Barbarian(Tag):
        @Post
        def Strength_Capped(agent): return agent.strength <= 20
    class Berserk(Barbarian):
        @Post
        def Strength_Capped(agent): return agent.strength <= 24
    b = Character(); b.strength = 10
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always"); Berserk(b)
    assert any(issubclass(x.category, TagContractWarning) for x in caught)

    # 3.2 scope
    log = []
    class Sentry(Tag):
        @Rip
        def stand_down(agent): log.append("down")
    with Scope(Character(), Sentry) as s: assert s in Sentry
    assert log == ["down"]

    # 1.8 Flags, and their words
    @Flag
    class Undead(Tag): pass
    ghoul = Character("Ghoul"); Undead(ghoul)
    assert "Undead" in ghoul and Undead in ghoul and Keyword(ghoul, "Undead") and ghoul in Undead
    @Flag("Wolf", "Lycanthrope")
    class Werewolf(Tag): pass
    howler = Character("Howler"); Werewolf(howler)
    assert "Wolf" in howler and "Werewolf" in howler and Werewolf in howler
    assert Keyword(howler, "Lycanthrope")
    @Flag
    class Beast(Tag): pass
    @Flag("Beast")
    class Skinwalker(Tag): pass
    walker = Character("Walker"); Skinwalker(walker)
    assert "Beast" in walker and walker not in Beast and Beast not in walker   # a word, not membership

    # 1.9 Pins
    @Pin
    class Rare(Tag):
        @Record
        def rarity(tag): return "rare"
        @Action
        def Describe(tag): return f"{tag.__name__} is {tag.rarity}"
    Rare(Wizard)
    assert Wizard in Rare and list(Rare) == [Wizard]
    assert Wizard.rarity == "rare" and Wizard.Describe() == "Wizard is rare"
    assert not hasattr(charlie, "rarity")
    class War_Caster(Wizard): pass
    assert War_Caster.rarity == "rare" and War_Caster not in Rare
    try: Rare(charlie); raise SystemExit("pin on object")
    except TagCompositionError: pass
    try: Wizard(Rare); raise SystemExit("tag on class")
    except TypeError: pass
    assert f"{Wizard:pins}" == "Rare"
    del Rare[Wizard]; assert Wizard not in Rare and isinstance(Wizard, Rare) and Wizard.rarity == "rare"
    with warnings.catch_warnings():
        warnings.simplefilter("error"); Rare(Wizard)
    @Pin
    @Flag("Obsolete")
    class Deprecated(Tag): pass
    Deprecated(Wizard)
    assert "Deprecated" in Wizard and "Obsolete" in Wizard and Keyword(Wizard, "Obsolete")
