with Ada.Finalization;

--  Expected compile refusal: a checked local Target cannot escape this scope.
procedure Escape_Static is
   type Host is tagged null record;
   type Companion (Target : not null access Host) is
     new Ada.Finalization.Limited_Controlled with null record;
   type Companion_Access is access Companion;
   Escaped : Companion_Access;
   pragma Unreferenced (Escaped);
begin
   declare
      Target : aliased Host;
   begin
      Escaped := new Companion (Target'Access);
   end;
end Escape_Static;
