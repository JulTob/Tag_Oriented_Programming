"""A synchronous Link call cannot borrow a Contact's async authority."""

import asyncio
import unittest

from TopKit import Link, Operation, Public, Record, Report, Secret, Tag


class Host:
    pass


def Read_Or_Shut(agent):
    try:
        return agent.secret
    except AttributeError:
        return "shut"


class Link_Secret_Doors_Tests(unittest.TestCase):
    def In_Contact_Hook(self, callback):
        class Contact(Tag):
            @Secret
            @Record
            def secret(agent):
                return "contact secret"

            def Read_Own(agent):
                return agent.secret

            async def __aenter__(agent):
                before = agent.secret
                result = callback(agent)
                return before, result, agent.secret

            async def __aexit__(agent, kind, value, traceback):
                return None

        contact = Host()
        Contact(contact)

        async def Run():
            async with contact as result:
                return result

        result = asyncio.run(Run())
        self.assertEqual(result[0], "contact secret")
        self.assertEqual(result[2], "contact secret")
        self.assertEqual(Read_Or_Shut(contact), "shut")
        return result[1]

    def test_pair_action_shuts_the_contacts_async_door(self):
        class Owner(Tag):
            @Link
            class Knows(Tag):
                def Inspect(agent, contact):
                    return Read_Or_Shut(contact)

        owner = Host()
        Owner(owner)

        def Call(contact):
            owner.Knows(contact)
            return owner.Knows[contact].Inspect()

        self.assertEqual(self.In_Contact_Hook(Call), "shut")

    def test_public_line_shuts_the_contacts_async_door(self):
        class Owner(Tag):
            @Link
            class Knows(Tag):
                @Public
                def Inspect(agent, contact):
                    return Read_Or_Shut(contact)

        owner = Host()
        Owner(owner)

        def Call(contact):
            owner.Knows(contact)
            return contact.Inspect()

        self.assertEqual(self.In_Contact_Hook(Call), "shut")

    def test_operation_shuts_the_contacts_async_door(self):
        class Owner(Tag):
            @Link
            class Knows(Tag):
                @Operation
                def Inspect(link, contact):
                    return Read_Or_Shut(contact)

        owner = Host()
        Owner(owner)

        def Call(contact):
            owner.Knows(contact)
            return owner.Knows.Inspect(contact=contact)

        self.assertEqual(self.In_Contact_Hook(Call), "shut")

    def test_report_builder_cannot_cache_a_contacts_secret(self):
        class Owner(Tag):
            @Link
            class Knows(Tag):
                @Public
                @Report
                def summary(link):
                    return [Read_Or_Shut(contact) for contact in link[:]]

        owner = Host()
        Owner(owner)

        def Call(contact):
            owner.Knows(contact)
            return contact.summary

        self.assertEqual(self.In_Contact_Hook(Call), ["shut"])
        self.assertEqual(owner.Knows.summary, ["shut"])

    def test_an_exception_restores_the_hook_without_leaving_the_owner_open(self):
        seen = []

        class Owner(Tag):
            @Secret
            @Record
            def secret(agent):
                return "owner secret"

            @Link
            class Knows(Tag):
                @Public
                def Fail(agent, contact):
                    seen.append((agent.secret, Read_Or_Shut(contact)))
                    raise ValueError("failed inside the Link")

        owner = Host()
        Owner(owner)

        def Call(contact):
            owner.Knows(contact)
            with self.assertRaisesRegex(ValueError, "failed inside the Link"):
                contact.Fail()

        self.In_Contact_Hook(Call)
        self.assertEqual(seen, [("owner secret", "shut")])
        self.assertEqual(Read_Or_Shut(owner), "shut")

    def test_the_contacts_own_action_opens_only_its_own_call(self):
        class Owner(Tag):
            @Link
            class Knows(Tag):
                @Public
                def Inspect(agent, contact):
                    before = Read_Or_Shut(contact)
                    own = contact.Read_Own()
                    return before, own, Read_Or_Shut(contact)

        owner = Host()
        Owner(owner)

        def Call(contact):
            owner.Knows(contact)
            return contact.Inspect()

        self.assertEqual(
            self.In_Contact_Hook(Call),
            ("shut", "contact secret", "shut"),
        )


if __name__ == "__main__":
    unittest.main()
