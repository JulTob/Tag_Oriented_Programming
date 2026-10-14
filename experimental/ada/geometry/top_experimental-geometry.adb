with Ada.Containers.Hashed_Sets;

package body TOP_Experimental.Geometry is
   use type Ada.Containers.Count_Type;

   Last_Owner : Natural := 0;

   function New_Owner return Positive is
   begin
      --  Exhaustion raises Constraint_Error rather than recycling identity.
      --  Registry creation is single-threaded in this provisional experiment.
      Last_Owner := Last_Owner + 1;
      return Last_Owner;
   end New_Owner;

   procedure Validate (Graph : Registry; Id : Tag_Id) is
   begin
      if Id.Owner /= Graph.Owner or else Id.Position = 0
        or else Id.Position > Graph.Tags.Last_Index
      then
         raise Invalid_Tag;
      end if;
   end Validate;

   function Add_Tag
     (Graph : in out Registry;
      Bases : Tag_Lists.Vector := Tag_Lists.Empty_Vector) return Tag_Id
   is
   begin
      for Base of Bases loop
         Validate (Graph, Base);
      end loop;
      Graph.Tags.Append (Node'(Bases => Bases));
      return (Owner => Graph.Owner, Position => Graph.Tags.Last_Index);
   end Add_Tag;

   type Frame is record
      Position  : Positive;
      Next_Base : Ada.Containers.Count_Type := 0;
   end record;
   package Frames is new Ada.Containers.Vectors
     (Index_Type => Positive, Element_Type => Frame);
   function Hash (Position : Positive) return Ada.Containers.Hash_Type is
     (Ada.Containers.Hash_Type (Position));
   package Marks is new Ada.Containers.Hashed_Sets
     (Element_Type => Positive, Hash => Hash, Equivalent_Elements => "=");

   function Form (Graph : Registry; Root : Tag_Id) return Tag_Lists.Vector is
      Result : Tag_Lists.Vector;
      Stack  : Frames.Vector;
      Seen   : Marks.Set;
   begin
      Validate (Graph, Root);
      Seen.Insert (Root.Position);
      Stack.Append (Frame'(Position => Root.Position, Next_Base => 0));

      while not Stack.Is_Empty loop
         declare
            Current : Frame := Stack.Last_Element;
         begin
            if Current.Next_Base < Graph.Tags (Current.Position).Bases.Length then
               Current.Next_Base := Current.Next_Base + 1;
               Stack.Replace_Element (Stack.Last_Index, Current);
               declare
                  Base : constant Tag_Id := Graph.Tags (Current.Position).Bases
                    (Positive (Current.Next_Base));
               begin
                  if not Seen.Contains (Base.Position) then
                     Seen.Insert (Base.Position);
                     Stack.Append
                       (Frame'(Position => Base.Position, Next_Base => 0));
                  end if;
               end;
            else
               Result.Append
                 (Tag_Id'(Owner => Graph.Owner, Position => Current.Position));
               Stack.Delete_Last;
            end if;
         end;
      end loop;
      return Result;
   end Form;
end TOP_Experimental.Geometry;
