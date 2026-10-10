with Ada.Assertions;
with Ada.Text_IO;
with TOP_Experimental.Geometry;

procedure Geometry_Tests is
   pragma Assertion_Policy (Check);
   use TOP_Experimental.Geometry;
   use type TOP_Experimental.Tag_Id;
   use type Tag_Lists.Vector;

   type Tag_Array is array (Positive range <>) of Tag_Id;

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
         raise Program_Error with "Geometry tests require enabled assertions";
      end if;
   end Check_Assertions;

   function List (Ids : Tag_Array) return Tag_Lists.Vector is
      Result : Tag_Lists.Vector;
   begin
      for Id of Ids loop
         Result.Append (Id);
      end loop;
      return Result;
   end List;

   procedure Check (Graph : Registry; Root : Tag_Id; Expected : Tag_Array) is
   begin
      pragma Assert (Form (Graph, Root) = List (Expected));
   end Check;

   procedure Reject (Graph : Registry; Id : Tag_Id) is
   begin
      declare
         Unexpected : constant Tag_Lists.Vector := Form (Graph, Id);
         pragma Unreferenced (Unexpected);
      begin
         raise Program_Error with "Invalid handle was accepted";
      end;
   exception
      when Invalid_Tag => null;
   end Reject;

   procedure Empty_And_Root is
      Graph    : Registry;
      Unissued : Tag_Id;
   begin
      Reject (Graph, Unissued);
      declare
         Root : constant Tag_Id := Add_Tag (Graph);
      begin
         Check (Graph, Root, [Root]);
      end;
   end Empty_And_Root;

   procedure Chain is
      Graph : Registry;
      Root  : constant Tag_Id := Add_Tag (Graph);
      Base  : constant Tag_Id := Add_Tag (Graph, List ([Root]));
      Shape : constant Tag_Id := Add_Tag (Graph, List ([Base]));
   begin
      Check (Graph, Shape, [Root, Base, Shape]);
   end Chain;

   procedure Sibling_Order is
      Graph : Registry;
      First : constant Tag_Id := Add_Tag (Graph);
      Next  : constant Tag_Id := Add_Tag (Graph);
      Shape : constant Tag_Id := Add_Tag (Graph, List ([Next, First]));
   begin
      Check (Graph, Shape, [Next, First, Shape]);
   end Sibling_Order;

   procedure Diamond is
      Graph : Registry;
      Root  : constant Tag_Id := Add_Tag (Graph);
      Left  : constant Tag_Id := Add_Tag (Graph, List ([Root]));
      Right : constant Tag_Id := Add_Tag (Graph, List ([Root]));
      Shape : constant Tag_Id := Add_Tag (Graph, List ([Left, Right]));
   begin
      Check (Graph, Shape, [Root, Left, Right, Shape]);
   end Diamond;

   procedure Overlapping_Bases is
      Graph : Registry;
      Root  : constant Tag_Id := Add_Tag (Graph);
      Left  : constant Tag_Id := Add_Tag (Graph, List ([Root]));
      Right : constant Tag_Id := Add_Tag (Graph, List ([Root, Left]));
      Shape : constant Tag_Id := Add_Tag (Graph, List ([Right, Left, Root]));
   begin
      Check (Graph, Shape, [Root, Left, Right, Shape]);
      Check (Graph, Left, [Root, Left]);
   end Overlapping_Bases;

   procedure Duplicate_Bases is
      Graph : Registry;
      Root  : constant Tag_Id := Add_Tag (Graph);
      Shape : constant Tag_Id := Add_Tag (Graph, List ([Root, Root]));
   begin
      Check (Graph, Shape, [Root, Shape]);
   end Duplicate_Bases;

   procedure Detached_Lists is
      Graph : Registry;
      Root  : constant Tag_Id := Add_Tag (Graph);
      Other : constant Tag_Id := Add_Tag (Graph);
      Bases : Tag_Lists.Vector := List ([Root]);
      Shape : constant Tag_Id := Add_Tag (Graph, Bases);
      Read  : Tag_Lists.Vector := Form (Graph, Shape);
   begin
      Bases.Clear;
      Bases.Append (Other);
      Read.Clear;
      Check (Graph, Shape, [Root, Shape]);
   end Detached_Lists;

   procedure Deep_Chain is
      Graph    : Registry;
      Expected : Tag_Lists.Vector;
      Previous : Tag_Id := Add_Tag (Graph);
   begin
      Expected.Append (Previous);
      for Depth in 2 .. 3_000 loop
         Previous := Add_Tag (Graph, List ([Previous]));
         Expected.Append (Previous);
      end loop;
      pragma Assert (Form (Graph, Previous) = Expected);
   end Deep_Chain;

   procedure Invalid_Handles is
      Graph    : Registry;
      Other    : Registry;
      Unissued : Tag_Id;
      Local    : constant Tag_Id := Add_Tag (Graph);
      Foreign  : constant Tag_Id := Add_Tag (Other);
   begin
      pragma Assert (Local /= Foreign);
      Reject (Graph, Unissued);
      Reject (Graph, Foreign);
      begin
         declare
            Unexpected : constant Tag_Id := Add_Tag
              (Graph, List ([Local, Foreign]));
            pragma Unreferenced (Unexpected);
         begin
            raise Program_Error with "Foreign Base was accepted";
         end;
      exception
         when Invalid_Tag => null;
      end;
      Check (Graph, Local, [Local]);
      declare
         Next : constant Tag_Id := Add_Tag (Graph, List ([Local]));
      begin
         Check (Graph, Next, [Local, Next]);
      end;
   end Invalid_Handles;

   procedure Ended_Registry is
      Expired : Tag_Id;
   begin
      declare
         Old_Graph : Registry;
      begin
         Expired := Add_Tag (Old_Graph);
      end;
      declare
         New_Graph : Registry;
         Root      : constant Tag_Id := Add_Tag (New_Graph);
      begin
         pragma Assert (Expired /= Root);
         Reject (New_Graph, Expired);
      end;
   end Ended_Registry;
begin
   Check_Assertions;
   Empty_And_Root;
   Chain;
   Sibling_Order;
   Diamond;
   Overlapping_Bases;
   Duplicate_Bases;
   Detached_Lists;
   Deep_Chain;
   Invalid_Handles;
   Ended_Registry;
   Ada.Text_IO.Put_Line ("Geometry/Form: 10 tests passed (including depth 3000)");
end Geometry_Tests;
