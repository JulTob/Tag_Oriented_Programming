with Ada.Finalization;

--  Paired compile probe: Illegal changes only the Target's declaration scope.
procedure Escape_Static is
   type Host is tagged null record;
   type Companion (Target : not null access Host) is
     new Ada.Finalization.Limited_Controlled with null record;
   type Companion_Access is access Companion;
#if not Illegal then
   Target : aliased Host;
#end if;
   Escaped : Companion_Access;
   pragma Unreferenced (Escaped);
begin
   declare
#if Illegal then
      Target : aliased Host;
#end if;
   begin
      Escaped := new Companion (Target'Access);
   end;
end Escape_Static;
