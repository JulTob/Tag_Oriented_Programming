"""Replay the WalkTurns PO3 break-class trace on the REAL code.

Model trace (WalkTurns_arrestedSound.cfg, Break="arrestedSound", view="sound"):
  State 1: members={1,2}, all sound, none arrested, cursor=1.
  State 2: ArrestElsewhere(1) -- agent 1 arrested by ANOTHER tag, stays a member.
  State 3: Yield(1) under the broken rule yields agent 1 -> PO3_ArrestExcluded.

On the real code the CURRENT implementation must NOT yield the arrested
agent: it is in neither `Wizard` nor `~Wizard`
(spec/SPECIFICATION.md:1432-1434). Prints observed vs expected.
"""
import sys

sys.path.insert(0, "/home/io2007/Documents/Tag_Oriented_Programming")

from TopKit import Post, Rip, Tag, TagCompositionError
from TopKit.arrest import _arrest_of, _safehouse


class Host:
    def __init__(self, name):
        self.name = name


def main() -> None:
    _safehouse.clear()

    class Wizard(Tag):
        @Post
        def Ready(agent):
            return True

    class Duty(Tag):
        @Rip
        def Leave(agent):
            if getattr(agent, "blocked", False):
                raise ValueError("cleanup blocked")

    ada, bea = Host("ada"), Host("bea")
    Wizard(ada)
    Wizard(bea)
    # State 2: arrest ada via ANOTHER tag; ada stays in Wizard's Field.
    Duty(ada)
    ada.blocked = True
    try:
        del Duty[ada]
    except TagCompositionError:
        pass
    assert _arrest_of(ada) is not None, "expected ada arrested"
    assert ada in Wizard[:], "arrested ada stays in the raw Field"

    # State 3: the walk's turn for ada. Correct code skips it.
    got = [m.name for m in Wizard]
    print("observed sound walk:", got)
    print("expected sound walk: ['bea'] (arrested ada excluded)")
    got_broken = [m.name for m in ~Wizard]
    print("observed defective walk:", got_broken)
    print("expected defective walk: [] (arrested ada excluded)")

    ok = (
        got == ["bea"]
        and got_broken == []
        and ada not in Wizard
        and ada not in (~Wizard)
    )
    print("REPLAY:", "OK (current code excludes the arrested agent)" if ok
          else "MISMATCH (bug: arrested agent yielded)")
    _safehouse.clear()
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
