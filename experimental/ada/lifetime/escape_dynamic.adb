with Ada.Assertions;
with Ada.Finalization;
with Ada.Text_IO;
with Ada.Unchecked_Deallocation;

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
   procedure Free is new Ada.Unchecked_Deallocation
     (Companion, Companion_Access);
   function Attach (Target : not null access Host) return Companion_Access is
   begin
      return new Companion (Target);
   end Attach;
   Target : aliased Host;
   Attached : Companion_Access;
begin
   begin
      pragma Assert (Probe, "assertion-enabled sentinel");
   exception
      when Ada.Assertions.Assertion_Error => Enabled := True;
   end;
   if not Enabled then
      raise Program_Error with "Accessibility probe requires enabled assertions";
   end if;

   Attached := Attach (Target'Access);
   pragma Assert (Attached /= null);
   Free (Attached);
   pragma Assert (Attached = null);
   Ada.Text_IO.Put_Line ("shared scope: Attach accepted");

   declare
      Inner_Target : aliased Host;
   begin
      begin
         Attached := Attach (Inner_Target'Access);
      exception
         when Program_Error => Rejected := True;
      end;
      --  If a broken check accepts the call, dispose it before Target ends.
      if not Rejected then
         Free (Attached);
      end if;
   end;
   pragma Assert (Rejected, "escaped local Target was accepted");
   Ada.Text_IO.Put_Line ("dynamic escape: Program_Error accessibility rejection");
end Escape_Dynamic;
