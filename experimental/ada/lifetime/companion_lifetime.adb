with Ada.Assertions;
with Ada.Finalization;
with Ada.Text_IO;
with Ada.Unchecked_Deallocation;

procedure Companion_Lifetime is
   pragma Assertion_Policy (Check);
   Live_Hosts : Natural := 0;
   Host_Finalizations : Natural := 0;
   Companion_Finalizations : Natural := 0;
   Expected_Host_Alive : Boolean := True;

   procedure Check_Assertions is
      Enabled : Boolean := False;
      function Probe return Boolean is
      begin
         return False;
      end Probe;
   begin
      begin
         pragma Assert (Probe, "assertion-enabled sentinel");
      exception
         when Ada.Assertions.Assertion_Error => Enabled := True;
      end;
      if not Enabled then
         raise Program_Error with "Companion probes require enabled assertions";
      end if;
   end Check_Assertions;

   type Host is new Ada.Finalization.Limited_Controlled with null record;
   overriding procedure Initialize (Object : in out Host);
   overriding procedure Finalize (Object : in out Host);
   overriding procedure Initialize (Object : in out Host) is
      pragma Unreferenced (Object);
   begin
      Live_Hosts := Live_Hosts + 1;
   end Initialize;
   overriding procedure Finalize (Object : in out Host) is
      pragma Unreferenced (Object);
   begin
      Live_Hosts := Live_Hosts - 1;
      Host_Finalizations := Host_Finalizations + 1;
   end Finalize;

   type Companion (Target : not null access Host) is
     new Ada.Finalization.Limited_Controlled with null record;
   overriding procedure Finalize (Object : in out Companion);
   overriding procedure Finalize (Object : in out Companion) is
      pragma Unreferenced (Object);
   begin
      --  External counters only: the heap case must never read Target.all.
      pragma Assert ((Live_Hosts = 1) = Expected_Host_Alive);
      Companion_Finalizations := Companion_Finalizations + 1;
   end Finalize;

   type Host_Access is access all Host;
   procedure Free is new Ada.Unchecked_Deallocation (Host, Host_Access);
begin
   Check_Assertions;
   declare
      Target : aliased Host;
      Guard : Companion (Target'Access);
      pragma Unreferenced (Guard);
   begin
      pragma Assert (Live_Hosts = 1 and Companion_Finalizations = 0);
   end;
   pragma Assert (Live_Hosts = 0 and Host_Finalizations = 1
                  and Companion_Finalizations = 1);
   Ada.Text_IO.Put_Line ("shared scope: companion ended before Target");

   declare
      Target : aliased Host;
   begin
      declare
         Guard : Companion (Target'Access);
         pragma Unreferenced (Guard);
      begin
         pragma Assert (Live_Hosts = 1 and Companion_Finalizations = 1);
      end;
      pragma Assert (Live_Hosts = 1 and Host_Finalizations = 1
                     and Companion_Finalizations = 2);
   end;
   pragma Assert (Live_Hosts = 0 and Host_Finalizations = 2);
   Ada.Text_IO.Put_Line ("nested scope: companion ended while Target lived");

   Expected_Host_Alive := False;
   declare
      Target : Host_Access := new Host;
      Guard : Companion (Target);
      pragma Unreferenced (Guard);
   begin
      pragma Assert (Live_Hosts = 1);
      Free (Target);
      pragma Assert (Target = null and Live_Hosts = 0
                     and Host_Finalizations = 3 and Companion_Finalizations = 2);
   end;
   pragma Assert (Live_Hosts = 0 and Companion_Finalizations = 3);
   Ada.Text_IO.Put_Line ("explicit Free: Target ended before companion; no dereference");
end Companion_Lifetime;
