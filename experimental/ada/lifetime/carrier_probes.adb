with Ada.Assertions;
with Ada.Exceptions;
with Ada.Finalization;
with Ada.Text_IO;
with Ada.Unchecked_Deallocation;

procedure Carrier_Probes is
   pragma Assertion_Policy (Check);
   Parent_Cleanups : Natural := 0;
   Parent_Host_Finalizations : Natural := 0;
   Plain_Component_Cleanups : Natural := 0;
   Plain_Host_Finalizations : Natural := 0;
   Controlled_Component_Cleanups : Natural := 0;
   Controlled_Parent_Finalizations : Natural := 0;
   Controlled_Host_Finalizations : Natural := 0;
   Host_Failure : exception;

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
         raise Program_Error with "Lifetime probes require enabled assertions";
      end if;
   end Check_Assertions;

   package Parent_Carrier is
      type Carrier is abstract new Ada.Finalization.Limited_Controlled
        with null record;
      overriding procedure Finalize (Object : in out Carrier);
   end Parent_Carrier;
   package body Parent_Carrier is
      overriding procedure Finalize (Object : in out Carrier) is
         pragma Unreferenced (Object);
      begin
         Parent_Cleanups := Parent_Cleanups + 1;
      end Finalize;
   end Parent_Carrier;

   type Parent_Host is new Parent_Carrier.Carrier with null record;
   overriding procedure Finalize (Object : in out Parent_Host);
   overriding procedure Finalize (Object : in out Parent_Host) is
      pragma Unreferenced (Object);
   begin
      Parent_Host_Finalizations := Parent_Host_Finalizations + 1;
   end Finalize;

   type Calling_Host is new Parent_Carrier.Carrier with null record;
   overriding procedure Finalize (Object : in out Calling_Host);
   overriding procedure Finalize (Object : in out Calling_Host) is
   begin
      Parent_Host_Finalizations := Parent_Host_Finalizations + 1;
      Parent_Carrier.Finalize (Parent_Carrier.Carrier (Object));
   end Finalize;

   package Plain_Contained is
      type Carrier is abstract tagged limited private;
   private
      type Lifetime is new Ada.Finalization.Limited_Controlled with null record;
      overriding procedure Finalize (Object : in out Lifetime);
      type Carrier is abstract tagged limited record
         Token : Lifetime;
      end record;
   end Plain_Contained;
   package body Plain_Contained is
      overriding procedure Finalize (Object : in out Lifetime) is
         pragma Unreferenced (Object);
      begin
         Plain_Component_Cleanups := Plain_Component_Cleanups + 1;
      end Finalize;
   end Plain_Contained;

   package Plain_Hosts is
      type Host is new Plain_Contained.Carrier with null record;
      procedure Finalize (Object : in out Host);
   end Plain_Hosts;
   package body Plain_Hosts is
      procedure Finalize (Object : in out Host) is
         pragma Unreferenced (Object);
      begin
         Plain_Host_Finalizations := Plain_Host_Finalizations + 1;
      end Finalize;
   end Plain_Hosts;

   package Controlled_Contained is
      type Carrier is abstract new Ada.Finalization.Limited_Controlled
        with private;
      overriding procedure Finalize (Object : in out Carrier);
   private
      type Lifetime is new Ada.Finalization.Limited_Controlled with null record;
      overriding procedure Finalize (Object : in out Lifetime);
      type Carrier is abstract new Ada.Finalization.Limited_Controlled
        with record
         Token : Lifetime;
      end record;
   end Controlled_Contained;
   package body Controlled_Contained is
      overriding procedure Finalize (Object : in out Carrier) is
         pragma Unreferenced (Object);
      begin
         Controlled_Parent_Finalizations := Controlled_Parent_Finalizations + 1;
      end Finalize;
      overriding procedure Finalize (Object : in out Lifetime) is
         pragma Unreferenced (Object);
      begin
         Controlled_Component_Cleanups := Controlled_Component_Cleanups + 1;
      end Finalize;
   end Controlled_Contained;

   type Controlled_Host is new Controlled_Contained.Carrier with null record;
   overriding procedure Finalize (Object : in out Controlled_Host);
   overriding procedure Finalize (Object : in out Controlled_Host) is
      pragma Unreferenced (Object);
   begin
      Controlled_Host_Finalizations := Controlled_Host_Finalizations + 1;
   end Finalize;

   type Raising_Host is new Controlled_Contained.Carrier with null record;
   overriding procedure Finalize (Object : in out Raising_Host);
   overriding procedure Finalize (Object : in out Raising_Host) is
      pragma Unreferenced (Object);
   begin
      Controlled_Host_Finalizations := Controlled_Host_Finalizations + 1;
      raise Host_Failure;
   end Finalize;

   type Host_Access is access Controlled_Host;
   procedure Free is new Ada.Unchecked_Deallocation (Controlled_Host, Host_Access);
begin
   Check_Assertions;
   declare
      Object : Parent_Host;
      pragma Unreferenced (Object);
   begin
      null;
   end;
   pragma Assert (Parent_Host_Finalizations = 1 and Parent_Cleanups = 0);
   Ada.Text_IO.Put_Line ("parent Finalize omitted: host=1 cleanup=0");

   declare
      Object : Calling_Host;
      pragma Unreferenced (Object);
   begin
      null;
   end;
   pragma Assert (Parent_Host_Finalizations = 2 and Parent_Cleanups = 1);
   Ada.Text_IO.Put_Line ("parent Finalize explicitly called: cleanup=1");

   declare
      Object : Plain_Hosts.Host;
      pragma Unreferenced (Object);
   begin
      null;
   end;
   pragma Assert (Plain_Host_Finalizations = 0 and Plain_Component_Cleanups = 1);
   Ada.Text_IO.Put_Line ("plain tagged limited carrier: component=1 ordinary Finalize=0");

   declare
      Object : Controlled_Host;
      pragma Unreferenced (Object);
   begin
      null;
   end;
   pragma Assert (Controlled_Host_Finalizations = 1
                  and Controlled_Parent_Finalizations = 0
                  and Controlled_Component_Cleanups = 1);
   Ada.Text_IO.Put_Line ("controlled containing carrier: host=1 parent=0 component=1");

   declare
      Object : Host_Access := new Controlled_Host;
   begin
      Free (Object);
      pragma Assert (Object = null);
   end;
   pragma Assert (Controlled_Host_Finalizations = 2
                  and Controlled_Component_Cleanups = 2);
   Ada.Text_IO.Put_Line ("explicit Free of contained carrier: component finalized");

   declare
      Raised : Boolean := False;
   begin
      begin
         declare
            Object : Raising_Host;
            pragma Unreferenced (Object);
         begin
            null;
         end;
      exception
         when Error : Host_Failure | Program_Error =>
            Raised := True;
            Ada.Text_IO.Put_Line ("raising host Finalize: "
                                 & Ada.Exceptions.Exception_Name (Error));
      end;
      pragma Assert (Raised);
   end;
   pragma Assert (Controlled_Host_Finalizations = 3
                  and Controlled_Parent_Finalizations = 0
                  and Controlled_Component_Cleanups = 3);
   Ada.Text_IO.Put_Line ("raising host Finalize still finalized its private component");
end Carrier_Probes;
