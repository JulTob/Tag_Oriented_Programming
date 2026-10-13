--  Provisional experiments, not the Ada TOP language profile.
package TOP_Experimental is
   type Tag_Id is private;
   function "=" (Left, Right : Tag_Id) return Boolean;
private
   type Tag_Id is record
      Owner    : Natural := 0;
      Position : Natural := 0;
   end record;
   function "=" (Left, Right : Tag_Id) return Boolean is
     (Left.Owner = Right.Owner and then Left.Position = Right.Position);
end TOP_Experimental;
