#if Illegal then
pragma Restrictions (No_Finalization);
#end if;
with Ada.Finalization;

--  GNAT-specific paired control: the only change is the runtime restriction.
procedure No_Finalization is
   type Lifetime is new Ada.Finalization.Limited_Controlled with null record;
   Object : Lifetime;
   pragma Unreferenced (Object);
begin
   null;
end No_Finalization;
