with Ada.Assertions;
with Ada.Finalization;
with Ada.Text_IO;
with System;

procedure Rosen_Probes is
   pragma Assertion_Policy (Check);
   use type System.Address;

   type Event_Kind is
     (Token_End, Extension_End, Dependent_End, Host_Call, Ancestor_Call);
   type Event is record
      Kind : Event_Kind;
      Id : Positive;
   end record;
   Trace : array (1 .. 32) of Event;
   Last : Natural := 0;
   Issued : Natural := 0;
   Cleanups : array (1 .. 8) of Natural := [others => 0];

   procedure Log (Kind : Event_Kind; Id : Positive) is
   begin
      Last := Last + 1;
      Trace (Last) := (Kind, Id);
   end Log;

   function Issue return Positive is
   begin
      Issued := Issued + 1;
      return Issued;
   end Issue;

   procedure Cleanup (Id : Positive) is
   begin
      --  No owner pointer, host callback, address, or extension state is read.
      Cleanups (Id) := Cleanups (Id) + 1;
      Log (Token_End, Id);
   end Cleanup;

   function Position (Kind : Event_Kind; Id : Positive) return Natural is
   begin
      for Index in 1 .. Last loop
         if Trace (Index) = (Kind, Id) then
            return Index;
         end if;
      end loop;
      return 0;
   end Position;

   function Count (Kind : Event_Kind; Id : Positive) return Natural is
      Result : Natural := 0;
   begin
      for Index in 1 .. Last loop
         if Trace (Index) = (Kind, Id) then
            Result := Result + 1;
         end if;
      end loop;
      return Result;
   end Count;

   procedure Show (Label : String; Id : Positive) is
   begin
      Ada.Text_IO.Put (Label & ":");
      for Index in 1 .. Last loop
         if Trace (Index).Id = Id then
            Ada.Text_IO.Put (" " & Event_Kind'Image (Trace (Index).Kind));
         end if;
      end loop;
      Ada.Text_IO.New_Line;
   end Show;

   procedure Check_Assertions is
      Enabled : Boolean := False;
      function Probe return Boolean is (False);
   begin
      begin
         pragma Assert (Probe, "assertion-enabled sentinel");
      exception
         when Ada.Assertions.Assertion_Error => Enabled := True;
      end;
      if not Enabled then
         raise Program_Error with "Rosen probes require enabled assertions";
      end if;
   end Check_Assertions;

   package Ordinary_Carrier is
      type Carrier is abstract tagged limited private;
      function Id (Object : Carrier) return Positive;
   private
      type Lifetime is new Ada.Finalization.Limited_Controlled with record
         Id : Positive := Issue;
      end record;
      overriding procedure Finalize (Object : in out Lifetime);
      type Carrier is abstract tagged limited record
         Token : Lifetime;
      end record;
   end Ordinary_Carrier;
   package body Ordinary_Carrier is
      function Id (Object : Carrier) return Positive is (Object.Token.Id);
      overriding procedure Finalize (Object : in out Lifetime) is
      begin
         Cleanup (Object.Id);
      end Finalize;
   end Ordinary_Carrier;

   package Plain_Rosen is
      type Carrier is abstract tagged limited private;
      function Id (Object : Carrier) return Positive;
      function Self_Address (Object : Carrier) return System.Address;
   private
      type Lifetime (Owner : not null access Carrier) is
        new Ada.Finalization.Limited_Controlled with record
         Id : Natural := 0;
         Live_Address : System.Address := System.Null_Address;
      end record;
      overriding procedure Initialize (Object : in out Lifetime);
      overriding procedure Finalize (Object : in out Lifetime);
      type Carrier is abstract tagged limited record
         Token : Lifetime (Carrier'Access);
      end record;
   end Plain_Rosen;
   package body Plain_Rosen is
      function Id (Object : Carrier) return Positive is (Object.Token.Id);
      function Self_Address (Object : Carrier) return System.Address is
        (Object.Token.Live_Address);
      overriding procedure Initialize (Object : in out Lifetime) is
      begin
         Object.Id := Issue;
         Object.Live_Address := Object.Owner.all'Address;
      end Initialize;
      overriding procedure Finalize (Object : in out Lifetime) is
      begin
         Cleanup (Object.Id);
      end Finalize;
   end Plain_Rosen;

   package Controlled_Rosen is
      type Carrier is abstract new Ada.Finalization.Limited_Controlled
        with private;
      function Id (Object : Carrier) return Positive;
      function Self_Address (Object : Carrier) return System.Address;
      overriding procedure Finalize (Object : in out Carrier);
   private
      type Lifetime (Owner : not null access Carrier) is
        new Ada.Finalization.Limited_Controlled with record
         Id : Natural := 0;
         Live_Address : System.Address := System.Null_Address;
      end record;
      overriding procedure Initialize (Object : in out Lifetime);
      overriding procedure Finalize (Object : in out Lifetime);
      type Carrier is abstract new Ada.Finalization.Limited_Controlled
        with record
         Token : Lifetime (Carrier'Access);
      end record;
   end Controlled_Rosen;
   package body Controlled_Rosen is
      function Id (Object : Carrier) return Positive is (Object.Token.Id);
      function Self_Address (Object : Carrier) return System.Address is
        (Object.Token.Live_Address);
      overriding procedure Finalize (Object : in out Carrier) is
      begin
         Log (Ancestor_Call, Id (Object));
      end Finalize;
      overriding procedure Initialize (Object : in out Lifetime) is
      begin
         Object.Id := Issue;
         Object.Live_Address := Object.Owner.all'Address;
      end Initialize;
      overriding procedure Finalize (Object : in out Lifetime) is
      begin
         Cleanup (Object.Id);
      end Finalize;
   end Controlled_Rosen;

   type Part is new Ada.Finalization.Limited_Controlled with record
      Id : Natural := 0;
   end record;
   overriding procedure Finalize (Object : in out Part);
   overriding procedure Finalize (Object : in out Part) is
   begin
      --  A failed declaration may unwind before the live test assigns its ID.
      if Object.Id /= 0 then
         Log (Extension_End, Object.Id);
      end if;
   end Finalize;

   type Ordinary_Host is new Ordinary_Carrier.Carrier with record
      Extension : Part;
   end record;
   procedure Finalize (Object : in out Ordinary_Host) is
   begin
      Log (Host_Call, Ordinary_Carrier.Id (Ordinary_Carrier.Carrier (Object)));
   end Finalize;

   type Plain_Host is new Plain_Rosen.Carrier with record
      Extension : Part;
   end record;
   procedure Finalize (Object : in out Plain_Host) is
   begin
      Log (Host_Call, Plain_Rosen.Id (Plain_Rosen.Carrier (Object)));
   end Finalize;
   function Make return Plain_Host is
   begin
      return Object : Plain_Host do
         Object.Extension.Id := Plain_Rosen.Id (Plain_Rosen.Carrier (Object));
         pragma Assert (Plain_Rosen.Self_Address (Plain_Rosen.Carrier (Object))
                        = Object'Address);
      end return;
   end Make;

   type Controlled_Host is new Controlled_Rosen.Carrier with record
      Extension : Part;
   end record;
   overriding procedure Finalize (Object : in out Controlled_Host);
   overriding procedure Finalize (Object : in out Controlled_Host) is
   begin
      Log (Host_Call, Controlled_Rosen.Id (Controlled_Rosen.Carrier (Object)));
   end Finalize;

   type Dependent_Host is tagged;
   type Dependent_Part (Owner : not null access Dependent_Host) is
     new Ada.Finalization.Limited_Controlled with record
      Id : Natural := 0;
   end record;
   overriding procedure Finalize (Object : in out Dependent_Part);
   type Dependent_Host is new Controlled_Rosen.Carrier with record
      Extension : Part;
      Dependent : Dependent_Part (Dependent_Host'Access);
   end record;
   overriding procedure Finalize (Object : in out Dependent_Host);
   overriding procedure Finalize (Object : in out Dependent_Part) is
   begin
      if Object.Id /= 0 then
         Log (Dependent_End, Object.Id);
      end if;
   end Finalize;
   overriding procedure Finalize (Object : in out Dependent_Host) is
   begin
      Log (Host_Call, Controlled_Rosen.Id (Controlled_Rosen.Carrier (Object)));
   end Finalize;

   Ordinary_Id, Plain_Id, Built_Id, Controlled_Id, Dependent_Id : Positive;
   Before_End : Natural;
begin
   Check_Assertions;
   declare
      Object : Ordinary_Host;
   begin
      Ordinary_Id := Ordinary_Carrier.Id (Ordinary_Carrier.Carrier (Object));
      Object.Extension.Id := Ordinary_Id;
      Finalize (Object);
      Finalize (Object);
      pragma Assert (Cleanups (Ordinary_Id) = 0
                     and Position (Extension_End, Ordinary_Id) = 0);
   end;
   pragma Assert (Cleanups (Ordinary_Id) = 1
                  and Count (Extension_End, Ordinary_Id) = 1
                  and Count (Host_Call, Ordinary_Id) = 2);
   Show ("ordinary component order (observation only)", Ordinary_Id);

   declare
      Object : Plain_Host;
      Built : Plain_Host := Make;
   begin
      Plain_Id := Plain_Rosen.Id (Plain_Rosen.Carrier (Object));
      Built_Id := Plain_Rosen.Id (Plain_Rosen.Carrier (Built));
      Object.Extension.Id := Plain_Id;
      pragma Assert (Plain_Id /= Built_Id and Object'Address /= Built'Address);
      pragma Assert (Plain_Rosen.Self_Address (Plain_Rosen.Carrier (Object))
                       = Object'Address
                     and Plain_Rosen.Self_Address (Plain_Rosen.Carrier (Built))
                       = Built'Address);
      Finalize (Object);
      Finalize (Object);
      pragma Assert (Cleanups (Plain_Id) = 0 and Cleanups (Built_Id) = 0
                     and Position (Extension_End, Plain_Id) = 0);
   end;
   for Id in Plain_Id .. Built_Id loop
      pragma Assert (Cleanups (Id) = 1
                     and Count (Extension_End, Id) = 1
                     and Position (Token_End, Id) < Position (Extension_End, Id));
      Show ("Rosen token before ordinary extension", Id);
   end loop;
   pragma Assert (Count (Host_Call, Plain_Id) = 2
                  and Count (Host_Call, Built_Id) = 0);

   declare
      Object : Controlled_Host;
   begin
      Controlled_Id := Controlled_Rosen.Id (Controlled_Rosen.Carrier (Object));
      Object.Extension.Id := Controlled_Id;
      pragma Assert
        (Controlled_Rosen.Self_Address (Controlled_Rosen.Carrier (Object))
           = Object'Address);
      Finalize (Object);
      Finalize (Object);
      Controlled_Rosen.Finalize (Controlled_Rosen.Carrier (Object));
      Controlled_Rosen.Finalize (Controlled_Rosen.Carrier (Object));
      pragma Assert (Cleanups (Controlled_Id) = 0
                     and Position (Extension_End, Controlled_Id) = 0);
      Before_End := Last;
   end;
   pragma Assert (Trace (Before_End + 1) = (Host_Call, Controlled_Id));
   pragma Assert (Cleanups (Controlled_Id) = 1
                  and Count (Host_Call, Controlled_Id) = 3
                  and Count (Ancestor_Call, Controlled_Id) = 2
                  and Count (Extension_End, Controlled_Id) = 1
                  and Position (Token_End, Controlled_Id)
                    < Position (Extension_End, Controlled_Id));
   Show ("explicit calls do not finalize the private token", Controlled_Id);

   declare
      Object : Dependent_Host;
   begin
      Dependent_Id := Controlled_Rosen.Id (Controlled_Rosen.Carrier (Object));
      Object.Extension.Id := Dependent_Id;
      Object.Dependent.Id := Dependent_Id;
      pragma Assert
        (Controlled_Rosen.Self_Address (Controlled_Rosen.Carrier (Object))
           = Object'Address);
      Before_End := Last;
   end;
   pragma Assert (Trace (Before_End + 1) = (Host_Call, Dependent_Id));
   pragma Assert (Cleanups (Dependent_Id) = 1
                  and Count (Host_Call, Dependent_Id) = 1
                  and Count (Dependent_End, Dependent_Id) = 1
                  and Count (Extension_End, Dependent_Id) = 1
                  and Position (Dependent_End, Dependent_Id)
                    < Position (Token_End, Dependent_Id)
                  and Position (Token_End, Dependent_Id)
                    < Position (Extension_End, Dependent_Id));
   Show ("dependent extension before parent Rosen token", Dependent_Id);
   pragma Assert (Issued = 5);
end Rosen_Probes;
