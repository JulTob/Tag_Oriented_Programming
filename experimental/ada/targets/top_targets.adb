with Ada.Unchecked_Deallocation;

package body Top_Targets is
   Last_Issued : Identity_Id := 0;

   procedure Free is new Ada.Unchecked_Deallocation
     (Identity_State, Identity_Access);

   function Issue return Identity_Id is
   begin
      if Last_Issued = Identity_Id'Last then
         raise Identity_Exhausted with "Target identity space exhausted";
      end if;
      Last_Issued := Last_Issued + 1;
      return Last_Issued;
   end Issue;

   procedure Retain (State : not null Identity_Access) is
   begin
      if State.References = Positive'Last then
         raise Storage_Error with "Target identity handle count exhausted";
      end if;
      State.References := State.References + 1;
   end Retain;

   procedure Release (State : in out Identity_Access) is
      Previous : Identity_Access := State;
   begin
      --  Clear the owner before release; repeated finalization is harmless.
      State := null;
      if Previous /= null then
         if Previous.References = 1 then
            Free (Previous);
         else
            Previous.References := Previous.References - 1;
         end if;
      end if;
   end Release;

   overriding procedure Initialize (Object : in out Lifetime_Token) is
   begin
      --  The token owns only metadata, not a host pointer or a host address.
      Object.State := new Identity_State'
        (Id => Issue, Live => True, References => 1);
   end Initialize;

   overriding procedure Finalize (Object : in out Lifetime_Token) is
   begin
      if Object.State /= null then
         Object.State.Live := False;
         Release (Object.State);
      end if;
   end Finalize;

   overriding procedure Adjust (Object : in out Identity_Handle) is
      Copied : constant Identity_Access := Object.State;
   begin
      --  A failed retain must not leave an unowned copy that releases its source.
      Object.State := null;
      if Copied /= null then
         Retain (Copied);
         Object.State := Copied;
      end if;
   end Adjust;

   overriding procedure Finalize (Object : in out Identity_Handle) is
   begin
      Release (Object.State);
   end Finalize;

   function Identity (Object : Target'Class) return Identity_Handle is
   begin
      return Result : Identity_Handle do
         Retain (Object.Token.State);
         Result.State := Object.Token.State;
      end return;
   end Identity;

   function Is_Present (Handle : Identity_Handle) return Boolean is
     (Handle.State /= null);

   function Is_Live (Handle : Identity_Handle) return Boolean is
     (Handle.State /= null and then Handle.State.Live);

   function "=" (Left, Right : Identity_Handle) return Boolean is
   begin
      if Left.State = null or else Right.State = null then
         return Left.State = Right.State;
      end if;
      return Left.State.Id = Right.State.Id;
   end "=";

   procedure Refuse_Read
     (Stream : not null access Ada.Streams.Root_Stream_Type'Class;
      Item : out Identity_Handle) is
      pragma Unreferenced (Stream, Item);
   begin
      raise Program_Error with "Target identity handles cannot be streamed";
   end Refuse_Read;

   procedure Refuse_Write
     (Stream : not null access Ada.Streams.Root_Stream_Type'Class;
      Item : Identity_Handle) is
      pragma Unreferenced (Stream, Item);
   begin
      raise Program_Error with "Target identity handles cannot be streamed";
   end Refuse_Write;

   function Refuse_Input
     (Stream : not null access Ada.Streams.Root_Stream_Type'Class)
      return Identity_Handle is
      pragma Unreferenced (Stream);
   begin
      return (raise Program_Error with
        "Target identity handles cannot be streamed");
   end Refuse_Input;

   procedure Refuse_Output
     (Stream : not null access Ada.Streams.Root_Stream_Type'Class;
      Item : Identity_Handle) is
      pragma Unreferenced (Stream, Item);
   begin
      raise Program_Error with "Target identity handles cannot be streamed";
   end Refuse_Output;
end Top_Targets;
