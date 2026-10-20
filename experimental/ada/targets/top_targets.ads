with Ada.Finalization;
with Ada.Streams;

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

   --  Default streaming would copy the private State access value without
   --  retaining it. A handle has no persistent or cross-process meaning.
   procedure Refuse_Read
     (Stream : not null access Ada.Streams.Root_Stream_Type'Class;
      Item : out Identity_Handle);
   procedure Refuse_Write
     (Stream : not null access Ada.Streams.Root_Stream_Type'Class;
      Item : Identity_Handle);
   function Refuse_Input
     (Stream : not null access Ada.Streams.Root_Stream_Type'Class)
      return Identity_Handle;
   procedure Refuse_Output
     (Stream : not null access Ada.Streams.Root_Stream_Type'Class;
      Item : Identity_Handle);
   for Identity_Handle'Read use Refuse_Read;
   for Identity_Handle'Write use Refuse_Write;
   for Identity_Handle'Input use Refuse_Input;
   for Identity_Handle'Output use Refuse_Output;
end Top_Targets;
