with Ada.Finalization;

--  Paired compile probe: Illegal changes only the Companion's limitedness.
procedure Limited_Copy is
   type Host is tagged null record;
   type Companion (Target : not null access Host) is
#if Illegal then
     new Ada.Finalization.Limited_Controlled with null record;
#else
     new Ada.Finalization.Controlled with null record;
#end if;
   Target : aliased Host;
   First : Companion (Target'Access);
   Second : Companion (Target'Access);
begin
   Second := First;
   pragma Assert (Second.Target = First.Target);
end Limited_Copy;
