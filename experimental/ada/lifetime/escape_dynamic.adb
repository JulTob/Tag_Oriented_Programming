with Ada.Assertions;
with Ada.Exceptions;
with Ada.Finalization;
with Ada.Strings.Fixed;
with Ada.Text_IO;

procedure Escape_Dynamic is
   pragma Assertion_Policy (Check);
   Enabled : Boolean := False;
   Rejected : Boolean := False;
   function Probe return Boolean is
   begin
      return False;
   end Probe;

   type Host is tagged null record;
   type Companion (Target : not null access Host) is
     new Ada.Finalization.Limited_Controlled with null record;
   type Companion_Access is access Companion;
   function Attach (Target : not null access Host) return Companion_Access is
   begin
      return new Companion (Target);
   end Attach;
   Escaped : Companion_Access;
   pragma Unreferenced (Escaped);
begin
   begin
      pragma Assert (Probe, "assertion-enabled sentinel");
   exception
      when Ada.Assertions.Assertion_Error => Enabled := True;
   end;
   if not Enabled then
      raise Program_Error with "Accessibility probe requires enabled assertions";
   end if;

   begin
      declare
         Target : aliased Host;
      begin
         Escaped := Attach (Target'Access);
      end;
   exception
      when Failure : Program_Error =>
         if Ada.Strings.Fixed.Index
           (Ada.Exceptions.Exception_Message (Failure),
            "accessibility check failed") = 0
         then
            raise;
         end if;
         Rejected := True;
   end;
   pragma Assert (Rejected, "escaped local Target was accepted");
   Ada.Text_IO.Put_Line ("dynamic escape: Program_Error accessibility rejection");
end Escape_Dynamic;
