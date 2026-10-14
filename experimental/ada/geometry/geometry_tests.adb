with Ada.Assertions;
with Ada.Text_IO;
with TOP_Experimental.Geometry;

procedure Geometry_Tests is
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
      --  Raw-DAG coverage: Python refuses Right (Root, Left) by C3.
      Check (Graph, Shape, [Root, Left, Right, Shape]);
      Check (Graph, Left, [Root, Left]);
   end Overlapping_Bases;

   procedure Duplicate_Bases is
      Graph : Registry;
      Root  : constant Tag_Id := Add_Tag (Graph);
      Shape : constant Tag_Id := Add_Tag (Graph, List ([Root, Root]));
   begin
      --  Raw-DAG coverage: Python refuses repeated direct Bases.
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

   procedure Exhaustive_Forms is
      subtype Position is Positive range 1 .. 5;
      type Positions is array (Position) of Position;
      type Declaration is record
         Length : Natural range 0 .. 4 := 0;
         Bases  : Positions := [others => 1];
      end record;
      Model : array (Position) of Declaration;
      Graphs_Checked : Natural := 0;
      Forms_Checked : Natural := 0;
      Python_Graphs : Natural := 0;
      Experimental_Only_Graphs : Natural := 0;
      Python_Forms : Natural := 0;

      --  Admission classifier only: C3 does not define the expected Form,
      --  filter the enumeration, or change the experimental Registry policy.
      function Python_Admissible return Boolean is
         type Linearization is record
            Length : Natural range 0 .. 5 := 0;
            Order : Positions := [others => 1];
         end record;
         MRO : array (Position) of Linearization;
      begin
         for Current in Position loop
            declare
               Sequences : array (Position) of Linearization;
               Heads : array (Position) of Positive := [others => 1];
               Count : constant Positive := Model (Current).Length + 1;
            begin
               for Slot in 1 .. Model (Current).Length loop
                  Sequences (Slot) := MRO (Model (Current).Bases (Slot));
               end loop;
               Sequences (Count).Length := Model (Current).Length;
               Sequences (Count).Order := Model (Current).Bases;
               MRO (Current).Length := 1;
               MRO (Current).Order (1) := Current;

               loop
                  declare
                     Active : Boolean := False;
                     Selected : Boolean := False;
                  begin
                     for Slot in 1 .. Count loop
                        if Heads (Slot) <= Sequences (Slot).Length then
                           Active := True;
                           declare
                              Candidate : constant Position :=
                                Sequences (Slot).Order (Heads (Slot));
                              Eligible : Boolean := True;
                           begin
                              --  C3 chooses a head absent from every tail.
                              for Other in 1 .. Count loop
                                 for Tail in Heads (Other) + 1
                                   .. Sequences (Other).Length
                                 loop
                                    if Sequences (Other).Order (Tail) = Candidate
                                    then
                                       Eligible := False;
                                    end if;
                                 end loop;
                              end loop;
                              if Eligible then
                                 MRO (Current).Length := MRO (Current).Length + 1;
                                 MRO (Current).Order (MRO (Current).Length) :=
                                   Candidate;
                                 for Other in 1 .. Count loop
                                    if Heads (Other) <= Sequences (Other).Length
                                      and then Sequences (Other).Order
                                        (Heads (Other)) = Candidate
                                    then
                                       Heads (Other) := Heads (Other) + 1;
                                    end if;
                                 end loop;
                                 Selected := True;
                                 exit;
                              end if;
                           end;
                        end if;
                     end loop;
                     exit when not Active;
                     if not Selected then
                        return False;
                     end if;
                  end;
               end loop;
            end;
         end loop;
         return True;
      end Python_Admissible;

      procedure Check_Admission_Fixtures is
      begin
         Model := [others => (Length => 0, Bases => [others => 1])];
         Model (2) := (Length => 1, Bases => [others => 1]);
         Model (3) := (Length => 2, Bases => [1 => 2, 2 => 1, others => 1]);
         pragma Assert (Python_Admissible, "descendant-first redundant Bases");
         Model (3).Bases (1) := 1;
         Model (3).Bases (2) := 2;
         pragma Assert (not Python_Admissible, "ancestor-first conflicting Bases");
         Model (3).Bases (2) := 1;
         pragma Assert (not Python_Admissible, "repeated direct Bases");

         Model := [others => (Length => 0, Bases => [others => 1])];
         Model (3) := (Length => 2, Bases => [1 => 1, 2 => 2, others => 1]);
         Model (4) := (Length => 2, Bases => [1 => 2, 2 => 1, others => 1]);
         pragma Assert (Python_Admissible, "independent opposing Base orders");
         Model (5) := (Length => 2, Bases => [1 => 3, 2 => 4, others => 1]);
         pragma Assert (not Python_Admissible, "combined opposing Base orders");
      end Check_Admission_Fixtures;

      procedure Check_Graph is
         Graph : Registry;
         Ids : Tag_Array (Position);
         Bases, Expected : Tag_Lists.Vector;
         Order : Positions := [others => 1];
         Length : Natural := 0;
         Visited : array (Position) of Boolean := [others => False];
         Admissible : constant Boolean := Python_Admissible;

         --  A bounded recursive model, independent of the production stack
         --  and marks. It follows integer Base lists, not Registry internals.
         procedure Visit (Current : Position) is
         begin
            for Slot in 1 .. Model (Current).Length loop
               Visit (Model (Current).Bases (Slot));
            end loop;
            if not Visited (Current) then
               Visited (Current) := True;
               Length := Length + 1;
               Order (Length) := Current;
            end if;
         end Visit;
      begin
         if Admissible then
            Python_Graphs := Python_Graphs + 1;
         else
            Experimental_Only_Graphs := Experimental_Only_Graphs + 1;
         end if;
         for Current in Position loop
            Bases.Clear;
            for Slot in 1 .. Model (Current).Length loop
               Bases.Append (Ids (Model (Current).Bases (Slot)));
            end loop;
            Ids (Current) := Add_Tag (Graph, Bases);
         end loop;

         for Root in Position loop
            Length := 0;
            Visited := [others => False];
            Visit (Root);
            Expected.Clear;
            for Slot in 1 .. Length loop
               Expected.Append (Ids (Order (Slot)));
            end loop;
            pragma Assert
              (Form (Graph, Ids (Root)) = Expected,
               "Form oracle mismatch at graph" & Natural'Image (Graphs_Checked + 1)
               & " root" & Position'Image (Root));
            Forms_Checked := Forms_Checked + 1;
            if Admissible then
               Python_Forms := Python_Forms + 1;
            end if;
         end loop;
         Graphs_Checked := Graphs_Checked + 1;
      end Check_Graph;

      procedure Enumerate (Current : Position) is
         Used : array (Position) of Boolean := [others => False];

         --  Each prefix is one ordered subset of the earlier positions.
         --  Stopping here emits it; extending with an unused Base emits the
         --  longer subsets without repetitions or randomized sampling.
         procedure Extend is
         begin
            if Current = Position'Last then
               Check_Graph;
            else
               Enumerate (Current + 1);
            end if;

            for Base in 1 .. Current - 1 loop
               if not Used (Base) then
                  Used (Base) := True;
                  Model (Current).Length := Model (Current).Length + 1;
                  Model (Current).Bases (Model (Current).Length) := Base;
                  Extend;
                  Model (Current).Length := Model (Current).Length - 1;
                  Used (Base) := False;
               end if;
            end loop;
         end Extend;
      begin
         Model (Current).Length := 0;
         Extend;
      end Enumerate;
   begin
      Check_Admission_Fixtures;
      Enumerate (Position'First);
      pragma Assert (Graphs_Checked = 10_400 and Forms_Checked = 52_000);
      pragma Assert (Python_Graphs = 2_422
                     and Experimental_Only_Graphs = 7_978
                     and Python_Forms = 12_110);
      Ada.Text_IO.Put_Line
        ("Abstract DAG Form oracle: 10400 graphs, 52000 Forms passed");
      Ada.Text_IO.Put_Line
        ("Test-only C3 admission: 2422 Python-admissible graphs (12110 Forms),"
         & " 7978 experimental-only graphs");
   end Exhaustive_Forms;
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
   Exhaustive_Forms;
   Ada.Text_IO.Put_Line
     ("Geometry/Form: 10 focused tests passed (including depth 3000)");
end Geometry_Tests;
