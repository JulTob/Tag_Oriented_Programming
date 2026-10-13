with Ada.Assertions;
with Ada.Finalization;
with Ada.Text_IO;
with Ada.Unchecked_Deallocation;
with Top_Targets;

procedure Target_Tests is
   use type Top_Targets.Identity_Handle;

   Passed : Natural := 0;
   Initializations : Natural := 0;
   Finalizations : Natural := 0;
   Captured : Top_Targets.Identity_Handle;
   Host_Initialization_Failure : exception;
   Host_Finalization_Failure : exception;

   procedure Pass (Name : String) is
   begin
      Passed := Passed + 1;
      Ada.Text_IO.Put_Line (Name & ": PASS");
   end Pass;

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
         raise Program_Error with "Target tests require enabled assertions";
      end if;
   end Check_Assertions;

   package Host_Types is
      type Host is new Top_Targets.Target with record
         Value : Integer := 0;
      end record;
      overriding procedure Initialize (Object : in out Host);
      overriding procedure Finalize (Object : in out Host);
      function "=" (Left, Right : Host) return Boolean;
   end Host_Types;
   package body Host_Types is
      overriding procedure Initialize (Object : in out Host) is
      begin
         Initializations := Initializations + 1;
         pragma Assert (Top_Targets.Is_Live (Top_Targets.Identity (Object)));
      end Initialize;

      overriding procedure Finalize (Object : in out Host) is
      begin
         --  The outer host runs first. It need not call its ancestor's hook.
         Finalizations := Finalizations + 1;
         pragma Assert (Top_Targets.Is_Live (Top_Targets.Identity (Object)));
      end Finalize;

      function "=" (Left, Right : Host) return Boolean is
        (Left.Value = Right.Value);
   end Host_Types;
   subtype Host is Host_Types.Host;
   use type Host;

   function Make (Value : Integer) return Host is
   begin
      return Result : Host do
         Result.Value := Value;
      end return;
   end Make;

   function Copy (Handle : Top_Targets.Identity_Handle)
     return Top_Targets.Identity_Handle is
   begin
      return Handle;
   end Copy;

   procedure Assign_Handle
     (Into : in out Top_Targets.Identity_Handle;
      Source : Top_Targets.Identity_Handle) is
   begin
      Into := Source;
   end Assign_Handle;

   type Failing_Initialization is new Top_Targets.Target with null record;
   overriding procedure Initialize (Object : in out Failing_Initialization);
   overriding procedure Initialize (Object : in out Failing_Initialization) is
   begin
      Captured := Top_Targets.Identity (Object);
      raise Host_Initialization_Failure;
   end Initialize;

   type Failing_Finalization is new Top_Targets.Target with null record;
   overriding procedure Finalize (Object : in out Failing_Finalization);
   overriding procedure Finalize (Object : in out Failing_Finalization) is
   begin
      pragma Assert (Top_Targets.Is_Live (Top_Targets.Identity (Object)));
      raise Host_Finalization_Failure;
   end Finalize;

   type Host_Access is access Host;
   procedure Free is new Ada.Unchecked_Deallocation (Host, Host_Access);

begin
   Check_Assertions;

   declare
      Empty, Other_Empty : Top_Targets.Identity_Handle;
   begin
      pragma Assert (not Top_Targets.Is_Present (Empty));
      pragma Assert (not Top_Targets.Is_Live (Empty));
      pragma Assert (Empty = Other_Empty);
      Other_Empty := Copy (Empty);
      pragma Assert (not Top_Targets.Is_Present (Other_Empty));
   end;
   Pass ("default and returned empty handles");

   declare
      Left, Right : Host;
      Left_Id : constant Top_Targets.Identity_Handle :=
        Top_Targets.Identity (Left);
      Right_Id : constant Top_Targets.Identity_Handle :=
        Top_Targets.Identity (Right);
   begin
      pragma Assert (Left = Right);
      pragma Assert (Left_Id /= Right_Id);
      pragma Assert (Left_Id = Top_Targets.Identity (Left));
      pragma Assert (Top_Targets.Is_Live (Left_Id));
      pragma Assert (Top_Targets.Is_Live (Right_Id));
   end;
   Pass ("equal hosts have distinct stable identities");

   declare
      Object : Host;
      Original : constant Top_Targets.Identity_Handle :=
        Top_Targets.Identity (Object);
      Assigned : Top_Targets.Identity_Handle;
   begin
      declare
         Copied : constant Top_Targets.Identity_Handle := Copy (Original);
      begin
         Assigned := Copied;
         pragma Assert (Assigned = Original);
      end;
      pragma Assert (Top_Targets.Is_Live (Assigned));
      Assign_Handle (Assigned, Assigned);
      pragma Assert (Assigned = Original);
      pragma Assert (Top_Targets.Is_Live (Assigned));
      declare
         Replacement : Host;
      begin
         Assigned := Top_Targets.Identity (Replacement);
         pragma Assert (Assigned /= Original);
      end;
      pragma Assert (not Top_Targets.Is_Live (Assigned));
      Assigned := Original;
      pragma Assert (Assigned = Original);
      pragma Assert (Top_Targets.Is_Live (Original));
   end;
   Pass ("copied returned self-assigned and overwritten handles");

   declare
      Before : constant Natural := Initializations;
      Object : constant Host := Make (42);
   begin
      pragma Assert (Object.Value = 42);
      pragma Assert (Initializations = Before + 1);
      pragma Assert (Top_Targets.Is_Live (Top_Targets.Identity (Object)));
   end;
   Pass ("limited build-in-place preserves host initialization");

   declare
      Survivor : Top_Targets.Identity_Handle;
      Before : constant Natural := Finalizations;
   begin
      declare
         Object : Host;
      begin
         Survivor := Top_Targets.Identity (Object);
      end;
      pragma Assert (Finalizations = Before + 1);
      pragma Assert (Top_Targets.Is_Present (Survivor));
      pragma Assert (not Top_Targets.Is_Live (Survivor));
      pragma Assert (Copy (Survivor) = Survivor);
   end;
   Pass ("handle observes normal host end without retaining host");

   declare
      Object : Host_Access := new Host;
      Survivor : constant Top_Targets.Identity_Handle :=
        Top_Targets.Identity (Object.all);
      Before : constant Natural := Finalizations;
   begin
      Free (Object);
      pragma Assert (Object = null);
      pragma Assert (Finalizations = Before + 1);
      pragma Assert (not Top_Targets.Is_Live (Survivor));
      Free (Object);
      pragma Assert (Finalizations = Before + 1);
   end;
   Pass ("handle observes explicit host deallocation");

   declare
      Refused : Boolean := False;
   begin
      begin
         declare
            Object : Failing_Initialization;
            pragma Unreferenced (Object);
         begin
            raise Program_Error with "host initialization unexpectedly returned";
         end;
      exception
         when Host_Initialization_Failure => Refused := True;
      end;
      pragma Assert (Refused);
      pragma Assert (Top_Targets.Is_Present (Captured));
      pragma Assert (not Top_Targets.Is_Live (Captured));
   end;
   Pass ("failed outer initialization retires private identity");

   declare
      Survivor : Top_Targets.Identity_Handle;
      Refused : Boolean := False;
   begin
      begin
         declare
            Object : Failing_Finalization;
         begin
            Survivor := Top_Targets.Identity (Object);
         end;
      exception
         --  RM 7.6.1(17.2/1): remaining finalizations, then Program_Error.
         when Program_Error => Refused := True;
      end;
      pragma Assert (Refused);
      pragma Assert (not Top_Targets.Is_Live (Survivor));
   end;
   Pass ("raising outer finalization still retires private identity");

   declare
      Survivor : Top_Targets.Identity_Handle;
      Before : constant Natural := Finalizations;
   begin
      declare
         Object : Host;
      begin
         Survivor := Top_Targets.Identity (Object);
         Host_Types.Finalize (Object);
         Host_Types.Finalize (Object);
         Top_Targets.Finalize (Top_Targets.Target (Object));
         Ada.Finalization.Finalize
           (Ada.Finalization.Limited_Controlled (Object));
         pragma Assert (Top_Targets.Is_Live (Survivor));
         pragma Assert (Finalizations = Before + 2);
      end;
      pragma Assert (Finalizations = Before + 3);
      pragma Assert (not Top_Targets.Is_Live (Survivor));
   end;
   Pass ("explicit host and ancestor hooks do not revoke private identity");

   declare
      Object : Host;
      Original : constant Top_Targets.Identity_Handle :=
        Top_Targets.Identity (Object);
      Test_Exception : exception;
      Raised : Boolean := False;
   begin
      begin
         declare
            During_Exception : constant Top_Targets.Identity_Handle :=
              Copy (Original);
         begin
            pragma Assert (During_Exception = Original);
            raise Test_Exception;
         end;
      exception
         when Test_Exception => Raised := True;
      end;
      pragma Assert (Raised);
      pragma Assert (Top_Targets.Is_Live (Original));
   end;
   Pass ("exception cleanup of handles preserves living host");

   Ada.Text_IO.Put_Line (Natural'Image (Passed) & " Target identity tests passed");
end Target_Tests;
