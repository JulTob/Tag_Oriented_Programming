with Top_Targets;

--  Legal control constructs a second object; forbidden variant assigns one.
procedure Limited_Target_Copy is
   type Host is new Top_Targets.Target with null record;
   First, Second : Host;
begin
#if Illegal then
   Second := First;
#else
   pragma Assert (Top_Targets.Is_Live (Top_Targets.Identity (First)));
   pragma Assert (Top_Targets.Is_Live (Top_Targets.Identity (Second)));
#end if;
end Limited_Target_Copy;
