with Ada.Finalization;
#if not TokenAccess then
with System;
#end if;

--  An ordinary client outside the fixture package may use its public API,
--  but cannot name its private lifetime component or cleanup procedure.
procedure Private_Cleanup is
   package Fixture is
      type Carrier is tagged limited private;
      function Identity (Object : Carrier) return Positive;
   private
      type Lifetime is new Ada.Finalization.Limited_Controlled with record
         Id : Positive := 1;
      end record;
      overriding procedure Finalize (Object : in out Lifetime);
      type Carrier is tagged limited record
         Token : Lifetime;
      end record;
   end Fixture;
   package body Fixture is
      function Identity (Object : Carrier) return Positive is (Object.Token.Id);
      overriding procedure Finalize (Object : in out Lifetime) is
         pragma Unreferenced (Object);
      begin
         null;
      end Finalize;
   end Fixture;

   Object : Fixture.Carrier;
#if not TokenAccess then
   pragma Unreferenced (Object);
#end if;
begin
#if TokenAccess then
#if Illegal then
   pragma Assert (Object.Token.Id = 1);
#else
   pragma Assert (Fixture.Identity (Object) = 1);
#end if;
#else
   declare
#if Illegal then
      Callback_Address : constant System.Address := Fixture.Finalize'Address;
#else
      Callback_Address : constant System.Address := Fixture.Identity'Address;
#end if;
      pragma Unreferenced (Callback_Address);
   begin
      null;
   end;
#end if;
end Private_Cleanup;
