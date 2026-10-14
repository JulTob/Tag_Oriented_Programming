with Ada.Finalization;

--  Experimental identity groundwork: no Tagging or Field API is defined here.
package Top_Targets is
   type Target is abstract new Ada.Finalization.Limited_Controlled with private;
   type Identity_Handle is private;

   Identity_Exhausted : exception;

   function Identity (Object : Target'Class) return Identity_Handle;
   function Is_Present (Handle : Identity_Handle) return Boolean;
   function Is_Live (Handle : Identity_Handle) return Boolean;
   function "=" (Left, Right : Identity_Handle) return Boolean;

private
   type Identity_Id is range 0 .. Long_Long_Integer'Last;
   type Identity_State is record
      Id : Identity_Id;
      Live : Boolean;
      References : Positive;
   end record;
   type Identity_Access is access Identity_State;

   type Lifetime_Token is new Ada.Finalization.Limited_Controlled with record
      State : Identity_Access := null;
   end record;
   overriding procedure Initialize (Object : in out Lifetime_Token);
   overriding procedure Finalize (Object : in out Lifetime_Token);

   type Target is abstract new Ada.Finalization.Limited_Controlled with record
      Token : Lifetime_Token;
   end record;

   type Identity_Handle is new Ada.Finalization.Controlled with record
      State : Identity_Access := null;
   end record;
   overriding procedure Adjust (Object : in out Identity_Handle);
   overriding procedure Finalize (Object : in out Identity_Handle);
end Top_Targets;
