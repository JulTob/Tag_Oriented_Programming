with Ada.Finalization;

--  Expected compile refusal: a limited companion cannot be assignment-copied.
procedure Limited_Copy is
   type Host is tagged null record;
   type Companion (Target : not null access Host) is
     new Ada.Finalization.Limited_Controlled with null record;
   Target : aliased Host;
   First : Companion (Target'Access);
   Second : Companion (Target'Access);
begin
   Second := First;
end Limited_Copy;
