with Ada.Containers.Vectors;

package TOP_Experimental.Geometry is
   pragma Elaborate_Body;
   --  IDs are opaque and belong to one Registry. A Registry owns its Tags;
   --  it cannot be copied. This experiment has no Targets or Fields.
   subtype Tag_Id is TOP_Experimental.Tag_Id;
   package Tag_Lists is new Ada.Containers.Vectors
     (Index_Type => Positive, Element_Type => Tag_Id,
      "=" => TOP_Experimental."=");
   type Registry is limited private;

   Invalid_Tag : exception;

   --  Bases must already exist in this Registry. Their order is preserved.
   --  No operation changes a declared Tag's Bases, so cycles cannot form.
   function Add_Tag
     (Graph : in out Registry;
      Bases : Tag_Lists.Vector := Tag_Lists.Empty_Vector) return Tag_Id;

   function Form (Graph : Registry; Root : Tag_Id) return Tag_Lists.Vector;

private
   type Node is record
      Bases : Tag_Lists.Vector;
   end record;
   package Nodes is new Ada.Containers.Vectors
     (Index_Type => Positive, Element_Type => Node);

   function New_Owner return Positive;
   type Registry is limited record
      Owner : Positive := New_Owner;
      Tags  : Nodes.Vector;
   end record;
end TOP_Experimental.Geometry;
