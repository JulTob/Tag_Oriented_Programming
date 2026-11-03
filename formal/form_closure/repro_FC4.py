"""F1 (FormClosure FC1_ClosureExact): Form drops a Base under an
always-equal Tag metaclass. Real-code replay of the TLA+ witness
(FormClosure_f_FC4.cfg, EqMode="equal", N=2, bases[2]=<<1>>, target=2).

Spec: 'Each Tag has one **Form**: its Bases, deepest first, in declaration
order, each once, then the Tag' (spec/SPECIFICATION.md:141-143); 'A Base
reachable through several paths appears once' (SPECIFICATION.md:156);
'it applies every missing Tag in its Form, Bases first'
(SPECIFICATION.md:169); 'Base-first Form application, each Base once,
active reapply a no-op' (conformance 1808-1812).
Classification: spec-silent with real harm -- the spec's only
identity-vs-equality sentence ('Fields are indexed by identity: two equal
but distinct Agents are two members', SPECIFICATION.md:135-137) binds
Agents/Hosts, not Tag classes, so the Form promise does not say whether a
metaclass __eq__ may merge distinct Tags.

Guilty code: TopKit/geometry.py:199 (seen set), 214 (pop-time
`candidate in seen`), 226 (`base not in seen`); same hazard noted at
geometry.py:252-265, queries.py:80,86, transactions.py:124.
Prints observed vs expected; exits 1 while the finding is present.
"""
import sys

sys.path.insert(0, "/home/io2007/Documents/Tag_Oriented_Programming")

from TopKit import Form, Tag  # noqa: E402
from TopKit.tags import MetaTag  # noqa: E402


class Equal_Meta(MetaTag):
    def __eq__(cls, other):
        return isinstance(other, Equal_Meta)

    def __hash__(cls):
        return 17


class Prize(Tag, metaclass=Equal_Meta):
    pass


class Sub(Prize):
    pass


class Host:
    pass


def main() -> None:
    got = Form(Sub)
    print("observed Form(Sub):", tuple(c.__name__ for c in got))
    print("expected Form(Sub): ('Prize', 'Sub')")
    print("issubclass(Sub, Prize):", issubclass(Sub, Prize), "(expected True)")
    print("Prize == Sub:", Prize == Sub, "(metaclass says equal)")

    h = Host()
    Sub(h)
    print("observed: h in Prize[:]:", h in Prize[:], "(expected True)")
    print("observed: h in Sub[:]:", h in Sub[:], "(expected True)")

    ok = got == (Prize, Sub) and h in Prize[:] and h in Sub[:]
    print("REPLAY:", "OK (finding fixed)" if ok else "MISMATCH (finding F1 present)")
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
